import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config.config import TOKEN, ADMIN_ID, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from database.db_pool import init_db_pool
from database.db_operations import load_message_store, load_users, load_channels
from handlers.user_handlers import start, find_movie, help_command, change_language
from handlers.admin_handlers import top_movies, list_users, channels_cmd, admin_commands, broadcast, remove_channel, \
    add_channel
from handlers.channel_handlers import handle_channel_post
from utils.subscription import check_subscription, send_subscription_prompt
from locales.languages import LANGUAGES
from telegram import Update

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_lang = context.bot_data["users"].get(user_id, {}).get("language", "uz")

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        context.bot_data["users"][user_id]["language"] = lang
        from database.db_operations import save_user
        await save_user(context.bot_data["db_pool"], user_id, context.bot_data["users"][user_id])
        await query.edit_message_text(LANGUAGES[lang]["language_changed"])
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=LANGUAGES[lang]["welcome"].format(name=query.from_user.first_name))
    elif query.data == "check_subscription":
        is_subscribed, not_subscribed_channels = await check_subscription(user_id, context.bot,
                                                                          context.bot_data["channels"])
        if is_subscribed:
            await query.edit_message_text(LANGUAGES[user_lang]["subscribed"])
        else:
            await query.delete_message()
            await send_subscription_prompt(query.message.chat_id, context, not_subscribed_channels, user_lang)


async def main():
    db_pool = await init_db_pool(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
    message_store = {}
    users = {}
    channels = []

    await load_message_store(db_pool, message_store)
    await load_users(db_pool, users)
    await load_channels(db_pool, channels)

    app = ApplicationBuilder().token(TOKEN).build()

    app.bot_data["db_pool"] = db_pool
    app.bot_data["message_store"] = message_store
    app.bot_data["users"] = users
    app.bot_data["channels"] = channels
    app.bot_data["ADMIN_ID"] = ADMIN_ID

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", change_language))  # Til o‘zgartirish uchun
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("top", top_movies))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("addchannel", add_channel()))  # Qo‘shish kerak
    app.add_handler(CommandHandler("removechannel", remove_channel()))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("admin", admin_commands))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_movie))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot ishga tushdi...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Bot to‘xtatilmoqda...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
