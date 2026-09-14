from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config.settings import OWNER_USERNAME


def _owner_url() -> str:
    return f"https://t.me/{OWNER_USERNAME}" if OWNER_USERNAME else "https://t.me/"


# Botón Dueño reutilizable
def kb_owner() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👑 Dueño", url=_owner_url())
    ]])


# /start
def kb_start() -> InlineKeyboardMarkup:
    return kb_owner()


# /cmds — menú de servicios (2 columnas)
def kb_cmds() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    services = [
        ("🏦 BCP",            "svc_bcp"),
        ("🏦 Ágora",          "svc_agr"),
        ("🏦 IBK",            "svc_ibk"),
        ("🏦 Caja Arequipa",  "svc_cjaq"),
        ("🏦 BBVA",           "svc_bbva"),
        ("🏦 Scotiabank",     "svc_sbk"),
        ("📱 Yape",           "svc_yape"),
        ("🚫 Bloqueo Número", "svc_bloqueo"),
    ]
    for text, data in services:
        builder.button(text=text, callback_data=data)
    builder.button(text="🛒 Comprar Créditos", callback_data="open_buy")
    builder.adjust(2)
    return builder.as_markup()


# Detalle de servicio — botón Atrás
def kb_service_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Atrás", callback_data="back_cmds")
    ]])


# /buy — selector de paquetes
def kb_buy() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 BÁSICO",  callback_data="pack_basico")],
        [InlineKeyboardButton(text="⭐ PLUS",    callback_data="pack_plus")],
        [InlineKeyboardButton(text="💎 PRO",     callback_data="pack_pro")],
    ])


# QR de pago — botón enviar comprobante
def kb_send_voucher(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📤 Enviar comprobante",
            callback_data=f"voucher_{payment_id}"
        )
    ]])


# Grupo PAGOS — aprobar/rechazar en 1 columna
def kb_payment_review(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Aprobar pago",
            callback_data=f"pay_approve_{payment_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Rechazar pago",
            callback_data=f"pay_reject_{payment_id}"
        )],
    ])


# /me
def kb_me() -> InlineKeyboardMarkup:
    return kb_owner()


# Grupo SOLICITANDES — botones confirmar/cancelar
def kb_group_order(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Bloqueo confirmado",
            callback_data=f"confirm_{order_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Cancelar pedido",
            callback_data=f"cancel_{order_id}"
        )],
    ])


# Mensaje del grupo después de confirmar (sin botones)
def kb_empty() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])
