"""
Script de migración: agrega columnas nuevas a la tabla orders si no existen.
Se ejecuta automáticamente al arrancar el bot.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = logging.getLogger(__name__)

# Columnas a agregar: (nombre, definición SQL)
NEW_COLUMNS = [
    ('group_chat_id',    'BIGINT'),
    ('original_msg_id',  'BIGINT'),
    ('ask_msg_id',       'BIGINT'),
]


async def run_migrations(conn: AsyncConnection) -> None:
    for col_name, col_type in NEW_COLUMNS:
        try:
            await conn.execute(text(
                f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            ))
            logger.info(f"Migración: columna '{col_name}' verificada/agregada.")
        except Exception as e:
            logger.warning(f"Migración columna '{col_name}': {e}")
    await conn.commit()
