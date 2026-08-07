from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import SUPPORTED_LANGUAGES
from keyboards import language_keyboard, main_menu_keyboard
from messages import t
from utils import get_language, set_language, is_admin

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    lang = get_language(message.from_user.id)  # creates the user record (with signup bonus) if new
    await message.answer(
        f"{t(lang, 'choose_language_title')}\n\n{t(lang, 'choose_language_body')}",
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery):
    lang_code = callback.data.split(":", 1)[1]
    set_language(callback.from_user.id, lang_code)
    label = SUPPORTED_LANGUAGES.get(lang_code, lang_code)

    await callback.message.answer(t(lang_code, "language_set", language=label))
    await callback.message.answer(
        t(lang_code, "main_menu_title"),
        reply_markup=main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
    )
    await callback.answer()
