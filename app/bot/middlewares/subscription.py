import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import rbac
from app.services.subscription_service import SubscriptionService
from app.bot.keyboards.inline.user_keyboards import get_subscription_keyboard
from app.database.models.user import User

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Barcha foydalanuvchi so'rovlari uchun markaziy a'zolik himoyachisi (Subscription Guard).
    
    Handlerlarda obunani qayta-qayta tekshirishni (DRY buzilishini) yo'qotadi.
    """

    def __init__(self, subscription_service: SubscriptionService):
        self.sub_service = subscription_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Faqat Message va CallbackQuery larni tekshiramiz
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        user: User | None = data.get("user")
        session: AsyncSession | None = data.get("session")
        bot: Bot | None = data.get("bot")

        if not user or not session or not bot:
            return await handler(event, data)

        # 1. GOD, Admin yoki VIP bypass
        if rbac.is_god(user.telegram_id) or getattr(user, "is_vip", False) or user.role_id in (2, 3):
            return await handler(event, data)

        # 2. Ruxsat etilgan istisnolar (Exceptions)
        # /start komandasi, til va yordam o'z handleriga to'siqsiz o'tishi kerak
        from app.core.i18n import i18n
        if isinstance(event, Message):
            text = (event.text or "").strip().lower()
            allowed_texts = set(i18n.get_button_variants("btn_language", emoji_key="language"))
            allowed_texts.update(i18n.get_button_variants("btn_help", emoji_key="help"))
            if text.startswith("/start") or text.startswith("/language") or text.startswith("/help") or text in allowed_texts:
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            cb_data = event.data or ""
            if cb_data.startswith("check_sub") or cb_data.startswith("set_lang"):
                return await handler(event, data)

        # 3. Keshlashtirilgan obunani tekshirish
        is_sub, not_sub = await self.sub_service.check_subscription(bot, user, session)
        if is_sub:
            return await handler(event, data)

        # 4. Agar obuna bo'lmasa -> markaziy ogohlantirish
        _ = data.get("_")
        text = _("subscribe_prompt") if _ else "Iltimos, botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:"
        pending_code = None
        if isinstance(event, Message) and event.text and not event.text.startswith("/"):
            pending_code = event.text.strip()

        keyboard = get_subscription_keyboard(
            unsubscribed_channels=not_sub,
            user_lang=user.language_code,
            pending_code=pending_code
        )

        if isinstance(event, Message):
            await event.answer(text=text, reply_markup=keyboard)
        elif isinstance(event, CallbackQuery):
            await event.answer(_("not_subscribed_warning") if _ else "Kanallarga obuna bo'lmagansiz!", show_alert=True)
            try:
                await event.message.answer(text=text, reply_markup=keyboard)
            except Exception:
                pass

        return None
