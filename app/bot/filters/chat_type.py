from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(BaseFilter):
    """Chat turini (private, group, supergroup, channel) tekshiruvchi filtr."""

    def __init__(self, chat_type: Union[str, list[str]]):
        self.chat_type = [chat_type] if isinstance(chat_type, str) else chat_type

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        chat = event.chat if isinstance(event, Message) else (event.message.chat if event.message else None)
        if not chat:
            return False
        return chat.type in self.chat_type
