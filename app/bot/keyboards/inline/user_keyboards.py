from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.emojis import emoji
from app.core.i18n import i18n
from app.database.models.channel import Channel


def get_subscription_keyboard(
    unsubscribed_channels: List[Channel],
    user_lang: str = "uz",
    pending_code: Optional[str] = None
) -> InlineKeyboardMarkup:
    """Majburiy kanallarga a'zo bo'lish va tekshirish tugmalari."""
    keyboard: List[List[InlineKeyboardButton]] = []

    total = len(unsubscribed_channels)
    for i, ch in enumerate(unsubscribed_channels, start=1):
        if total > 1:
            btn_text = i18n.get("sub_channel_item", lang=user_lang, num=i)
        else:
            btn_text = i18n.get("sub_channel_single", lang=user_lang)
        keyboard.append([
            emoji.inline_btn("speaker", btn_text, url=ch.url)
        ])


    # A'zolikni tekshirish tugmasi
    cb_data = f"check_sub:{pending_code}" if pending_code else "check_sub"
    check_btn = emoji.inline_btn("check", i18n.get("btn_check_sub", lang=user_lang), callback_data=cb_data)
    keyboard.append([check_btn])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Tilni tanlash inline klaviaturasi (Telegram Premium Custom Emojilar bilan)."""
    keyboard = [
        [
            emoji.inline_btn("flag_uz", "O'zbekcha", callback_data="set_lang:uz"),
            emoji.inline_btn("flag_ru", "Русский", callback_data="set_lang:ru"),
            emoji.inline_btn("flag_en", "English", callback_data="set_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
