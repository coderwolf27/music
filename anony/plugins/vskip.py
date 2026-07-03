# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


import math
from collections import defaultdict

from pyrogram import filters, types

from anony import anon, app, config, db, lang, queue
from anony.helpers import buttons, pemoji

# {chat_id: {track_id: {user_id, ...}}} -- kept in memory, resets naturally
# whenever the track changes since it's keyed by the current track's id.
_votes: dict[int, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))


async def _needed_votes(chat_id: int) -> int:
    try:
        count = await app.get_chat_members_count(chat_id)
    except Exception:
        count = config.VOTE_SKIP_MIN * 2
    return max(config.VOTE_SKIP_MIN, math.ceil(count * config.VOTE_SKIP_RATIO))


async def _register_vote(chat_id: int, user_id: int) -> tuple[int, int, bool]:
    """Returns (current_votes, needed_votes, already_voted)."""
    media = queue.get_current(chat_id)
    if not media:
        return 0, 0, False

    voters = _votes[chat_id][media.id]
    already = user_id in voters
    if not already:
        voters.add(user_id)

    needed = await _needed_votes(chat_id)
    return len(voters), needed, already


@app.on_message(filters.command(["vskip", "voteskip"]) & filters.group & ~app.bl_users)
@lang.language()
async def _vskip_cmd(_, m: types.Message):
    if not config.VOTE_SKIP_ENABLED:
        return await m.reply_text("Vote-skip is disabled — use /skip instead.")

    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    votes, needed, already = await _register_vote(m.chat.id, m.from_user.id)
    if already:
        return await m.reply_text(
            f'{pemoji.tag("vote")} You already voted to skip this track '
            f"({votes}/{needed})."
        )

    if votes >= needed:
        _votes[m.chat.id].pop(queue.get_current(m.chat.id).id, None)
        await anon.play_next(m.chat.id)
        return await m.reply_text(
            f'{pemoji.tag("skip")} Vote threshold reached — skipping!'
        )

    await m.reply_text(
        f'{pemoji.tag("vote")} <b>{m.from_user.mention}</b> voted to skip.',
        reply_markup=buttons.vskip_markup(m.chat.id, votes, needed),
    )


@app.on_callback_query(filters.regex(r"^vskip \d+") & ~app.bl_users)
@lang.language()
async def _vskip_button(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    if not await db.get_call(chat_id):
        return await query.answer(query.lang["not_playing"], show_alert=True)

    votes, needed, already = await _register_vote(chat_id, query.from_user.id)
    if already:
        return await query.answer(
            f"You've already voted ({votes}/{needed}).", show_alert=True
        )

    if votes >= needed:
        _votes[chat_id].pop(queue.get_current(chat_id).id, None)
        await query.answer("Vote threshold reached — skipping!", show_alert=True)
        await anon.play_next(chat_id)
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    await query.answer(f"Vote counted ({votes}/{needed}).")
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.vskip_markup(chat_id, votes, needed)
        )
    except Exception:
        pass
