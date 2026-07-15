# SweetHomeBot 🏠

Telegram-бот, который общается от лица девушки Алисы и генерирует изображения в домашней обстановке за 1 Telegram Star.

## Возможности

- Общение с Алиской — тёплый, игривый диалог
- Генерация изображений — девушка в домашней обстановке (за 1 звезду)
- Система звёзд — баланс хранится в SQLite
- Админ-команды — статистика и управление балансом

## Технологии

- Python 3.10+
- python-telegram-bot v20+
- SQLite (aiosqlite)
- HTTPX для запросов к API

## Установка

### 1. Клонируйте или скачайте проект

```bash
cd sweethome_bot
```

### 2. Создайте виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Создайте файл .env

Скопируйте пример и заполните своими данными:

```bash
cp .env.example .env
```

Или создайте файл `.env` вручную:

```
BOT_TOKEN=ваш_токен_бота
API_KEY=ваш_api_ключ
BASE_URL=https://api.agnes-ai.com
ADMIN_USER_ID=ваш_telegram_id
IMAGE_MODEL=agnes-image-2.1-flash
```

### 5. Запустите бота

```bash
python bot.py
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать общение с Алисой |
| `/buy` | Купить звёздочку |
| `/stats` | Статистика (только админ) |
| `/reset_balance <user_id>` | Сбросить баланс (только админ) |

## Как работает оплата

1. Пользователь отправляет сообщение с ключевым словом («покажи», «фото» и т.д.)
2. Бот предлагает купить звезду за 1 Telegram Star
3. Пользователь оплачивает через Telegram Stars
4. Бот генерирует изображение через API нейросети
5. Изображение отправляется пользователю

## Деплой на Render.com

### 1. Создайте Web Service

- Зайдите на [render.com](https://render.com)
- Нажмите "New" → "Background Worker"
- Подключите ваш GitHub репозиторий

### 2. Настройте окружение

В настройках сервиса добавьте переменные:
- `BOT_TOKEN`
- `API_KEY`
- `BASE_URL`
- `ADMIN_USER_ID`
- `IMAGE_MODEL`

### 3. Build Command

```
pip install -r requirements.txt
```

### 4. Start Command

```
python bot.py
```

## Деплой на Railway.app

### 1. Создайте проект

- Зайдите на [railway.app](https://railway.app)
- Нажмите "New Project" → "Deploy from GitHub"

### 2. Настройте переменные

В разделе "Variables" добавьте все переменные из `.env`

### 3. Deploy

Railway автоматически определит и запустит Python проект.

## Структура проекта

```
sweethome_bot/
├── .env                     # Переменные окружения (НЕ коммитить!)
├── config.py                # Загрузка конфигурации
├── bot.py                   # Точка входа
├── handlers/
│   ├── __init__.py
│   ├── start.py             # Команда /start
│   ├── chat.py              # Текстовый диалог
│   ├── stars.py             # Оплата звёздами
│   └── image_gen.py         # Генерация изображений
├── database/
│   ├── __init__.py
│   └── db.py                # SQLite операции
├── prompts/
│   └── personality.md       # Личность Алисы
├── README.md                # Эта инструкция
└── requirements.txt         # Зависимости
```

## Лицензия

MIT License
