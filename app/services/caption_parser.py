import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class ParsedMovieData:
    """Tahlil qilingan kino ma'lumotlari modeli."""
    code: Optional[str] = None
    title: str = "Nomsiz Film"
    release_year: Optional[int] = None
    rating: Optional[float] = None
    country: Optional[str] = None
    language: Optional[str] = None
    quality: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    description: Optional[str] = None
    promo_link: Optional[str] = None


class SmartCaptionParser:
    """Kanal postining izohidan (caption) kinoning barcha parametrlarini
    tartibidan va yozilish uslubidan qat'i nazar aqlli ajratib oluvchi tahlilchi (Heuristic NLP Parser).
    """

    # Lug'atlar (Normalizatsiya uchun)
    LANGUAGES = {
        "ozbek": "O'zbek tili",
        "o'zbek": "O'zbek tili",
        "oʻzbek": "O'zbek tili",
        "o‘zbek": "O'zbek tili",
        "uzbek": "O'zbek tili",
        "tarjima": "O'zbek tili (Tarjima)",
        "dublyaj": "O'zbek tili (Dublyaj)",
        "rus": "Rus tili",
        "ruscha": "Rus tili",
        "russian": "Rus tili",
        "ingliz": "Ingliz tili",
        "inglizcha": "Ingliz tili",
        "english": "Ingliz tili",
        "turk": "Turk tili",
        "turkcha": "Turk tili",
        "turkish": "Turk tili",
        "koreys": "Koreys tili",
        "koreyscha": "Koreys tili",
        "korean": "Koreys tili",
        "hind": "Hind tili",
        "hindcha": "Hind tili",
    }

    COUNTRIES = {
        "aqsh": "AQSH",
        "usa": "AQSH",
        "amerika": "AQSH",
        "rossiya": "Rossiya",
        "russia": "Rossiya",
        "o'zbekiston": "O'zbekiston",
        "ozbekiston": "O'zbekiston",
        "uzbekistan": "O'zbekiston",
        "turkiya": "Turkiya",
        "turkey": "Turkiya",
        "koreya": "Janubiy Koreya",
        "janubiy koreya": "Janubiy Koreya",
        "korea": "Janubiy Koreya",
        "hindiston": "Hindiston",
        "india": "Hindiston",
        "buyuk britaniya": "Buyuk Britaniya",
        "angliya": "Buyuk Britaniya",
        "uk": "Buyuk Britaniya",
        "fransiya": "Fransiya",
        "france": "Fransiya",
        "germaniya": "Germaniya",
        "germany": "Germaniya",
        "yaponiya": "Yaponiya",
        "japan": "Yaponiya",
        "xitoy": "Xitoy",
        "china": "Xitoy",
        "ispaniya": "Ispaniya",
        "spain": "Ispaniya",
        "italiya": "Italiya",
        "italy": "Italiya",
        "qozog'iston": "Qozog'iston",
        "qozogiston": "Qozog'iston",
    }

    GENRES = {
        "jangari": "Jangari",
        "boyevik": "Jangari",
        "boevik": "Jangari",
        "action": "Jangari",
        "komediya": "Komediya",
        "comedy": "Komediya",
        "drama": "Drama",
        "triller": "Triller",
        "thriller": "Triller",
        "fantastika": "Fantastika",
        "fantastik": "Fantastika",
        "sci-fi": "Fantastika",
        "sarguzasht": "Sarguzasht",
        "adventure": "Sarguzasht",
        "qo'rqinchli": "Qo'rqinchli",
        "qorqinchli": "Qo'rqinchli",
        "dahshat": "Qo'rqinchli",
        "horror": "Qo'rqinchli",
        "melodrama": "Melodrama",
        "romance": "Melodrama",
        "multfilm": "Multfilm",
        "multik": "Multfilm",
        "animatsiya": "Multfilm",
        "animation": "Multfilm",
        "anime": "Anime",
        "detektiv": "Detektiv",
        "detective": "Detektiv",
        "kriminal": "Kriminal",
        "jinoyat": "Kriminal",
        "crime": "Kriminal",
        "tarixiy": "Tarixiy",
        "history": "Tarixiy",
        "harbiy": "Harbiy",
        "urush": "Harbiy",
        "war": "Harbiy",
        "oilaviy": "Oilaviy",
        "family": "Oilaviy",
        "hujjatli": "Hujjatli",
        "documentary": "Hujjatli",
    }

    @classmethod
    def clean_title(cls, text: str) -> str:
        """Kino nomini oldidagi emojilar, strelkalar va ortiqcha bezak belgilaridan tozalash."""
        if not text:
            return "Nomsiz Film"
        t = text.strip()
        # 1. Oldidagi barcha emojilar va no-harf belgilarni olib tashlash
        t = re.sub(r'^[^\w"\'«»]+', '', t, flags=re.UNICODE).strip()
        # 2. Qolgan strelkalar yoki separatorlarni tozalash
        t = re.sub(r'^(?:➺|➜|➔|➤|->|—|-|:)\s*', '', t).strip()
        # 3. Qo'shtirnoqlarni tozalash
        t = t.strip('"\'«» ')
        return t or "Nomsiz Film"

    @classmethod
    def parse(cls, caption: Optional[str]) -> ParsedMovieData:
        """Berilgan xom caption matnidan barcha parametrlarni ajratib olish."""
        result = ParsedMovieData()
        if not caption or not caption.strip():
            return result

        raw_text = caption.strip()
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

        # 1. Havolalar (Links) ni ajratish
        remaining_lines = []
        for line in lines:
            link_match = re.search(r'(https?://\S+|t\.me/\S+|@[\w_]+)', line, re.IGNORECASE)
            if link_match and len(line) < 100 and ('http' in line.lower() or 't.me' in line.lower() or line.startswith('@')):
                result.promo_link = link_match.group(1)
            else:
                remaining_lines.append(line)

        # 2. Kalit so'zli (Labeled) va Emojili qatorlarni birinchi navbatda tahlil qilish
        unprocessed_lines = []
        for line in remaining_lines:
            # Kod belgisi (<122>, [122], #122)
            bracket_code = re.search(r'^[<\[#]([a-zA-Z0-9_-]+)[>\]]?$', line.strip())
            if bracket_code and not result.code:
                result.code = bracket_code.group(1).strip()
                continue

            # Kod label: Kodi: 122
            code_label = re.search(r'^(?:[^\w\s]*\s*)?(?:kodi|kod|code|id)\s*[:=-]\s*([a-zA-Z0-9_-]+)', line, re.IGNORECASE)
            if code_label and not result.code:
                result.code = code_label.group(1).strip()
                continue

            # Nom: 🎬, 🍿, 🎥, 🎞, 📽 bilan boshlangan yoki Nomi:, Kino:, Film: label
            title_match = re.search(r'^(?:nomi|nom|kino|film|title|name)\s*[:=-]\s*(.+)', line, re.IGNORECASE)
            if not title_match:
                title_match = re.search(r'^(?:🎬|🍿|🎥|🎞|📽)\s*(?:➺|➜|➔|➤|->|—|-|:)?\s*(.+)', line)

            if title_match and result.title == "Nomsiz Film":
                raw_title = cls.clean_title(title_match.group(1))
                in_title_year = re.search(r'\((\d{4})\)', raw_title)
                if in_title_year and not result.release_year:
                    result.release_year = int(in_title_year.group(1))
                    raw_title = re.sub(r'\(\d{4}\)', '', raw_title).strip()
                result.title = raw_title
                continue

            # Yil label: Yili: 2008 yoki 📅 Yili: 2008
            year_label = re.search(r'^(?:[^\w\s]*\s*)?(?:yili|yil|year)\s*[:=-]\s*(\d{4})', line, re.IGNORECASE)
            if year_label and not result.release_year:
                result.release_year = int(year_label.group(1))
                continue

            # Reyting label: IMDb: 9.0
            rating_label = re.search(r'^(?:[^\w\s]*\s*)?(?:imdb|kinopoisk|rating|reyting|baho)\s*[:=-]\s*(\d+(?:[.,]\d+)?)', line, re.IGNORECASE)
            if rating_label and not result.rating:
                try:
                    result.rating = float(rating_label.group(1).replace(",", "."))
                except ValueError:
                    pass
                continue

            # Sifat label: Sifati: 1080p yoki 📀 Sifati: 720p HD
            quality_label = re.search(r'^(?:[^\w\s]*\s*)?(?:sifati|sifat|quality)\s*[:=-]\s*(\d{3,4}\s*p|4k|2k|hd|fhd)', line, re.IGNORECASE)
            if quality_label and not result.quality:
                result.quality = quality_label.group(1).replace(" ", "").lower()
                continue

            # Til label: Tili: O'zbek tili yoki 🇺🇿 Tili: O'zbek tilida
            lang_label = re.search(r'^(?:[^\w\s]*\s*)?(?:tili|til|language|lang)\s*[:=-]\s*(.+)', line, re.IGNORECASE)
            if lang_label and not result.language:
                val = lang_label.group(1).strip()
                normalized = cls._find_dict_match(val, cls.LANGUAGES)
                result.language = normalized if normalized else val
                continue

            # Davlat label: Davlati: AQSH, Fransiya yoki 🌍 Davlati: AQSH
            country_label = re.search(r'^(?:[^\w\s]*\s*)?(?:davlati|davlat|countries|country)\s*[:=-]\s*(.+)', line, re.IGNORECASE)
            if country_label and not result.country:
                val = country_label.group(1).strip()
                extracted_countries = cls._extract_countries(val)
                if extracted_countries:
                    result.country = ", ".join(extracted_countries)
                else:
                    normalized = cls._find_dict_match(val, cls.COUNTRIES)
                    result.country = normalized if normalized else val
                continue

            # Janr label: Janri: Jangari, Triller yoki ⚔ Janri: Jangari
            genre_label = re.search(r'^(?:[^\w\s]*\s*)?(?:janri|janr|genres?)\s*[:=-]\s*(.+)', line, re.IGNORECASE)
            if genre_label:
                genre_str = genre_label.group(1).strip()
                result.genres.extend(cls._extract_genres(genre_str))
                continue

            # Tavsif label: Tavsif: ...
            desc_label = re.search(r'^(?:[^\w\s]*\s*)?(?:tavsif|haqida|desc|description|mazmuni)\s*[:=-]\s*(.+)', line, re.IGNORECASE)
            if desc_label and not result.description:
                result.description = desc_label.group(1).strip()
                continue

            unprocessed_lines.append(line)

        # 3. Label yo'q, erkin satrlar (Heuristic Entity Extraction)
        still_unclaimed = []
        for line in unprocessed_lines:
            clean = line.strip().strip('"\'«»')
            lower_clean = clean.lower()

            # A. Sifat (masalan: 720p, 1080p, 720 p, 4k)
            quality_match = re.search(r'\b(\d{3,4}\s*p|4k|2k|fhd|hd)\b', lower_clean)
            if quality_match and not result.quality:
                result.quality = quality_match.group(1).replace(" ", "").lower()
                continue

            # B. Reyting (masalan: 9.0, 8.5)
            rating_match = re.match(r'^\s*(\d{1,2}[.,]\d)\s*$', clean)
            if rating_match and not result.rating:
                try:
                    val = float(rating_match.group(1).replace(",", "."))
                    if 0.0 <= val <= 10.0:
                        result.rating = val
                        continue
                except ValueError:
                    pass

            # C. Yil (masalan: 2008, 1999)
            year_match = re.match(r'^\s*(19\d{2}|20\d{2})\b', clean)
            if year_match and not result.release_year:
                result.release_year = int(year_match.group(1))
                continue

            # D. Til tekshiruvi (lug'at bo'yicha)
            matched_lang = cls._find_dict_match(lower_clean, cls.LANGUAGES)
            if matched_lang and not result.language:
                result.language = matched_lang
                continue

            # E. Davlat tekshiruvi (faqat davlat indikatori bo'lsa yoki qatordagi so'zlar faqat davlatlardan iborat bo'lsa)
            is_country_indicator = bool(re.search(r'(?:🌍|🌎|🌏|davlat|filmi|mamlakat|ishlab)', lower_clean))
            matched_countries = cls._extract_countries(lower_clean)
            if matched_countries and not result.country:
                words_in_line = [w for w in re.findall(r"[\wʻ'‘]+", lower_clean) if len(w) > 1]
                is_pure_country = bool(words_in_line and all(w in cls.COUNTRIES for w in words_in_line))

                # 1. Davlat indikatori bo'lsa (🌍 ➺ Rossiya filmi)
                # 2. 2 yoki undan ortiq davlat yozilgan bo'lsa (Germaniya Amerika Ispaniya)
                # 3. Yoki qatordagi so'zlar FAQAT davlat nomidan iborat bo'lsa (masalan 'AQSH' yoki 'Rossiya')
                # (Agar 'Kapitan Amerika' kabi nom bo'lsa, 'Kapitan' so'zi borligi sababli davlat deb olinmaydi)
                if is_country_indicator or len(matched_countries) >= 2 or is_pure_country:
                    result.country = ", ".join(matched_countries)
                    continue

            # F. Janr tekshiruvi (faqat janr indikatori bo'lsa yoki qatordagi so'zlar faqat janrlardan iborat bo'lsa)
            is_genre_indicator = bool(re.search(r'(?:🎭|⚔|janr|genres?)', lower_clean))
            extracted_genres = cls._extract_genres(lower_clean)
            if extracted_genres:
                words_in_line = [w for w in re.findall(r"[\wʻ'‘]+", lower_clean) if len(w) > 1]
                is_pure_genre = bool(words_in_line and all(w in cls.GENRES for w in words_in_line))
                if is_genre_indicator or len(extracted_genres) >= 2 or is_pure_genre:
                    result.genres.extend(extracted_genres)
                    continue

            # G. Butun son (Kino kodi bo'lishi mumkin: 122)
            if clean.isdigit() and not result.code:
                num = int(clean)
                if not (1900 <= num <= 2099) or result.release_year is not None:
                    result.code = clean
                    continue

            still_unclaimed.append(clean)

        # 4. Qolgan satrlardan Nom va Kod / Tavsifni aniqlash
        for line in still_unclaimed:
            # Agar nom hali topilmagan bo'lsa
            if result.title == "Nomsiz Film":
                clean_t = cls.clean_title(line)
                in_title_year = re.search(r'\((\d{4})\)', clean_t)
                if in_title_year and not result.release_year:
                    result.release_year = int(in_title_year.group(1))
                    clean_t = re.sub(r'\(\d{4}\)', '', clean_t).strip()
                result.title = clean_t
            elif not result.code and line.isdigit():
                result.code = line.strip()
            elif len(line) > 30 and not result.description:
                result.description = line.strip()

        # Janrlardagi dublikatlarni tozalash
        result.genres = list(dict.fromkeys(result.genres))

        return result

    @classmethod
    def detect_quality_from_resolution(cls, width: Optional[int], height: Optional[int]) -> Optional[str]:
        """Telegram video o'lchamidan (piksellaridan) sifatni 100% avtomatik aniqlash."""
        if not width and not height:
            return None
        h = height or 0
        w = width or 0
        if h >= 2160 or w >= 3840:
            return "4k"
        if h >= 1440 or w >= 2560:
            return "2k"
        if h >= 1080 or w >= 1920:
            return "1080p"
        if h >= 720 or w >= 1280:
            return "720p"
        if h >= 480 or w >= 848:
            return "480p"
        if h >= 360 or w >= 640:
            return "360p"
        return None

    @classmethod
    def _find_dict_match(cls, text: str, dictionary: dict) -> Optional[str]:
        """Matn ichidan lug'atdagi kalitni qidirish."""
        text_lower = text.lower().strip()
        for key, val in dictionary.items():
            pattern = rf'\b{re.escape(key)}\b'
            if re.search(pattern, text_lower):
                return val
        return None

    @classmethod
    def _extract_countries(cls, text: str) -> List[str]:
        """Matn ichidan barcha davlatlarni ro'yxat qilib ajratib olish (AQSH, Fransiya va h.k.)."""
        found = []
        text_lower = text.lower().strip()
        for key, val in cls.COUNTRIES.items():
            pattern = rf'\b{re.escape(key)}\b'
            if re.search(pattern, text_lower):
                if val not in found:
                    found.append(val)
        return found

    @classmethod
    def _extract_genres(cls, text: str) -> List[str]:
        """Matn ichidan bir yoki bir nechta janrni ajratib olish (masalan 'jangari, fantastika')."""
        found = []
        text_lower = text.lower().strip()
        for key, val in cls.GENRES.items():
            pattern = rf'\b{re.escape(key)}\b'
            if re.search(pattern, text_lower):
                if val not in found:
                    found.append(val)
        return found
