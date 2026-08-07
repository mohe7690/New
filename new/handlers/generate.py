"""
Generate-ID flow: collects the data fields processor.IDProcessor.render_id_side()
needs (portrait photo, Amharic + English name, FAN, FIN, phone, address),
renders both card sides onto templates/front_blank.png + back_blank.png,
then lays them out on a printable A4 sheet via build_a4_batch() — the same
output step the photographed-ID flow uses.

Requires templates/front_blank.png and templates/back_blank.png to exist;
see processor.IDProcessor.render_id_side() for what it draws where.
"""
import io
import os

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from PIL import Image

from database import db
from handlers.states import GenerateIDFlow
from keyboards import cancel_keyboard, main_menu_keyboard
from messages import t
from processor import IDProcessor
from utils import get_language, get_credits, spend_credit, is_admin, logger

router = Router()
engine = IDProcessor()


@router.message(Command("generate_id"))
@router.callback_query(F.data == "generate_id")
async def start_generate_flow(event, state: FSMContext):
    user_id = event.from_user.id
    lang = get_language(user_id)
    target = event.message if isinstance(event, CallbackQuery) else event

    if get_credits(user_id) < 1:
        await target.answer(t(lang, "group_no_credits"))
        if isinstance(event, CallbackQuery):
            await event.answer()
        return

    await state.clear()
    await state.set_state(GenerateIDFlow.waiting_portrait)
    await target.answer(t(lang, "gen_ask_portrait"), reply_markup=cancel_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(GenerateIDFlow.waiting_portrait, F.photo)
async def on_portrait(message: Message, state: FSMContext, bot: Bot):
    lang = get_language(message.from_user.id)
    await state.update_data(portrait_id=message.photo[-1].file_id)
    await state.set_state(GenerateIDFlow.waiting_name_amh)
    await message.answer(t(lang, "gen_ask_name_amh"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_portrait)
async def on_portrait_not_photo(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "not_a_photo"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_name_amh, F.text & ~F.text.startswith("/"))
async def on_name_amh(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(name_amh=message.text.strip())
    await state.set_state(GenerateIDFlow.waiting_name_eng)
    await message.answer(t(lang, "gen_ask_name_eng"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_name_amh)
async def on_name_amh_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_text_only"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_name_eng, F.text & ~F.text.startswith("/"))
async def on_name_eng(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(name_eng=message.text.strip())
    await state.set_state(GenerateIDFlow.waiting_fan)
    await message.answer(t(lang, "gen_ask_fan"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_name_eng)
async def on_name_eng_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_text_only"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_fan, F.text.regexp(r"^\d+$"))
async def on_fan(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(fan=message.text.strip())
    await state.set_state(GenerateIDFlow.waiting_fin)
    await message.answer(t(lang, "gen_ask_fin"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_fan)
async def on_fan_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_digits_only"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_fin, F.text.regexp(r"^\d+$"))
async def on_fin(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(fin=message.text.strip())
    await state.set_state(GenerateIDFlow.waiting_phone)
    await message.answer(t(lang, "gen_ask_phone"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_fin)
async def on_fin_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_digits_only"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_phone, F.text & ~F.text.startswith("/"))
async def on_phone(message: Message, state: FSMContext):
    lang = get_language(message.from_user.id)
    await state.update_data(phone=message.text.strip())
    await state.set_state(GenerateIDFlow.waiting_address)
    await message.answer(t(lang, "gen_ask_address"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_phone)
async def on_phone_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_text_only"), reply_markup=cancel_keyboard())


@router.message(GenerateIDFlow.waiting_address, F.text & ~F.text.startswith("/"))
async def on_address(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = get_language(user_id)
    data = await state.get_data()
    data["address"] = message.text.strip()

    if not spend_credit(user_id, 1):
        await state.clear()
        await message.answer(t(lang, "group_no_credits"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return

    await message.answer(t(lang, "gen_processing"))

    tg_file = await bot.get_file(data["portrait_id"])
    buf = await bot.download_file(tg_file.file_path)
    portrait = Image.open(io.BytesIO(buf.read())).convert("RGB")

    render_data = {
        "name_amh": data["name_amh"],
        "name_eng": data["name_eng"],
        "fan": data["fan"],
        "fin": data["fin"],
        "phone": data["phone"],
        "address": data["address"],
        "portrait": portrait,
    }

    try:
        front = engine.render_id_side(render_data, side="front")
        back = engine.render_id_side(render_data, side="back")
        output_path = engine.build_a4_batch([{"front": front, "back": back}], user_id)
    except FileNotFoundError:
        logger.exception("Missing template for user %s", user_id)
        db.add_credits(user_id, 1)  # refund
        await state.clear()
        await message.answer(t(lang, "gen_template_missing"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return
    except Exception:
        logger.exception("Failed to generate ID for user %s", user_id)
        db.add_credits(user_id, 1)  # refund
        await state.clear()
        await message.answer(t(lang, "not_wired"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))
        return

    db.log_job(user_id, "generate_id")
    await message.answer_document(
        FSInputFile(output_path),
        caption=t(lang, "gen_done", credits=get_credits(user_id)),
    )
    await state.clear()
    await message.answer(t(lang, "main_menu_title"), reply_markup=main_menu_keyboard(is_admin=is_admin(user_id)))


@router.message(GenerateIDFlow.waiting_address)
async def on_address_invalid(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(t(lang, "gen_text_only"), reply_markup=cancel_keyboard())
