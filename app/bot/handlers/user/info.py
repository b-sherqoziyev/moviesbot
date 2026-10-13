import logging
from typing import Callable
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import settings
from app.core.emojis import emoji

from app.bot.filters.i18n import I18nButtonFilter

logger = logging.getLogger(__name__)
router = Router(name="user_help")


@router.message(Command("help"))
@router.message(I18nButtonFilter("btn_help", emoji_key="help"))
async def handle_help_command(
    message: Message,
    _: Callable[..., str]
) -> None:
    """Foydalanuvchilar uchun qisqa, minimalist va qulay qo'llanma."""
    help_icon = emoji.get("help")
    popcorn_icon = emoji.get("popcorn")
    channel_icon = emoji.get("broadcast")

    channel_info = ""
    clean_ch = settings.main_channel_username
    if clean_ch:
        channel_info = f"\n━━━━━━━━━━━━━━━━━━━━\n{channel_icon} <b>{_('movie_label_channel')}:</b> <a href=\"https://t.me/{clean_ch}\">@{clean_ch}</a>"

    text = (
        f"{help_icon} <b>{_('help_title')}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{popcorn_icon} <b>{_('help_how_to')}</b>\n"
        f"• {_('help_by_code')}\n"
        f"• {_('help_by_title')}\n\n"
        f"⚡️ <b>{_('help_commands')}</b>\n"
        f"/start — {_('help_cmd_start')}\n"
        f"/top — {_('help_cmd_top')}\n"
        f"/language — {_('help_cmd_lang')}\n"
        f"/help — {_('help_cmd_help')}"
        f"{channel_info}"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
