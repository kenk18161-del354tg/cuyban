from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from config.prices import PRICES, SERVICE_NAMES
from config.settings import OWNER_ID
import database.engine as db_engine
from database.queries import (
    ban_user, get_all_users, get_order, get_pending_orders,
    get_stats, get_user, set_credits, update_order_status,
)
from texts.messages import txt_stats, txt_user_info

router = Router()


def owner_only(func):
    """Decorador: solo el dueño puede ejecutar el comando."""
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id != OWNER_ID:
            return
        await func(message, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ── /admin ────────────────────────────────────────────────────────────────────

@router.message(Command('admin'))
@owner_only
async def cmd_admin(message: Message) -> None:
    text = (
        "👑 <b>PANEL DEL DUEÑO</b>\n\n"
        "📋 Comandos disponibles:\n\n"
        "<b>Usuarios:</b>\n"
        "/stats — Estadísticas\n"
        "/pedidos — Pedidos pendientes\n"
        "/buscar [id] — Buscar usuario\n"
        "/ban [id] — Banear usuario\n"
        "/unban [id] — Desbanear usuario\n"
        "/addbal [id] [monto] — Agregar créditos\n"
        "/delbal [id] [monto] — Quitar créditos\n\n"
        "<b>Sistema:</b>\n"
        "/setprice [servicio] [precio] — Cambiar precio\n"
        "/mantenimiento — Activar/desactivar\n"
        "/broadcast [mensaje] — Mensaje masivo\n"
        "/completar [id] — Completar pedido\n"
        "/rechazar [id] — Rechazar pedido"
    )
    await message.answer(text, parse_mode='HTML')


# ── /stats ────────────────────────────────────────────────────────────────────

@router.message(Command('stats'))
@owner_only
async def cmd_stats(message: Message) -> None:
    async with db_engine.AsyncSessionLocal() as session:
        s = await get_stats(session)
    await message.answer(
        txt_stats(s['total_users'], s['total_orders'],
                  s['completed'], s['cancelled'], s['pending']),
        parse_mode='HTML'
    )


# ── /pedidos ──────────────────────────────────────────────────────────────────

@router.message(Command('pedidos'))
@owner_only
async def cmd_pedidos(message: Message) -> None:
    async with db_engine.AsyncSessionLocal() as session:
        orders = await get_pending_orders(session)

    if not orders:
        await message.answer("✅ No hay pedidos pendientes.")
        return

    lines = ["⏳ <b>PEDIDOS PENDIENTES</b>\n"]
    for o in orders:
        lines.append(
            f"🔹 ID <code>{o.id}</code> | {SERVICE_NAMES.get(o.service, o.service)} "
            f"| <code>{o.data}</code> | TG: <code>{o.user_tg_id}</code>"
        )
    await message.answer('\n'.join(lines), parse_mode='HTML')


# ── /buscar ───────────────────────────────────────────────────────────────────

@router.message(Command('buscar'))
@owner_only
async def cmd_buscar(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Uso: /buscar [user_id]")
        return
    try:
        tg_id = int(parts[1].strip())
    except ValueError:
        await message.answer("⚠️ El ID debe ser numérico.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        user = await get_user(session, tg_id)

    if not user:
        await message.answer(f"❌ Usuario <code>{tg_id}</code> no encontrado.", parse_mode='HTML')
        return

    await message.answer(txt_user_info(user), parse_mode='HTML')


# ── /ban ──────────────────────────────────────────────────────────────────────

@router.message(Command('ban'))
@owner_only
async def cmd_ban(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Uso: /ban [user_id]")
        return
    try:
        tg_id = int(parts[1].strip())
    except ValueError:
        await message.answer("⚠️ El ID debe ser numérico.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        user = await ban_user(session, tg_id, banned=True)

    if not user:
        await message.answer(f"❌ Usuario <code>{tg_id}</code> no encontrado.", parse_mode='HTML')
        return

    await message.answer(f"🚫 Usuario <code>{tg_id}</code> baneado.", parse_mode='HTML')


# ── /unban ────────────────────────────────────────────────────────────────────

@router.message(Command('unban'))
@owner_only
async def cmd_unban(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Uso: /unban [user_id]")
        return
    try:
        tg_id = int(parts[1].strip())
    except ValueError:
        await message.answer("⚠️ El ID debe ser numérico.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        user = await ban_user(session, tg_id, banned=False)

    if not user:
        await message.answer(f"❌ Usuario <code>{tg_id}</code> no encontrado.", parse_mode='HTML')
        return

    await message.answer(f"✅ Usuario <code>{tg_id}</code> desbaneado.", parse_mode='HTML')


# ── /addbal ───────────────────────────────────────────────────────────────────

@router.message(Command('addbal'))
@owner_only
async def cmd_addbal(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Uso: /addbal [user_id] [monto]")
        return
    try:
        tg_id  = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("⚠️ ID y monto deben ser numéricos.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        user = await set_credits(session, tg_id, amount)

    if not user:
        await message.answer(f"❌ Usuario <code>{tg_id}</code> no encontrado.", parse_mode='HTML')
        return

    await message.answer(
        f"✅ +{amount} créditos a <code>{tg_id}</code>.\n"
        f"💳 Saldo actual: <b>{user.credits}</b>",
        parse_mode='HTML'
    )


# ── /delbal ───────────────────────────────────────────────────────────────────

@router.message(Command('delbal'))
@owner_only
async def cmd_delbal(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Uso: /delbal [user_id] [monto]")
        return
    try:
        tg_id  = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("⚠️ ID y monto deben ser numéricos.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        user = await set_credits(session, tg_id, -amount)

    if not user:
        await message.answer(f"❌ Usuario <code>{tg_id}</code> no encontrado.", parse_mode='HTML')
        return

    await message.answer(
        f"✅ -{amount} créditos a <code>{tg_id}</code>.\n"
        f"💳 Saldo actual: <b>{user.credits}</b>",
        parse_mode='HTML'
    )


# ── /setprice ─────────────────────────────────────────────────────────────────

@router.message(Command('setprice'))
@owner_only
async def cmd_setprice(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 3:
        servicios = ', '.join(PRICES.keys())
        await message.answer(
            f"Uso: /setprice [servicio] [precio]\n"
            f"Servicios: {servicios}"
        )
        return
    key = parts[1].lower()
    if key not in PRICES:
        await message.answer(f"❌ Servicio <code>{key}</code> no existe.", parse_mode='HTML')
        return
    try:
        price = int(parts[2])
    except ValueError:
        await message.answer("⚠️ El precio debe ser numérico.")
        return

    PRICES[key] = price
    name = SERVICE_NAMES.get(key, key)
    await message.answer(
        f"✅ Precio actualizado:\n{name} ➤ <b>{price}</b> créditos",
        parse_mode='HTML'
    )


# ── /mantenimiento ────────────────────────────────────────────────────────────

@router.message(Command('mantenimiento'))
@owner_only
async def cmd_mantenimiento(message: Message) -> None:
    import config.settings as cfg
    cfg.MAINTENANCE = not cfg.MAINTENANCE
    estado = "ACTIVADO 🔧" if cfg.MAINTENANCE else "DESACTIVADO ✅"
    await message.answer(f"Mantenimiento: <b>{estado}</b>", parse_mode='HTML')


# ── /broadcast ────────────────────────────────────────────────────────────────

@router.message(Command('broadcast'))
@owner_only
async def cmd_broadcast(message: Message, bot: Bot) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Uso: /broadcast [mensaje]")
        return

    texto = parts[1].strip()

    async with db_engine.AsyncSessionLocal() as session:
        users = await get_all_users(session)

    enviados  = 0
    fallidos  = 0
    for user in users:
        try:
            await bot.send_message(user.tg_id, texto)
            enviados += 1
        except Exception:
            fallidos += 1

    await message.answer(
        f"📢 Broadcast completado.\n"
        f"✅ Enviados: {enviados}\n"
        f"❌ Fallidos: {fallidos}"
    )


# ── /completar ────────────────────────────────────────────────────────────────

@router.message(Command('completar'))
@owner_only
async def cmd_completar(message: Message, bot: Bot) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Uso: /completar [order_id]")
        return
    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ El ID debe ser numérico.")
        return

    async with db_engine.AsyncSessionLocal() as session:
        order = await get_order(session, order_id)
        if not order:
            await message.answer(f"❌ Pedido <code>{order_id}</code> no encontrado.", parse_mode='HTML')
            return
        await update_order_status(session, order_id, 'COMPLETADO')

    await message.answer(
        f"✅ Pedido <code>{order_id}</code> marcado como COMPLETADO.", parse_mode='HTML'
    )
    # Notificar al cliente
    try:
        await bot.send_message(
            order.user_tg_id,
            f"✅ Tu pedido <code>{order_id}</code> ha sido <b>COMPLETADO</b>.",
            parse_mode='HTML'
        )
    except Exception:
        pass


# ── /rechazar ─────────────────────────────────────────────────────────────────

@router.message(Command('rechazar'))
@owner_only
async def cmd_rechazar(message: Message, bot: Bot) -> None:
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer("Uso: /rechazar [order_id] [motivo opcional]")
        return
    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ El ID debe ser numérico.")
        return

    motivo = parts[2] if len(parts) > 2 else "Sin motivo especificado."

    async with db_engine.AsyncSessionLocal() as session:
        order = await get_order(session, order_id)
        if not order:
            await message.answer(f"❌ Pedido <code>{order_id}</code> no encontrado.", parse_mode='HTML')
            return
        await update_order_status(session, order_id, 'CANCELADO')

    await message.answer(
        f"❌ Pedido <code>{order_id}</code> rechazado.", parse_mode='HTML'
    )
    try:
        await bot.send_message(
            order.user_tg_id,
            f"❌ Tu pedido <code>{order_id}</code> fue <b>CANCELADO</b>.\n"
            f"📌 Motivo: {motivo}",
            parse_mode='HTML'
        )
    except Exception:
        pass
