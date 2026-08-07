from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards import settings_keyboard, language_keyboard
from messages import t
from utils import get_language, get_settings

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(
        t(lang, "settings_title"),
        reply_markup=settings_keyboard(get_settings(message.from_user.id)),
    )


@router.callback_query(F.data == "settings")
async def on_settings_pressed(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    await callback.message.answer(
        t(lang, "settings_title"),
        reply_markup=settings_keyboard(get_settings(callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"settings:mirror_layout", "settings:fit_to_size", "settings:regenerate_qr"}))
async def on_toggle_pressed(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    new_value = db.toggle_setting(callback.from_user.id, key)

    await callback.message.edit_reply_markup(
        reply_markup=settings_keyboard(get_settings(callback.from_user.id))
    )
    await callback.answer(f"{key} is now {'ON' if new_value else 'OFF'}")


@router.callback_query(F.data.startswith("settings:format:"))
async def on_format_pressed(callback: CallbackQuery):
    fmt = callback.data.split(":", 2)[2]
    db.set_setting(callback.from_user.id, "file_type", fmt)
    await callback.message.edit_reply_markup(
        reply_markup=settings_keyboard(get_settings(callback.from_user.id))
    )
    await callback.answer(f"Format set to {fmt}")


@router.callback_query(F.data.startswith("settings:color:"))
async def on_color_pressed(callback: CallbackQuery):
    mode = callback.data.split(":", 2)[2]
    db.set_setting(callback.from_user.id, "color_mode", mode)
    await callback.message.edit_reply_markup(
        reply_markup=settings_keyboard(get_settings(callback.from_user.id))
    )
    await callback.answer(f"Color mode set to {mode}")


@router.message(Command("language"))
@router.callback_query(F.data == "settings:language")
async def on_change_language(event):
    lang = get_language(event.from_user.id)
    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(t(lang, "choose_language_title"), reply_markup=language_keyboard())
    if isinstance(event, CallbackQuery):
        await event.answer()
