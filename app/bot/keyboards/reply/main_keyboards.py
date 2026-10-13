from aiogram.types import ReplyKeyboardMarkup
from app.core.emojis import emoji
from app.core.i18n import i18n


def get_main_reply_keyboard(is_admin: bool = False, lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyu Reply klaviaturasi (Qat'iy 1 : 2 : 1 professional formati).
    
    Telegram Premium Custom Emojilar (icon_custom_emoji_id) bilan avtomatik boyitiladi.
    
    Row 1: [ 🏆 TOP Kinolar ]
    Row 2: [ 🌐 Til ] [ ℹ️ Qo'llanma ]
    Row 3: [ 🛡 Boshqaruv ] (Admin uchun) yoki [ 🔍 Qidiruv ] (Foydalanuvchi uchun)
    """
    row1 = [
        emoji.keyboard_btn("top_movies", i18n.get("btn_top", lang))
    ]
    row2 = [
        emoji.keyboard_btn("language", i18n.get("btn_language", lang)),
        emoji.keyboard_btn("help", i18n.get("btn_help", lang))
    ]
    row3 = [
        emoji.keyboard_btn("admin", i18n.get("btn_manage", lang))
        if is_admin
        else emoji.keyboard_btn("search", i18n.get("btn_search", lang))
    ]

    return ReplyKeyboardMarkup(
        keyboard=[row1, row2, row3],
        resize_keyboard=True,
        is_persistent=True
    )


def get_admin_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Admin boshqaruv paneli Reply menyusi (Qat'iy 2 : 2 professional formati).
    
    Telegram Premium Custom Emojilar (icon_custom_emoji_id) bilan boyitilgan.
    
    Row 1: [ 🎬 Kinolar ] [ 📡 Kanallar ]
    Row 2: [ 📢 Xabarnoma ] [ 📊 Statistika ]
    Row 3: [ ⬅️ Asosiy menyu ]
    """
    keyboard = [
        [
            emoji.keyboard_btn("movie", i18n.get("btn_movies_manage", lang)),
            emoji.keyboard_btn("channel", i18n.get("btn_channels_manage", lang))
        ],
        [
            emoji.keyboard_btn("broadcast", i18n.get("btn_broadcast_menu", lang)),
            emoji.keyboard_btn("stats", i18n.get("btn_stats_menu", lang))
        ],
        [
            emoji.keyboard_btn("back", i18n.get("btn_main_menu", lang))
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
