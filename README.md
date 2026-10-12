# 🎬 Cinema / Movies Telegram Bot

Zamonaviy, xavfsiz, yuqori unumdorlikka ega va toza arxitektura (**Clean Layered Architecture**) asosida qurilgan Telegram kino bot loyihasi.

---

## 🏛️ Arxitektura Qatlamlari (Architecture Overview)

Loyihada kodlar qat'iy ravishda o'z vazifasiga ko'ra ajratilgan:

```
moviesbot/
├── alembic/                         # Ma'lumotlar bazasi migratsiyalari
├── app/
│   ├── core/                        # Konfiguratsiya, logging va xatoliklar
│   ├── database/                    # Baza modellari va Repository pattern
│   │   ├── models/                  # SQLAlchemy Declarative modellar
│   │   └── repositories/            # SQL amallarini bajaruvchi CRUD sinflar
│   ├── services/                    # Asosiy biznes logika (Services)
│   ├── bot/                         # Telegram bot (Delivery layer)
│   │   ├── filters/                 # Maxsus xabar filtrlari (Admin, ChatType)
│   │   ├── middlewares/             # Avtomatik sessiya, obuna, til va throttling
│   │   ├── states/                  # FSM (Finite State Machine) holatlari
│   │   ├── keyboards/               # Inline va Reply tugmalar
│   │   └── handlers/                # Buyruqlar va xabarlarni qayta ishlovchilar
│   └── locales/                     # Ko'p tillilik (uz, ru, en)
├── tests/                           # Avtomatlashtirilgan testlar
├── docker/                          # Konteynerizatsiya (Dockerfile, docker-compose)
└── main.py                          # Botni ishga tushiruvchi yagona start nuqtasi
```

---

## ⚙️ Asosiy Tamoyillar
* **SOLID & DRY:** Har bir modul va klass yagona javobgarlikka ega (SRP), qayta-qayta takrorlanuvchi SQL yoki logika yo'q.
* **Asinxronlik (Asyncio):** Barcha I/O operatsiyalar (Baza, Telegram API, Redis) to'liq asinxron ishlaydi.
* **Xavfsiz Xabar Tarqatish:** FloodWait va API cheklovlariga qarshi nazoratli broadcast mexanizmi.
* **Obunani Keshlashtirish:** Har safar Telegram API ga ortiqcha so'rov yubormaslik uchun obuna holatini Redis orqali keshda saqlash imkoniyati.
