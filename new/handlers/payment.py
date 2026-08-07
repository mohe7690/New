"""
Manual top-up flow, ported from the old Ggg prototype (Handlers.py / main1.py)
and wired into aiogram + persistent storage:

  1. User picks a credit package.
  2. Bot shows Telebirr/CBE account details from config/.env.
  3. User sends a screenshot or transaction-ID text as proof.
  4. Proof is forwarded to the admin with Approve/Reject buttons.
  5. Admin approval credits the user's account (see handlers/admin.py).
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import (
    CREDIT_PACKAGES,
    JOBS_HISTORY_WINDOW_HOURS,
    TELEBIRR_NAME,
    TELEBIRR_NUMBER,
    CBE_NAME,
    CBE_ACCOUNT,
    ADMIN_IDS,
)
from database import db
from handlers.states import PaymentFlow
from keyboards import balance_keyboard, topup_keyboard, main_menu_keyboard, payment_approval_keyboard
from messages import t
from utils import get_language, get_credits, is_admin

router = Router()


@router.message(Command("balance"))
@router.callback_query(F.data == "balance")
async def on_balance(event):
    user_id = event.from_user.id
    lang = get_language(user_id)
    credits = get_credits(user_id)
    body = t(lang, "balance_body", credits=credits)
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(
        f"{t(lang, 'balance_title')}\n\n{body}",
        reply_markup=balance_keyboard(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.message(Command("topup"))
@router.callback_query(F.data == "topup")
async def on_topup(event):
    lang = get_language(event.from_user.id)
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(
        f"{t(lang, 'topup_title')}\n\n{t(lang, 'topup_body')}",
        reply_markup=topup_keyboard(),
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("topup:"))
async def on_package_chosen(callback: CallbackQuery, state: FSMContext):
    pkg_id = callback.data.split(":", 1)[1]
    pkg = next((p for p in CREDIT_PACKAGES if p["id"] == pkg_id), None)
    if not pkg:
        await callback.answer("Package not found", show_alert=True)
        return

    lang = get_language(callback.from_user.id)
    request_id = db.create_payment_request(callback.from_user.id, pkg_id, pkg["credits"], pkg["price"])
    await state.set_state(PaymentFlow.awaiting_proof)
    await state.update_data(request_id=request_id)

    await callback.message.answer(
        t(
            lang,
            "topup_account_details",
            credits=pkg["credits"],
            price=pkg["price"],
            currency=pkg["currency"],
            telebirr_name=TELEBIRR_NAME or "—",
            telebirr_number=TELEBIRR_NUMBER or "—",
            cbe_name=CBE_NAME or "—",
            cbe_account=CBE_ACCOUNT or "—",
        )
    )
    await callback.answer()


async def _forward_proof(message: Message, state: FSMContext, bot):
    lang = get_language(message.from_user.id)
    data = await state.get_data()
    request_id = data.get("request_id")
    req = db.get_payment_request(request_id) if request_id else None

    if not req or req["status"] != "pending":
        await message.answer(t(lang, "proof_not_awaiting"))
        await state.clear()
        return

    caption = t(
        lang,
        "payment_admin_caption",
        user_id=message.from_user.id,
        credits=req["credits"],
        price=req["price"],
        currency="ETB",
        request_id=request_id,
    )

    sent = None
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                sent = await bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=caption,
                    reply_markup=payment_approval_keyboard(request_id),
                )
            else:
                sent = await bot.send_message(
                    admin_id,
                    f"{caption}\n\nTX ID / note: {message.text}",
                    reply_markup=payment_approval_keyboard(request_id),
                )
        except Exception:
            continue

    if sent is not None:
        db.set_payment_admin_message(request_id, sent.message_id)

    await message.answer(t(lang, "proof_forwarded"))
    await state.clear()


@router.message(PaymentFlow.awaiting_proof, F.photo)
async def on_payment_proof_photo(message: Message, state: FSMContext, bot):
    await _forward_proof(message, state, bot)


@router.message(PaymentFlow.awaiting_proof, F.text & ~F.text.startswith("/"))
async def on_payment_proof_text(message: Message, state: FSMContext, bot):
    await _forward_proof(message, state, bot)


@router.callback_query(F.data == "jobs")
async def on_jobs(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    jobs = db.recent_jobs(callback.from_user.id, JOBS_HISTORY_WINDOW_HOURS)
    if not jobs:
        await callback.message.answer(
            t(lang, "no_jobs", hours=JOBS_HISTORY_WINDOW_HOURS),
            reply_markup=main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
        )
    else:
        lines = [f"• {j['kind']} ({j['pairs']} pair(s)) — {j['created_at']}" for j in jobs]
        await callback.message.answer(
            f"📊 Jobs in the last {JOBS_HISTORY_WINDOW_HOURS}h:\n\n" + "\n".join(lines),
            reply_markup=main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
        )
    await callback.answer()
