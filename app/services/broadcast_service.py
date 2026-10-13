import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import async_session_maker
from app.database.repositories.user_repository import UserRepository
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


class BroadcastService:
    """Yuqori unumdorlikka ega, rate-limited va non-blocking xabar tarqatish xizmati."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def start_broadcast(
        self,
        from_chat_id: int,
        message_id: int,
        admin_id: int
    ) -> None:
        """Broadcast jarayonini fonda ishga tushirish (Non-blocking)."""
        if self._is_running:
            logger.warning("Broadcast allaqachon bajarilmoqda.")
            return

        self._is_running = True
        asyncio.create_task(
            self._execute_broadcast(from_chat_id, message_id, admin_id)
        )

    async def _execute_broadcast(
        self,
        from_chat_id: int,
        message_id: int,
        admin_id: int
    ) -> None:
        """Fonda xabarlarni nusxalash (copy_message) va statistika yig'ish."""
        total = 0
        success = 0
        blocked = 0
        failed = 0

        logger.info(f"Broadcast boshlandi: admin {admin_id}")
        try:
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                user_service = UserService(session)

                async for chunk in user_repo.get_all_active_telegram_ids_stream(chunk_size=500):
                    for telegram_id in chunk:
                        total += 1
                        try:
                            await self.bot.copy_message(
                                chat_id=telegram_id,
                                from_chat_id=from_chat_id,
                                message_id=message_id
                            )
                            success += 1
                        except TelegramRetryAfter as e:
                            # Telegram Flood cheklovi
                            logger.warning(f"Flood control: {e.retry_after} soniya kutilmoqda...")
                            await asyncio.sleep(e.retry_after)
                            try:
                                await self.bot.copy_message(
                                    chat_id=telegram_id,
                                    from_chat_id=from_chat_id,
                                    message_id=message_id
                                )
                                success += 1
                            except Exception:
                                failed += 1
                        except TelegramForbiddenError:
                            # Botni bloklagan foydalanuvchi -> nofaol qilish
                            blocked += 1
                            await user_service.set_active(telegram_id, is_active=False)
                        except TelegramBadRequest as e:
                            failed += 1
                        except Exception as e:
                            failed += 1

                        # Telegram cheklovi: sekundiga ~25-30 xabar
                        await asyncio.sleep(0.04)

            # Tugagani haqida adminga hisobot
            report = (
                f"📢 <b>Xabar tarqatish yakunlandi!</b>\n\n"
                f"👥 Jami qamrov: {total}\n"
                f"✅ Yetkazildi: {success}\n"
                f"🚫 Botni bloklaganlar: {blocked}\n"
                f"⚠️ Yetib bormadi: {failed}"
            )
            await self.bot.send_message(chat_id=admin_id, text=report)

        except Exception as e:
            logger.error(f"Broadcast jarayonida jiddiy xatolik: {e}")
            await self.bot.send_message(chat_id=admin_id, text=f"❌ Xabar tarqatish to'xtatildi: {e}")
        finally:
            self._is_running = False
