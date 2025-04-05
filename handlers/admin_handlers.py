from telegram import Update
from telegram.ext import ContextTypes
from locales.languages import LANGUAGES
from utils.decorators import admin_only, with_db_connection
from database.db_operations import save_user


@admin_only
@with_db_connection
async def top_movies(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.bot_data["users"].get(update.effective_user.id, {}).get("language", "uz")
    rows = await conn.fetch("SELECT name, movie_code, views FROM message_store ORDER BY views DESC LIMIT 10")
    if not rows:
        await update.message.reply_text(LANGUAGES[user_lang]["no_movies_watched"])
        return
    top_list = "\n".join([f"{i + 1}. {row['name']} - {row['movie_code']} ({row['views']} marta ko‘rilgan)"
                          for i, row in enumerate(rows)])
    await update.message.reply_text(LANGUAGES[user_lang]["top_movies"].format(list=top_list))


@admin_only
@with_db_connection
async def list_users(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.bot_data["users"].get(update.effective_user.id, {}).get("language", "uz")
    rows = await conn.fetch("SELECT user_id, data FROM users")
    if not rows:
        await update.message.reply_text(LANGUAGES[user_lang]["no_users"])
        return
    user_list = "\n".join([
        f"ID: {row['user_id']}, Username: {'@' + json.loads(row['data'])['username'] if json.loads(row['data'])['username'] != 'None' else 'None'}, Name: {json.loads(row['data'])['first_name']}"
        for row in rows])
    await update.message.reply_text(LANGUAGES[user_lang]["user_list"].format(list=user_list))


@admin_only
async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.bot_data["users"].get(update.effective_user.id, {}).get("language", "uz")
    if context.bot_data["channels"]:
        channel_list = "\n".join([f"ID: {ch_id} | URL: {ch_url}" for ch_id, ch_url in context.bot_data["channels"]])
        await update.message.reply_text(LANGUAGES[user_lang]["channel_list"].format(list=channel_list))
    else:
        await update.message.reply_text(LANGUAGES[user_lang]["no_channels"])


@admin_only
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_list = (
        "🚀 /start - Botni boshlash\n"
        "🌐 /language - Tilni o‘zgartirish\n"
        "📊 /stat - Botning statistikasi\n"
        "🏆 /top - Eng ko'p tomosha qilingan filmlar\n"
        "👥 /users - Foydalanuvchilar ro'yxati\n"
        "➕ /addchannel <id> <url> - Kanal qo‘shish\n"
        "➖ /removechannel <id> - Kanal olib tashlash\n"
        "📡 /channels - Mavjud kanallar\n"
        "📢 /broadcast - Xabar tarqatish\n"
        "🛠️ /admin - Admin komandalari\n"
        "ℹ️ /help - Yordam"
    )
    await update.message.reply_text(commands_list)


@admin_only
@with_db_connection
async def broadcast(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = context.bot_data["users"].get(update.effective_user.id, {}).get("language", "uz")
    if not update.message.reply_to_message:
        await update.message.reply_text(LANGUAGES[user_lang]["broadcast_usage"])
        return
    reply_message = update.message.reply_to_message
    rows = await conn.fetch("SELECT user_id FROM users")
    user_ids = [row["user_id"] for row in rows]
    failed_users = []
    for user_id in user_ids:
        try:
            if reply_message.text:
                await context.bot.send_message(chat_id=user_id, text=reply_message.text)
            elif reply_message.photo:
                await context.bot.send_photo(chat_id=user_id, photo=reply_message.photo[-1].file_id,
                                             caption=reply_message.caption)
            elif reply_message.video:
                await context.bot.send_video(chat_id=user_id, video=reply_message.video.file_id,
                                             caption=reply_message.caption)
            elif reply_message.document:
                await context.bot.send_document(chat_id=user_id, document=reply_message.document.file_id,
                                                caption=reply_message.caption)
            elif reply_message.animation:
                await context.bot.send_animation(chat_id=user_id, animation=reply_message.animation.file_id,
                                                 caption=reply_message.caption)
        except Exception as e:
            logger.warning(f"Xabar yuborishda xato {user_id}: {e}")
            failed_users.append(user_id)
    await update.message.reply_text(LANGUAGES[user_lang]["broadcast_result"].format(count=len(failed_users)))


# Kanal qo‘shish/o‘chirish
@admin_only
@with_db_connection
async def add_channel(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = users.get(update.effective_user.id, {}).get("language", "uz")
    if len(context.args) < 2:
        await update.message.reply_text(LANGUAGES[user_lang]["add_channel_usage"])
        return

    try:
        channel_id = int(context.args[0])
        channel_url = context.args[1]
    except ValueError:
        await update.message.reply_text(LANGUAGES[user_lang]["invalid_channel_id"])
        return

    if not channel_url.startswith("https://t.me/"):
        await update.message.reply_text(LANGUAGES[user_lang]["invalid_url"])
        return

    channel_username = channel_url.split("https://t.me/")[-1]
    if any(ch_id == channel_id for ch_id, _ in channels):
        await update.message.reply_text(LANGUAGES[user_lang]["channel_exists"])
    else:
        await conn.execute(
            "INSERT INTO channels (channel_id, channel_username) VALUES ($1, $2)",
            channel_id, channel_username
        )
        channels.append((channel_id, channel_url))
        await update.message.reply_text(LANGUAGES[user_lang]["channel_added"].format(id=channel_id, url=channel_url))


@admin_only
@with_db_connection
async def remove_channel(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_lang = users.get(update.effective_user.id, {}).get("language", "uz")
    if not context.args:
        await update.message.reply_text(LANGUAGES[user_lang]["remove_channel_usage"])
        return

    try:
        channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(LANGUAGES[user_lang]["invalid_channel_id"])
        return

    result = await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)
    if result == "DELETE 1":
        channels[:] = [(ch_id, ch_url) for ch_id, ch_url in channels if ch_id != channel_id]
        await update.message.reply_text(LANGUAGES[user_lang]["channel_removed"].format(id=channel_id))
    else:
        await update.message.reply_text(LANGUAGES[user_lang]["channel_not_found"])
