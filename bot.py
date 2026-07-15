import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from config import BOT_TOKEN, ADMIN_USER_ID, validate_config
from database.db import init_db, get_user_count, get_total_stars, reset_user_balance
from handlers.start import start_handler
from handlers.chat import chat_handler
from handlers.stars import pre_checkout_handler, successful_payment_handler
from handlers.image_gen import image_gen_handler, handle_callback_query, contains_image_keyword

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /buy — покупка звезды"""
    from telegram import LabeledPrice
    await context.bot.send_invoice(
        chat_id=update.message.chat_id,
        title="Звёздочка для Алисы",
        description="1 звезда для просмотра домашнего фото",
        payload="buy_star",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="1 звезда", amount=100)]
    )

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats — статистика (только для админа)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return
    user_count = await get_user_count()
    total_stars = await get_total_stars()
    stats_text = (
        f"Статистика бота:\n\n"
        f"Пользователей: {user_count}\n"
        f"Всего звёзд на балансах: {total_stars}"
    )
    await update.message.reply_text(stats_text)

async def reset_balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reset_balance — сброс баланса (только для админа)"""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /reset_balance <user_id>")
        return
    try:
        target_user_id = int(context.args[0])
        await reset_user_balance(target_user_id)
        await update.message.reply_text(f"Баланс пользователя {target_user_id} обнулён.")
    except ValueError:
        await update.message.reply_text("user_id должен быть числом.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик текстовых сообщений"""
    user_message = update.message.text
    if user_message.lower() in ["купить", "buy", "купить звезду", "купить звезды"]:
        await buy_handler(update, context)
        return
    if contains_image_keyword(user_message):
        success = await image_gen_handler(update, context)
        if success:
            return
    await chat_handler(update, context)

async def post_init(application: Application):
    """Инициализация БД и установка команд бота"""
    await init_db()
    commands = [
        BotCommand("start", "Начать общение с Алисой"),
        BotCommand("buy", "Купить звёздочку"),
        BotCommand("stats", "Статистика (админ)"),
        BotCommand("reset_balance", "Сбросить баланс (админ)")
    ]
    await application.bot.set_my_commands(commands)
    print("[BOT] Бот инициализирован, команды установлены")

def main():
    """Главная функция запуска бота"""
    print("=" * 50)
    print("SweetHomeBot - Запуск...")
    print("=" * 50)

    validate_config()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("buy", buy_handler))
    application.add_handler(CommandHandler("stats", stats_handler))
    application.add_handler(CommandHandler("reset_balance", reset_balance_handler))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("[BOT] Запуск polling...")
    print("=" * 50)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
