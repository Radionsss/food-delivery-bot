from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import PAYMENT_METHODS, ORDER_STATUSES


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🍽 Мәзір", "🛒 Себет"],
            ["📋 Менің тапсырыстарым", "👤 Профиль"],
            ["ℹ️ Біз туралы", "📞 Байланыс"],
        ],
        resize_keyboard=True,
    )


def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(cat["name"], callback_data=f"cat_{cat['id']}")] for cat in categories]
    buttons.append([InlineKeyboardButton("🔙 Басты мәзір", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def items_keyboard(items: list, category_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for item in items:
        buttons.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']}₸",
            callback_data=f"item_{item['id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Санаттар", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)


def item_detail_keyboard(item_id: int, category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Себетке қосу", callback_data=f"add_{item_id}")],
        [InlineKeyboardButton("🔙 Артқа", callback_data=f"cat_{category_id}")],
    ])


def cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    buttons = []
    for ci in cart_items:
        buttons.append([
            InlineKeyboardButton("➖", callback_data=f"cart_dec_{ci.item_id}"),
            InlineKeyboardButton(f"{ci.item_name} x{ci.quantity}", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"cart_inc_{ci.item_id}"),
        ])
    buttons.append([InlineKeyboardButton("🗑 Себетті тазалау", callback_data="cart_clear")])
    buttons.append([InlineKeyboardButton("✅ Тапсырысты ресімдеу", callback_data="checkout")])
    buttons.append([InlineKeyboardButton("🔙 Мәзірге", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)


def payment_keyboard() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(label, callback_data=f"pay_{key}")] for key, label in PAYMENT_METHODS.items()]
    buttons.append([InlineKeyboardButton("❌ Болдырмау", callback_data="cancel_order")])
    return InlineKeyboardMarkup(buttons)


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Тапсырысты растау", callback_data="confirm_order")],
        [InlineKeyboardButton("✏️ Мекенжайды өзгерту", callback_data="change_address")],
        [InlineKeyboardButton("❌ Болдырмау", callback_data="cancel_order")],
    ])


def simulate_payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Төлеу (сынақ режимі)", callback_data=f"sim_pay_{order_id}")],
        [InlineKeyboardButton("❌ Болдырмау", callback_data=f"cancel_pay_{order_id}")],
    ])


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for status_key, status_label in ORDER_STATUSES.items():
        buttons.append([InlineKeyboardButton(
            f"→ {status_label}", callback_data=f"admin_status_{order_id}_{status_key}"
        )])
    return InlineKeyboardMarkup(buttons)


def orders_list_keyboard(orders: list) -> InlineKeyboardMarkup:
    buttons = []
    for order in orders[:10]:
        buttons.append([InlineKeyboardButton(
            f"Тапсырыс #{order.id} — {order.total_price}₸ ({ORDER_STATUSES.get(order.status, order.status)})",
            callback_data=f"order_{order.id}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Басты мәзір", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)


def share_phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Нөмірмен бөлісу", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_keyboard():
    return ReplyKeyboardMarkup(
        [["⏩ Өткізіп жіберу"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
