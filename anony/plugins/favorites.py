# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


from pathlib import Path

from pyrogram import filters, types

from anony import anon, app, db, lang, queue, yt
from anony.helpers import Track, buttons, pemoji


def _to_dict(media) -> dict:
    return {
        "id": media.id,
        "title": media.title,
        "url": media.url,
        "duration": media.duration,
        "duration_sec": media.duration_sec,
        "thumbnail": getattr(media, "thumbnail", None),
    }


@app.on_message(filters.command(["fav", "addfav"]) & filters.group & ~app.bl_users)
@lang.language()
async def _fav(_, m: types.Message):
    media = queue.get_current(m.chat.id)
    if not media:
        return await m.reply_text(m.lang["not_playing"])

    added = await db.add_favorite(m.from_user.id, _to_dict(media))
    if not added:
        return await m.reply_text(f'{pemoji.tag("heart")} Already in your favorites!')

    await m.reply_text(
        f'{pemoji.tag("heart")} Saved <b>{media.title}</b> to your favorites! '
        f"Check them anytime with /favs in my DM."
    )


@app.on_message(filters.command(["favs", "favorites"]) & ~app.bl_users)
@lang.language()
async def _favs(_, m: types.Message):
    favs = await db.get_favorites(m.from_user.id)
    if not favs:
        return await m.reply_text(
            f'{pemoji.tag("heart")} You have no favorites yet -- use /fav while '
            f"a song is playing in a group to save it here."
        )

    text = f'{pemoji.tag("heart")} <b>Your Favorites</b>\n\n<blockquote expandable>'
    for i, t in enumerate(favs, start=1):
        text += f"<b>{i}.</b> {t['title']} ({t['duration']})\n"
    text += (
        "</blockquote>\n\nUse <code>/playfav &lt;number&gt;</code> in a group "
        "to queue one, or <code>/unfav &lt;number&gt;</code> to remove one."
    )
    await m.reply_text(text)


@app.on_message(filters.command(["unfav"]) & ~app.bl_users)
@lang.language()
async def _unfav(_, m: types.Message):
    if len(m.command) < 2 or not m.command[1].isdigit():
        return await m.reply_text(
            "Usage: <code>/unfav &lt;number&gt;</code> (see /favs for the numbers)."
        )

    favs = await db.get_favorites(m.from_user.id)
    idx = int(m.command[1]) - 1
    if idx < 0 or idx >= len(favs):
        return await m.reply_text("That number isn't in your favorites list.")

    track = favs[idx]
    await db.remove_favorite(m.from_user.id, track["id"])
    await m.reply_text(f"Removed <b>{track['title']}</b> from your favorites.")


@app.on_message(filters.command(["playfav"]) & filters.group & ~app.bl_users)
@lang.language()
async def _playfav(_, m: types.Message):
    if len(m.command) < 2 or not m.command[1].isdigit():
        return await m.reply_text(
            "Usage: <code>/playfav &lt;number&gt;</code> (see /favs in my DM "
            "for the numbers)."
        )

    favs = await db.get_favorites(m.from_user.id)
    idx = int(m.command[1]) - 1
    if idx < 0 or idx >= len(favs):
        return await m.reply_text("That number isn't in your favorites list.")

    fav = favs[idx]
    track = Track(
        id=fav["id"],
        title=fav["title"],
        url=fav["url"],
        duration=fav["duration"],
        duration_sec=fav["duration_sec"],
        thumbnail=fav.get("thumbnail"),
        message_id=m.id,
        user=m.from_user.mention,
        user_id=m.from_user.id,
    )

    sent = await m.reply_text(f'{pemoji.tag("loading")} {m.lang["play_searching"]}')
    position = queue.add(m.chat.id, track)
    if position != 0 or await db.get_call(m.chat.id):
        return await sent.edit_text(
            m.lang["play_queued"].format(
                position, track.url, track.title, track.duration, m.from_user.mention
            ),
            reply_markup=buttons.play_queued(m.chat.id, track.id, m.lang["play_now"]),
        )

    fname = f"downloads/{track.id}.webm"
    if Path(fname).exists():
        track.file_path = fname
    else:
        await sent.edit_text(f'{pemoji.tag("loading")} {m.lang["play_downloading"]}')
        track.file_path = await yt.download(track.id, video=False)

    await anon.play_media(chat_id=m.chat.id, message=sent, media=track)
