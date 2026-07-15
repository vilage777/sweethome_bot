import httpx
import tempfile
import os
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import get_or_create_user, deduct_star
from config import API_KEY, BASE_URL, IMAGE_MODEL

# Ключевые слова для генерации изображения
IMAGE_KEYWORDS = ["покажи", "фото", "фотку", "картинку", "сфоткай", "хочу тебя видеть", "показаться"]

# Промпт для генерации изображения
IMAGE_PROMPT = (
    "Девушка 22 года, домашняя обстановка, уютная комната, мягкий свет, "
    "сидит на диване перед веб-камерой, лёгкая пижама или топ, "
    "прямой взгляд в камеру, лёгкая улыбка, реалистичное фото, "
    "естественные позы, 4k"
)

# Стоимость 1 звезды (в копейках Telegram Stars = 100)
STAR_PRICE = 100

def contains_image_keyword(text: str) -> bool:
    """Проверяем, содержит ли сообщение ключевые слова для генерации изображения"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in IMAGE_KEYWORDS)

async def send_invoice_for_image(update: Update):
    """Отправляем инвойс для оплаты изображения"""
    keyboard = [[InlineKeyboardButton("⭐ Купить за 1 звезду", callback_data="buy_star")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Хочешь увидеть меня дома? 😊\n"
        "Это стоит 1 звёздочку.\n\n"
        "Нажми кнопку ниже, чтобы купить!",
        reply_markup=reply_markup
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку покупки"""
    query = update.callback_query
    await query.answer()

    if query.data == "buy_star":
        # Отправляем инвойс через Telegram Stars
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Домашнее фото Алисы",
            description="Одно фото Алисы в домашней обстановке",
            payload="buy_star",
            provider_token="",  # Для Telegram Stars пустая строка
            currency="XTR",  # Валюта Telegram Stars
            prices=[LabeledPrice(label="Фото", amount=STAR_PRICE)]
        )

async def image_gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик генерации изображения"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_message = update.message.text

    # Проверяем ключевые слова
    if not contains_image_keyword(user_message):
        return False

    # Получаем пользователя
    user = await get_or_create_user(user_id, username)

    # Проверяем баланс
    if user["stars_balance"] < 1:
        await update.message.reply_text(
            "Надо пополнить звёздочки, чтобы я показалась 😊\n"
            "Напиши «купить звезду» или нажми /buy"
        )
        return True

    # Списываем звезду
    success = await deduct_star(user_id)
    if not success:
        await update.message.reply_text("Ой, что-то не так со звёздочками 😅 Попробуй ещё раз.")
        return True

    # Показываем статус загрузки
    loading_msg = await update.message.reply_text("Секунду, я preparationуюсь... 📸")

    # Генерируем изображение
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": IMAGE_MODEL,
                    "prompt": IMAGE_PROMPT,
                    "n": 1,
                    "size": "512x512"
                }
            )

            if response.status_code == 200:
                data = response.json()
                image_url = data["data"][0]["url"]

                # Скачиваем изображение
                img_response = await client.get(image_url)

                if img_response.status_code == 200:
                    # Сохраняем во временный файл
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp.write(img_response.content)
                        tmp_path = tmp.name

                    # Отправляем изображение
                    with open(tmp_path, "rb") as photo:
                        await context.bot.send_photo(
                            chat_id=update.message.chat_id,
                            photo=photo,
                            caption="Лови, это я 😉"
                        )

                    # Удаляем временный файл
                    os.unlink(tmp_path)

                    # Удаляем сообщение о загрузке
                    await loading_msg.delete()

                    print(f"[IMAGE] Изображение отправлено пользователю {user_id}")
                    return True
                else:
                    raise Exception(f"Ошибка скачивания изображения: {img_response.status_code}")
            else:
                raise Exception(f"Ошибка API генерации: {response.status_code}")

    except Exception as e:
        print(f"[IMAGE] Ошибка генерации: {e}")
        await loading_msg.edit_text("Ой, что-то не загрузилось, попробуй ещё раз 😅")
        # Возвращаем звезду при ошибке
        from database.db import update_stars
        await update_stars(user_id, 1)
        return True

    return True
