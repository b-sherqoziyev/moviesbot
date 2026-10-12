from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.i18n import i18n
from app.services.user_service import UserService


class I18nMiddleware(BaseMiddleware):
    """Foydalanuvchini aniqlash, ro'yxatdan o'tkazish va mos tilni inject qiluvchi middleware."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: TgUser | None = data.get("event_from_user")
        session: AsyncSession = data.get("session")

        if event_user and session:
            user_service = UserService(session)
            # Standart tilni Telegram tilidan yoki 'uz' dan olish
            lang_code = "uz"
            if event_user.language_code and event_user.language_code in i18n.SUPPORTED_LANGUAGES:
                lang_code = event_user.language_code

            # Foydalanuvchini olish yoki yangilash
            user, _ = await user_service.get_or_create_user(
                telegram_id=event_user.id,
                first_name=event_user.first_name,
                username=event_user.username,
                language_code=lang_code
            )

            data["user"] = user
            data["user_lang"] = user.language_code

            # Handlerlar ichida to'g'ridan-to'g'ri _("kalit") deb chaqirish uchun funksiya
            data["_"] = lambda key, **kwargs: i18n.get(key, lang=user.language_code, **kwargs)
        else:
            data["user_lang"] = "uz"
            data["_"] = lambda key, **kwargs: i18n.get(key, lang="uz", **kwargs)

        return await handler(event, data)
