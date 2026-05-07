import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def _build_db_url() -> str:
    raw = os.getenv("DATABASE_URL", "")
    if raw.startswith("postgres://"):
        # Railway возвращает postgres://, SQLAlchemy ожидает postgresql+asyncpg://
        raw = raw.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgresql://"):
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw or "sqlite+aiosqlite:///food_delivery.db"

DATABASE_URL = _build_db_url()

DELIVERY_PRICE = 800
FREE_DELIVERY_THRESHOLD = 8000

PAYMENT_METHODS = {
    "card": "💳 Банк картасы (сынақ режимі)",
    "cash": "💵 Алған кезде қолма-қол",
    "online": "📱 Онлайн төлем (сынақ режимі)",
}

ORDER_STATUSES = {
    "new": "🆕 Жаңа",
    "confirmed": "✅ Расталған",
    "cooking": "👨‍🍳 Дайындалуда",
    "delivering": "🚚 Жолда",
    "delivered": "✔️ Жеткізілді",
    "cancelled": "❌ Болдырылмады",
}
