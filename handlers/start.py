from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database.db import get_or_create_user
from keyboards.keyboards import main_menu_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )
    await update.message.reply_text(
        f"👋 Сәлем, *{user.first_name}*!\n\n"
        "*FoodBot* қош келдіңіз 🍕🍔🍜\n\n"
        "Мұнда сіз үйіңізге дейін жеткізілетін дәмді тағам тапсырыс бере аласыз.\n\n"
        "Төмендегі мәзірден әрекетті таңдаңыз:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Біз туралы*\n\n"
        "🍽 *FoodBot* — дәмді тағам жеткізу сервисі.\n\n"
        "🕐 Жұмыс уақыты: 10:00 — 23:00\n"
        "🚚 Жеткізу: 30-60 минут\n"
        "💰 8000₸-ден бастап тегін жеткізу\n"
        "📞 Телефон: +7 (777) 123-45-67\n"
        "📍 Мекенжай: Үлгі көшесі, 1\n\n"
        "Сіз тоқ болу үшін жұмыс істейміз! 😊",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Бізбен байланысыңыз*\n\n"
        "Телефон: +7 (777) 123-45-67\n"
        "Email: support@foodbot.kz\n"
        "Telegram: @foodbot_support\n\n"
        "Біз әрқашан көмектесуге дайынбыз! 💬",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


def get_start_handlers():
    return [
        CommandHandler("start", start),
        MessageHandler(filters.Regex(r"Біз туралы"), about),
        MessageHandler(filters.Regex(r"Байланыс"), contact),
    ]
