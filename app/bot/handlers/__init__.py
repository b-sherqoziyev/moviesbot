from aiogram import Router

from app.bot.handlers.user.start import router as start_router
from app.bot.handlers.user.language import router as language_router
from app.bot.handlers.user.info import router as info_router
from app.bot.handlers.user.movie import router as movie_router
from app.bot.handlers.admin.panel import router as admin_panel_router
from app.bot.handlers.admin.movies import router as admin_movies_router
from app.bot.handlers.admin.channels import router as admin_channels_router
from app.bot.handlers.admin.broadcast import router as admin_broadcast_router
from app.bot.handlers.channel.post_watcher import router as channel_router
from app.bot.handlers.errors.error_handler import router as error_router


def setup_handlers() -> Router:
    """Barcha routerlarni yig'uvchi bosh router."""
    main_router = Router(name="main_router")

    # 1. Xatoliklar handleri
    main_router.include_router(error_router)

    # 2. Kanal postlari va so'rovlar
    main_router.include_router(channel_router)

    # 3. Admin boshqaruv paneli va bo'limlari (Faqat tugmalar bilan ishlaydi)
    main_router.include_router(admin_panel_router)
    main_router.include_router(admin_movies_router)
    main_router.include_router(admin_channels_router)
    main_router.include_router(admin_broadcast_router)

    # 4. Foydalanuvchi buyruqlari va tugmalari (/start, /help, /top, /language)
    main_router.include_router(start_router)
    main_router.include_router(language_router)
    main_router.include_router(info_router)
    main_router.include_router(movie_router)

    return main_router
