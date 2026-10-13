import logging
from typing import Callable
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.emojis import emoji
from app.bot.filters.admin import AdminPermissionFilter
from app.bot.loader import subscription_service
from app.bot.states.admin_states import AdminChannelStates
from app.database.models.channel import Channel
from app.database.repositories.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)
router = Router(name="admin_channels")
router.message.filter(AdminPermissionFilter("channels.manage"))
router.callback_query.filter(AdminPermissionFilter("channels.manage"))


from app.bot.filters.i18n import I18nButtonFilter


async def render_channels_list(session: AsyncSession, _: Callable[..., str]) -> tuple[str, InlineKeyboardMarkup]:
    """Majburiy kanallar ro'yxati matni va boshqaruv klaviaturasini tayyorlash (DRY)."""
    repo = ChannelRepository(session)
    channels = await repo.get_active_channels()

    channel_icon = emoji.get("channel")
    title_text = f"{channel_icon} <b>{_('channel_list_title')}</b>\n"

    if not channels:
        text = title_text + "\n" + _("no_channels")
    else:
        lines = []
        for i, ch in enumerate(channels, 1):
            link = f'<a href="{ch.url}">{ch.title}</a>' if ch.url else f"<b>{ch.title}</b>"
            lines.append(f"{i}. 🟢 {link} (<code>{ch.channel_id}</code>)")
        text = title_text + "\n" + "\n".join(lines)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=emoji.btn("add", _("btn_add_channel")), callback_data="channel_add"),
                InlineKeyboardButton(text=emoji.btn("delete", _("btn_remove_channel")), callback_data="channel_del_list")
            ]
        ]
    )
    return text, markup


@router.message(I18nButtonFilter("btn_channels_manage", emoji_key="channel"))
async def show_admin_channels_list(
    message: Message,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Majburiy a'zolik kanallari ro'yxati va boshqaruvi."""
    text, markup = await render_channels_list(session, _)
    await message.answer(
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "channel_add")
async def cb_channel_add_prompt(
    callback: CallbackQuery,
    state: FSMContext,
    _: Callable[..., str]
) -> None:
    """Kanal qo'shish so'rovi."""
    await state.set_state(AdminChannelStates.waiting_for_channel_id_or_forward)
    prompt = _("add_channel_prompt")
    cancel_btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn_cancel"), callback_data="channel_cancel")]]
    )
    await callback.message.edit_text(text=prompt, reply_markup=cancel_btn)
    await callback.answer()


@router.callback_query(F.data == "channel_del_list")
async def cb_channel_del_list(
    callback: CallbackQuery,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """O'chirish uchun kanallar ro'yxati."""
    repo = ChannelRepository(session)
    channels = await repo.get_active_channels()
    if not channels:
        await callback.answer(_("no_channels"), show_alert=True)
        return

    keyboard = []
    for ch in channels:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 {ch.title}",
                callback_data=f"channel_del:{ch.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text=_("btn_cancel"), callback_data="channel_cancel")])

    await callback.message.edit_text(
        text=_("remove_channel_prompt"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("channel_del:"))
async def cb_channel_del_action(
    callback: CallbackQuery,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Tanlangan kanalni nofaol qilish va ro'yxatga qaytish."""
    channel_db_id = int(callback.data.split(":")[1])
    repo = ChannelRepository(session)
    channel = await repo.get_by_id(channel_db_id)
    if channel:
        await session.delete(channel)
        await session.commit()
        await subscription_service.bump_channels_version()
        # Muvaffaqiyat xabari chatda emas, oynachada (alert) ko'rsatiladi
        await callback.answer(f"✅ {_('channel_removed')}: {channel.title}", show_alert=True)
        # Xabar esa darhol yangilangan kanallar ro'yxatiga qaytadi
        text, markup = await render_channels_list(session, _)
        await callback.message.edit_text(
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        await callback.answer("Kanal topilmadi!", show_alert=True)


@router.callback_query(F.data == "channel_cancel")
async def cb_channel_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kanal amallarini bekor qilish va asosiy ro'yxatga qaytish."""
    await state.clear()
    await callback.answer("Amal bekor qilindi.")
    text, markup = await render_channels_list(session, _)
    await callback.message.edit_text(
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )



@router.message(AdminChannelStates.waiting_for_channel_id_or_forward)
async def process_add_channel(
    message: Message,
    state: FSMContext,
    bot: Bot,
    session: AsyncSession,
    _: Callable[..., str]
) -> None:
    """Kanal ID yoki forward qilingan postdan kanalni bazaga qo'shish."""
    channel_id = None
    title = None
    invite_link = None
    err_icon = emoji.get("error") or "❌"

    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        title = message.forward_from_chat.title or "Kanal"
        if message.forward_from_chat.username:
            invite_link = f"https://t.me/{message.forward_from_chat.username}"
    else:
        text = message.text.strip()
        # 1. Agar shunchaki @username yoki t.me/username yuborilgan bo'lsa
        if text.startswith("@") or (text.startswith("https://t.me/") and " " not in text and "+" not in text):
            try:
                username = text.replace("https://t.me/", "").replace("@", "").strip()
                chat = await bot.get_chat(f"@{username}")
                channel_id = chat.id
                title = chat.title or username
                invite_link = f"https://t.me/{username}"
            except Exception as e:
                await message.reply(
                    f"{err_icon} <b>Kanal topilmadi:</b> {e}\n\n"
                    f"Iltimos, botni kanalga ADMIN qilib tayinlanganini tekshiring."
                )
                return
        else:
            parts = text.split()
            try:
                channel_id = int(parts[0])
            except ValueError:
                await message.reply(
                    f"{err_icon} <b>Kanal ID raqam bo'lishi kerak!</b>\n"
                    f"Masalan: <code>-1002344042559 https://t.me/kanal</code>"
                )
                return

            if len(parts) == 2:
                # 2 ta parametr: [ID, HAVOLA] yoki [ID, NOMI]
                if parts[1].startswith("http") or parts[1].startswith("@"):
                    invite_link = parts[1]
                    title = f"Kanal {channel_id}"
                else:
                    title = parts[1]
            elif len(parts) >= 3:
                # 3 ta parametr: [ID, NOMI, HAVOLA]
                title = parts[1]
                invite_link = parts[2]
            else:
                title = f"Kanal {channel_id}"

    # Botning kanalga a'zo / adminligini tekshirish va ma'lumotlarni boyitish
    try:
        chat = await bot.get_chat(channel_id)
        if chat.title:
            title = chat.title
        if not invite_link:
            if chat.username:
                invite_link = f"https://t.me/{chat.username}"
            elif chat.invite_link:
                invite_link = chat.invite_link
            else:
                try:
                    inv = await bot.create_chat_invite_link(channel_id)
                    invite_link = inv.invite_link
                except Exception as ex:
                    logger.warning(f"Taklif havolasi yaratib bo'lmadi: {ex}")
    except Exception as e:
        logger.warning(f"Bot kanaldan to'liq ma'lumot ololmadi ({channel_id}): {e}")
        # Agar havola ham berilmagan bo'lsa va bot kanalni ko'ra olmasa
        if not invite_link:
            await message.reply(
                f"{err_icon} <b>Bot kanalni topa olmadi!</b>\n\n"
                f"1. Botni <code>{channel_id}</code> kanaliga <b>ADMIN</b> qilib qo'shing;\n"
                f"2. Yoki kanal taklif havolasini ham qo'shib yuboring:\n"
                f"<code>{channel_id} https://t.me/...</code>"
            )
            return

    repo = ChannelRepository(session)
    existing = await repo.get_by_channel_id(channel_id)
    if existing:
        existing.title = title
        existing.is_active = True
        if invite_link:
            existing.url = invite_link
        await session.commit()
    else:
        ch = Channel(
            channel_id=channel_id,
            title=title,
            url=invite_link or "",
            is_active=True
        )
        session.add(ch)
        await session.commit()

    # RULES.md 4.3: Barcha keshlarni 0 soniyada yangilash
    await subscription_service.bump_channels_version()
    await state.clear()

    await message.reply(text=f"✅ {_('channel_added')}: <b>{title}</b>")
    text, markup = await render_channels_list(session, _)
    await message.answer(
        text=text,
        reply_markup=markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


