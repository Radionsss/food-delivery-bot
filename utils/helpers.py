import json
from pathlib import Path
from config import DELIVERY_PRICE, FREE_DELIVERY_THRESHOLD

_menu_cache = None


def load_menu() -> dict:
    global _menu_cache
    if _menu_cache is None:
        menu_path = Path(__file__).parent.parent / "data" / "menu.json"
        with open(menu_path, encoding="utf-8") as f:
            _menu_cache = json.load(f)
    return _menu_cache


def get_category(category_id: int) -> dict | None:
    menu = load_menu()
    for cat in menu["categories"]:
        if cat["id"] == category_id:
            return cat
    return None


def get_item(item_id: int) -> dict | None:
    menu = load_menu()
    for cat in menu["categories"]:
        for item in cat["items"]:
            if item["id"] == item_id:
                return item, cat["id"]
    return None, None


def format_cart(cart_items) -> str:
    if not cart_items:
        return "Себет бос 🛒"

    lines = ["🛒 *Сіздің себетіңіз:*\n"]
    total = 0
    for ci in cart_items:
        item_total = ci.price * ci.quantity
        total += item_total
        lines.append(f"• {ci.item_name} × {ci.quantity} = *{item_total:.0f}₸*")

    lines.append(f"\n💰 Тауарлар сомасы: *{total:.0f}₸*")

    delivery = 0 if total >= FREE_DELIVERY_THRESHOLD else DELIVERY_PRICE
    if delivery == 0:
        lines.append("🚚 Жеткізу: *Тегін* 🎉")
    else:
        lines.append(f"🚚 Жеткізу: *{delivery}₸*")
        lines.append(f"_(Тегін жеткізу {FREE_DELIVERY_THRESHOLD}₸-ден бастап)_")

    grand_total = total + delivery
    lines.append(f"\n🧾 *Жиыны: {grand_total:.0f}₸*")
    return "\n".join(lines)


def calculate_total(cart_items) -> float:
    subtotal = sum(ci.price * ci.quantity for ci in cart_items)
    delivery = 0 if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_PRICE
    return subtotal + delivery


def format_order_summary(order, order_items) -> str:
    from config import ORDER_STATUSES, PAYMENT_METHODS
    lines = [
        f"📦 *Тапсырыс #{order.id}*",
        f"📅 Күні: {order.created_at.strftime('%d.%m.%Y %H:%M')}",
        f"📊 Күйі: {ORDER_STATUSES.get(order.status, order.status)}",
        f"💳 Төлем: {PAYMENT_METHODS.get(order.payment_method, order.payment_method)}",
        f"💰 Төлем күйі: {'✅ Төленді' if order.payment_status == 'paid' else '⏳ Төлемді күтуде'}",
        "",
        "🧾 *Тапсырыс құрамы:*",
    ]
    for item in order_items:
        lines.append(f"• {item.item_name} × {item.quantity} = {item.price * item.quantity:.0f}₸")
    lines.append(f"\n💵 *Жиыны: {order.total_price:.0f}₸*")
    lines.append(f"📍 Мекенжай: {order.delivery_address}")
    lines.append(f"📞 Телефон: {order.phone}")
    if order.comment:
        lines.append(f"💬 Пікір: {order.comment}")
    return "\n".join(lines)
