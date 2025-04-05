from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from locales.languages import LANGUAGES
from database.db_operations import save_user
from utils.subscription import check_subscription, send_subscription_prompt
from utils.decorators import with_db_connection


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    username = update.effective_user.username or "None"

    if user_id not in context.bot_data["users"]:
        user_data = {"username": username, "first_name": user_name, "language": None}
        await save_user(context.bot_data["db_pool"], user_id, user_data)
        context.bot_data["users"][user_id] = user_data

    if "language" not in context.bot_data["users"][user_id] or context.bot_data["users"][user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
    else:
        user_lang = context.bot_data["users"][user_id]["language"]
        await update.message.reply_text(LANGUAGES[user_lang]["welcome"].format(name=user_name))


async def find_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_code = update.message.text.strip()
    user_id = update.effective_user.id
    user_lang = context.bot_data["users"].get(user_id, {}).get("language", "uz")

    if "language" not in context.bot_data["users"][user_id] or context.bot_data["users"][user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    is_subscribed, not_subscribed_channels = await check_subscription(user_id, context.bot,
                                                                      context.bot_data["channels"])
    if not is_subscribed:
        await send_subscription_prompt(update.effective_chat.id, context, not_subscribed_channels, user_lang)
        return

    if user_code in context.bot_data["message_store"]:
        movie = context.bot_data["message_store"][user_code]
        async with context.bot_data["db_pool"].acquire() as conn:
            await conn.execute("UPDATE message_store SET views = views + 1 WHERE movie_code = $1", user_code)
        context.bot_data["message_store"][user_code]["views"] += 1
        if movie["video"]:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=movie["video"],
                                         caption=movie["caption"])
        elif movie["document"]:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=movie["document"],
                                            caption=movie["caption"])
    else:
        await update.message.reply_text(LANGUAGES[user_lang]["no_such_movie"])


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang = context.bot_data["users"].get(user_id, {}).get("language", "uz")

    if "language" not in context.bot_data["users"][user_id] or context.bot_data["users"][user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    if user_id == context.bot_data["ADMIN_ID"]:
        await update.message.reply_text(LANGUAGES[user_lang]["help_admin"])
    else:
        await update.message.reply_text(LANGUAGES[user_lang]["help_user"])


async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)


@with_db_connection
async def stat(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = users.get(update.effective_user.id, {}).get("language", "uz")
    users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
    movies_count = await conn.fetchval("SELECT COUNT(*) FROM message_store")
    await update.message.reply_text(LANGUAGES[user_lang]["stats"].format(users=users_count, movies=movies_count))
