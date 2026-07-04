# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


from pyrogram import filters, types

from anony import app, db, lang
from anony.helpers import pemoji

MEDALS = ["🥇", "🥈", "🥉"]


@app.on_message(filters.command(["topsongs"]) & filters.group & ~app.bl_users)
@lang.language()
async def _top_songs(_, m: types.Message):
    top = await db.top_songs(m.chat.id)
    if not top:
        return await m.reply_text(
            f'{pemoji.tag("medal")} No plays recorded in this chat yet -- '
            f"play something first!"
        )

    text = f'{pemoji.tag("medal")} <b>Top Songs in {m.chat.title}</b>\n\n'
    for i, doc in enumerate(top):
        rank = MEDALS[i] if i < 3 else f"{i + 1}."
        text += f"{rank} {doc['title']} — <i>{doc['count']} plays</i>\n"
    await m.reply_text(text)


@app.on_message(filters.command(["topusers"]) & filters.group & ~app.bl_users)
@lang.language()
async def _top_users(_, m: types.Message):
    top = await db.top_users(m.chat.id)
    if not top:
        return await m.reply_text(
            f'{pemoji.tag("medal")} No requests recorded in this chat yet -- '
            f"play something first!"
        )

    text = f'{pemoji.tag("medal")} <b>Top Requesters in {m.chat.title}</b>\n\n'
    for i, doc in enumerate(top):
        rank = MEDALS[i] if i < 3 else f"{i + 1}."
        text += f"{rank} {doc['user_name']} — <i>{doc['count']} requests</i>\n"
    await m.reply_text(text)
