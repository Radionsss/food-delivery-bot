import asyncio
import logging
from telegram import BotCommand
from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN
from database.db import init_db
from handlers.start import get_start_handlers
from handlers.menu import get_menu_handlers
from handlers.cart import get_cart_handlers
from handlers.order import get_order_handlers
from handlers.profile import get_profile_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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
        logger.error("BOT_TOKEN не задан! Создайте файл .env на основе .env.example")
        return

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ConversationHandler'ы должны регистрироваться первыми
    for handler in get_order_handlers():
        app.add_handler(handler)

    for handler in get_profile_handlers():
        app.add_handler(handler)

    for handler in get_start_handlers():
        app.add_handler(handler)

    for handler in get_menu_handlers():
        app.add_handler(handler)

    for handler in get_cart_handlers():
        app.add_handler(handler)

    logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
