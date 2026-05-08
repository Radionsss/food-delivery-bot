import logging
from telegram import BotCommand, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler,
)

from config import BOT_TOKEN
from database.db import init_db
from handlers.start import start, about, contact
from handlers.menu import show_menu, get_menu_handlers
from handlers.cart import show_cart, get_cart_handlers
from handlers.order import show_orders, get_order_conversation_handler
from handlers.profile import show_profile, get_profile_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Ошибка: %s", context.error, exc_info=context.error)


async def post_init(application):
    await init_db()
    logger.info("База данных инициализирована")
    await application.bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("menu", "Открыть меню"),
        BotCommand("cart", "Моя корзина"),
        BotCommand("orders", "Мои заказы"),
        BotCommand("profile", "Профиль"),
        BotCommand("cancel", "Отменить текущее действие"),
    ])


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан!")
        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_error_handler(error_handler)

    # 1. Команды
    app.add_handler(CommandHandler("start", start))

    # 2. Кнопки главного меню — регистрируем ДО ConversationHandler'ов
    #    Первый совпавший хендлер в группе 0 обрабатывает и останавливает цепочку
    app.add_handler(MessageHandler(filters.Regex(r"М.зір"), show_menu))
    app.add_handler(MessageHandler(filters.Regex(r"Себет"), show_cart))
    app.add_handler(MessageHandler(filters.Regex(r"тапсырыстарым"), show_orders))
    app.add_handler(MessageHandler(filters.Regex(r"Профиль"), show_profile))
    app.add_handler(MessageHandler(filters.Regex(r"Байланыс"), contact))
    app.add_handler(MessageHandler(filters.Regex(r"туралы"), about))

    # 3. ConversationHandler'ы (оформление заказа, редактирование профиля)
    app.add_handler(get_order_conversation_handler())
    app.add_handler(get_profile_handler())

    # 4. Callback обработчики меню и корзины
    for handler in get_menu_handlers():
        if not isinstance(handler, MessageHandler):
            app.add_handler(handler)

    for handler in get_cart_handlers():
        if not isinstance(handler, MessageHandler):
            app.add_handler(handler)

    logger.info("Бот запущен.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
