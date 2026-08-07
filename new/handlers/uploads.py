"""
Real upload handling: front/back ID photos get grouped onto a print-ready
A4 sheet (optionally in bulk, up to MAX_PAIRS_PER_SHEET pairs), and any
photo/screenshot/PDF sent via 'Smart Import' gets OCR'd. This replaces the
old stub handlers that just echoed 'not wired yet'.
"""
import io
import os
import uuid

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from PIL import Image, ImageEnhance, ImageOps

from config import MAX_PAIRS_PER_SHEET, TEMP_DIR, OUTPUT_DIR
from database import db
from handlers.states import GroupFlow, SmartImportFlow
from keyboards import cancel_keyboard, bulk_upload_keyboard, main_menu_keyboard
from messages import t
from processor import IDProcessor
from utils import get_language, get_credits, spend_credit, is_admin, logger

router = Router()
engine = IDProcessor()


async def _download_photo(bot: Bot, file_id: str) -> Image.Image:
    tg_file = await bot.get_file(file_id)
    buf = await bot.download_file(tg_file.file_path)
    return Image.open(io.BytesIO(buf.read())).convert("RGB")


def _basic_enhance(image: Image.Image) -> Image.Image:
    """
    processor.IDProcessor no longer has an auto_enhance() method, so this
    replaces it inline: normalize EXIF orientation, auto-contrast, light
    sharpen. Kept deliberately simple/dependency-light.
    """
    img = ImageOps.exif_transpose(image) or image
    img = img.convert("RGB")
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    return img


def _apply_color_mode(image: Image.Image, color_mode: str) -> Image.Image:
    """processor.IDProcessor no longer applies color_mode itself; do it here."""
    if color_mode == "B&W only":
        return ImageOps.grayscale(image).convert("RGB")
    return image


def _save_to_temp(image: Image.Image) -> str:
    """engine.extract_text() now takes a file path (cv2.imread), not a PIL
    Image, so downloaded photos need to hit disk first."""
    os.makedirs(TEMP_DIR, exist_ok=True)
    path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:12]}.jpg")
    image.convert("RGB").save(path, "JPEG", quality=95)
    return path


# --- Group ID -> A4 -----------------------------------------------------------
@router.message(Command("group"))
@router.callback_query(F.data.in_({"group_start", "bulk_upload"}))
async def start_group_flow(event, state: FSMContext):
    user_id = event.from_user.id
    lang = get_language(user_id)
    target = event.message if isinstance(event, CallbackQuery) else event

    if get_credits(user_id) < 1:
        await target.answer(t(lang, "group_no_credits"))
        if isinstance(event, CallbackQuery):
            await event.answer()
        return

    await state.clear()
    await state.set_state(GroupFlow.waiting_front)
    await state.update_data(pairs=[])
    await target.answer(t(lang, "group_start"), reply_markup=cancel_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(GroupFlow.waiting_front, F.photo)
async def on_front_photo(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(current_front_id=message.photo[-1].file_id)
    await state.set_state(GroupFlow.waiting_back)
    await message.answer(t(lang, "group_got_front"), reply_markup=cancel_keyboard())


@router.message(GroupFlow.waiting_front)
async def on_front_not_photo(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "not_a_photo"), reply_markup=cancel_keyboard())


@router.message(GroupFlow.waiting_back, F.photo)
async def on_back_photo(message: Message, state: FSMContext, bot: Bot):
    lang = get_language(message.from_user.id)
    data = await state.get_data()
    pairs = data.get("pairs", [])
    pairs.append({"front_id": data["current_front_id"], "back_id": message.photo[-1].file_id})
    await state.update_data(pairs=pairs, current_front_id=None)

    if len(pairs) >= MAX_PAIRS_PER_SHEET:
        await message.answer(t(lang, "group_max_pairs", max=MAX_PAIRS_PER_SHEET))
        await _process_and_send(message, message.from_user.id, pairs, state, bot)
        return

    await state.set_state(GroupFlow.collecting_more)
    await message.answer(t(lang, "group_pair_done", n=len(pairs)))
    await message.answer(t(lang, "group_add_another"), reply_markup=bulk_upload_keyboard())


@router.message(GroupFlow.waiting_back)
async def on_back_not_photo(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "not_a_photo"), reply_markup=cancel_keyboard())


@router.message(GroupFlow.collecting_more, F.photo)
async def on_more_front_photo(message: Message, state: FSMContext):
    """In bulk mode, a fresh photo after a completed pair starts the next pair's front."""
    lang = get_language(message.from_user.id)
    await state.update_data(current_front_id=message.photo[-1].file_id)
    await state.set_state(GroupFlow.waiting_back)
    await message.answer(t(lang, "group_got_front"), reply_markup=cancel_keyboard())


@router.callback_query(GroupFlow.collecting_more, F.data == "bulk:done")
async def on_bulk_done(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pairs = data.get("pairs", [])
    await callback.answer()
    await _process_and_send(callback.message, callback.from_user.id, pairs, state, bot)


async def _process_and_send(message: Message, user_id: int, pairs: list[dict], state: FSMContext, bot: Bot):
    lang = get_language(user_id)

    if not pairs:
        await state.clear()
        await message.answer(t(lang, "cancelled"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return

    if not spend_credit(user_id, 1):
        await state.clear()
        await message.answer(t(lang, "group_no_credits"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return

    await message.answer(t(lang, "group_got_back_processing"))

    settings = db.get_settings(user_id)
    # NOTE: engine.build_a4_batch() (the new processor.py) always mirrors the
    # back page and always outputs PDF — it no longer accepts color_mode,
    # mirror_back, or an output path/format. The "Mirror back layout" and
    # output-format Settings toggles are now effectively dead for this job
    # type; only color_mode is still honored, applied here before layout.
    id_pairs = []
    for pair in pairs:
        front = _basic_enhance(await _download_photo(bot, pair["front_id"]))
        back = _basic_enhance(await _download_photo(bot, pair["back_id"]))
        front = _apply_color_mode(front, settings["color_mode"])
        back = _apply_color_mode(back, settings["color_mode"])
        id_pairs.append({"front": front, "back": back})

    try:
        output_path = engine.build_a4_batch(id_pairs, user_id)
    except Exception:
        logger.exception("Failed to build grouped A4 sheet for user %s", user_id)
        db.add_credits(user_id, 1)  # refund on failure
        await state.clear()
        await message.answer(t(lang, "not_wired"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return

    db.log_job(user_id, "group_a4", pairs=len(pairs))
    await message.answer_document(
        FSInputFile(output_path),
        caption=t(lang, "group_done", credits=get_credits(user_id)),
    )
    await state.clear()
    await message.answer(t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))


# --- Smart import (OCR) -------------------------------------------------------
@router.message(Command("smart_import"))
@router.callback_query(F.data == "smart_import")
async def start_smart_import(event, state: FSMContext):
    user_id = event.from_user.id
    lang = get_language(user_id)
    target = event.message if isinstance(event, CallbackQuery) else event

    if get_credits(user_id) < 1:
        await target.answer(t(lang, "group_no_credits"))
        if isinstance(event, CallbackQuery):
            await event.answer()
        return

    await state.clear()
    await state.set_state(SmartImportFlow.waiting_file)
    await target.answer(t(lang, "smart_import_start"), reply_markup=cancel_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(SmartImportFlow.waiting_file, F.photo)
async def on_smart_import_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = get_language(user_id)
    if not spend_credit(user_id, 1):
        await state.clear()
        await message.answer(t(lang, "group_no_credits"))
        return

    image = _basic_enhance(await _download_photo(bot, message.photo[-1].file_id))
    temp_path = _save_to_temp(image)
    try:
        text = engine.extract_text(temp_path)
    except Exception:
        logger.exception("OCR failed for user %s", user_id)
        text = ""
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
    db.log_job(user_id, "smart_import")

    await message.answer(t(lang, "smart_import_result", text=text) if text else t(lang, "smart_import_empty"))
    await state.clear()
    await message.answer(t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))


@router.message(SmartImportFlow.waiting_file, F.document)
async def on_smart_import_document(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = get_language(user_id)
    doc = message.document

    if not spend_credit(user_id, 1):
        await state.clear()
        await message.answer(t(lang, "group_no_credits"))
        return

    tg_file = await bot.get_file(doc.file_id)
    buf = await bot.download_file(tg_file.file_path)
    raw = buf.read()

    if (doc.mime_type or "").endswith("pdf") or (doc.file_name or "").lower().endswith(".pdf"):
        # NOTE: engine.pdf_to_images() (PyMuPDF-rasterize-then-OCR) no longer
        # exists. The new engine.extract_from_pdf() reads the PDF's embedded
        # text layer directly (fitz page.get_text) instead — fast, but it
        # will return an empty string for scanned/photographed PDFs that
        # have no real text layer, since nothing rasterizes+OCRs them anymore.
        os.makedirs(TEMP_DIR, exist_ok=True)
        pdf_path = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex[:12]}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(raw)
        try:
            text = engine.extract_from_pdf(pdf_path)
        except Exception:
            logger.exception("PDF text extraction failed for user %s", user_id)
            text = ""
        finally:
            try:
                os.remove(pdf_path)
            except OSError:
                pass
        await message.answer(t(lang, "smart_import_result", text=text) if text else t(lang, "smart_import_empty"))
    else:
        image = _basic_enhance(Image.open(io.BytesIO(raw)).convert("RGB"))
        temp_path = _save_to_temp(image)
        try:
            text = engine.extract_text(temp_path)
        except Exception:
            logger.exception("OCR failed for user %s", user_id)
            text = ""
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        await message.answer(t(lang, "smart_import_result", text=text) if text else t(lang, "smart_import_empty"))

    db.log_job(user_id, "smart_import")
    await state.clear()
    await message.answer(t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))


# --- Fallback catch-alls (no active flow) -------------------------------------
@router.message(F.photo)
async def on_stray_photo(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(
        f"📷 Got a photo — tell me what to do with it first.",
        reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id)),
    )


@router.message(F.document)
async def on_stray_document(message: Message):
    doc = message.document
    name = doc.file_name or "file"
    await message.answer(
        f"📄 Got a document: {name}\nTap '📷 Smart Import' first, then send it again.",
        reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id)),
    )


@router.message(F.video)
async def on_video_received(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(f"🎥 Video isn't supported — please send a photo, screenshot, or PDF instead.")


@router.message(F.text & ~F.text.startswith("/"))
async def on_plain_text(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(
        f"🤔 {t(lang, 'not_wired')}\n(received: \"{message.text[:80]}\")",
        reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id)),
    )
