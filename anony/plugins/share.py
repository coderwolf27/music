# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


from pyrogram import filters, types

from anony import app, logger, queue, thumb
from anony.helpers import Track, pemoji


@app.on_callback_query(filters.regex(r"^share -?\d+") & ~app.bl_users)
async def _share_card(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    media = queue.get_current(chat_id)

    if not media or not isinstance(media, Track):
        return await query.answer(
            "Nothing shareable playing right now.", show_alert=True
        )

    await query.answer("Generating your share card...")

    try:
        image = await thumb.generate_share_card(
            media, app.name, app.username, elapsed=media.time
        )

        caption = (
            f'{pemoji.tag("logo")} <b>{media.title}</b>\n'
            f'{pemoji.tag("music")} Streaming now on <b>{app.name}</b> {pemoji.tag("shining_heart")}\n\n'
            f"Tap and hold to save, then share it to your story! 📤"
        )
        await query.message.reply_photo(
            photo=image,
            caption=caption,
            reply_markup=types.InlineKeyboardMarkup(
                [
                    [
                        types.InlineKeyboardButton(
                            text=f"🎧 Add {app.name} to your group",
                            url=f"https://t.me/{app.username}?startgroup=true",
                        )
                    ]
                ]
            ),
            quote=False,
        )
    except Exception as ex:
        logger.warning("Share card failed: %s", ex)
        try:
            await query.message.reply_text(
                "Couldn't generate a share card right now -- try again in a bit.",
                quote=False,
            )
        except Exception:
            pass
