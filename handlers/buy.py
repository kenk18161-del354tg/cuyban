from datetime import datetime

import pytz
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config.prices import PACKS
from config.settings import (
    BOT_NAME, OWNER_ID, PAYMENTS_GROUP_ID, QR_IMAGE, TIMEZONE,
)
import database.engine as db_engine
from database.queries import (
    create_payment, get_or_create_user, get_payment,
    get_pending_payment_by_user, set_credits, update_payment,
)
from keyboards.builders import kb_buy, kb_empty, kb_payment_review, kb_send_voucher
from texts.messages import (
    txt_buy, txt_payment_approved, txt_payment_group,
    txt_payment_rejected, txt_qr_payment, txt_send_voucher,
    txt_voucher_received,
)
from utils.checks import check_banned, check_maintenance
from utils.sender import send_with_image

router = Router()

PACK_NAMES = {
    'basico': '💳 PACK BÁSICO',
    'plus':   '⭐ PACK PLUS',
    'pro':    '💎 PACK PRO',
}

# Estado temporal: user_tg_id → payment_id (esperando foto del comprobante)
_waiting_voucher: dict[int, int] = {}


# ── /buy ──────────────────────────────────────────────────────────────────────

@router.message(Command('buy'))
async def cmd_buy(message: Message) -> None:
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

    await send_with_image(message, txt_buy(user.credits), reply_markup=kb_buy())


# Callback desde /cmds
@router.callback_query(lambda c: c.data == 'open_buy')
async def cb_open_buy(call: CallbackQuery) -> None:
    async with db_engine.AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session,
            tg_id=call.from_user.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name,
        )
    text = txt_buy(user.credits)
    try:
        await call.message.edit_caption(caption=text, reply_markup=kb_buy(), parse_mode='HTML')
    except Exception:
        await call.message.edit_text(text, reply_markup=kb_buy(), parse_mode='HTML')
    await call.answer()


# ── Selección de paquete → mostrar QR ────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('pack_'))
async def cb_select_pack(call: CallbackQuery, bot: Bot) -> None:
    pack_key  = call.data.replace('pack_', '')
    pack      = PACKS.get(pack_key)
    pack_name = PACK_NAMES.get(pack_key, pack_key.upper())

    if not pack:
        await call.answer("❌ Paquete no encontrado.", show_alert=True)
        return

    # Crear registro de pago en BD
    async with db_engine.AsyncSessionLocal() as session:
        payment = await create_payment(
            session,
            user_tg_id=call.from_user.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name,
            pack=pack_key,
            credits=pack['credits'],
            bonus=pack['bonus'],
            price_soles=pack['price_soles'],
        )
        payment_id = payment.id

    text = txt_qr_payment(
        pack_name=pack_name,
        credits=pack['credits'],
        bonus=pack['bonus'],
        price=pack['price_soles'],
    )

    await call.answer()

    # Enviar QR con botón de comprobante
    if QR_IMAGE:
        try:
            await call.message.answer_photo(
                photo=QR_IMAGE,
                caption=text,
                reply_markup=kb_send_voucher(payment_id),
                parse_mode='HTML',
            )
            return
        except Exception:
            pass
    # Fallback sin QR
    await call.message.answer(
        text, reply_markup=kb_send_voucher(payment_id), parse_mode='HTML'
    )


# ── Botón "Enviar comprobante" ────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('voucher_'))
async def cb_voucher(call: CallbackQuery) -> None:
    payment_id = int(call.data.split('_')[1])

    # Verificar que el pago pertenece a este usuario y sigue PENDIENTE
    async with db_engine.AsyncSessionLocal() as session:
        payment = await get_payment(session, payment_id)

    if not payment or payment.user_tg_id != call.from_user.id:
        await call.answer("❌ Pago no encontrado.", show_alert=True)
        return
    if payment.status != 'PENDIENTE':
        await call.answer("⚠️ Este pago ya fue procesado.", show_alert=True)
        return

    # Registrar que este usuario está esperando enviar foto
    _waiting_voucher[call.from_user.id] = payment_id

    await call.answer()
    await call.message.answer(txt_send_voucher(), parse_mode='HTML')


# ── Recibir foto del comprobante ──────────────────────────────────────────────

@router.message(lambda m: (
    m.from_user is not None
    and m.from_user.id in _waiting_voucher
    and m.photo is not None
    and m.chat.type == 'private'
))
async def receive_voucher(message: Message, bot: Bot) -> None:
    user_tg_id = message.from_user.id
    payment_id = _waiting_voucher.pop(user_tg_id, None)
    if not payment_id:
        return

    photo_file_id = message.photo[-1].file_id

    async with db_engine.AsyncSessionLocal() as session:
        payment = await get_payment(session, payment_id)
        if not payment or payment.status != 'PENDIENTE':
            return

        # Zona horaria
        tz    = pytz.timezone(TIMEZONE)
        now   = datetime.now(tz)
        fecha = now.strftime('%d/%m/%Y')
        hora  = now.strftime('%H:%M')

        pack_name = PACK_NAMES.get(payment.pack, payment.pack.upper())

        # Texto para el grupo PAGOS
        group_text = txt_payment_group(
            username=message.from_user.username,
            tg_id=user_tg_id,
            full_name=message.from_user.full_name,
            pack_name=pack_name,
            credits=payment.credits,
            bonus=payment.bonus,
            price=payment.price_soles,
            fecha=fecha,
            hora=hora,
        )

        # Enviar al grupo PAGOS
        target = PAYMENTS_GROUP_ID or OWNER_ID
        group_msg = await bot.send_photo(
            chat_id=target,
            photo=photo_file_id,
            caption=group_text,
            reply_markup=kb_payment_review(payment_id),
            parse_mode='HTML',
        )

        # Guardar file_id y msg_id del grupo
        await update_payment(
            session, payment_id,
            status='PENDIENTE',
            photo_file_id=photo_file_id,
            group_msg_id=group_msg.message_id,
        )

    # Confirmar al cliente
    await message.answer(txt_voucher_received(), parse_mode='HTML')


# ── Aprobar pago ──────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('pay_approve_'))
async def cb_approve_payment(call: CallbackQuery, bot: Bot) -> None:
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Solo el dueño puede aprobar.", show_alert=True)
        return

    payment_id = int(call.data.split('_')[2])

    async with db_engine.AsyncSessionLocal() as session:
        payment = await get_payment(session, payment_id)
        if not payment:
            await call.answer("❌ Pago no encontrado.", show_alert=True)
            return
        if payment.status != 'PENDIENTE':
            await call.answer("⚠️ Este pago ya fue procesado.", show_alert=True)
            return

        total = payment.credits + payment.bonus
        pack_name = PACK_NAMES.get(payment.pack, payment.pack.upper())

        # Agregar créditos al usuario
        await set_credits(session, payment.user_tg_id, total)
        await update_payment(session, payment_id, status='APROBADO')

    await call.answer("✅ Pago aprobado.")

    # Editar mensaje del grupo PAGOS
    try:
        await call.message.edit_caption(
            caption=call.message.caption + "\n\n✅ <b>ESTADO: APROBADO</b>",
            reply_markup=kb_empty(),
            parse_mode='HTML',
        )
    except Exception:
        pass

    # Notificar al cliente
    try:
        await bot.send_message(
            chat_id=payment.user_tg_id,
            text=txt_payment_approved(payment.credits, payment.bonus, pack_name),
            parse_mode='HTML',
        )
    except Exception:
        pass


# ── Rechazar pago ─────────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('pay_reject_'))
async def cb_reject_payment(call: CallbackQuery, bot: Bot) -> None:
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Solo el dueño puede rechazar.", show_alert=True)
        return

    payment_id = int(call.data.split('_')[2])

    async with db_engine.AsyncSessionLocal() as session:
        payment = await get_payment(session, payment_id)
        if not payment:
            await call.answer("❌ Pago no encontrado.", show_alert=True)
            return
        if payment.status != 'PENDIENTE':
            await call.answer("⚠️ Este pago ya fue procesado.", show_alert=True)
            return
        await update_payment(session, payment_id, status='RECHAZADO')

    await call.answer("❌ Pago rechazado.")

    # Editar mensaje del grupo PAGOS
    try:
        await call.message.edit_caption(
            caption=call.message.caption + "\n\n❌ <b>ESTADO: RECHAZADO</b>",
            reply_markup=kb_empty(),
            parse_mode='HTML',
        )
    except Exception:
        pass

    # Notificar al cliente
    try:
        await bot.send_message(
            chat_id=payment.user_tg_id,
            text=txt_payment_rejected(),
            parse_mode='HTML',
        )
    except Exception:
        pass
