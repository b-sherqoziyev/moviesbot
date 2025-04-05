from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

logger = logging.getLogger(__name__)

async def check_subscription(user_id, bot, channels):
    not_subscribed_channels = []
    for channel_id, channel_url in channels:
        try:
            chat_member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status not in ['member', 'administrator', 'creator']:
                not_subscribed_channels.append((channel_id, channel_url))
        except Exception as e:
            logger.warning(f"Kanal {channel_id} tekshirilganda xatolik: {e}")
            not_subscribed_channels.append((channel_id, channel_url))
    return len(not_subscribed_channels) == 0, not_subscribed_channels

async def send_subscription_prompt(chat_id, context, not_subscribed_channels, user_lang):
    from locales.languages import LANGUAGES
    if not not_subscribed_channels:
        await context.bot.send_message(chat_id=chat_id, text=LANGUAGES[user_lang]["subscribed"])
        return

    keyboard = [[InlineKeyboardButton(f"Kanal {i + 1}", url=channel_url)]
                for i, (_, channel_url) in enumerate(not_subscribed_channels)]
    keyboard.append([InlineKeyboardButton(LANGUAGES[user_lang]["check_subscription"], callback_data='check_subscription')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text=LANGUAGES[user_lang]["subscribe_prompt"], reply_markup=reply_markup)