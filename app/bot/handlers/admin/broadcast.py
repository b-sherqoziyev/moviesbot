import logging
from typing import Callable
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from app.core.emojis import emoji
from app.bot.filters.admin import AdminPermissionFilter
from app.bot.states.broadcast_states import BroadcastStates
from app.services.broadcast_service import BroadcastService

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")
router.message.filter(AdminPermissionFilter("broadcast.send"))
router.callback_query.filter(AdminPermissionFilter("broadcast.send"))


from app.bot.filters.i18n import I18nButtonFilter


@router.message(I18nButtonFilter("btn_broadcast_menu", emoji_key="broadcast"))
async def cmd_broadcast_start(
    message: Message,
    state: FSMContext,
    _: Callable[..., str]
) -> None:
    """Xabar tarqatishni boshlash buyrug'i."""
    await state.set_state(BroadcastStates.waiting_for_message)
    prompt_text = _("broadcast_prompt")
    cancel_btn = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=_("btn_cancel"), callback_data="broadcast_cancel")]]
    )
    await message.answer(text=prompt_text, reply_markup=cancel_btn)


@router.callback_query(F.data == "broadcast_cancel")
async def cb_broadcast_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    _: Callable[..., str]
) -> None:
    """Broadcastni bekor qilish."""
    await state.clear()
    await callback.answer(f"🚫 {_('broadcast_cancelled')}", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(
    message: Message,
    state: FSMContext,
    _: Callable[..., str]
) -> None:
    """Tarqatiladigan xabarni saqlash va tasdiqlash tugmasini ko'rsatish."""
    await state.update_data(
        from_chat_id=message.chat.id,
        message_id=message.message_id
    )
    await state.set_state(BroadcastStates.confirm_broadcast)

    confirm_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborishni boshlash", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text=_("btn_cancel"), callback_data="broadcast_cancel")
            ]
        ]
    )
    await message.reply(
        text="Ushbu xabarni barcha faol foydalanuvchilarga yuborishni tasdiqlaysizmi?",
        reply_markup=confirm_markup
    )


@router.callback_query(F.data == "broadcast_confirm", BroadcastStates.confirm_broadcast)
async def process_broadcast_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    _: Callable[..., str]
) -> None:
    """Xabar tarqatishni fonda ishga tushirish."""
    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    await state.clear()

    broadcast_service = BroadcastService(bot)
    await broadcast_service.start_broadcast(
        from_chat_id=from_chat_id,
        message_id=message_id,
        admin_id=callback.from_user.id
    )

    start_text = _("broadcast_started")
    await callback.answer(f"📢 {start_text}", show_alert=True)
    try:
        await callback.message.delete()
    except Exception:
        pass

