from aiogram import Router

from app.bot.handlers.user.start import router as start_router
from app.bot.handlers.user.language import router as language_router
from app.bot.handlers.user.info import router as info_router
from app.bot.handlers.admin.movies import router as admin_movies_router
from app.bot.handlers.user.movie import router as movie_router
from app.bot.handlers.channel.post_watcher import router as channel_router
from app.bot.handlers.errors.error_handler import router as error_router


def setup_handlers() -> Router:
    """Barcha routerlarni yig'uvchi bosh router."""
    main_router = Router(name="main_router")

    # Xatoliklar handleri
    main_router.include_router(error_router)

    # Kanal postlari va so'rovlar
    main_router.include_router(channel_router)

    # Admin buyruqlari
    main_router.include_router(admin_movies_router)

    # Foydalanuvchi buyruqlari
    main_router.include_router(start_router)
    main_router.include_router(language_router)
    main_router.include_router(info_router)
    main_router.include_router(movie_router)

    return main_router
