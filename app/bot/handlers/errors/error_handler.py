import logging
from aiogram import Router
from aiogram.types import ErrorEvent

from app.core.i18n import i18n
from app.core.emojis import emoji

logger = logging.getLogger(__name__)
router = Router(name="error_handler")


@router.error()
async def global_error_handler(event: ErrorEvent) -> None:
    """Botdagi barcha kutilmagan xatoliklarni xavfsiz tutuvchi ko'p tilli global handler."""
    logger.exception(
        f"Kutilmagan xatolik yuz berdi: {event.exception} (Update: {event.update})"
    )

    # 1. Foydalanuvchining tilini aniqlash (Baza modeli yoki Telegram mijozidan)
    lang = "uz"
    try:
        user_obj = event.data.get("user") if hasattr(event, "data") and event.data else None
        if user_obj and getattr(user_obj, "language_code", None):
            lang = user_obj.language_code
        elif event.update.message and event.update.message.from_user:
            tg_lang = event.update.message.from_user.language_code
            if tg_lang in ("uz", "ru", "en"):
                lang = tg_lang
        elif event.update.callback_query and event.update.callback_query.from_user:
            tg_lang = event.update.callback_query.from_user.language_code
            if tg_lang in ("uz", "ru", "en"):
                lang = tg_lang
    except Exception:
        lang = "uz"

    err_icon = emoji.get("error") or "❌"
    error_msg = f"{err_icon} {i18n.get('error_unexpected', lang)}"

    if event.update.message:
        try:
            await event.update.message.answer(error_msg)
        except Exception:
            pass
    elif event.update.callback_query:
        try:
            await event.update.callback_query.answer(error_msg, show_alert=True)
        except Exception:
            pass
