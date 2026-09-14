from aiogram import Bot
from aiogram.types import Message

from config.settings import (
    CHANNEL_ID, GROUP_ID, MAINTENANCE,
    OWNER_ID, REQUIRE_GROUP_MEMBER,
)
from database.models import User
from texts.messages import txt_banned, txt_maintenance, txt_not_member


async def check_maintenance(message: Message) -> bool:
    """True si el bot está en mantenimiento (y no es el dueño)."""
    if MAINTENANCE and message.from_user.id != OWNER_ID:
        await message.answer(txt_maintenance())
        return True
    return False


async def check_banned(message: Message, user: User) -> bool:
    """True si el usuario está baneado."""
    if user.is_banned:
        await message.answer(txt_banned())
        return True
    return False


async def check_membership(message: Message, bot: Bot) -> bool:
    """True si NO es miembro (y se requiere membresía)."""
    if not REQUIRE_GROUP_MEMBER:
        return False
    uid = message.from_user.id
    if uid == OWNER_ID:
        return False
    chat_id = CHANNEL_ID or GROUP_ID
    if not chat_id:
        return False
    try:
        member = await bot.get_chat_member(chat_id, uid)
        if member.status in ('left', 'kicked', 'banned'):
            await message.answer(txt_not_member())
            return True
    except Exception:
        pass
    return False
