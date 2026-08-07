"""
Admin-only screens, gated by utils.is_admin(). Unlike the original stub
handlers, these now do real work against the persistent database:
payment-proof approval/rejection, broadcast, user lookup, and stats.
"""
import platform

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ACTIONS
from database import db
from handlers.states import AdminFlow
from keyboards import admin_menu_keyboard, admin_detail_keyboard, cancel_keyboard
from messages import t
from utils import is_admin, get_language

router = Router()

NOT_AUTHORIZED = "⛔ You don't have access to this."


async def _reply(event, *args, **kwargs):
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(*args, **kwargs)
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("admin"))
@router.callback_query(F.data == "admin")
async def on_admin_panel(event):
    if not is_admin(event.from_user.id):
        await _reply(event, NOT_AUTHORIZED)
        return
    await _reply(event, "🛠️ Admin panel", reply_markup=admin_menu_keyboard())


# --- Payment approval (available to any admin, not just via the panel) -------
@router.callback_query(F.data.startswith("pay_approve:"))
async def on_payment_approve(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return

    request_id = int(callback.data.split(":", 1)[1])
    req = db.get_payment_request(request_id)
    if req is None:
        await callback.answer("Request not found", show_alert=True)
        return
    if req["status"] != "pending":
        lang = get_language(callback.from_user.id)
        await callback.answer(t(lang, "payment_already_resolved", status=req["status"]), show_alert=True)
        return

    new_balance = db.add_credits(req["user_id"], req["credits"])
    db.resolve_payment_request(request_id, "approved")

    user_lang = get_language(req["user_id"])
    try:
        await bot.send_message(
            req["user_id"],
            t(user_lang, "payment_approved_user", credits=req["credits"], balance=new_balance),
        )
    except Exception:
        pass

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Approved ✅")


@router.callback_query(F.data.startswith("pay_reject:"))
async def on_payment_reject(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return

    request_id = int(callback.data.split(":", 1)[1])
    req = db.get_payment_request(request_id)
    if req is None:
        await callback.answer("Request not found", show_alert=True)
        return
    if req["status"] != "pending":
        lang = get_language(callback.from_user.id)
        await callback.answer(t(lang, "payment_already_resolved", status=req["status"]), show_alert=True)
        return

    db.resolve_payment_request(request_id, "rejected")

    user_lang = get_language(req["user_id"])
    try:
        await bot.send_message(req["user_id"], t(user_lang, "payment_rejected_user"))
    except Exception:
        pass

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Rejected ❌")


# --- Stats ---------------------------------------------------------------------
@router.callback_query(F.data == "admin:stats")
async def on_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return
    lang = get_language(callback.from_user.id)
    stats = db.stats()
    await callback.message.answer(
        t(lang, "admin_stats", **stats), reply_markup=admin_detail_keyboard()
    )
    await callback.answer()


# --- System status ---------------------------------------------------------------
@router.callback_query(F.data == "admin:system_status")
async def on_admin_system_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return
    # NOTE: processor.py now imports cv2/fitz/pytesseract/barcode/qrcode
    # unconditionally at module level, so if any of these were actually
    # missing, the bot would fail at startup before this handler could ever
    # run. This check is mostly useful for confirming versions/paths are
    # sane on the host, not for graceful-degradation like before.
    checks = [
        ("pytesseract", "pip install pytesseract + tesseract-ocr"),
        ("fitz", "pip install pymupdf"),
        ("cv2", "pip install opencv-python-headless"),
        ("barcode", "pip install python-barcode"),
        ("qrcode", "pip install qrcode"),
    ]
    lines = []
    for module_name, hint in checks:
        try:
            __import__(module_name)
            lines.append(f"{module_name} available: ✅")
        except ImportError:
            lines.append(f"{module_name} available: ❌ ({hint})")

    body = (
        f"🩺 System status\n\n"
        f"Python: {platform.python_version()}\n" + "\n".join(lines) + "\n"
    )
    await callback.message.answer(body, reply_markup=admin_detail_keyboard())
    await callback.answer()


# --- Broadcast -------------------------------------------------------------------
@router.callback_query(F.data == "admin:broadcast")
async def on_admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return
    lang = get_language(callback.from_user.id)
    await state.set_state(AdminFlow.awaiting_broadcast)
    await callback.message.answer(t(lang, "admin_broadcast_prompt"), reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(AdminFlow.awaiting_broadcast, F.text & ~F.text.startswith("/"))
async def on_admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    lang = get_language(message.from_user.id)
    sent = 0
    user_ids = db.all_user_ids()
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            continue
    await state.clear()
    await message.answer(t(lang, "admin_broadcast_done", sent=sent, total=len(user_ids)))


# --- User lookup -------------------------------------------------------------------
@router.callback_query(F.data == "admin:user_lookup")
async def on_admin_lookup_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return
    lang = get_language(callback.from_user.id)
    await state.set_state(AdminFlow.awaiting_lookup_id)
    await callback.message.answer(t(lang, "admin_lookup_prompt"), reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(AdminFlow.awaiting_lookup_id, F.text.regexp(r"^\d+$"))
async def on_admin_lookup_result(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    lang = get_language(message.from_user.id)
    target_id = int(message.text)
    row = db.get_user(target_id)
    settings = db.get_settings(target_id)
    await state.clear()
    await message.answer(
        t(
            lang,
            "admin_lookup_result",
            user_id=target_id,
            credits=row["credits"],
            lang=row["lang"],
            is_admin=bool(row["is_admin"]),
            settings=settings,
        ),
        reply_markup=admin_detail_keyboard(),
    )


# --- Manage admins -------------------------------------------------------------------
@router.callback_query(F.data == "admin:manage_admins")
async def on_admin_manage(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(NOT_AUTHORIZED, show_alert=True)
        return
    info = ADMIN_ACTIONS["manage_admins"]
    await callback.message.answer(
        f"{info['title']}\n\n{info['body']}\n\n"
        "Use:\n/promote <user_id> — grant admin\n/demote <user_id> — revoke admin",
        reply_markup=admin_detail_keyboard(),
    )
    await callback.answer()


@router.message(Command("promote"))
async def cmd_promote(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(NOT_AUTHORIZED)
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /promote <user_id>")
        return
    db.set_admin(int(parts[1]), True)
    await message.answer(f"✅ {parts[1]} is now an admin.")


@router.message(Command("demote"))
async def cmd_demote(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(NOT_AUTHORIZED)
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Usage: /demote <user_id>")
        return
    db.set_admin(int(parts[1]), False)
    await message.answer(f"✅ {parts[1]} is no longer an admin.")
