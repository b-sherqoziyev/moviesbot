# 🎬 Movies Reel — Muhandislik Standartlari va Tizim Qoidalari (Engineering Rules & Architecture)

Ushbu hujjat **Movies Reel** loyihasidagi barcha dasturchilar va AI agentlar uchun **umumlashtirilgan, mustahkam va qat'iy muhandislik qoidalari to'plamidir**. Tizimga kiritilayotgan har qanday o'zgarish (yangi buyruq, servis, model yoki arxitektura) ushbu umumiy tamoyillarga 100% mos kelishi shart.

---

## 1. Qatlamlar Intizomi va Mas'uliyatlar Chegarasi (Layered Architecture & Separation of Concerns)

Tizim qat'iy **4 ta qatlam** bo'yicha tashkil etiladi. Har bir qatlam faqat o'z mas'uliyatiga ega:

```
[ Telegram Ingress Event ]
           │
           ▼
[ Middlewares Layer ]    ──▶ Throttling, DbSession, Cache Layer, i18n, Global Guards
           │
           ▼
[ Handlers Layer ]       ──▶ Sof Dispatcher (Faqat marshrutlash va UI topshirish)
           │
           ▼
[ Services Layer ]       ──▶ Biznes logika, Tranzaksiyalar, Keshlar, Orkestratsiya
           │
           ▼
[ Repositories Layer ]   ──▶ Sof SQL / ORM ma'lumotlar ombori
```

### 1.1. Handlerlar Sofligi Qoidasi (Pure Dispatcher Principle):
* **Handlerlar hech qachon biznes mantiq yozmaydi:** Barcha turdagi handlerlar (komandalar, matnli xabarlar, inline callbacklar, inline querylar) faqat so'rovni qabul qilib, mos servisga yo'naltiruvchi sof marshrutizator hisoblanadi.
* **SQL va Tranzaksiyalar daxlsizligi:** Handler ichida to'g'ridan-to'g'ri SQL so'rovlar yozish yoki `session.commit()` chaqirish qat'iyan taqiqlanadi. Tranzaksiya nazorati to'liq Service qatlamiga tegishli.
* **Qo'lda tekshiruvlar yozish taqiqlanadi:** Qayta ishlanishi kerak bo'lgan umumiy shartlar (huquqlar, faollik, a'zolik) handler ichida qo'lda qayta-qayta yozilmaydi.

---

## 2. Buyruqlar va Hodisalarni Qayta Ishlash Standarti (Unified Command & Event Lifecycle)

Loyihadagi **har qanday buyruq (Command) yoki kiruvchi xabar oqimi** quyidagi yagona hayotiy sikl bosqichlaridan o'tishi shart:

1. **Ingress & Throttling (Spamdan himoya):** So'rovlar chastotasi eng birinchi middleware qatlamida tekshiriladi.
2. **Context Enrichment (Kontekst boyitish):** Foydalanuvchi ma'lumotlari, sessiya va til sozlamalari xotira/kesh orqali hodisaga avtomatik ineksiya qilinadi.
3. **Access & Verification Guards (Ruxsat va holat nazorati):** Foydalanuvchining botdan foydalanish huquqi va talab qilingan shartlarga muvofiqligi markaziy himoyachilar orqali tasdiqlanadi.
4. **State Hygiene (Holat gigiyenasi):** Yangi mustaqil buyruq yoki bosh menyu oqimi boshlanganda, chalkashliklarning oldini olish uchun oldingi FSM holatlari tozalanishi (`await state.clear()`) yoki nazorat ostida yangisiga o'tkazilishi shart.
5. **Business Execution (Biznes ijro):** Amallar parametrlar bilan mos xizmatga (Service) beriladi.
6. **Presentation Delivery (Javob qaytarish):** Natija dinamik emojilar va ko'p tillilik lug'atlari orqali formatlanib, foydalanuvchiga yuboriladi.

---

## 3. DRY va Markazlashgan Nazorat (Don't Repeat Yourself & Cross-Cutting Concerns)

* **Ko'ndalang talablar (Cross-Cutting Concerns) faqat markazlashadi:** Bir nechta joyda kerak bo'ladigan barcha tekshiruvlar (autentifikatsiya, rollar, til, kanallar a'zoligi, sessiya boshqaruvi) faqat **Middlewares** yoki **Filters** darajasida bitta joyda yoziladi.
* **Yagona haqiqat manbai (Single Source of Truth):** Hech bir qiymat, xabar matni, ro'yxat yoki parametr kodning turli qismlarida takroran e'lon qilinmaydi.

---

## 4. Ma'lumotlar Bazasi va Konkurrentlik Gigiyenasi (Database & Concurrency Hygiene)

Yuqori yuklamada ma'lumotlar bazasining barqaror ishlashi uchun quyidagi tamoyillar majburiydir:

### 4.1. N+1 So'rovlarga Mutlaq Taqiqlik:
* Sikllar ichida bazaga `SELECT` yuborish man etiladi.
* Bog'langan modellar (Relationships) doimo `selectinload` yoki `joinedload` orqali optimal tortib olinadi.

### 4.2. Race Condition va Atomik Hisoblagichlar:
* Yangi identifikator yoki ketma-ket kodlar yaratishda statistik hisoblashlar (masalan, `COUNT + 1`) kabi poyga holatiga (Race Condition) moyil usullardan foydalanish taqiqlanadi.
* Identifikatorlar va hisoblagichlar PostgreSQL `Sequence`, xavfsiz tartiblash yoki Redis atomik amallari (`INCR`) orqali shakllantiriladi.
* Reyting, ko'rishlar yoki faollik hisoblagichlari atomik SQL yangilash ifodalari (`update(...).values(counter=Model.counter + 1)`) orqali oshiriladi.

### 4.3. Indekslash va Xavfsiz O'chirish:
* Tez-tez saralanadigan va qidiriladigan maydonlar B-Tree yoki mos indekslar bilan ta'minlanishi shart.
* Muhim yozuvlar jismoniy o'chirilmasdan, mantiqiy faolsizlantirish (`is_active = False` — Soft Delete) orqali boshqariladi.

---

## 5. Yuqori Yuklama va Masshtablash (High-Load, Scalability & Caching)

Bot har qanday kutilmagan trafik to'lqinlarida (Traffic Spikes) sekinlashmasdan va qulamasdan barqaror ishlashi shart.

### 5.1. Zero DB Hit on Frequent Events (O'qish oqimini keshlashtirish):
* Tez-tez keladigan har bir xabarda yoki tugma bosilishida relyatsion ma'lumotlar bazasiga murojaat qilish qat'iyan man etiladi.
* Foydalanuvchining faol profili, roli, tili va tizim sozlamalari **Redis keshida (TTL asosida)** saqlanadi. Baza faqat kesh yangilanishida yoki keshda ma'lumot bo'lmaganda ishlatiladi.

### 5.2. Dinamik Versiyalash orqali Kesh Boshqaruvi:
* Tizim miqyosidagi o'zgarishlar (masalan, obuna kanallari, global konfiguratsiya) yuz berganda, millionlab kesh yozuvlarini navbatma-navbat tozalash o'rniga, versiya hisoblagichini oshirish (`version_increment`) orqali barcha eski keshlar 0 soniyada kuchsizlantiriladi.

### 5.3. Asinxron Fon Jarayonlari (Non-blocking Background Offloading):
* Ko'p vaqt talab qiladigan operatsiyalar (ommaviy xabarnomalar, og'ir statistik hisobotlar, tahlillar) botning asosiy kiruvchi oqimini (Polling/Webhook event-loop) hech qachon to'xtatib qo'ymaydi.
* Ushbu amallar asinxron fon vazifalari (`Background Tasks / Workers`) orqali, qat'iy Rate Limiting nazorati ostida bajariladi.

---

## 6. Xavfsizlik va Ruxsatlar Tizimi (RBAC & Defense in Depth)

* **Ruxsatlarga asoslangan boshqaruv (Permission-Driven Access):** Har qanday ma'muriy yoki maxsus harakat aniq belgilangan rollar va huquqlar (Permissions) orqali tekshiriladi.
* **0 Hardcoded Identifiers:** Kod ichida foydalanuvchi yoki kanal ID larini (`if user_id == 123456`) qattiq yozish taqiqlanadi.
* **Kiruvchi Manbalar Xavfsizligi:** Kanal postlari va guruh hodisalarini qabul qilishda ruxsat etilgan manbalar filtri qo'llaniladi. Begona manbalardan kelgan so'rovlar qayta ishlanmasdan darhol chetlatiladi.

---

## 7. Dinamik UI va 100% Ko'p Tillilik (i18n & Dynamic UI Tokens)

* **0 Hardcoded Emojis:** Dastur kodida (`.py` fayllarda) birorta ham grafik yoki unicode emoji belgisi to'g'ridan-to'g'ri yozilishi taqiqlanadi. Barcha vizual belgilar markazlashgan konfiguratsiya va dinamik xizmat orqali (Platforma imkoniyatiga qarab Premium `<tg-emoji>` yoki fallback ko'rinishida) olinadi.
* **0 Hardcoded Strings:** Tizimdagi har qanday xabar, tugma matni, bildirishnoma yoki xatolik matni mahalliylashtirish lug'atlari (`locales`) orqali foydalanuvchi tilida generatsiya qilinadi.
* Dinamik parametrlar (janrlar, toifalar) ham foydalanuvchi tiliga mos ustunlardan tanlanadi.

---

## 8. Istisnolar Taksonomiyasi va Barqarorlik (Resilience & Error Taxonomy)

* **Yagona xatoliklar iyerarxiyasi:** Barcha biznes va tizim xatoliklari maxsus domen istisnolaridan (`Domain Exceptions`) kelib chiqadi.
* **Graceful Degradation:** Tizimning biror ikkinchi darajali xizmati (masalan, Premium emojilar yoki media metama'lumotlari) ishlamay qolsa, tizim to'xtab qolmasdan asosiy vazifasini xatosiz yakunlaydi.
* **Global Error Interception:** Kutilmagan texnik nosozliklar botni qulatmaydi — ular markaziy Error Handler tomonidan to'liq loglanadi va foydalanuvchiga madaniyatli standart xabar qaytariladi.

---

## 9. Izolyatsiya qilingan Virtual Muhit (.venv Strictness)

* Loyihaga oid har qanday kutubxona o'rnatish, kodni ishga tushirish, formatlash va migratsiyalar faqat joriy loyihadagi `.venv` muhiti doirasida amalga oshiriladi.
