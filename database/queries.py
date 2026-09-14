from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, User


# ── Usuarios ────────────────────────────────────────────────────────────────

async def get_or_create_user(session: AsyncSession, tg_id: int,
                              username: str | None,
                              full_name: str | None) -> tuple[User, bool]:
    """Devuelve (user, created). Si no existe lo crea."""
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        # Actualiza datos de perfil si cambiaron
        user.username  = username
        user.full_name = full_name
        await session.commit()
        return user, False

    user = User(tg_id=tg_id, username=username, full_name=full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def set_credits(session: AsyncSession, tg_id: int, amount: int) -> User | None:
    user = await get_user(session, tg_id)
    if user:
        user.credits = max(0, user.credits + amount)
        await session.commit()
    return user


async def ban_user(session: AsyncSession, tg_id: int, banned: bool) -> User | None:
    user = await get_user(session, tg_id)
    if user:
        user.is_banned = banned
        await session.commit()
    return user


# ── Pedidos ──────────────────────────────────────────────────────────────────

async def create_order(session: AsyncSession, user_tg_id: int, service: str,
                       data: str, price: int,
                       balance_before: int, balance_after: int) -> Order:
    order = Order(
        user_tg_id=user_tg_id,
        service=service,
        data=data,
        price=price,
        balance_before=balance_before,
        balance_after=balance_after,
        status='PENDIENTE',
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def update_order_status(session: AsyncSession, order_id: int,
                               status: str,
                               result_data: str | None = None,
                               group_msg_id: int | None = None,
                               client_msg_id: int | None = None) -> Order | None:
    order = await get_order(session, order_id)
    if order:
        order.status = status
        if result_data  is not None: order.result_data  = result_data
        if group_msg_id  is not None: order.group_msg_id  = group_msg_id
        if client_msg_id is not None: order.client_msg_id = client_msg_id
        await session.commit()
    return order


async def get_pending_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.status == 'PENDIENTE')
        .order_by(Order.created_at.asc())
    )
    return list(result.scalars().all())


async def get_user_orders(session: AsyncSession, tg_id: int) -> list[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.user_tg_id == tg_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_stats(session: AsyncSession) -> dict:
    total_users  = (await session.execute(select(func.count(User.id)))).scalar() or 0
    total_orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0
    completed    = (await session.execute(
        select(func.count()).where(Order.status == 'COMPLETADO')
    )).scalar() or 0
    cancelled    = (await session.execute(
        select(func.count()).where(Order.status == 'CANCELADO')
    )).scalar() or 0
    pending      = (await session.execute(
        select(func.count()).where(Order.status == 'PENDIENTE')
    )).scalar() or 0
    return {
        'total_users':  total_users,
        'total_orders': total_orders,
        'completed':    completed,
        'cancelled':    cancelled,
        'pending':      pending,
    }


async def get_processing_order_by_group(session: AsyncSession,
                                         group_chat_id: int) -> Order | None:
    """Devuelve el pedido en estado PROCESANDO para ese grupo."""
    result = await session.execute(
        select(Order)
        .where(Order.status == 'PROCESANDO')
        .where(Order.group_chat_id == group_chat_id)
        .order_by(Order.updated_at.desc())
    )
    return result.scalar_one_or_none()


# ── Pagos ─────────────────────────────────────────────────────────────────────

from database.models import Payment


async def create_payment(session: AsyncSession, user_tg_id: int,
                          username: str | None, full_name: str | None,
                          pack: str, credits: int, bonus: int,
                          price_soles: int) -> Payment:
    payment = Payment(
        user_tg_id=user_tg_id,
        username=username,
        full_name=full_name,
        pack=pack,
        credits=credits,
        bonus=bonus,
        price_soles=price_soles,
        status='PENDIENTE',
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment(session: AsyncSession, payment_id: int) -> Payment | None:
    result = await session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    return result.scalar_one_or_none()


async def update_payment(session: AsyncSession, payment_id: int,
                          status: str,
                          photo_file_id: str | None = None,
                          group_msg_id: int | None = None,
                          qr_msg_id: int | None = None,
                          instructions_msg_id: int | None = None,
                          confirm_msg_id: int | None = None) -> Payment | None:
    payment = await get_payment(session, payment_id)
    if payment:
        payment.status = status
        if photo_file_id         is not None: payment.photo_file_id         = photo_file_id
        if group_msg_id          is not None: payment.group_msg_id          = group_msg_id
        if qr_msg_id             is not None: payment.qr_msg_id             = qr_msg_id
        if instructions_msg_id   is not None: payment.instructions_msg_id   = instructions_msg_id
        if confirm_msg_id        is not None: payment.confirm_msg_id        = confirm_msg_id
        await session.commit()
    return payment


async def get_pending_payment_by_user(session: AsyncSession,
                                       user_tg_id: int) -> Payment | None:
    """Devuelve el pago PENDIENTE más reciente del usuario."""
    result = await session.execute(
        select(Payment)
        .where(Payment.user_tg_id == user_tg_id)
        .where(Payment.status == 'PENDIENTE')
        .order_by(Payment.created_at.desc())
    )
    return result.scalar_one_or_none()
