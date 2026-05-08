import os
from telegram import Update, InputFile
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
from utils.helpers import load_menu, get_category, get_item
from keyboards.keyboards import categories_keyboard, items_keyboard, item_detail_keyboard, main_menu_keyboard
from database.db import add_to_cart, get_or_create_user


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = load_menu()
    text = "🍽 *Біздің мәзір*\n\nСанатты таңдаңыз:"

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=categories_keyboard(menu["categories"]),
        )
    else:
        query = update.callback_query
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=categories_keyboard(menu["categories"]),
            )
        except Exception:
            await query.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode="Markdown",
                reply_markup=categories_keyboard(menu["categories"]),
            )


async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split("_")[1])
    category = get_category(category_id)
    if not category:
        await query.edit_message_text("Санат табылмады.")
        return

    text = f"{category['name']}\n\nТағамды таңдаңыз:"
    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=items_keyboard(category["items"], category_id),
        )
    except Exception:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="Markdown",
            reply_markup=items_keyboard(category["items"], category_id),
        )


async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split("_")[1])
    item, category_id = get_item(item_id)
    if not item:
        await query.edit_message_text("Тағам табылмады.")
        return

    text = (
        f"🍽 *{item['name']}*\n\n"
        f"📝 {item['description']}\n\n"
        f"⚖️ Салмағы: {item['weight']}\n"
        f"💰 Бағасы: *{item['price']}₸*"
    )

    photo = item.get("photo")
    keyboard = item_detail_keyboard(item_id, category_id)

    if photo and os.path.exists(photo):
        deleted = False
        try:
            await query.message.delete()
            deleted = True
            with open(photo, "rb") as f:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=InputFile(f),
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
        except Exception:
            if deleted:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            else:
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def add_item_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Себетке қосылды!")

    item_id = int(query.data.split("_")[1])
    item, category_id = get_item(item_id)
    if not item:
        return

    user = update.effective_user
    await get_or_create_user(user.id, user.username, user.full_name)
    await add_to_cart(user.id, item_id, item["name"], item["price"])

    text = (
        f"✅ *{item['name']}* себетке қосылды!\n\n"
        f"💰 Бағасы: {item['price']}₸\n\n"
        "Сатып алуды жалғастыру немесе себетке өту?"
    )
    from keyboards.keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Себетке өту", callback_data="cart")],
        [InlineKeyboardButton("🔙 Жалғастыру", callback_data=f"cat_{category_id}")],
    ])
    try:
        await query.edit_message_caption(caption=text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        try:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            await query.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )


async def go_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Әрекетті таңдаңыз:",
        reply_markup=main_menu_keyboard(),
    )


def get_menu_handlers():
    return [
        MessageHandler(filters.Regex(r"Мәзір"), show_menu),
        CallbackQueryHandler(show_menu, pattern="^menu$"),
        CallbackQueryHandler(show_category, pattern="^cat_"),
        CallbackQueryHandler(show_item, pattern="^item_"),
        CallbackQueryHandler(add_item_to_cart, pattern="^add_"),
        CallbackQueryHandler(go_to_main_menu, pattern="^main_menu$"),
        CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop$"),
    ]
