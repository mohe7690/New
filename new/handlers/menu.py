from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from keyboards import main_menu_keyboard
from messages import t
from utils import get_language, is_admin

router = Router()

HELP_COMMANDS = [
    ("/start", "— show the language picker"),
    ("/menu", "— show the main menu"),
    ("/group", "— group an ID's front + back onto an A4 sheet"),
    ("/generate_id", "— generate a new ID card from a template + your details"),
    ("/settings", "— output settings"),
    ("/balance", "— check your credits"),
    ("/topup", "— buy credits"),
    ("/language", "— change language"),
    ("/help", "— show all commands"),
    ("/cancel", "— cancel the current step"),
]


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    lang = get_language(message.from_user.id)
    await message.answer(
        t(lang, "main_menu_title"),
        reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id)),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    lang = get_language(message.from_user.id)
    body = "\n".join(f"{cmd}  {desc}" for cmd, desc in HELP_COMMANDS)
    await message.answer(f"{t(lang, 'help_title')}\n\n{body}")


@router.callback_query(F.data == "help")
async def on_help_pressed(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    body = "\n".join(f"{cmd}  {desc}" for cmd, desc in HELP_COMMANDS)
    await callback.message.answer(f"{t(lang, 'help_title')}\n\n{body}")
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    lang = get_language(message.from_user.id)
    await message.answer(
        t(lang, "cancelled"),
        reply_markup=main_menu_keyboard(is_admin=is_admin(message.from_user.id)),
    )


@router.callback_query(F.data == "cancel")
async def on_cancel_pressed(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    lang = get_language(callback.from_user.id)
    await callback.message.answer(
        t(lang, "cancelled"),
        reply_markup=main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("noop:"))
async def on_noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == "menu")
async def on_menu_pressed(callback: CallbackQuery):
    lang = get_language(callback.from_user.id)
    await callback.message.answer(
        t(lang, "main_menu_title"),
        reply_markup=main_menu_keyboard(is_admin=is_admin(callback.from_user.id)),
    )
    await callback.answer()
