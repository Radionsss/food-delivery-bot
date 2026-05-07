from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from config import DATABASE_URL
from database.models import Base, User, CartItem, Order, OrderItem


engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def update_user_contact(telegram_id: int, phone: str = None, address: str = None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            if phone:
                user.phone = phone
            if address:
                user.address = address
            await session.commit()


async def get_cart(telegram_id: int) -> list[CartItem]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return []
        items = await session.execute(select(CartItem).where(CartItem.user_id == user.id))
        return items.scalars().all()


async def add_to_cart(telegram_id: int, item_id: int, item_name: str, price: float):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        existing = await session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.item_id == item_id)
        )
        cart_item = existing.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(user_id=user.id, item_id=item_id, item_name=item_name, price=price)
            session.add(cart_item)

        await session.commit()


async def remove_from_cart(telegram_id: int, item_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        existing = await session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.item_id == item_id)
        )
        cart_item = existing.scalar_one_or_none()
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                await session.delete(cart_item)
            await session.commit()


async def clear_cart(telegram_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return
        items = await session.execute(select(CartItem).where(CartItem.user_id == user.id))
        for item in items.scalars().all():
            await session.delete(item)
        await session.commit()


async def create_order(
    telegram_id: int,
    cart_items: list[CartItem],
    total_price: float,
    delivery_address: str,
    phone: str,
    payment_method: str,
    comment: str = None,
) -> Order:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        order = Order(
            user_id=user.id,
            total_price=total_price,
            delivery_address=delivery_address,
            phone=phone,
            payment_method=payment_method,
            comment=comment,
        )
        session.add(order)
        await session.flush()

        for ci in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                item_id=ci.item_id,
                item_name=ci.item_name,
                quantity=ci.quantity,
                price=ci.price,
            )
            session.add(order_item)

        await session.commit()
        await session.refresh(order)
        return order


async def get_user_orders(telegram_id: int) -> list[Order]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return []
        orders = await session.execute(
            select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
        )
        return orders.scalars().all()


async def get_order_with_items(order_id: int):
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            items = await session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
            return order, items.scalars().all()
        return None, []


async def update_order_status(order_id: int, status: str):
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            order.status = status
            await session.commit()


async def simulate_payment(order_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            order.payment_status = "paid"
            await session.commit()
            return True
        return False


async def get_all_orders_admin() -> list[Order]:
    async with AsyncSessionLocal() as session:
        orders = await session.execute(
            select(Order).order_by(Order.created_at.desc()).limit(50)
        )
        return orders.scalars().all()
