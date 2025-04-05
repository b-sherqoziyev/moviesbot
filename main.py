import logging
import asyncpg
import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from functools import wraps

# Logging sozlamalari
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# .env fayldan o'zgaruvchilarni yuklash
load_dotenv()
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Global ma'lumotlar
message_store = {}
users = {}
channels = []  # [(channel_id, channel_url), ...]

# Connection Pool
db_pool = None

# Tillarni qo‘llab-quvvatlash uchun so‘zlar (faqat foydalanuvchi komandalari uchun)
LANGUAGES = {
    "uz": {
        "welcome": "🎉 Xush kelibsiz, {name}! Kerakli film kodini yuboring",
        "choose_language": "🌐 Tilni tanlang:",
        "language_changed": "✅ Til muvaffaqiyatli o‘zgartirildi!",
        "subscribed": "🎊 Siz barcha kanallarga obuna bo‘lgansiz! Film kodini yuboring. 🎥",
        "subscribe_prompt": "🔗 Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
        "check_subscription": "🔍 Obunani tekshirish",
        "no_such_movie": "❌ Afsuski, bunday film mavjud emas.",
        "no_permission": "🚫 Sizda bu buyruqni ishlatish huquqi yo‘q.",
        "stats": "📊 Statistika:\n👤 Foydalanuvchilar: {users}\n🎬 Kinolar: {movies}",
        "help_user": "📚 Botdan foydalanish bo‘yicha qo‘llanma:\n"
                     "🚀 /start - Botni boshlash\n"
                     "🌐 /language - Tilni o‘zgartirish\n"
                     "📊 /stat - Statistika\n"
                     "🏆 /top - Eng ko‘p ko‘rilgan filmlar\n"
                     "ℹ️ /help - Yordam\n"
                     "🎥 Film kodini yuboring va filmni oling!",
        "no_movies_watched": "❌ Hozircha ko‘rilgan filmlar yo‘q.",
        "top_movies": "🏆 Eng ko‘p ko‘rilgan filmlar:\n{list}"
    },
    "en": {
        "welcome": "🎉 Welcome, {name}! Send the movie code you need.",
        "choose_language": "🌐 Choose a language:",
        "language_changed": "✅ Language successfully changed!",
        "subscribed": "🎊 You are subscribed to all channels! Send a movie code. 🎥",
        "subscribe_prompt": "🔗 Subscribe to the following channels to use the bot:",
        "check_subscription": "🔍 Check subscription",
        "no_such_movie": "❌ Sorry, no such movie exists.",
        "no_permission": "🚫 You don’t have permission to use this command.",
        "stats": "📊 Statistics:\n👤 Users: {users}\n🎬 Movies: {movies}",
        "help_user": "📚 Guide to using the bot:\n"
                     "🚀 /start - Start the bot\n"
                     "🌐 /language - Change language\n"
                     "📊 /stat - Statistics\n"
                     "🏆 /top - Most watched movies\n"
                     "ℹ️ /help - This help\n"
                     "🎥 Send a movie code to get the movie!",
        "no_movies_watched": "❌ No movies have been watched yet.",
        "top_movies": "🏆 Most watched movies:\n{list}"
    },
    "ru": {
        "welcome": "🎉 Добро пожаловать, {name}! Отправьте нужный код фильма.",
        "choose_language": "🌐 Выберите язык:",
        "language_changed": "✅ Язык успешно изменён!",
        "subscribed": "🎊 Вы подписаны на все каналы! Отправьте код фильма. 🎥",
        "subscribe_prompt": "🔗 Подпишитесь на следующие каналы, чтобы использовать бота:",
        "check_subscription": "🔍 Проверить подписку",
        "no_such_movie": "❌ К сожалению, такого фильма нет.",
        "no_permission": "🚫 У вас нет прав для использования этой команды.",
        "stats": "📊 Статистика:\n👤 Пользователи: {users}\n🎬 Фильмы: {movies}",
        "help_user": "📚 Руководство по использованию бота:\n"
                     "🚀 /start - Запустить бот\n"
                     "🌐 /language - Сменить язык\n"
                     "📊 /stat - Статистика\n"
                     "🏆 /top - Самые просматриваемые фильмы\n"
                     "ℹ️ /help - Эта помощь\n"
                     "🎥 Отправьте код фильма, чтобы получить фильм!",
        "no_movies_watched": "❌ Пока нет просмотренных фильмов.",
        "top_movies": "🏆 Самые просматриваемые фильмы:\n{list}"
    }
}

# Ma'lumotlar bazasi ulanishini boshlash
async def init_db_pool():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            database=DB_NAME, user=DB_USER,
            password=DB_PASSWORD, host=DB_HOST, port=DB_PORT,
            min_size=1, max_size=10
        )
        logger.info("Ma'lumotlar bazasi pooli muvaffaqiyatli ishga tushdi.")
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasi poolini ishga tushirishda xato: {e}")
        raise

# Dekorator: Ma'lumotlar bazasi ulanishini boshqarish
def with_db_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with db_pool.acquire() as conn:
            return await func(conn, *args, **kwargs)
    return wrapper

# Ma'lumotlarni yuklash
@with_db_connection
async def load_message_store(conn):
    global message_store
    rows = await conn.fetch("SELECT * FROM message_store")
    message_store.update({
        row["movie_code"]: {
            "message_id": row["message_id"],
            "video": row["video"],
            "document": row["document"],
            "caption": row["caption"],
            "name": row["name"],
            "views": row["views"]
        } for row in rows
    })

@with_db_connection
async def load_users(conn):
    global users
    rows = await conn.fetch("SELECT user_id, data FROM users")
    users.update({row["user_id"]: json.loads(row["data"]) for row in rows})

@with_db_connection
async def load_channels(conn):
    global channels
    rows = await conn.fetch("SELECT channel_id, channel_username FROM channels")
    channels[:] = [(row['channel_id'], f"https://t.me/{row['channel_username']}") for row in rows]

# Ma'lumotlarni saqlash
@with_db_connection
async def save_message_store(conn, movie_code, data):
    await conn.execute("""
        INSERT INTO message_store (movie_code, message_id, video, document, caption, name, views)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (movie_code) DO UPDATE 
        SET message_id = EXCLUDED.message_id,
            video = EXCLUDED.video,
            document = EXCLUDED.document,
            caption = EXCLUDED.caption,
            name = EXCLUDED.name,
            views = EXCLUDED.views
    """, movie_code, data["message_id"], data["video"], data["document"],
         data["caption"], data["name"], data["views"])

@with_db_connection
async def save_user(conn, user_id: int, user_data: dict):
    await conn.execute("""
        INSERT INTO users (user_id, data) 
        VALUES ($1, $2)
        ON CONFLICT (user_id) 
        DO UPDATE SET data = EXCLUDED.data
    """, user_id, json.dumps(user_data))

# Admin tekshiruvi dekoratori
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_lang = users.get(update.effective_user.id, {}).get("language", "uz")
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text(LANGUAGES[user_lang]["no_permission"])
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# Obuna tekshiruvi
async def check_subscription(user_id, bot):
    not_subscribed_channels = []
    for channel_id, channel_url in channels:
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_subscribed_channels.append((channel_id, channel_url))
        except Exception as e:
            logger.warning(f"Kanal {channel_id} tekshirilganda xatolik: {e}")
            not_subscribed_channels.append((channel_id, channel_url))
    is_subscribed = len(not_subscribed_channels) == 0
    return is_subscribed, not_subscribed_channels

async def send_subscription_prompt(chat_id, context, not_subscribed_channels, user_lang):
    if not not_subscribed_channels:
        await context.bot.send_message(chat_id=chat_id, text=LANGUAGES[user_lang]["subscribed"])
        return

    keyboard = [[InlineKeyboardButton(f"Kanal {i + 1}", url=channel_url)]
                for i, (_, channel_url) in enumerate(not_subscribed_channels)]
    keyboard.append([InlineKeyboardButton(LANGUAGES[user_lang]["check_subscription"], callback_data='check_subscription')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=LANGUAGES[user_lang]["subscribe_prompt"], reply_markup=reply_markup)

# Foydalanuvchi funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    username = update.effective_user.username or "None"

    if user_id not in users:
        user_data = {"username": username, "first_name": user_name, "language": None}
        await save_user(user_id, user_data)
        users[user_id] = user_data

    if "language" not in users[user_id] or users[user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
    else:
        user_lang = users[user_id]["language"]
        await update.message.reply_text(LANGUAGES[user_lang]["welcome"].format(name=user_name))

async def change_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users or "language" not in users[user_id] or users[user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    user_lang = users[user_id]["language"]
    await update.message.reply_text(LANGUAGES[user_lang]["help_user"])

async def find_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users or "language" not in users[user_id] or users[user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    user_lang = users[user_id]["language"]
    user_code = update.message.text.strip()

    is_subscribed, not_subscribed_channels = await check_subscription(user_id, context.bot)
    if not is_subscribed:
        await send_subscription_prompt(update.effective_chat.id, context, not_subscribed_channels, user_lang)
        return

    if user_code in message_store:
        movie = message_store[user_code]
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE message_store SET views = views + 1 WHERE movie_code = $1", user_code)
        message_store[user_code]["views"] += 1
        if movie["video"]:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=movie["video"], caption=movie["caption"])
        elif movie["document"]:
            await context.bot.send_document(chat_id=update.effective_chat.id, document=movie["document"], caption=movie["caption"])
    else:
        await update.message.reply_text(LANGUAGES[user_lang]["no_such_movie"])

@with_db_connection
async def stat(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users or "language" not in users[user_id] or users[user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    user_lang = users[user_id]["language"]
    users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
    movies_count = await conn.fetchval("SELECT COUNT(*) FROM message_store")
    await update.message.reply_text(LANGUAGES[user_lang]["stats"].format(users=users_count, movies=movies_count))

@with_db_connection
async def top_movies(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in users or "language" not in users[user_id] or users[user_id]["language"] is None:
        keyboard = [
            [InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
             InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(LANGUAGES["uz"]["choose_language"], reply_markup=reply_markup)
        return

    user_lang = users[user_id]["language"]
    rows = await conn.fetch("SELECT name, movie_code, views FROM message_store ORDER BY views DESC LIMIT 10")
    if not rows:
        await update.message.reply_text(LANGUAGES[user_lang]["no_movies_watched"])
        return
    top_list = "\n".join([f"{i + 1}. {row['name']} - {row['movie_code']} ({row['views']} marta ko‘rilgan)"
                          for i, row in enumerate(rows)])
    await update.message.reply_text(LANGUAGES[user_lang]["top_movies"].format(list=top_list))

# Admin funksiyalari (faqat o‘zbekcha statik matn)
@admin_only
@with_db_connection
async def list_users(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await conn.fetch("SELECT user_id, data FROM users")
    if not rows:
        await update.message.reply_text("❌ Hozircha foydalanuvchilar yo‘q.")
        return
    user_list = "\n".join([
        f"ID: {row['user_id']}, Username: {'@' + json.loads(row['data'])['username'] if json.loads(row['data'])['username'] != 'None' else 'None'}, Name: {json.loads(row['data'])['first_name']}"
        for row in rows])
    await update.message.reply_text(f"👥 Foydalanuvchilar ro‘yxati:\n{user_list}")

@admin_only
async def channels_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if channels:
        channel_list = "\n".join([f"ID: {ch_id} | URL: {ch_url}" for ch_id, ch_url in channels])
        await update.message.reply_text(f"📡 Mavjud kanallar:\n{channel_list}")
    else:
        await update.message.reply_text("❌ Hozircha kanal mavjud emas.")

@admin_only
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_list = (
        "🚀 /start - Botni boshlash\n"
        "🌐 /language - Tilni o‘zgartirish\n"
        "📊 /stat - Botning statistikasi\n"
        "🏆 /top - Eng ko‘p tomosha qilingan filmlar\n"
        "👥 /users - Foydalanuvchilar ro‘yxati\n"
        "➕ /addchannel <id> <url> - Kanal qo‘shish\n"
        "➖ /removechannel <id> - Kanal olib tashlash\n"
        "📡 /channels - Mavjud kanallar\n"
        "📢 /broadcast - Xabar tarqatish\n"
        "🛠️ /admin - Admin komandalari\n"
        "ℹ️ /help - Yordam"
    )
    await update.message.reply_text(f"⚙️ Admin komandalari:\n{commands_list}")

@admin_only
@with_db_connection
async def add_channel(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Iltimos, kanal ID va URL ni kiriting. Masalan: /addchannel -100123456789 https://t.me/kanal")
        return

    try:
        channel_id = int(context.args[0])
        channel_url = context.args[1]
    except ValueError:
        await update.message.reply_text("❌ Kanal ID raqam bo‘lishi kerak!")
        return

    if not channel_url.startswith("https://t.me/"):
        await update.message.reply_text("❌ Kanal URL noto‘g‘ri formatda! Masalan: https://t.me/kanal")
        return

    channel_username = channel_url.split("https://t.me/")[-1]
    if any(ch_id == channel_id for ch_id, _ in channels):
        await update.message.reply_text("❌ Bu kanal allaqachon mavjud!")
    else:
        await conn.execute(
            "INSERT INTO channels (channel_id, channel_username) VALUES ($1, $2)",
            channel_id, channel_username
        )
        channels.append((channel_id, channel_url))
        await update.message.reply_text(f"✅ Kanal qo‘shildi!\nID: {channel_id} | URL: {channel_url}")

@admin_only
@with_db_connection
async def remove_channel(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Iltimos, o‘chiriladigan kanal ID sini kiriting. Masalan: /removechannel -100123456789")
        return

    try:
        channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Kanal ID raqam bo‘lishi kerak!")
        return

    result = await conn.execute("DELETE FROM channels WHERE channel_id = $1", channel_id)
    if result == "DELETE 1":
        channels[:] = [(ch_id, ch_url) for ch_id, ch_url in channels if ch_id != channel_id]
        await update.message.reply_text(f"✅ Kanal o‘chirildi! ID: {channel_id}")
    else:
        await update.message.reply_text("❌ Bunday kanal topilmadi!")

@admin_only
@with_db_connection
async def broadcast(conn, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Iltimos, tarqatiladigan xabarga javob bering!")
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
                await context.bot.send_photo(chat_id=user_id, photo=reply_message.photo[-1].file_id, caption=reply_message.caption)
            elif reply_message.video:
                await context.bot.send_video(chat_id=user_id, video=reply_message.video.file_id, caption=reply_message.caption)
            elif reply_message.document:
                await context.bot.send_document(chat_id=user_id, document=reply_message.document.file_id, caption=reply_message.caption)
            elif reply_message.animation:
                await context.bot.send_animation(chat_id=user_id, animation=reply_message.animation.file_id, caption=reply_message.caption)
        except Exception as e:
            logger.warning(f"Xabar yuborishda xato {user_id}: {e}")
            failed_users.append(user_id)
    await update.message.reply_text(f"📢 Xabar tarqatildi! Muvaffaqiyatsiz: {len(failed_users)} foydalanuvchi")

# Kanal postlarini qayta ishlash
async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.caption:
        return
    caption = update.channel_post.caption.strip()
    movie_name = "Nom mavjud emas"
    if 'Nomi:' in caption:
        try:
            name_start = caption.index('Nomi:') + len('Nomi:') + 1
            name_end = caption.index('"', name_start)
            movie_name = caption[name_start:name_end].strip()
        except ValueError:
            logger.warning("Kino nomini ajratib bo‘lmadi.")
    if '<' in caption and '>' in caption:
        code_start = caption.index('<') + 1
        code_end = caption.index('>')
        movie_code = caption[code_start:code_end].strip()
        data = {
            "message_id": update.channel_post.message_id,
            "video": update.channel_post.video.file_id if update.channel_post.video else None,
            "document": update.channel_post.document.file_id if update.channel_post.document else None,
            "caption": caption,
            "name": movie_name,
            "views": 0
        }
        await save_message_store(movie_code, data)
        message_store[movie_code] = data

# Tugma callback’lari
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_lang = users.get(user_id, {}).get("language", "uz")

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        users[user_id]["language"] = lang
        await save_user(user_id, users[user_id])
        await query.edit_message_text(LANGUAGES[lang]["language_changed"])
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=LANGUAGES[lang]["welcome"].format(name=query.from_user.first_name))
    elif query.data == "check_subscription":
        is_subscribed, not_subscribed_channels = await check_subscription(user_id, context.bot)
        if is_subscribed:
            await query.edit_message_text(LANGUAGES[user_lang]["subscribed"])
        else:
            await query.delete_message()
            await send_subscription_prompt(query.message.chat_id, context, not_subscribed_channels, user_lang)

# Asosiy funksiya
async def main():
    await init_db_pool()
    await load_message_store()
    await load_users()
    await load_channels()

    app = ApplicationBuilder().token(TOKEN).build()

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("language", change_language))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("top", top_movies))  # Hamma uchun ochiq
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("removechannel", remove_channel))
    app.add_handler(CommandHandler("channels", channels_cmd))
    app.add_handler(CommandHandler("admin", admin_commands))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_movie))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    app.add_handler(CallbackQueryHandler(button_callback))

    # Xatolik handleri
    async def error_handler(update, context):
        logger.error(f"Xatolik yuz berdi: {context.error}")
        if update and update.message:
            await update.message.reply_text("❌ Nimadir xato ketdi, iltimos keyinroq urinib ko‘ring.")
    app.add_error_handler(error_handler)

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