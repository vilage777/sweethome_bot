from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from database.db import get_or_create_user, update_stars, deduct_star

# Стоимость 1 звезды (в копейках Telegram Stars = 100)
STAR_PRICE = 100

# Промпт для генерации изображения
IMAGE_PROMPT = (
    "Девушка 22 года, домашняя обстановка, уютная комната, мягкий свет, "
    "сидит на диване перед веб-камерой, лёгкая пижама или топ, "
    "прямой взгляд в камеру, лёгкая улыбка, реалистичное фото, "
    "естественные позы, 4k"
)

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик предварительной проверки оплаты"""
    query = update.pre_checkout_query
    
    # Всегда подтверждаем оплату
    await query.answer(ok=True)
    print(f"[STARS] Предварительная проверка оплаты от {query.from_user.id}")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик успешной оплаты"""
    user_id = update.effective_user.id
    payment = update.message.successful_payment
    
    if payment.invoice_payload == "buy_star":
        # Начисляем звезду пользователю
        await update_stars(user_id, 1)
        
        await update.message.reply_text(
            "Оплата прошла успешно! ⭐\n"
            "Теперь у тебя есть 1 звёздочка.\n"
            "Напиши «покажи» или «фото» и я пришлю тебе картинку 😉"
        )
        print(f"[STARS] Пользователь {user_id} пополнил баланс: +1 звезда")
    else:
        print(f"[STARS] Неизвестный payload оплаты: {payment.invoice_payload}")
