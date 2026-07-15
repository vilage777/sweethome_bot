import httpx
from telegram import Update
from telegram.ext import ContextTypes
from database.db import get_or_create_user, add_to_history, get_history
from config import API_KEY, BASE_URL, CHAT_MODEL
import os

# Загружаем промпт личности
PERSONALITY_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "personality.md")
with open(PERSONALITY_PATH, "r", encoding="utf-8") as f:
    PERSONALITY_PROMPT = f.read().strip()

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_message = update.message.text

    # Получаем пользователя из БД
    user = await get_or_create_user(user_id, username)

    # Сохраняем сообщение пользователя в историю
    await add_to_history(user_id, "user", user_message)

    # Получаем историю диалога
    history = await get_history(user_id)

    # Формируем сообщения для API
    messages = [{"role": "system", "content": PERSONALITY_PROMPT}]
    messages.extend(history)

    # Отправляем запрос к API нейросети
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.8
                }
            )

            if response.status_code == 200:
                data = response.json()
                reply = data["choices"][0]["message"]["content"]
            else:
                print(f"[CHAT] Ошибка API: {response.status_code}")
                reply = "Ой, что-то не загрузилось, попробуй ещё раз 😅"
    except Exception as e:
        print(f"[CHAT] Исключение: {e}")
        reply = "Ой, что-то не загрузилось, попробуй ещё раз 😅"

    # Сохраняем ответ бота в историю
    await add_to_history(user_id, "assistant", reply)

    await update.message.reply_text(reply)
    print(f"[CHAT] {user_id}: {user_message[:50]}... -> {reply[:50]}...")
