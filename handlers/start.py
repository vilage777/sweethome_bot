from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Создаём пользователя в БД
    user = await get_or_create_user(user_id, username)
    
    greeting = (
        "Привет! Я Алиса 😊\n\n"
        "Общайся со мной, а за 1 звёздочку я пришлю тебе своё домашнее фото 😉\n\n"
        "Просто напиши мне что-нибудь!"
    )
    
    await update.message.reply_text(greeting)
    print(f"[START] Пользователь {user_id} (@{username}) запустил бота")
