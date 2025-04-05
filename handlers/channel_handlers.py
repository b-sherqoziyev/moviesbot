from telegram import Update
from telegram.ext import ContextTypes
from database.db_operations import save_message_store
import logging

logger = logging.getLogger(__name__)

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
        await save_message_store(context.bot_data["db_pool"], movie_code, data)
        context.bot_data["message_store"][movie_code] = data