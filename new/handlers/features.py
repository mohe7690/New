from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import FEATURES
from database import db
from keyboards import features_menu_keyboard, feature_detail_keyboard, print_style_keyboard
from messages import t
from utils import get_language

router = Router()


@router.message(Command("features"))
@router.callback_query(F.data == "features")
async def on_features(event):
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer("✨ Features", reply_markup=features_menu_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("feature:"))
async def on_feature_selected(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    info = FEATURES.get(key)
    if not info:
        await callback.answer("Unknown feature", show_alert=True)
        return

    await callback.message.answer(
        f"{info['title']}\n\n{info['body']}",
        reply_markup=feature_detail_keyboard(key),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("feature_start:"))
async def on_feature_start(callback: CallbackQuery, state: FSMContext):
    """Route 'Get Started' on a feature card to the real handler that does it."""
    key = callback.data.split(":", 1)[1]

    # Imported lazily to avoid a circular import (uploads.py doesn't import features.py).
    from handlers import uploads, settings as settings_handlers

    if key in {"bulk_upload", "grouped_layout"}:
        await uploads.start_group_flow(callback, state)
    elif key == "smart_import":
        await uploads.start_smart_import(callback, state)
    elif key == "color_modes":
        await settings_handlers.on_settings_pressed(callback)
    elif key == "auto_enhance":
        await callback.message.answer(
            "✨ Auto Enhance runs automatically on every photo you send — nothing to turn on."
        )
        await callback.answer()
    elif key == "one_click_output":
        await callback.message.answer(
            "🖨️ Once you've sent all the ID pairs you need, tap 'Done' and the sheet is generated instantly."
        )
        await callback.answer()
    else:
        await callback.answer("Not available yet", show_alert=True)


# --- Print style (color/B&W), persisted as the user's color_mode setting -----
@router.message(Command("print_style"))
@router.callback_query(F.data == "print_style")
async def on_print_style(event):
    target = event.message if isinstance(event, CallbackQuery) else event
    current = db.get_settings(event.from_user.id)["color_mode"]
    selected = "bw" if current == "B&W only" else "color"
    await target.answer("🖨️ Choose output style:", reply_markup=print_style_keyboard(selected=selected))
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.callback_query(F.data.startswith("print_style:"))
async def on_print_style_toggle(callback: CallbackQuery):
    choice = callback.data.split(":", 1)[1]  # "color" | "bw"
    db.set_setting(callback.from_user.id, "color_mode", "B&W only" if choice == "bw" else "Both")
    await callback.message.edit_reply_markup(reply_markup=print_style_keyboard(selected=choice))
    await callback.answer(f"Style set to {choice}")
