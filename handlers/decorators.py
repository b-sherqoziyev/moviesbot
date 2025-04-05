from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from locales.languages import LANGUAGES

def with_db_connection(func):
    @wraps(func)
    async def wrapper(db_pool, *args, **kwargs):
        async with db_pool.acquire() as conn:
            return await func(conn, *args, **kwargs)
    return wrapper

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_lang = context.bot_data["users"].get(update.effective_user.id, {}).get("language", "uz")
        if update.effective_user.id != context.bot_data["ADMIN_ID"]:
            await update.message.reply_text(LANGUAGES[user_lang]["no_permission"])
            return
        return await func(update, context, *args, **kwargs)
    return wrapper