import asyncio
from datetime import datetime

import pytz
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from config.prices import PRICES, SERVICE_NAMES
from config.settings import (
    GROUP_ID, LOG_CHANNEL_ID, NOTIFY_ON_ORDER, OWNER_ID, TIMEZONE,
)
import database.engine as db_engine
from database.queries import (
    create_order, get_or_create_user, update_order_status,
)
from keyboards.builders import kb_group_order
from texts.messages import (
    txt_group_notification, txt_no_credits, txt_request_received,
)
from utils.checks import check_banned, check_maintenance, check_membership

router = Router()

SERVICES = list(PRICES.keys())  # ['bcp', 'agr', 'ibk', 'cjaq', 'bbva', 'sbk', 'yape', 'bloqueo']


async def _handle_service(message: Message, bot: Bot, service_key: str) -> None:
    """Lógica común para todos los comandos de servicio."""
    if await check_maintenance(message):
        return

    async with db_engine.AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        if await check_banned(message, user):
            return

        if await check_membership(message, bot):
            return

        # Extraer el dato enviado
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await message.answer(
                f"⚠️ Debes enviar el dato.\n"
                f"Ejemplo: <code>/{service_key} 123456789</code>",
                parse_mode='HTML'
            )
            return

        dato  = parts[1].strip()
        price = PRICES.get(service_key, 0)

        # Verificar saldo
        if user.credits < price:
            await message.answer(
                txt_no_credits(price, user.credits), parse_mode='HTML'
            )
            return

        bal_before = user.credits
        user.credits -= price
        await session.commit()
        bal_after = user.credits

        # Zona horaria
        tz   = pytz.timezone(TIMEZONE)
        now  = datetime.now(tz)
        fecha = now.strftime('%d/%m/%Y')
        hora  = now.strftime('%H:%M')

        # Crear pedido en BD
        order = await create_order(
            session,
            user_tg_id=message.from_user.id,
            service=service_key,
            data=dato,
            price=price,
            balance_before=bal_before,
            balance_after=bal_after,
        )

    # Mensaje de confirmación al cliente
    client_msg = await message.answer(
        txt_request_received(service_key, dato), parse_mode='HTML'
    )

    # Notificación al grupo/owner
    group_text = txt_group_notification(
        service_key=service_key,
        dato=dato,
        username=message.from_user.username,
        tg_id=message.from_user.id,
        price=price,
        bal_before=bal_before,
        bal_after=bal_after,
        fecha=fecha,
        hora=hora,
    )

    target = GROUP_ID or OWNER_ID
    group_msg = await bot.send_message(
        chat_id=target,
        text=group_text,
        reply_markup=kb_group_order(order.id),
        parse_mode='HTML',
    )

    # Guardar IDs de mensajes en el pedido
    async with db_engine.AsyncSessionLocal() as session:
        await update_order_status(
            session,
            order_id=order.id,
            status='PENDIENTE',
            group_msg_id=group_msg.message_id,
            client_msg_id=client_msg.message_id,
        )

    # Log channel
    if NOTIFY_ON_ORDER and LOG_CHANNEL_ID:
        try:
            await bot.send_message(LOG_CHANNEL_ID, group_text, parse_mode='HTML')
        except Exception:
            pass


# ── Registrar un handler por cada servicio ────────────────────────────────────

def _make_handler(key: str):
    async def handler(message: Message, bot: Bot) -> None:
        await _handle_service(message, bot, key)
    handler.__name__ = f'cmd_{key}'
    return handler


for _key in SERVICES:
    router.message(Command(_key))(_make_handler(_key))
