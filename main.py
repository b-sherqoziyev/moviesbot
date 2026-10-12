import asyncio
import logging
import sys

from app.core.config import settings
from app.core.rbac import rbac
from app.core.emojis import emoji
from app.core.i18n import i18n
from app.database.session import async_session_maker, close_db
from app.bot.loader import bot, dp, redis_client
from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.middlewares.i18n import I18nMiddleware
from app.bot.handlers import setup_handlers

# Logging sozlamalari
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("moviesbot")


async def on_startup() -> None:
    """Bot ishga tushganda bajariladigan dastlabki amallar."""
    logger.info("Bot ishga tushmoqda...")

    # 1. Emojilar va i18n lug'atlarini xotiraga olish
    emoji.load()
    i18n.load()

    # 2. Baza seeder va RBAC keshini yuklash
    async with async_session_maker() as session:
        await rbac.seed_roles_and_permissions(session)
        await rbac.load_cache(session)

    logger.info("Barcha yadro tizimlari muvaffaqiyatli ishga tushdi.")


async def on_shutdown() -> None:
    """Bot to'xtaganda ulanishlarni toza yopish."""
    logger.info("Bot to'xtatilmoqda...")
    await bot.session.close()
    await redis_client.close()
    await close_db()
    logger.info("Barcha ulanishlar yopildi.")


async def main() -> None:
    """Asosiy ishga tushirish funksiyasi."""
    # 1. Startup amallari
    await on_startup()

    # 2. Middlewares ni ro'yxatdan o'tkazish
    db_middleware = DbSessionMiddleware()
    i18n_middleware = I18nMiddleware()

    # Sessiya middleware har bir so'rovga sessiyani ineksiya qiladi
    dp.update.middleware(db_middleware)

    # I18n middleware xabarlar va tugmalarga tilni ineksiya qiladi
    dp.message.middleware(i18n_middleware)
    dp.callback_query.middleware(i18n_middleware)

    # 3. Routerlarni ulash
    main_router = setup_handlers()
    dp.include_router(main_router)

    # 4. Eski o'qilmagan updatelarni tozalash va Pollingni boshlash
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot Telegram Polling rejimida muvaffaqiyatli ishga tushdi!")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await on_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
