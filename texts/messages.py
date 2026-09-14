from config.settings import BOT_NAME, OWNER_USERNAME
from config.prices import PRICES, PACKS, SERVICE_NAMES


def txt_start(full_name: str, tg_id: int, rank: str, credits: int) -> str:
    return (
        f"👋 ¡Hola, {full_name}!\n\n"
        f"🔐 Bienvenido a <b>{BOT_NAME}</b>\n\n"
        f"Servicio especializado en Bloqueo de IMEI + Línea.\n\n"
        f"🆔 ID de usuario: <code>{tg_id}</code>\n"
        f"⭐ Rango: <b>{rank}</b>\n"
        f"💳 Saldo disponible: <b>{credits}</b> créditos\n\n"
        f"🕐 Horario de atención:\n"
        f"Lunes a Domingo\n"
        f"00:00 — 00:00\n\n"
        f"📋 Comandos principales:\n\n"
        f"/cmds → Ver servicios disponibles\n"
        f"/me → Consultar mi perfil\n"
        f"/buy → Comprar créditos\n\n"
        f"⚡ Gracias por utilizar <b>{BOT_NAME}</b>."
    )


def txt_cmds() -> str:
    return (
        f"[<b>{BOT_NAME}</b>] ➤ MENÚ DE SERVICIOS\n\n"
        f"📋 Selecciona una opción para continuar.\n\n"
        f"🔐 Servicios disponibles:\n\n"
        f"👇 Elige el servicio que deseas utilizar:"
    )


def txt_service_detail(key: str) -> str:
    name  = SERVICE_NAMES.get(key, key.upper())
    price = PRICES.get(key, 0)
    emoji = name.split()[0]
    return (
        f"{emoji} <b>Bloqueo {name.split(' ', 1)[1]}</b>\n\n"
        f"• Estado ➤ OPERATIVO ✅\n"
        f"• Comando ➤ <code>/{key} [datos]</code>\n"
        f"• Ejemplo ➤ <code>/{key} 123456789</code>\n"
        f"• Precio ➤ <b>{price}</b> créditos\n\n"
        f"• Resultado ➤ Bloqueo de banca.\n\n"
        f"⚡ Gracias por utilizar <b>{BOT_NAME}</b>."
    )


def txt_service_detail_bloqueo() -> str:
    price = PRICES.get('bloqueo', 0)
    return (
        f"🚫 <b>Bloqueo Número</b>\n\n"
        f"• Estado ➤ OPERATIVO ✅\n"
        f"• Comando ➤ <code>/bloqueo [datos]</code>\n"
        f"• Ejemplo ➤ <code>/bloqueo 919871711</code>\n"
        f"• Precio ➤ <b>{price}</b> créditos\n\n"
        f"• Resultado ➤ Bloqueo de línea + IMEI.\n\n"
        f"⚡ Gracias por utilizar <b>{BOT_NAME}</b>."
    )


def txt_buy(credits: int) -> str:
    b = PACKS['basico']
    p = PACKS['plus']
    pr = PACKS['pro']
    return (
        f"💳 Tu saldo actual: <b>{credits}</b> créditos\n\n"
        f"🎟️ <b>PAQUETES DE CRÉDITOS</b>\n\n"
        f"💳 <b>PACK BÁSICO</b>\n"
        f"➜ {b['credits']} créditos — S/ {b['price_soles']}\n\n"
        f"⭐ <b>PACK PLUS</b>\n"
        f"➜ {p['credits']} créditos + {p['bonus']} GRATIS — S/ {p['price_soles']}\n\n"
        f"💎 <b>PACK PRO</b>\n"
        f"➜ {pr['credits']} créditos + {pr['bonus']} GRATIS — S/ {pr['price_soles']}\n\n"
        f"🚀 Recarga rápida y sencilla\n"
        f"🔒 Servicio seguro y confiable\n"
        f"📩 Escríbenos para realizar tu compra\n\n"
        f"👇 Selecciona un paquete para continuar."
    )


def txt_me(tg_id: int, username: str, rank: str, credits: int,
           total: int, completadas: int, canceladas: int) -> str:
    user_str = f"@{username}" if username else "Sin usuario"
    return (
        f"👤 <b>MI PERFIL</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"👤 Usuario: {user_str}\n\n"
        f"⭐ Rango: <b>{rank}</b>\n"
        f"💳 Saldo: <b>{credits}</b> créditos\n\n"
        f"📊 Solicitudes:\n"
        f"• Total: <b>{total}</b>\n"
        f"• Completadas: <b>{completadas}</b>\n"
        f"• Canceladas: <b>{canceladas}</b>"
    )


def txt_request_received(service_key: str, dato: str) -> str:
    name = SERVICE_NAMES.get(service_key, service_key.upper())
    return (
        f"{name.split()[0]} <b>BLOQUEO {name.split(' ', 1)[1].upper()}</b>\n\n"
        f"🆔 Dato recibido: <code>{dato}</code>\n\n"
        f"⏳ Procesando solicitud...\n\n"
        f"✅ Solicitud de bloqueo enviada.\n\n"
        f"📌 Resultado ➤ Bloqueo de banca.\n\n"
        f"⏱️ Espera tu confirmación de bloqueo.\n"
        f"Tiempo de espera: mín. 1 h.\n\n"
        f"⚡ Gracias por utilizar <b>{BOT_NAME}</b>."
    )


def txt_group_notification(service_key: str, dato: str, username: str,
                           tg_id: int, price: int,
                           bal_before: int, bal_after: int,
                           fecha: str, hora: str) -> str:
    name = SERVICE_NAMES.get(service_key, service_key.upper())
    user_str = f"@{username}" if username else str(tg_id)
    return (
        f"🔔 <b>NUEVA SOLICITUD DE BLOQUEO</b>\n\n"
        f"{name.split()[0]} <b>SERVICIO: {name.split(' ', 1)[1].upper()}</b>\n\n"
        f"👤 USUARIO: {user_str}\n"
        f"🆔 ID: <code>{tg_id}</code>\n\n"
        f"📋 <b>DATOS DE LA SOLICITUD:</b>\n"
        f"• Dato: <code>{dato}</code>\n"
        f"• Servicio: Bloqueo {name.split(' ', 1)[1]}\n"
        f"• Precio: <b>{price}</b> créditos\n"
        f"• Saldo anterior: <b>{bal_before}</b>\n"
        f"• Saldo actual: <b>{bal_after}</b>\n\n"
        f"📅 FECHA: {fecha}\n"
        f"🕐 HORA: {hora}\n\n"
        f"⏳ <b>ESTADO: PENDIENTE</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Solicitud enviada para revisión."
    )


def txt_processing(pct: int) -> str:
    return f"⏳ Procesando... {pct}%"


def txt_ask_result_data() -> str:
    return (
        f"📋 <b>INGRESAR DATOS DEL RESULTADO</b>\n\n"
        f"Envía los datos del resultado.\n\n"
        f"El cliente está esperando...\n"
        f"Cuando termines de enviar los datos,\n"
        f"el bot los enviará automáticamente al cliente."
    )


def txt_result_template() -> str:
    return (
        "📋 <b>DATOS DEL RESULTADO</b>\n\n"
        "NÚMERO:\n"
        "FECHA:\n"
        "OPERADORA:\n"
        "NOMBRE:\n"
        "DNI:\n"
        "FECHA DE NACIMIENTO:\n"
        "DIRECCIÓN:\n"
        "EQUIPO:\n"
        "IMEI:\n"
        "CORREO:"
    )


def txt_final_report(data: str) -> str:
    return (
        f"📄 <b>REPORTE FINAL</b>\n"
        f"<b>EQUIPO SUSPENDIDO CON NÚMERO</b>\n\n"
        f"{data}\n\n"
        f"BAJADA REALIZADA, COMPRUEBE LLAMANDO AL NÚMERO."
    )


def txt_cancelled_client(service_key: str, dato: str) -> str:
    name = SERVICE_NAMES.get(service_key, service_key.upper())
    return (
        f"❌ <b>SOLICITUD CANCELADA</b>\n\n"
        f"🏦 Servicio: {name}\n"
        f"🆔 Dato: <code>{dato}</code>\n\n"
        f"📌 Estado ➤ CANCELADO\n\n"
        f"⚡ Gracias por utilizar <b>{BOT_NAME}</b>."
    )


def txt_group_cancelled(service_key: str, dato: str) -> str:
    name = SERVICE_NAMES.get(service_key, service_key.upper())
    return (
        f"❌ <b>ESTADO: CANCELADO</b>\n\n"
        f"🏦 Servicio: {name}\n"
        f"🆔 Dato: <code>{dato}</code>"
    )


def txt_maintenance() -> str:
    return (
        f"🔧 <b>{BOT_NAME}</b> se encuentra en mantenimiento.\n\n"
        f"Por favor, vuelve más tarde."
    )


def txt_banned() -> str:
    return "🚫 Has sido suspendido del bot."


def txt_no_credits(needed: int, have: int) -> str:
    return (
        f"❌ Saldo insuficiente.\n\n"
        f"💳 Necesitas: <b>{needed}</b> créditos\n"
        f"💰 Tienes: <b>{have}</b> créditos\n\n"
        f"Usa /buy para recargar."
    )


def txt_not_member() -> str:
    return (
        f"⚠️ Debes ser miembro del grupo para usar el bot.\n\n"
        f"Únete y vuelve a intentarlo."
    )


# --- Comandos del dueño ---

def txt_stats(total_users: int, total_orders: int,
              completed: int, cancelled: int, pending: int) -> str:
    return (
        f"📊 <b>ESTADÍSTICAS</b>\n\n"
        f"👥 Usuarios: <b>{total_users}</b>\n"
        f"📋 Pedidos totales: <b>{total_orders}</b>\n"
        f"✅ Completados: <b>{completed}</b>\n"
        f"❌ Cancelados: <b>{cancelled}</b>\n"
        f"⏳ Pendientes: <b>{pending}</b>"
    )


def txt_user_info(user) -> str:
    uname = f"@{user.username}" if user.username else "Sin usuario"
    status = "🚫 BANEADO" if user.is_banned else "✅ ACTIVO"
    return (
        f"👤 <b>USUARIO</b>\n\n"
        f"🆔 ID: <code>{user.tg_id}</code>\n"
        f"👤 Usuario: {uname}\n"
        f"📛 Nombre: {user.full_name}\n"
        f"💳 Saldo: <b>{user.credits}</b> créditos\n"
        f"🔰 Estado: {status}\n"
        f"📅 Registro: {user.created_at.strftime('%d/%m/%Y %H:%M')}"
    )


def txt_group_completed(service_key: str, dato: str, username: str,
                         tg_id: int, price: int,
                         bal_before: int, bal_after: int,
                         fecha: str, hora: str,
                         result_data: str) -> str:
    name     = SERVICE_NAMES.get(service_key, service_key.upper())
    user_str = f"@{username}" if username else str(tg_id)
    return (
        f"✅ <b>SOLICITUD COMPLETADA</b>\n\n"
        f"{name.split()[0]} <b>SERVICIO: {name.split(' ', 1)[1].upper()}</b>\n\n"
        f"👤 USUARIO: {user_str}\n"
        f"🆔 ID: <code>{tg_id}</code>\n\n"
        f"📋 <b>DATOS DE LA SOLICITUD:</b>\n"
        f"• Dato: <code>{dato}</code>\n"
        f"• Servicio: Bloqueo {name.split(' ', 1)[1]}\n"
        f"• Precio: <b>{price}</b> créditos\n"
        f"• Saldo anterior: <b>{bal_before}</b>\n"
        f"• Saldo actual: <b>{bal_after}</b>\n\n"
        f"📅 FECHA: {fecha}\n"
        f"🕐 HORA: {hora}\n\n"
        f"📄 <b>DATOS DEL RESULTADO:</b>\n"
        f"{result_data}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>ESTADO: COMPLETADO</b>\n"
        f"📨 Reporte enviado al cliente."
    )


# ── Flujo de compra ───────────────────────────────────────────────────────────

def txt_qr_payment(pack_name: str, credits: int, bonus: int, price: int) -> str:
    total = credits + bonus
    bonus_txt = f" + {bonus} GRATIS" if bonus else ""
    return (
        f"🎟️ <b>{pack_name}</b>\n\n"
        f"💳 {credits} créditos{bonus_txt} = <b>{total} créditos</b>\n"
        f"💰 Total a pagar: <b>S/ {price}</b>\n\n"
        f"👇 <b>Escanea el QR y realiza tu pago</b>\n\n"
        f"Una vez pagado, presiona el botón\n"
        f"<b>📤 Enviar comprobante</b> para continuar."
    )


def txt_send_voucher() -> str:
    return (
        f"📸 <b>ENVÍO DE COMPROBANTE</b>\n\n"
        f"Envía tu captura de pago <b>aquí en este chat</b> 👇\n\n"
        f"📲 Solo sube la foto del comprobante\n"
        f"directamente en esta conversación.\n\n"
        f"⏳ Una vez recibida, verificaremos tu pago\n"
        f"y tus créditos serán agregados automáticamente."
    )


def txt_voucher_received() -> str:
    return (
        f"✅ <b>Comprobante recibido.</b>\n\n"
        f"⏳ Estamos verificando tu pago...\n"
        f"Te notificaremos cuando sea aprobado."
    )


def txt_payment_group(username: str, tg_id: int, full_name: str,
                       pack_name: str, credits: int, bonus: int,
                       price: int, fecha: str, hora: str) -> str:
    user_str  = f"@{username}" if username else str(tg_id)
    total     = credits + bonus
    bonus_txt = f" + {bonus} GRATIS" if bonus else ""
    return (
        f"💳 <b>NUEVO COMPROBANTE DE PAGO</b>\n\n"
        f"👤 Usuario: {user_str}\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"📛 Nombre: {full_name or '—'}\n\n"
        f"📦 Paquete: <b>{pack_name}</b>\n"
        f"💳 Créditos: <b>{credits}{bonus_txt} = {total} créditos</b>\n"
        f"💰 Monto: <b>S/ {price}</b>\n\n"
        f"📅 Fecha: {fecha}\n"
        f"🕐 Hora: {hora}\n\n"
        f"⏳ <b>ESTADO: PENDIENTE</b>"
    )


def txt_payment_approved(credits: int, bonus: int, pack_name: str) -> str:
    total     = credits + bonus
    bonus_txt = f" + {bonus} GRATIS" if bonus else ""
    return (
        f"✅ <b>PAGO APROBADO</b>\n\n"
        f"📦 Paquete: <b>{pack_name}</b>\n"
        f"💳 Se agregaron <b>{total}</b> créditos{bonus_txt} a tu cuenta.\n\n"
        f"¡Gracias por tu compra! Ya puedes usar los servicios."
    )


def txt_payment_rejected() -> str:
    return (
        f"❌ <b>PAGO RECHAZADO</b>\n\n"
        f"Tu comprobante no pudo ser verificado.\n\n"
        f"Si crees que es un error, contáctate con el dueño."
    )
