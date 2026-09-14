import asyncio

from aiogram import Bot, Router
from aiogram.types import CallbackQuery, Message

from config.settings import GROUP_ID, OWNER_ID
import database.engine as db_engine
from database.queries import get_order, update_order_status
from keyboards.builders import kb_empty
from texts.messages import (
    txt_ask_result_data, txt_cancelled_client, txt_final_report,
    txt_group_cancelled, txt_processing, txt_result_template,
)

router = Router()

# Estado temporal en memoria
# order_id → info del pedido
_pending_results: dict[int, dict] = {}
# group_chat_id → order_id (esperando que el owner envíe los datos EN EL GRUPO)
_waiting_in_group: dict[int, int] = {}


# ── Confirmar pedido ──────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('confirm_'))
async def cb_confirm(call: CallbackQuery, bot: Bot) -> None:
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Solo el dueño puede confirmar.", show_alert=True)
        return

    order_id = int(call.data.split('_')[1])

    async with db_engine.AsyncSessionLocal() as session:
        order = await get_order(session, order_id)
        if not order:
            await call.answer("❌ Pedido no encontrado.", show_alert=True)
            return
        if order.status != 'PENDIENTE':
            await call.answer("⚠️ Este pedido ya fue procesado.", show_alert=True)
            return
        await update_order_status(session, order_id, 'PROCESANDO')

    await call.answer("✅ Confirmado. Iniciando proceso...")

    # Quitar botones del mensaje del grupo
    await call.message.edit_reply_markup(reply_markup=kb_empty())

    # El grupo donde llegó la solicitud
    group_chat_id = call.message.chat.id

    # Guardar estado — esperar respuesta del owner EN ESTE GRUPO
    _pending_results[order_id] = {
        'client_tg_id':  order.user_tg_id,
        'client_msg_id': order.client_msg_id,
        'service':       order.service,
        'data':          order.data,
        'group_chat_id': group_chat_id,
    }
    _waiting_in_group[group_chat_id] = order_id

    # ── Animar progreso en el mensaje del cliente ─────────────────────────────
    client_chat = order.user_tg_id
    client_msg  = order.client_msg_id

    async def animate():
        for pct in [1, 25, 50, 75, 100]:
            try:
                await bot.edit_message_caption(
                    chat_id=client_chat,
                    message_id=client_msg,
                    caption=txt_processing(pct),
                    parse_mode='HTML',
                )
            except Exception:
                try:
                    await bot.edit_message_text(
                        chat_id=client_chat,
                        message_id=client_msg,
                        text=txt_processing(pct),
                        parse_mode='HTML',
                    )
                except Exception:
                    pass
            if pct < 100:
                await asyncio.sleep(1.2)

    asyncio.create_task(animate())

    # ── Pedir datos al owner EN EL GRUPO ─────────────────────────────────────
    await bot.send_message(
        chat_id=group_chat_id,
        text=txt_ask_result_data(),
        parse_mode='HTML',
    )


# ── Cancelar pedido ───────────────────────────────────────────────────────────

@router.callback_query(lambda c: c.data and c.data.startswith('cancel_'))
async def cb_cancel(call: CallbackQuery, bot: Bot) -> None:
    if call.from_user.id != OWNER_ID:
        await call.answer("⛔ Solo el dueño puede cancelar.", show_alert=True)
        return

    order_id = int(call.data.split('_')[1])

    async with db_engine.AsyncSessionLocal() as session:
        order = await get_order(session, order_id)
        if not order:
            await call.answer("❌ Pedido no encontrado.", show_alert=True)
            return
        if order.status not in ('PENDIENTE', 'PROCESANDO'):
            await call.answer("⚠️ Este pedido ya fue procesado.", show_alert=True)
            return
        await update_order_status(session, order_id, 'CANCELADO')

    await call.answer("❌ Pedido cancelado.")

    # Editar mensaje del grupo
    await call.message.edit_text(
        txt_group_cancelled(order.service, order.data),
        reply_markup=kb_empty(),
        parse_mode='HTML',
    )

    # Notificar al cliente
    try:
        if order.client_msg_id:
            await bot.edit_message_caption(
                chat_id=order.user_tg_id,
                message_id=order.client_msg_id,
                caption=txt_cancelled_client(order.service, order.data),
                parse_mode='HTML',
            )
    except Exception:
        try:
            await bot.send_message(
                order.user_tg_id,
                txt_cancelled_client(order.service, order.data),
                parse_mode='HTML',
            )
        except Exception:
            pass

    # Limpiar estado
    group_chat_id = call.message.chat.id
    _pending_results.pop(order_id, None)
    _waiting_in_group.pop(group_chat_id, None)


# ── Recibir datos del resultado — SOLO en el grupo de solicitudes ─────────────

@router.message(lambda m: (
    m.from_user and m.from_user.id == OWNER_ID
    and m.chat.id in _waiting_in_group
))
async def receive_result_data(message: Message, bot: Bot) -> None:
    group_chat_id = message.chat.id
    order_id = _waiting_in_group.get(group_chat_id)
    if not order_id:
        return

    result_text = message.text or message.caption or ''
    if not result_text.strip():
        return

    info = _pending_results.get(order_id)
    if not info:
        return

    # Limpiar estado
    _waiting_in_group.pop(group_chat_id, None)
    _pending_results.pop(order_id, None)

    # Actualizar pedido en BD
    async with db_engine.AsyncSessionLocal() as session:
        await update_order_status(
            session, order_id, 'COMPLETADO', result_data=result_text
        )

    # Eliminar mensaje de progreso del cliente
    try:
        await bot.delete_message(
            chat_id=info['client_tg_id'],
            message_id=info['client_msg_id'],
        )
    except Exception:
        pass

    # Enviar reporte final al cliente
    try:
        await bot.send_message(
            chat_id=info['client_tg_id'],
            text=txt_final_report(result_text),
            parse_mode='HTML',
        )
    except Exception:
        pass

    # Confirmar en el grupo
    await message.reply(
        f"✅ Reporte enviado al cliente.\n"
        f"📋 Pedido <code>{order_id}</code> — <b>COMPLETADO</b>.",
        parse_mode='HTML',
    )
