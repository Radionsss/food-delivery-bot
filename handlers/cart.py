from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from database.db import get_cart, add_to_cart, remove_from_cart, clear_cart
from keyboards.keyboards import cart_keyboard, main_menu_keyboard
from utils.helpers import format_cart


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart_items = await get_cart(user.id)
    text = format_cart(cart_items)

    if update.message:
        if cart_items:
            await update.message.reply_text(
                text, parse_mode="Markdown", reply_markup=cart_keyboard(cart_items)
            )
        else:
            await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        query = update.callback_query
        await query.answer()
        if cart_items:
            await query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=cart_keyboard(cart_items)
            )
        else:
            await query.edit_message_text(text)


async def cart_increase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[2])
    from utils.helpers import get_item
    item, _ = get_item(item_id)
    if item:
        await add_to_cart(update.effective_user.id, item_id, item["name"], item["price"])
    await _refresh_cart(query, update.effective_user.id)


async def cart_decrease(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[2])
    await remove_from_cart(update.effective_user.id, item_id)
    await _refresh_cart(query, update.effective_user.id)


async def cart_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🗑 Себет тазаланды")
    await clear_cart(update.effective_user.id)
    await query.edit_message_text("Себет тазаланды 🗑")


async def _refresh_cart(query, telegram_id: int):
    cart_items = await get_cart(telegram_id)
    text = format_cart(cart_items)
    if cart_items:
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=cart_keyboard(cart_items)
        )
    else:
        await query.edit_message_text("Себет бос 🛒")


def get_cart_handlers():
    return [
        MessageHandler(filters.Regex(r"Себет"), show_cart),
        CallbackQueryHandler(show_cart, pattern="^cart$"),
        CallbackQueryHandler(cart_increase, pattern="^cart_inc_"),
        CallbackQueryHandler(cart_decrease, pattern="^cart_dec_"),
        CallbackQueryHandler(cart_clear, pattern="^cart_clear$"),
    ]
