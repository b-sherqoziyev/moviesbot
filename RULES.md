# 🎬 Movies Reel (Cinema Bot) - Loyiha Qoidalari va Muhandislik Tamoyillari

Ushbu hujjat **Movies Reel** loyihasida kod yozuvchi dasturchilar va Sun'iy Intellekt yordamchilari (AI Assistants / Agents) uchun **qat'iy muhandislik qoidalarini** belgilaydi. Loyihaga kiritilayotgan har qanday o'zgarish (kod, fayl, arxitektura) ushbu tamoyillarga to'la mos kelishi shart.

---

## 1. Qatlamli Arxitektura va DRY (Layered Architecture & Separation of Concerns)
- **Handlers faqat boshqaruvchi (Dispatcher):** Handlerlar faqat Telegramdan kelgan so'rovni qabul qiladi, mos servisni chaqiradi va natijani foydalanuvchiga yuboradi. Handler ichida to'g'ridan-to'g'ri biznes logika yoki murakkab amallar yozilishi qat'iyan man etiladi!
  - *Misol:* `/start` komandasi juda ko'p amallarni bajaradi (deep-link/film kodini o'qish, foydalanuvchini ro'yxatga olish, tilni tekshirish, majburiy kanal obunasini tekshirish, bosh menyuni shakllantirish). Ushbu amallarning barchasi `start.py` da emas, balki `UserService`, `SubscriptionService`, `MovieService` larda yoziladi va faqat chaqiriladi.
- **DRY (Don't Repeat Yourself):** Hech bir logika, SQL so'rov yoki UI komponenti takrorlanmasligi kerak. Barcha umumiy amallar Repositories va Services qatlamlarida markazlashadi.
- **SOLID tamoyillari:** Har bir modul faqat bitta mas'uliyatga ega bo'ladi (SRP). Baza operatsiyalari faqat `repositories/`, biznes qoidalar faqat `services/` ichida bo'ladi.

---

## 2. Qat'iy Virtual Muhit (Virtual Environment Strictness)
- Loyihaga oid har qanday kutubxona o'rnatish (`pip install ...`), dasturni ishga tushirish (`python main.py`) va migratsiyalar (`alembic ...`) **faqatgina joriy loyihadagi `.venv` muhiti ichida** bajarilishi qat'iyan talab qilinadi.
- Global operatsion tizim Python muhitiga mutlaqo tegish taqiqlanadi. Buyruqlar har doim `.venv\Scripts\...` (Windows) orqali bajarilishi shart.

---

## 3. Dinamik va Premium Emojilar Tizimi (Dynamic Emojis)
- Kod ichida, `.py` fayllarda emojilarni **hardcode qilib yozish QAT'IYAN TAQIQLANADI** (masalan, `text="🎬 Kinolar"` yoki `text="🔍 Qidiruv"` deb yozish mumkin emas).
- Barcha emojilar `emojis.json` orqali markazlashgan servis yordamida olinadi: `emojis.get("movie")` yoki `emojis.get("search")`.
- **Telegram Premium / Custom Emoji qo'llab-quvvatlash:**
  - `emojis.json` faylida har bir emoji uchun `fallback` (oddiy unicode emoji) va `custom_emoji_id` (Telegram Premium Custom Emoji ID) mavjud.
  - Agar bot egasida Premium mavjud bo'lsa va `enabled: true` qilinsa, tizim avtomatik ravishda HTML `<tg-emoji emoji-id="12345">🎬</tg-emoji>` ko'rinishida yuboradi.
  - Agar Premium yo'q bo'lsa yoki o'chirilsa, bot xatosiz va avtomatik ravishda oddiy `fallback` emojiga qaytadi (Graceful Degradation).

---

## 4. Qat'iy Ko'p Tillilik (i18n - No Hardcoded Strings)
- Bot xabarlari, tugma nomlari, ogohlantirishlar va admin panel yozuvlarining barchasi **qattiq (hardcode) yozilishi qat'iyan man etiladi**.
- Barcha matnlar `app/locales/` ichidagi fayllardan (`uz.json`, `ru.json`, `en.json`) kalitlar bo'yicha olinishi shart: masalan, `_("welcome_text", name=user.first_name)`.
- Loyihaga yangi xabar yoki tugma qo'shilganda, uning kaliti darhol har uchala tildagi JSON fayllarga kiritilishi shart.

---

## 5. Kino Bot UX va Yuqori Yuklamaga Moslik (Scalability & Non-blocking)
- **Keshlashtirilgan Obuna Tekshiruvi:** Foydalanuvchi har safar kino so'raganda Telegram API ga N+1 so'rov yuborib botni vaqtincha bloklanishiga (`FloodWait / 429`) yo'l qo'ymaslik uchun, a'zolik natijalari qisqa muddatga keshlanishi (Cache) lozim.
- **Xavfsiz Xabar Tarqatish (Broadcast):** Broadcast buyrug'i asinxron va nazoratli (Rate Limiting: sekundiga ~25-30 xabar) fonda bajariladi. U hech qachon botning asosiy oqimini qotirib qo'ymasligi va bloklangan foydalanuvchilarni avtomatik hisobdan chiqarishi shart.
- **Kanal Postlarini Qabul Qilish (Movie Watcher):** Kanaldan kino yuklanganda post sarlavhasi (caption) mustahkam va xatoliklarga bardoshli parser orqali tahlil qilinadi. Faqat ruxsat etilgan kino kanallaridan kelgan postlar bazaga kiritiladi.
- **FSM Holatlarini Tozalash (State Killer):** Foydalanuvchi biron holatda (masalan, admin kanali qo'shish yoki kod qidirish) turganida asosiy menyu yoki `/start` bosilsa, oldingi holat to'liq tozalanadi (`await state.clear()`) va chalkashliklarning oldi olinadi.
