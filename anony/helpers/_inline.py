# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


from pyrogram import enums, types

from anony import app, config, lang
from anony.core.lang import lang_codes
from ._emoji import pemoji


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: tuple = None,
        remove: bool = False,
        lyrics: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(self._progress_row(chat_id, *timer))

        if not remove:
            keyboard.append(
                [
                    self._styled("▶️", "play", enums.ButtonStyle.SUCCESS, f"controls resume {chat_id}"),
                    self._styled("⏸", "pause", enums.ButtonStyle.PRIMARY, f"controls pause {chat_id}"),
                    self._styled("🔁", "replay", enums.ButtonStyle.PRIMARY, f"controls replay {chat_id}"),
                    self._styled("⏭", "skip", enums.ButtonStyle.PRIMARY, f"controls skip {chat_id}"),
                    self._styled("⏹", "stop", enums.ButtonStyle.DANGER, f"controls stop {chat_id}"),
                ]
            )
            if lyrics:
                keyboard.append(
                    [self._styled("Lyrics", "lyrics", enums.ButtonStyle.PRIMARY, f"lyrics {chat_id}")]
                )
        return self.ikm(keyboard)

    def _progress_row(
        self, chat_id: int, played: int, duration: int, length: int = 20
    ) -> list:
        """
        Single continuous line-style progress bar (like a media seek bar),
        built entirely from line-drawing / plain text characters -- no
        emoji, no button colour. Renders identically on every client since
        it doesn't depend on colour-emoji font support at all.
        """
        import time as _time

        cb = f"controls status {chat_id}"
        pos = min(int((played / duration) * length), length - 1) if duration else 0
        bar = "━" * pos + "●" + "─" * (length - pos - 1)

        elapsed = self.ikb(text=_time.strftime("%M:%S", _time.gmtime(played)), callback_data=cb)
        line = self.ikb(text=bar, callback_data=cb)
        remaining = self.ikb(
            text=f"-{_time.strftime('%M:%S', _time.gmtime(max(duration - played, 0)))}",
            callback_data=cb,
        )
        return [elapsed, line, remaining]

    def _styled(
        self, text: str, emoji_key: str, style: "enums.ButtonStyle", callback_data: str
    ) -> types.InlineKeyboardButton:
        """Build a coloured button (Bot API 9.4+), optionally with a premium
        emoji icon if one is configured in emoji_pack.json for `emoji_key`.
        Falls back gracefully to a plain-coloured button with no icon."""
        return self.ikb(
            text=text,
            callback_data=callback_data,
            style=style,
            icon_custom_emoji_id=pemoji.ids.get(emoji_key),
        )

    def vskip_markup(
        self, chat_id: int, votes: int, needed: int
    ) -> types.InlineKeyboardMarkup:
        style = enums.ButtonStyle.DANGER if votes >= needed else enums.ButtonStyle.PRIMARY
        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"🗳 Vote to Skip ({votes}/{needed})",
                        callback_data=f"vskip {chat_id}",
                        style=style,
                        icon_custom_emoji_id=pemoji.ids.get("grow"),
                    )
                ]
            ]
        )

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text=_lang["back"], callback_data="help back"),
                    self.ikb(text=_lang["close"], callback_data="help close"),
                ]
            ]
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            buttons = [
                self.ikb(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
                for i, cb in enumerate(cbs)
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}"
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        on_style, off_style = enums.ButtonStyle.SUCCESS, enums.ButtonStyle.DANGER
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text="✅ On" if admin_only else "❌ Off",
                        callback_data="settings play",
                        style=on_style if admin_only else off_style,
                    ),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text="✅ On" if cmd_delete else "❌ Off",
                        callback_data="settings delete",
                        style=on_style if cmd_delete else off_style,
                    ),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(
                        text=lang_codes[language],
                        callback_data="language",
                        style=enums.ButtonStyle.PRIMARY,
                        icon_custom_emoji_id=pemoji.ids.get("flag"),
                    ),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=enums.ButtonStyle.SUCCESS,
                    icon_custom_emoji_id=pemoji.ids.get("heart"),
                )
            ],
            [self.ikb(text=lang["help"], callback_data="help")],
            [
                self.ikb(
                    text=lang["support"],
                    url=config.SUPPORT_CHAT,
                    style=enums.ButtonStyle.PRIMARY,
                    icon_custom_emoji_id=pemoji.ids.get("teddy"),
                ),
                self.ikb(
                    text=lang["channel"],
                    url=config.SUPPORT_CHANNEL,
                    style=enums.ButtonStyle.PRIMARY,
                    icon_custom_emoji_id=pemoji.ids.get("music"),
                ),
            ],
        ]
        if not private:
            rows += [
                [
                    self.ikb(
                        text=lang["language"],
                        callback_data="language",
                        icon_custom_emoji_id=pemoji.ids.get("flag"),
                    )
                ]
            ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
