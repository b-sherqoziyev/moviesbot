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

    for i, ch in enumerate(unsubscribed_channels, start=1):
        btn_text = emoji.btn("channel", f"{ch.title}")
        keyboard.append([InlineKeyboardButton(text=btn_text, url=ch.url)])

    # A'zolikni tekshirish tugmasi
    check_text = emoji.btn("check", i18n.get("btn_check_sub", lang=user_lang))
    cb_data = f"check_sub:{pending_code}" if pending_code else "check_sub"
    keyboard.append([InlineKeyboardButton(text=check_text, callback_data=cb_data)])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Tilni tanlash inline klaviaturasi."""
    keyboard = [
        [
            InlineKeyboardButton(text=emoji.btn("flag_uz", "O'zbekcha"), callback_data="set_lang:uz"),
            InlineKeyboardButton(text=emoji.btn("flag_ru", "Русский"), callback_data="set_lang:ru"),
            InlineKeyboardButton(text=emoji.btn("flag_en", "English"), callback_data="set_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
