import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmojiService:
    """Telegram Premium/Custom va standart emojilar xizmati.
    
    RULES.md qoidasiga binoan kod ichida emojilar hardcode qilinmaydi.
    Barcha emojilar emojis.json dan dinamik yuklanadi.
    """

    def __init__(self, json_path: str = "emojis.json"):
        self.json_path = Path(json_path)
        self.enabled: bool = False
        self.emojis: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        """emojis.json faylini xotiraga yuklash."""
        if not self.json_path.exists():
            logger.warning(f"{self.json_path} topilmadi! Standart bo'sh rejimda ishlaydi.")
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.enabled = data.get("enabled", False)
                self.emojis = data.get("emojis", {})
                logger.info(f"Dinamik emojilar yuklandi: {len(self.emojis)} ta emoji mavjud.")
        except Exception as e:
            logger.error(f"emojis.json faylini o'qishda xatolik: {e}")

    def get(self, key: str) -> str:
        """Xabar matnlari uchun emoji olish.
        
        Agar Premium yoqilgan bo'lsa va custom_emoji_id mavjud bo'lsa,
        HTML <tg-emoji> formatida qaytaradi. Aks holda oddiy fallback qaytaradi.
        """
        item = self.emojis.get(key)
        if not item:
            return ""

        fallback = item.get("fallback", "")
        custom_id = item.get("custom_emoji_id")

        if self.enabled and custom_id:
            return f'<tg-emoji emoji-id="{custom_id}">{fallback}</tg-emoji>'

        return fallback

    def btn(self, key: str, text: str) -> str:
        """Tugmalar (Buttons) uchun xavfsiz emoji qo'shilgan matn.
        
        Tugmalarda Telegram Custom Emojilar render muammosi bo'lmasligi uchun
        har doim toza fallback unicode emojisi ishlatiladi.
        """
        item = self.emojis.get(key)
        if not item:
            return text

        fallback = item.get("fallback", "")
        if fallback:
            return f"{fallback} {text}"
        return text

    def raw(self, key: str) -> str:
        """Har doim faqat oddiy unicode (fallback) emojini olish."""
        item = self.emojis.get(key)
        if not item:
            return ""
        return item.get("fallback", "")


# Singleton nusxa
emoji = EmojiService()
