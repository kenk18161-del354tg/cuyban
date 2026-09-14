"""
Script de migración: agrega columnas nuevas si no existen.
Se ejecuta automáticamente al arrancar el bot.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# Columnas nuevas en tabla orders
ORDER_COLUMNS = [
    ('group_chat_id',    'BIGINT'),
    ('original_msg_id',  'BIGINT'),
    ('ask_msg_id',       'BIGINT'),
]


async def run_migrations(conn: AsyncConnection) -> None:
    # Tabla orders — columnas nuevas
    for col_name, col_type in ORDER_COLUMNS:
        try:
            await conn.execute(text(
                f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            ))
            logger.info(f"Migración orders: columna '{col_name}' verificada.")
        except Exception as e:
            logger.warning(f"Migración orders '{col_name}': {e}")

    # Tabla payments — crearla si no existe
    try:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id            SERIAL PRIMARY KEY,
                user_tg_id    BIGINT NOT NULL,
                username      VARCHAR(64),
                full_name     VARCHAR(128),
                pack          VARCHAR(16) NOT NULL,
                credits       INTEGER NOT NULL,
                bonus         INTEGER NOT NULL DEFAULT 0,
                price_soles   INTEGER NOT NULL,
                status        VARCHAR(16) NOT NULL DEFAULT 'PENDIENTE',
                photo_file_id VARCHAR(256),
                group_msg_id  BIGINT,
                qr_msg_id     BIGINT,
                instructions_msg_id BIGINT,
                confirm_msg_id BIGINT,
                created_at    TIMESTAMP DEFAULT NOW()
            )
        """))
        logger.info("Migración: tabla 'payments' verificada.")
    except Exception as e:
        logger.warning(f"Migración tabla payments: {e}")

    # Columnas nuevas en payments (por si la tabla ya existía)
    PAYMENTS_COLUMNS = [
        ('qr_msg_id',           'BIGINT'),
        ('instructions_msg_id', 'BIGINT'),
        ('confirm_msg_id',      'BIGINT'),
    ]
    for col_name, col_type in PAYMENTS_COLUMNS:
        try:
            await conn.execute(text(
                f"ALTER TABLE payments ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            ))
            logger.info(f"Migración payments: columna '{col_name}' verificada.")
        except Exception as e:
            logger.warning(f"Migración payments '{col_name}': {e}")

    await conn.commit()
