import asyncio
import logging
from telegram import BotCommand
from telegram.ext import ApplicationBuilder

from telegram.ext import MessageHandler, filters

from config import BOT_TOKEN
from database.db import init_db
from handlers.start import get_start_handlers, start, about, contact
from handlers.menu import get_menu_handlers, show_menu
from handlers.cart import get_cart_handlers, show_cart
from handlers.order import get_order_handlers, show_orders
from handlers.profile import get_profile_handlers, show_profile

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

    # Кнопки главного меню — высший приоритет (group=-1)
    # Работают всегда, даже внутри ConversationHandler
    for text, fn in [
        (r"Мәзір", show_menu),
        (r"Себет", show_cart),
        (r"тапсырыстарым", show_orders),
        (r"Профиль", show_profile),
        (r"Байланыс", contact),
        (r"Біз туралы", about),
    ]:
        app.add_handler(MessageHandler(filters.Regex(text), fn), group=-1)

    # ConversationHandler'ы и остальные обработчики
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
