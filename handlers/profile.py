from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from database.db import get_or_create_user, update_user_contact, get_user_orders
from keyboards.keyboards import main_menu_keyboard, share_phone_keyboard

EDIT_PHONE, EDIT_ADDRESS = range(10, 12)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await get_or_create_user(user.id, user.username, user.full_name)
    orders = await get_user_orders(user.id)

    phone = db_user.phone or "Көрсетілмеген"
    address = db_user.address or "Көрсетілмеген"

    text = (
        f"👤 *Сіздің профиліңіз*\n\n"
        f"Аты: {user.full_name}\n"
        f"Username: @{user.username or '—'}\n"
        f"📞 Телефон: {phone}\n"
        f"📍 Жеткізу мекенжайы: {address}\n"
        f"📦 Барлық тапсырыстар: {len(orders)}\n"
    )

    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Телефонды өзгерту", callback_data="edit_phone")],
        [InlineKeyboardButton("📍 Мекенжайды өзгерту", callback_data="edit_address")],
    ])

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def edit_phone_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📞 Жаңа телефон нөмірін енгізіңіз:",
        reply_markup=share_phone_keyboard(),
    )
    return EDIT_PHONE


async def edit_phone_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    await update_user_contact(update.effective_user.id, phone=phone)
    await update.message.reply_text(
        f"✅ Телефон жаңартылды: {phone}",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def edit_address_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📍 Жаңа жеткізу мекенжайын енгізіңіз:",
    )
    return EDIT_ADDRESS


async def edit_address_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    await update_user_contact(update.effective_user.id, address=address)
    await update.message.reply_text(
        f"✅ Мекенжай жаңартылды: {address}",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Өңдеу болдырылмады.", reply_markup=main_menu_keyboard())
    return ConversationHandler.END


def get_profile_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_phone_start, pattern="^edit_phone$"),
            CallbackQueryHandler(edit_address_start, pattern="^edit_address$"),
        ],
        states={
            EDIT_PHONE: [
                MessageHandler(filters.CONTACT, edit_phone_save),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_phone_save),
            ],
            EDIT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_address_save),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit)],
        allow_reentry=True,
    )


def get_profile_handlers():
    return [
        MessageHandler(filters.Text(["👤 Профиль"]), show_profile),
        get_profile_handler(),
    ]
