import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API ключ нейросети
API_KEY = os.getenv("API_KEY")

# Базовый URL API (https://apihub.agnes-ai.com/v1)
BASE_URL = os.getenv("BASE_URL")

# ID админа
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Модель для чата
CHAT_MODEL = os.getenv("CHAT_MODEL", "agnes-2.0-flash")

# Модель для генерации изображений
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "agnes-image-2.1-flash")

# Проверка обязательных переменных
def validate_config():
    """Проверяем, что все обязательные переменные заданы"""
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_KEY:
        missing.append("API_KEY")
    if not BASE_URL:
        missing.append("BASE_URL")

    if missing:
        raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")
    print("[CONFIG] Все переменные окружения загружены успешно")
