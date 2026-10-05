# AnzorikEPT

**Telegram Mini App** в стиле Hamster Kombat.  
Главный персонаж — кибер-лис **Anzorik**.

---

## Что есть в игре

- Тап по Anzorik → получение монет (ANZ)
- Энергия (восстанавливается)
- Пассивный доход
- 8 карточек прокачки (сила тапа, пассивка, энергия)
- Реферальная система (+500 ANZ за друга)
- Таблица лидеров
- Красивый неоновый интерфейс

---

## Структура проекта

```
AnzorikEPT/
├── backend/          # FastAPI + SQLite
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   └── __init__.py
├── bot/              # Telegram-бот (aiogram)
│   └── bot.py
├── frontend/         # Mini App
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

---

## Как запустить

### 1. Создай бота
1. Напиши @BotFather в Telegram
2. Создай бота командой `/newbot`
3. Скопируй токен
4. Вставь токен в `bot/bot.py` (строка `BOT_TOKEN`)

### 2. Установи зависимости

```bash
cd AnzorikEPT
pip install -r requirements.txt
```

### 3. Запусти Backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend будет доступен на `http://localhost:8000`

### 4. Запусти Frontend

Для теста можно просто открыть `frontend/index.html` в браузере,  
но лучше раздать через любой хостинг (Vercel, Netlify, Cloudflare Pages, или даже `python -m http.server`).

**Важно:** в файле `frontend/script.js` замени `API_URL` на адрес твоего бэкенда.

### 5. Запусти бота

```bash
cd bot
python bot.py
```

### 6. Подключи Mini App к боту

В @BotFather:
1. `/mybots` → выбери бота → **Bot Settings** → **Menu Button**
2. Укажи URL твоего фронтенда
3. В `bot/bot.py` тоже укажи этот URL в `WEBAPP_URL`

---

## Деплой (рекомендуется)

| Часть       | Куда деплоить              | Бесплатно? |
|-------------|----------------------------|----------|
| Backend     | Railway / Render / Fly.io  | Да       |
| Frontend    | Vercel / Netlify / CF Pages| Да       |
| База данных | SQLite (уже в проекте)     | Да       |

После деплоя не забудь обновить:
- `API_URL` в `script.js`
- `WEBAPP_URL` в `bot.py`
- Токен бота

---

## Игровая экономика (стартовая)

| Параметр              | Значение     |
|-----------------------|--------------|
| Стартовый баланс      | 100 ANZ      |
| Сила тапа             | 1            |
| Энергия               | 1000         |
| Восстановление энергии| 1 ед. / 3 сек|
| Бонус за реферала     | 500 ANZ      |

---

## Дальнейшее развитие (идеи)

- Ежедневное комбо
- Ежедневные задания
- Скин для Anzorik
- Бусты (x2 на 1 час)
- Кланы
- Сезоны и награды

---

Сделано с любовью для AnzorikEPT 🦊⚡

