import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import BOT_TOKEN
from database.engine import init_db
from handlers import buy, callbacks, owner, profile, services, start

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN no configurado. Agrégalo en Railway Variables.")

    # Inicializar base de datos
    await init_db()
    logger.info("Base de datos inicializada.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Registrar routers en orden de prioridad
    dp.include_router(owner.router)      # comandos del dueño primero
    dp.include_router(callbacks.router)  # callbacks inline + recepción resultado
    dp.include_router(start.router)      # /start y /cmds
    dp.include_router(profile.router)    # /me
    dp.include_router(buy.router)        # /buy
    dp.include_router(services.router)   # /bcp /agr /ibk /cjaq /bbva /sbk /yape /bloqueo

    logger.info("Bot arrancando con polling...")
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_member"],
    )


if __name__ == '__main__':
    asyncio.run(main())
