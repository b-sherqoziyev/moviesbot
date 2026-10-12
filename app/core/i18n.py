import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class I18nService:
    """Ko'p tillilik (Internationalization) xizmati.
    
    RULES.md qoidasiga ko'ra kod ichida UI matnlari hardcode qilinmaydi.
    Barcha matnlar uz, ru, en JSON fayllaridan olinadi.
    """

    SUPPORTED_LANGUAGES = ("uz", "ru", "en")
    DEFAULT_LANGUAGE = "uz"

    def __init__(self, locales_dir: str = "app/locales"):
        self.locales_dir = Path(locales_dir)
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load()

    def load(self) -> None:
        """Barcha til lug'atlarini xotiraga yuklash."""
        for lang in self.SUPPORTED_LANGUAGES:
            file_path = self.locales_dir / f"{lang}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                    logger.info(f"Til lug'ati yuklandi: {lang} ({len(self.translations[lang])} ta kalit)")
                except Exception as e:
                    logger.error(f"{file_path} ni o'qishda xatolik: {e}")
                    self.translations[lang] = {}
            else:
                logger.warning(f"Lug'at fayli topilmadi: {file_path}")
                self.translations[lang] = {}

    def get(self, key: str, lang: str = "uz", **kwargs: Any) -> str:
        """Kalit va til bo'yicha matnni olish.
        
        Agar so'ralgan tilda kalit topilmasa, avtomatik ravishda standart 'uz'
        tiliga o'tadi (Graceful Fallback).
        """
        # Tilni normallashtirish
        if not lang or lang not in self.SUPPORTED_LANGUAGES:
            lang = self.DEFAULT_LANGUAGE

        # 1. Asosiy tildan qidirish
        text = self.translations.get(lang, {}).get(key)

        # 2. Topilmasa standart 'uz' tilidan qidirish
        if text is None and lang != self.DEFAULT_LANGUAGE:
            text = self.translations.get(self.DEFAULT_LANGUAGE, {}).get(key)

        # 3. Hech qayerda topilmasa, kalitning o'zini xavfsiz qaytarish
        if text is None:
            logger.warning(f"I18n kaliti topilmadi: '{key}' (til: {lang})")
            return f"[{key}]"

        # 4. Parametrlarni xavfsiz joylashtirish
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"I18n formatlashda yetishmayotgan parametr {e} (kalit: '{key}')")
                return text

        return text


# Singleton nusxa va qulay alias
i18n = I18nService()
_ = i18n.get
