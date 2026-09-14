from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config.settings import OWNER_ID
import database.engine as db_engine
from database.queries import get_or_create_user, get_user_orders
from keyboards.builders import kb_me
from texts.messages import txt_me
from utils.checks import check_banned, check_maintenance
from utils.sender import send_with_image

router = Router()


@router.message(Command('me'))
async def cmd_me(message: Message) -> None:
    if await check_maintenance(message):
        return

    async with db_engine.AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        orders = await get_user_orders(session, message.from_user.id)

    if await check_banned(message, user):
        return

    total       = len(orders)
    completadas = sum(1 for o in orders if o.status == 'COMPLETADO')
    canceladas  = sum(1 for o in orders if o.status == 'CANCELADO')
    rank        = 'OWNER' if message.from_user.id == OWNER_ID else 'USUARIO'

    text = txt_me(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        rank=rank,
        credits=user.credits,
        total=total,
        completadas=completadas,
        canceladas=canceladas,
    )
    await send_with_image(message, text, reply_markup=kb_me())
