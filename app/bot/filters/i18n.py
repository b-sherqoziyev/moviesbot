from typing import Optional
from aiogram.filters import BaseFilter
from aiogram.types import Message
from app.core.i18n import i18n


class I18nButtonFilter(BaseFilter):
    """Foydalanuvchi bosgan Reply tugma matnini barcha 3 ta tildagi lug'atdan dinamik tekshiruvchi filtr.
    
    RULES.md qoidasiga ko'ra kod ichida til matnlarini hardcode qilishni 100% yo'qotadi.
    """

    def __init__(self, key: str, emoji_key: Optional[str] = None):
        self.key = key
        self.emoji_key = emoji_key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False

        incoming = message.text.strip().lower()
        incoming_clean = incoming.replace("\ufe0f", "")
        variants = i18n.get_button_variants(self.key, self.emoji_key)
        variants_clean = [v.replace("\ufe0f", "") for v in variants]

        return incoming in variants or incoming_clean in variants_clean

