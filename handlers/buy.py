from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.engine import AsyncSessionLocal
from database.queries import get_or_create_user
from keyboards.builders import kb_buy
from texts.messages import txt_buy
from utils.checks import check_banned, check_maintenance

router = Router()


@router.message(Command('buy'))
async def cmd_buy(message: Message) -> None:
    if await check_maintenance(message):
        return

    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    if await check_banned(message, user):
        return

    await message.answer(txt_buy(user.credits), reply_markup=kb_buy(), parse_mode='HTML')


# Callback desde el menú /cmds
@router.callback_query(lambda c: c.data == 'open_buy')
async def cb_open_buy(call: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session,
            tg_id=call.from_user.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name,
        )
    await call.message.edit_text(
        txt_buy(user.credits), reply_markup=kb_buy(), parse_mode='HTML'
    )
    await call.answer()
