# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


import json
from pathlib import Path

# Fallback unicode used whenever a custom emoji id hasn't been configured
# (or when the viewing client doesn't support custom emoji, e.g. some
# desktop/web clients on very old versions). Keeps the bot fully usable
# even before you've set up your premium emoji pack.
DEFAULTS = {
    "play": "▶️",
    "pause": "⏸",
    "stop": "⏹",
    "skip": "⏭",
    "replay": "🔁",
    "queue": "📜",
    "music": "🎧",
    "mic": "🎤",
    "clock": "⏱",
    "user": "👤",
    "fire": "🔥",
    "star": "⭐",
    "check": "✅",
    "cross": "❌",
    "heart": "💜",
    "vote": "🗳",
    "lyrics": "📝",
    "sparkle": "✨",
    "link": "🔗",
    "medal": "🏅",
    "flag": "🎌",
    "flower": "🌸",
    "grow": "🌱",
    "logo": "🎧",
    "shining_heart": "💖",
    "teddy": "🧸",
    "verified": "☑️",
    "ghost": "👻",
    "lightning": "⚡",
    "no": "🚫",
    "two_hearts": "💕",
    "loading": "⏳",
    "shine": "✨",
    "hi": "👋",
    "music_alt": "🎵",
    "music_alt2": "🎶",
    "new": "🆕",
    "day_night": "🌗",
    "hearts": "💞",
    "help_back": "◀️",
    "language": "🌐",
    "stats": "📊",
    "help_play": "▶️",
    "ping": "🏓",
    "admins": "🛡",
    "auth": "🔑",
    "blacklist": "🚫",
    "help_queue": "📜",
}


class PremiumEmoji:
    """
    Thin wrapper around Telegram custom (premium) emoji.

    Custom emoji can be embedded in message TEXT/CAPTIONS (via the
    `<emoji id="...">` HTML tag that Pyrogram's HTML parser understands) via
    `.tag()`, and -- since Bot API 9.4 -- directly on inline buttons via the
    `icon_custom_emoji_id` field (see helpers/_inline.py's `_styled()`); use
    `.ids.get(name)` for that. Buttons additionally get a `style` colour
    (primary/danger/success), which is a separate Bot API 9.4 field.

    IDs are loaded from `emoji_pack.json` in the project root. Populate that
    file by running `scripts/get_emoji_ids.py` with a Premium account's
    session string (see that script's docstring for instructions), or just
    hand-edit it with IDs Telegram gives you directly.
    """

    def __init__(self, path: str = "emoji_pack.json"):
        self.path = Path(path)
        self.ids: dict[str, str] = {}
        self.reload()

    def reload(self) -> None:
        if self.path.exists():
            try:
                self.ids = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.ids = {}

    def tag(self, name: str, fallback: str = None) -> str:
        """Return an HTML-ready emoji tag for use inside .format()'d strings."""
        char = fallback or DEFAULTS.get(name, "•")
        emoji_id = self.ids.get(name)
        if emoji_id:
            return f'<emoji id="{emoji_id}">{char}</emoji>'
        return char

    def raw(self, name: str) -> str:
        """Plain unicode fallback only -- safe for button labels."""
        return DEFAULTS.get(name, "•")


# Module-level singleton -- imported directly by _inline.py (and re-exported
# from helpers/__init__.py) to avoid a circular import at package init time.
pemoji = PremiumEmoji()
