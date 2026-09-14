from aiogram.types import InlineKeyboardMarkup, Message

from config.media import MAIN_IMAGE


async def send_with_image(message: Message, text: str,
                           reply_markup: InlineKeyboardMarkup | None = None) -> Message:
    """Envía el mensaje con la imagen principal si está configurada."""
    if MAIN_IMAGE:
        try:
            return await message.answer_photo(
                photo=MAIN_IMAGE,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='HTML',
            )
        except Exception:
            pass
    # Fallback sin imagen
    return await message.answer(text, reply_markup=reply_markup, parse_mode='HTML')
