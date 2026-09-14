from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config.settings import OWNER_ID
from database.engine import AsyncSessionLocal
from database.queries import get_or_create_user
from keyboards.builders import kb_cmds, kb_service_back, kb_start
from texts.messages import txt_cmds, txt_service_detail, txt_service_detail_bloqueo, txt_start
from utils.checks import check_banned, check_maintenance

router = Router()

BANK_KEYS = ['bcp', 'agr', 'ibk', 'cjaq', 'bbva', 'sbk', 'yape']


@router.message(Command('start'))
async def cmd_start(message: Message) -> None:
    if await check_maintenance(message):
        return

    async with AsyncSessionLocal() as session:
        user, created = await get_or_create_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    if await check_banned(message, user):
        return

    rank = 'OWNER' if message.from_user.id == OWNER_ID else 'USUARIO'
    text = txt_start(
        full_name=message.from_user.full_name or 'Usuario',
        tg_id=message.from_user.id,
        rank=rank,
        credits=user.credits,
    )
    await message.answer(text, reply_markup=kb_start(), parse_mode='HTML')


@router.message(Command('cmds'))
async def cmd_cmds(message: Message) -> None:
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

    await message.answer(txt_cmds(), reply_markup=kb_cmds(), parse_mode='HTML')


# ── Callbacks del menú de servicios ──────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('svc_'))
async def cb_service_detail(call: CallbackQuery) -> None:
    key = call.data.replace('svc_', '')
    if key == 'bloqueo':
        text = txt_service_detail_bloqueo()
    else:
        text = txt_service_detail(key)
    await call.message.edit_text(text, reply_markup=kb_service_back(), parse_mode='HTML')
    await call.answer()


@router.callback_query(lambda c: c.data == 'back_cmds')
async def cb_back_cmds(call: CallbackQuery) -> None:
    await call.message.edit_text(txt_cmds(), reply_markup=kb_cmds(), parse_mode='HTML')
    await call.answer()
