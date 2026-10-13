from typing import Callable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import rbac
from app.bot.keyboards.inline.user_keyboards import get_language_keyboard
from app.bot.keyboards.reply.main_keyboards import get_main_reply_keyboard
from app.database.models.user import User
from app.services.user_service import UserService

from app.bot.filters.i18n import I18nButtonFilter

router = Router(name="language")


@router.message(Command("language"))
@router.message(I18nButtonFilter("btn_language", emoji_key="language"))
async def handle_language_command(
    message: Message,
    user: User,
    _: Callable[..., str]
) -> None:
    """Tilni tanlash komandasi yoki tugmasi."""
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

    is_admin = rbac.is_god(user.telegram_id) or user.role_id in (2, 3)
    main_kb = get_main_reply_keyboard(is_admin=is_admin, lang=new_lang)

    await callback.answer(_("language_changed"))
    await callback.message.edit_text(
        text=_("welcome", name=user.first_name)
    )
    # Yangi tildagi reply klaviaturani yuborish
    await callback.message.answer(
        text=_("language_changed"),
        reply_markup=main_kb
    )
