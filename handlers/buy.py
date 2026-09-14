from datetime import datetime

import pytz
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config.prices import PACKS
from config.settings import (
    OWNER_ID, PAYMENTS_GROUP_ID, TIMEZONE,
)
import database.engine as db_engine
from database.queries import (
    create_payment, get_or_create_user, get_payment,
    set_credits, update_payment,
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

# Estado temporal: user_tg_id → payment_id (esperando foto)
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

    # Leer QR en tiempo de ejecución
    import config.settings as cfg
    qr = cfg.QR_IMAGE

    qr_msg = None
    if qr:
        try:
            qr_msg = await bot.send_photo(
                chat_id=call.from_user.id,
                photo=qr,
                caption=text,
                reply_markup=kb_send_voucher(payment_id),
                parse_mode='HTML',
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error enviando QR: {e}")

    if not qr_msg:
        qr_msg = await bot.send_message(
            chat_id=call.from_user.id,
            text=text,
            reply_markup=kb_send_voucher(payment_id),
            parse_mode='HTML',
        )

    # Guardar ID del mensaje QR en BD
    async with db_engine.AsyncSessionLocal() as session:
        await update_payment(
            session, payment_id, status='PENDIENTE',
            qr_msg_id=qr_msg.message_id,
        )


# ── Botón "Enviar comprobante" ────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('voucher_'))
async def cb_voucher(call: CallbackQuery, bot: Bot) -> None:
    payment_id = int(call.data.split('_')[1])

    async with db_engine.AsyncSessionLocal() as session:
        payment = await get_payment(session, payment_id)

    if not payment or payment.user_tg_id != call.from_user.id:
        await call.answer("❌ Pago no encontrado.", show_alert=True)
        return
    if payment.status != 'PENDIENTE':
        await call.answer("⚠️ Este pago ya fue procesado.", show_alert=True)
        return

    _waiting_voucher[call.from_user.id] = payment_id

    await call.answer()

    # Enviar instrucciones y guardar su ID
    instr_msg = await bot.send_message(
        chat_id=call.from_user.id,
        text=txt_send_voucher(),
        parse_mode='HTML',
    )

    async with db_engine.AsyncSessionLocal() as session:
        await update_payment(
            session, payment_id, status='PENDIENTE',
            instructions_msg_id=instr_msg.message_id,
        )


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

        tz    = pytz.timezone(TIMEZONE)
        now   = datetime.now(tz)
        fecha = now.strftime('%d/%m/%Y')
        hora  = now.strftime('%H:%M')
        pack_name = PACK_NAMES.get(payment.pack, payment.pack.upper())

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

        target    = PAYMENTS_GROUP_ID or OWNER_ID
        group_msg = await bot.send_photo(
            chat_id=target,
            photo=photo_file_id,
            caption=group_text,
            reply_markup=kb_payment_review(payment_id),
            parse_mode='HTML',
        )

        # Enviar confirmación al cliente y guardar su ID
        confirm_msg = await message.answer(txt_voucher_received(), parse_mode='HTML')

        # Guardar todos los IDs en BD
        await update_payment(
            session, payment_id,
            status='PENDIENTE',
            photo_file_id=photo_file_id,
            group_msg_id=group_msg.message_id,
            confirm_msg_id=confirm_msg.message_id,
        )


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

        total     = payment.credits + payment.bonus
        pack_name = PACK_NAMES.get(payment.pack, payment.pack.upper())

        # Guardar IDs antes de cerrar sesión
        client_id           = payment.user_tg_id
        qr_msg_id           = payment.qr_msg_id
        instructions_msg_id = payment.instructions_msg_id
        confirm_msg_id      = payment.confirm_msg_id

        await set_credits(session, client_id, total)
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

    # Eliminar todos los mensajes del flujo de compra del cliente
    for msg_id in [qr_msg_id, instructions_msg_id, confirm_msg_id]:
        if msg_id:
            try:
                await bot.delete_message(chat_id=client_id, message_id=msg_id)
            except Exception:
                pass

    # Enviar solo el mensaje de PAGO APROBADO con detalle
    try:
        await bot.send_message(
            chat_id=client_id,
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

        client_id = payment.user_tg_id
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
            chat_id=client_id,
            text=txt_payment_rejected(),
            parse_mode='HTML',
        )
    except Exception:
        pass
