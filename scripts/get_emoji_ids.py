# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
"""
One-off helper to pull custom (premium) emoji IDs into emoji_pack.json.

WHY A SEPARATE SCRIPT:
Custom emoji document IDs can only be *read* from a message that already
contains them -- and only a Telegram Premium account can *compose* a message
using custom emoji in the first place. So this script logs in with your
Premium account's session string, reads one message you send, and extracts
the emoji IDs for you. It has nothing to do with the bot process itself and
is not imported anywhere in anony/ -- run it once, locally or on your VPS,
whenever you want to (re)build emoji_pack.json.

SETUP:
    1. pip install pyrogram tgcrypto
    2. Set these two env vars (same values as your bot's API_ID / API_HASH):
           export API_ID=...
           export API_HASH=...
    3. Set PREMIUM_SESSION to your Premium account's Pyrogram session string.
       (Parth: this is the session string you already have -- do NOT commit
       it anywhere, paste it only into this env var.)
           export PREMIUM_SESSION="..."

USAGE:
    1. Run this script: python scripts/get_emoji_ids.py
    2. It will print a template message and wait.
    3. Open Telegram (with the SAME Premium account), open "Saved Messages",
       and send ONE message that looks like the template it printed --
       one "name emoji" pair per line, using your own custom emoji picks
       from your Premium emoji keyboard in place of each placeholder.
       Keep the names exactly as printed (e.g. "play", "pause", ...).
    4. The script detects the new message, extracts each line's custom
       emoji document ID, and writes anony/../emoji_pack.json for you.
    5. Restart the bot -- pemoji.tag() will now use your real emoji.

You can re-run this any time to update/replace emoji_pack.json.
"""

import asyncio
import json
import os
import sys

from pyrogram import Client, enums

TEMPLATE_NAMES = [
    "play", "pause", "stop", "skip", "replay", "queue", "music", "mic",
    "clock", "user", "fire", "star", "check", "cross", "heart", "vote",
    "lyrics", "sparkle", "link",
]

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "emoji_pack.json")


async def main():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session = os.getenv("PREMIUM_SESSION")

    if not (api_id and api_hash and session):
        sys.exit(
            "Missing API_ID / API_HASH / PREMIUM_SESSION env vars. "
            "See the docstring at the top of this file."
        )

    app = Client("emoji_fetch", api_id=int(api_id), api_hash=api_hash, session_string=session, in_memory=True)

    async with app:
        me = await app.get_me()
        print(f"Logged in as {me.first_name} (premium: {me.is_premium}).")
        if not me.is_premium:
            print(
                "WARNING: this account isn't flagged as Premium -- you won't "
                "be able to pick custom emoji from the keyboard to send."
            )

        print("\nSend the following as ONE message to your own Saved Messages,\n"
              "replacing each emoji with your chosen custom emoji (keep the words):\n")
        for name in TEMPLATE_NAMES:
            print(f"  {name} <pick a custom emoji here>")

        print("\nWaiting for your message in Saved Messages (Ctrl+C to cancel)...")

        last_id = 0
        async for msg in app.get_chat_history("me", limit=1):
            last_id = msg.id

        found: dict[str, str] = {}
        while True:
            await asyncio.sleep(2)
            async for msg in app.get_chat_history("me", limit=5):
                if msg.id <= last_id:
                    break
                last_id = max(last_id, msg.id)
                if not msg.text or not msg.entities:
                    continue

                lines = msg.text.split("\n")
                for entity in msg.entities:
                    if entity.type != enums.MessageEntityType.CUSTOM_EMOJI:
                        continue
                    offset, length = entity.offset, entity.length
                    line_start = msg.text.rfind("\n", 0, offset) + 1
                    line_end = msg.text.find("\n", offset)
                    line_end = line_end if line_end != -1 else len(msg.text)
                    line = msg.text[line_start:line_end]
                    name = line.strip().split()[0].lower() if line.strip() else None
                    if name in TEMPLATE_NAMES:
                        found[name] = str(entity.custom_emoji_id)

                if found:
                    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                        json.dump(found, f, indent=2, ensure_ascii=False)
                    print(f"\nSaved {len(found)} emoji ID(s) to {OUTPUT_PATH}:")
                    for k, v in found.items():
                        print(f"  {k}: {v}")
                    missing = set(TEMPLATE_NAMES) - found.keys()
                    if missing:
                        print(f"\nStill missing: {', '.join(sorted(missing))}")
                        print("Send another message with just those names + emoji "
                              "and re-run to top up (or edit emoji_pack.json by hand).")
                    return


if __name__ == "__main__":
    asyncio.run(main())
