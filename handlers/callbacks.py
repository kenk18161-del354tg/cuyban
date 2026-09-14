import asyncio

from aiogram import Bot, Router
from aiogram.types import CallbackQuery, Message

from config.settings import OWNER_ID
import database.engine as db_engine
from database.queries import (
    get_order, get_processing_order_by_group, update_order_status,
)
from keyboards.builders import kb_empty
from texts.messages import (
    txt_ask_result_data, txt_cancelled_client, txt_final_report,
    txt_group_cancelled, txt_group_completed, txt_processing,
)

router = Router()


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

        group_chat_id   = call.message.chat.id
        original_msg_id = call.message.message_id

        # Enviar mensaje pidiendo datos ANTES de cambiar estado
        ask_msg = await bot.send_message(
            chat_id=group_chat_id,
            text=txt_ask_result_data(),
            parse_mode='HTML',
        )

        # Guardar todo en BD — sobrevive reinicios
        await update_order_status(
            session, order_id, 'PROCESANDO',
            group_msg_id=original_msg_id,
            client_msg_id=order.client_msg_id,
        )
        # Guardar campos extra directamente
        order.group_chat_id   = group_chat_id
        order.original_msg_id = original_msg_id
        order.ask_msg_id      = ask_msg.message_id
        await session.commit()

    await call.answer("✅ Confirmado. Iniciando proceso...")

    # Quitar botones del mensaje original
    await call.message.edit_reply_markup(reply_markup=kb_empty())

    # Animar progreso al cliente
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

    await call.message.edit_text(
        txt_group_cancelled(order.service, order.data),
        reply_markup=kb_empty(),
        parse_mode='HTML',
    )

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


# ── Recibir datos del resultado — SOLO en el grupo, del owner ─────────────────

@router.message(lambda m: (
    m.from_user is not None
    and m.from_user.id == OWNER_ID
    and m.chat.type in ('group', 'supergroup')
))
async def receive_result_data(message: Message, bot: Bot) -> None:
    group_chat_id = message.chat.id

    # Buscar en BD si hay un pedido PROCESANDO para este grupo
    async with db_engine.AsyncSessionLocal() as session:
        order = await get_processing_order_by_group(session, group_chat_id)
        if not order:
            return  # No hay pedido esperando en este grupo

        result_text = message.text or message.caption or ''
        if not result_text.strip():
            return

        # Guardar datos y marcar COMPLETADO
        await update_order_status(
            session, order.id, 'COMPLETADO', result_data=result_text
        )
        # Capturar datos antes de cerrar sesión
        client_tg_id    = order.user_tg_id
        client_msg_id   = order.client_msg_id
        original_msg_id = order.original_msg_id
        ask_msg_id      = order.ask_msg_id
        service         = order.service
        dato            = order.data
        price           = order.price
        bal_before      = order.balance_before
        bal_after       = order.balance_after
        username        = message.from_user.username
        fecha           = order.created_at.strftime('%d/%m/%Y')
        hora            = order.created_at.strftime('%H:%M')

    # 1. Eliminar mensaje "📋 INGRESAR DATOS DEL RESULTADO"
    if ask_msg_id:
        try:
            await bot.delete_message(chat_id=group_chat_id, message_id=ask_msg_id)
        except Exception:
            pass

    # 2. Eliminar mensaje del owner con los datos
    try:
        await bot.delete_message(chat_id=group_chat_id, message_id=message.message_id)
    except Exception:
        pass

    # 3. Editar mensaje original con resumen completo, o enviar nuevo si no hay
    resumen = txt_group_completed(
        service_key=service,
        dato=dato,
        username=username,
        tg_id=client_tg_id,
        price=price,
        bal_before=bal_before,
        bal_after=bal_after,
        fecha=fecha,
        hora=hora,
        result_data=result_text,
    )
    if original_msg_id:
        try:
            await bot.edit_message_text(
                chat_id=group_chat_id,
                message_id=original_msg_id,
                text=resumen,
                parse_mode='HTML',
            )
        except Exception:
            await bot.send_message(
                chat_id=group_chat_id,
                text=resumen,
                parse_mode='HTML',
            )
    else:
        await bot.send_message(
            chat_id=group_chat_id,
            text=resumen,
            parse_mode='HTML',
        )

    # 4. Eliminar mensaje de progreso del cliente
    if client_msg_id:
        try:
            await bot.delete_message(chat_id=client_tg_id, message_id=client_msg_id)
        except Exception:
            pass

    # 5. Enviar reporte final al cliente
    try:
        await bot.send_message(
            chat_id=client_tg_id,
            text=txt_final_report(result_text),
            parse_mode='HTML',
        )
    except Exception:
        pass
