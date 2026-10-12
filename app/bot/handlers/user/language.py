from typing import Callable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline.user_keyboards import get_language_keyboard
from app.database.models.user import User
from app.services.user_service import UserService

router = Router(name="language")


@router.message(Command("language"))
async def handle_language_command(
    message: Message,
    user: User,
    _: Callable[..., str]
) -> None:
    """Tilni tanlash komandasi."""
    await message.answer(
        text=_("choose_language"),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Tilni o'zgartirish callback handleri."""
    new_lang = callback.data.split(":")[1]
    user_service = UserService(session)
    await user_service.set_language(user.telegram_id, new_lang)
    user.language_code = new_lang

    await callback.answer(_("language_changed"))
    await callback.message.edit_text(
        text=_("welcome", name=user.first_name)
    )
