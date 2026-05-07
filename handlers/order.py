from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from database.db import (
    get_cart, clear_cart, create_order,
    get_user_orders, get_order_with_items,
    update_order_status, simulate_payment,
)
from keyboards.keyboards import (
    payment_keyboard, confirm_order_keyboard, simulate_payment_keyboard,
    orders_list_keyboard, main_menu_keyboard, share_phone_keyboard, skip_keyboard,
)
from utils.helpers import format_cart, calculate_total, format_order_summary
from config import ADMIN_ID

ENTER_PHONE, ENTER_ADDRESS, ENTER_COMMENT, CHOOSE_PAYMENT = range(4)


async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart_items = await get_cart(update.effective_user.id)
    if not cart_items:
        await query.edit_message_text("Себетіңіз бос. Ресімдеу алдында тауарлар қосыңыз.")
        return ConversationHandler.END

    context.user_data["cart_items"] = cart_items
    context.user_data["total"] = calculate_total(cart_items)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📞 Курьермен байланысу үшін телефон нөміріңізді енгізіңіз:",
        reply_markup=share_phone_keyboard(),
    )
    return ENTER_PHONE


async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()

    if not phone or len(phone) < 7:
        await update.message.reply_text("Дұрыс телефон нөмірін енгізіңіз.")
        return ENTER_PHONE

    context.user_data["phone"] = phone
    await update.message.reply_text(
        "📍 Жеткізу мекенжайын енгізіңіз (көше, үй, пәтер):",
        reply_markup=skip_keyboard(),
    )
    return ENTER_ADDRESS


async def enter_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if address == "⏩ Өткізіп жіберу":
        address = "Өздігінен алу"

    context.user_data["address"] = address

    await update.message.reply_text(
        "💬 Тапсырысқа пікір қосыңыз (аллергия, тілектер):",
        reply_markup=skip_keyboard(),
    )
    return ENTER_COMMENT


async def enter_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text.strip()
    context.user_data["comment"] = None if comment == "⏩ Өткізіп жіберу" else comment

    cart_items = context.user_data["cart_items"]
    total = context.user_data["total"]
    address = context.user_data["address"]
    phone = context.user_data["phone"]

    summary = (
        f"📋 *Тапсырысты растау*\n\n"
        f"{format_cart(cart_items)}\n\n"
        f"📍 Мекенжай: {address}\n"
        f"📞 Телефон: {phone}\n"
    )
    if context.user_data.get("comment"):
        summary += f"💬 Пікір: {context.user_data['comment']}\n"

    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=confirm_order_keyboard(),
    )
    return CHOOSE_PAYMENT


async def change_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="📍 Жаңа жеткізу мекенжайын енгізіңіз:",
    )
    return ENTER_ADDRESS


async def choose_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 Төлем тәсілін таңдаңыз:",
        reply_markup=payment_keyboard(),
    )
    return CHOOSE_PAYMENT


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    payment_method = query.data.split("_")[1]
    context.user_data["payment_method"] = payment_method

    cart_items = context.user_data["cart_items"]
    order = await create_order(
        telegram_id=update.effective_user.id,
        cart_items=cart_items,
        total_price=context.user_data["total"],
        delivery_address=context.user_data["address"],
        phone=context.user_data["phone"],
        payment_method=payment_method,
        comment=context.user_data.get("comment"),
    )
    await clear_cart(update.effective_user.id)

    if payment_method in ("card", "online"):
        await query.edit_message_text(
            f"🧾 Тапсырыс *#{order.id}* жасалды!\n\n"
            "Ресімдеуді аяқтау үшін сынақ төлемін орындаңыз:",
            parse_mode="Markdown",
            reply_markup=simulate_payment_keyboard(order.id),
        )
    else:
        await _finish_order(query, order.id, context, paid=False)

    await _notify_admin(context, order.id, update.effective_user)
    return ConversationHandler.END


async def simulate_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("💳 Төлем өңделуде...")

    order_id = int(query.data.split("_")[2])
    await simulate_payment(order_id)
    await update_order_status(order_id, "confirmed")

    await query.edit_message_text(
        f"✅ *Төлем сәтті өтті!*\n\n"
        f"🎉 Тапсырыс *#{order_id}* расталды!\n\n"
        "Біз дайындауды бастадық. "
        "Күтілетін жеткізу уақыты: 30–60 минут.\n\n"
        "Күйді «📋 Менің тапсырыстарым» бөлімінен қадағалай аласыз",
        parse_mode="Markdown",
        reply_markup=None,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Басты мәзір:",
        reply_markup=main_menu_keyboard(),
    )


async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[2])
    await update_order_status(order_id, "cancelled")
    await query.edit_message_text(f"❌ #{order_id} тапсырысының төлемі болдырылмады.")


async def _finish_order(query, order_id: int, context, paid: bool):
    status_text = "✅ Төленді" if paid else "💵 Алған кезде төлем"
    await query.edit_message_text(
        f"🎉 Тапсырыс *#{order_id}* ресімделді!\n\n"
        f"💰 Төлем күйі: {status_text}\n\n"
        "Күтілетін жеткізу уақыты: 30–60 минут.",
        parse_mode="Markdown",
        reply_markup=None,
    )
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Басты мәзір:",
        reply_markup=main_menu_keyboard(),
    )


async def _notify_admin(context, order_id: int, user):
    if not ADMIN_ID:
        return
    try:
        order, items = await get_order_with_items(order_id)
        text = (
            f"🔔 *Жаңа тапсырыс #{order_id}!*\n\n"
            f"👤 Клиент: {user.full_name} (@{user.username})\n"
        ) + format_order_summary(order, items)
        from keyboards.keyboards import order_status_keyboard
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=order_status_keyboard(order_id),
        )
    except Exception:
        pass


async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Тапсырыс болдырылмады")
    await query.edit_message_text("❌ Тапсырысты ресімдеу болдырылмады.")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Басты мәзір:",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Тапсырысты ресімдеу болдырылмады.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = await get_user_orders(update.effective_user.id)
    if not orders:
        await update.message.reply_text(
            "Сізде әлі тапсырыс жоқ. Алғашқы тапсырысыңызды беріңіз! 🍕",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(
        "📋 *Сіздің тапсырыстарыңыз:*\n\nМәліметтер үшін тапсырысты таңдаңыз:",
        parse_mode="Markdown",
        reply_markup=orders_list_keyboard(orders),
    )


async def show_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split("_")[1])
    order, items = await get_order_with_items(order_id)
    if not order:
        await query.edit_message_text("Тапсырыс табылмады.")
        return

    text = format_order_summary(order, items)
    from keyboards.keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Тапсырыстар тізіміне", callback_data="my_orders")]
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def admin_update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    parts = query.data.split("_")
    order_id = int(parts[2])
    new_status = parts[3]

    await update_order_status(order_id, new_status)

    order, items = await get_order_with_items(order_id)
    from config import ORDER_STATUSES
    await query.edit_message_text(
        f"✅ #{order_id} тапсырысының күйі өзгертілді: *{ORDER_STATUSES.get(new_status, new_status)}*\n\n"
        + format_order_summary(order, items),
        parse_mode="Markdown",
    )

    await context.bot.send_message(
        chat_id=order.user.telegram_id if hasattr(order, 'user') else update.effective_chat.id,
        text=f"📦 *#{order_id}* тапсырысыңыздың күйі жаңартылды:\n*{ORDER_STATUSES.get(new_status, new_status)}*",
        parse_mode="Markdown",
    ) if False else None


def get_order_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_checkout, pattern="^checkout$")],
        states={
            ENTER_PHONE: [
                MessageHandler(filters.CONTACT, enter_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone),
            ],
            ENTER_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_address),
            ],
            ENTER_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment),
            ],
            CHOOSE_PAYMENT: [
                CallbackQueryHandler(choose_payment, pattern="^confirm_order$"),
                CallbackQueryHandler(change_address, pattern="^change_address$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
                CallbackQueryHandler(process_payment, pattern="^pay_"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
        ],
        allow_reentry=True,
    )


def get_order_handlers():
    return [
        get_order_conversation_handler(),
        MessageHandler(filters.Text(["📋 Менің тапсырыстарым"]), show_orders),
        CallbackQueryHandler(show_order_detail, pattern="^order_"),
        CallbackQueryHandler(simulate_payment_handler, pattern="^sim_pay_"),
        CallbackQueryHandler(cancel_payment, pattern="^cancel_pay_"),
        CallbackQueryHandler(admin_update_status, pattern="^admin_status_"),
        CallbackQueryHandler(show_orders, pattern="^my_orders$"),
    ]
