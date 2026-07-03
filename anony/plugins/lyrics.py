# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


import aiohttp

from pyrogram import filters, types

from anony import app, config, db, lang, queue
from anony.helpers import Track, pemoji

LRCLIB_SEARCH = "https://lrclib.net/api/search"


async def fetch_lyrics(title: str) -> tuple[str, str] | None:
    """Look up plain lyrics for a title via lrclib.net (free, no API key)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                LRCLIB_SEARCH, params={"q": title}, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return None
                results = await resp.json()
    except Exception:
        return None

    for item in results or []:
        text = item.get("plainLyrics")
        if text:
            name = item.get("trackName") or title
            artist = item.get("artistName") or ""
            return f"{name} - {artist}".strip(" -"), text
    return None


def build_reply(header_title: str, lyrics: str, lang_dict: dict) -> str:
    text = f'{pemoji.tag("lyrics")} <b>Lyrics — {header_title}</b>\n\n'
    body = lyrics.strip()
    # Keep messages within Telegram's caption/text limits; wrap the rest in
    # an expandable blockquote like the existing playlist/queue displays.
    if len(body) > 3500:
        body = body[:3500] + "\n…"
    text += f"<blockquote expandable>{body}</blockquote>"
    return text


@app.on_message(filters.command(["lyrics", "lyric"]) & filters.group & ~app.bl_users)
@lang.language()
async def _lyrics_cmd(_, m: types.Message):
    if not config.LYRICS_ENABLED:
        return await m.reply_text("Lyrics lookup is disabled on this bot.")

    if len(m.command) >= 2:
        query = " ".join(m.command[1:])
    else:
        media = queue.get_current(m.chat.id)
        if not media:
            return await m.reply_text(
                "Give me a song name, e.g. <code>/lyrics Blinding Lights</code>, "
                "or use it while something is playing."
            )
        query = media.title

    sent = await m.reply_text(f'{pemoji.tag("lyrics")} Searching lyrics for "{query}"...')
    result = await fetch_lyrics(query)
    if not result:
        return await sent.edit_text(
            f"Couldn't find lyrics for <b>{query}</b>. Try a more specific title."
        )

    title, lyrics = result
    await sent.edit_text(build_reply(title, lyrics, m.lang))


@app.on_callback_query(filters.regex(r"^lyrics \d+") & ~app.bl_users)
@lang.language()
async def _lyrics_button(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    media = queue.get_current(chat_id)
    if not media:
        return await query.answer("Nothing is playing right now.", show_alert=True)

    await query.answer("Fetching lyrics...")
    result = await fetch_lyrics(media.title)
    if not result:
        return await query.message.reply_text(
            f"Couldn't find lyrics for <b>{media.title}</b>.", quote=False
        )

    title, lyrics = result
    await query.message.reply_text(
        build_reply(title, lyrics, query.lang), quote=False
    )
