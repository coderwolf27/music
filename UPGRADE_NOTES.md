# EarBudBot Upgrade Pack

Changes on top of upstream `AnonymousX1025/AnonXMusic`. Everything here is additive —
no existing commands, DB schema, or config were removed, so it's a drop-in update.
This file gets updated alongside every new feature, so it should stay a reliable
map of what's changed and why.

## 1. Real coloured buttons (Bot API 9.4)
`anony/helpers/_inline.py` → `Inline.controls()`, `vskip_markup()`, `settings_markup()`, `start_key()`

Telegram added actual button colours in **Bot API 9.4** (Feb 2026): a `style` field
(`primary` = blue, `danger` = red, `success` = green) plus an `icon_custom_emoji_id`
field for a small emoji icon before the button text. `kurigram` (the Pyrogram fork
this project uses) already supports both natively — no raw MTProto calls needed.

Applied:
- Now Playing controls: ▶️ resume = green, ⏸/🔁/⏭ = blue, ⏹ stop = red.
- `/vskip` button turns red once the vote threshold is reached.
- `/settings` toggles: green "On" / red "Off" (this also fixed a pre-existing bug
  where the toggle button literally displayed the Python text `True`/`False`).
- `/start`'s "Add me to a group" button is green; Support/Channel buttons are blue.

**Icon caveat:** `icon_custom_emoji_id` on buttons only renders if the *bot's
owner account* (the one that created the bot via @BotFather) has an active
Telegram Premium subscription, or the bot purchased extra usernames via
Fragment. This is separate from your assistant/session account's Premium
status. Icons are populated from `emoji_pack.json` (see #3) — if a key isn't
in there, the button just renders with colour and no icon, nothing breaks.

## 2. Live progress bar
`anony/helpers/_inline.py` → `Inline._progress_row()`, used in `anony/plugins/misc.py`.

Went through a few iterations based on feedback:
- v1: coloured block-emoji bar (🟪🟪🔘⬜⬜) — looked flat/monochrome on some
  clients (Desktop/Web render emoji inside button text with a system font,
  not Telegram's colour emoji set).
- v2: real coloured button segments (native Telegram colour, no font issue).
- v3 (current): a single continuous line using plain line-drawing characters
  only (━━●─────────────────), no emoji, no button colour — renders
  identically everywhere. Flanked by elapsed/remaining time as two small
  plain buttons either side.

`/queue`'s "now playing" line still uses `Utilities.progress_bar()` (the
block-emoji version) since that's regular message text, not button text —
the font-rendering issue only affects inline button labels.

## 3. Custom premium emoji branding
`anony/helpers/_emoji.py` — `PremiumEmoji` class, exposed as `pemoji` from `anony.helpers`.

Used two ways:
- In message text/captions via Pyrogram's `<emoji id="...">` HTML tag —
  e.g. `pemoji.tag("music")` brands the "Now Streaming"/"Queue" headers,
  `/start`, `/stats`.
- Directly on buttons via `icon_custom_emoji_id` (see #1) — subject to the
  Premium-owner/Fragment caveat above.

If no ID is configured for a given key, both paths fall back to a plain
unicode emoji — nothing breaks either way.

Current pack (`emoji_pack.json`): medal, flag, flower, grow, logo, heart,
shining_heart, music, teddy. Used across the `/start` welcome message, Now
Playing/Queue headers, `/stats`, language buttons (flag), the green "Add me"
button (heart), and the blue Support/Channel buttons (teddy/music).

**Setup:** run `scripts/get_emoji_ids.py` once with a Premium account's
session string (instructions in the script's docstring), or just hand-edit
`emoji_pack.json` directly if you already have IDs from somewhere else.

## 4. /lyrics (new)
`anony/plugins/lyrics.py`

- `/lyrics <song name>` or just `/lyrics` while something is playing.
- A "Lyrics" button is added under the controls row whenever a
  YouTube-searched track (not a replied-file/M3U8 stream) starts playing.
- Pulls plain lyrics from lrclib.net — free, keyless API. If nothing is
  found it says so instead of guessing.
- Toggle with LYRICS_ENABLED=False in your .env.

## 5. /vskip - vote to skip (new)
`anony/plugins/vskip.py`

Lets regular members (not just admins/auth users) start a vote to skip the
current track — useful for open groups where /skip is admin-only.
- Needed votes = max(VOTE_SKIP_MIN, ceil(group_member_count * VOTE_SKIP_RATIO)).
- Votes are tracked per currently-playing track ID, so they auto-reset on
  track change — no manual cleanup needed.
- Config: VOTE_SKIP_ENABLED (default True), VOTE_SKIP_RATIO (default 0.5),
  VOTE_SKIP_MIN (default 2).

## 6. Leaderboards & Favorites (new)
`anony/plugins/leaderboard.py`, `anony/plugins/favorites.py`, `anony/core/mongo.py`,
`anony/helpers/_dataclass.py`

- Every genuine track start (guarded so seeking doesn't double-count) logs a
  play to two new Mongo collections: per-chat song play counts, and per-chat
  per-user request counts.
- /topsongs, /topusers — per-chat leaderboards, medal emoji for the top 3.
  Data only accumulates from when this shipped — no historical backfill.
- /fav — save the currently-playing track to a personal favorites list
  (works from any group; needs something actually playing).
- /favs — view your favorites (DM or group), capped at 50.
- /playfav <n> — requeue a favorite into the current group, reusing the
  same queue/download path as /play.
- /unfav <n> — remove one.
- Added user_id to the Track/Media dataclasses (alongside the existing
  mention-string user field) so leaderboards aggregate by stable numeric ID
  rather than display name.

## 7. /stats fix
Was restricted to filters.group, but /help (where people discover the
/stats command) only works in private chats — so tapping Help then Stats
then trying /stats right there silently did nothing. /stats only reports
bot-wide data (nothing chat-specific), so it's now allowed in private chats too.

## 8. Audio stutter mitigation
Reported symptom: audio randomly stutters 2-3s then fast-forwards to catch up,
worse with many (6+) concurrent group streams on a 2 vCPU VPS.
- Bumped py-tgcalls 2.2.11 -> 2.3.3 (verified API-compatible; picks up
  upstream ntgcalls native-backend stability work).
- The background "next track" prefetch download thread now lowers its own
  scheduling niceness on Linux so it can't starve the ffmpeg process actively
  feeding a live voice call.
- Added MAX_CONCURRENT_CALLS (default 0 = unlimited) — an admission-control
  cap so once you're at capacity, new /play requests get a polite "try again
  shortly" message instead of everyone's stream quality degrading together
  as load grows.
- Added AUDIO_QUALITY (LOW/MEDIUM/HIGH/STUDIO, default HIGH) — lower
  settings use less CPU per stream, useful on limited vCPUs.
- Honest caveat: with 6+ real-time streams on only 2 vCPUs, some contention
  is close to structurally expected — these changes reduce it, they don't
  guarantee it's fully gone. The deepest fix at that concurrency level is
  more CPU headroom (bigger VPS, or splitting groups across multiple
  smaller instances).

## 9. Support/Channel links, branding, misc cleanup
`config.py`, `anony/helpers/_inline.py` -> `start_key()`, `anony/core/userbot.py`

- SUPPORT_CHAT -> t.me/hankie, SUPPORT_CHANNEL -> t.me/vidmage.
- Both buttons are blue (PRIMARY) with teddy/music icons.
- Removed the "source" (GitHub repo link) button from /start.
- The assistant account's automatic channel-join on startup
  (anony/core/userbot.py) now joins vidmage instead of the original
  upstream dev's channel — a pre-existing, undocumented behaviour in the
  base template worth checking for in any repo you fork.
- Fixed a few stale github.com/.../blob/master/... links in README.md
  (this repo's default branch is main).

## New config keys
All optional, sane defaults, add to .env only if you want to change them:
```
VOTE_SKIP_ENABLED=True
VOTE_SKIP_RATIO=0.5
VOTE_SKIP_MIN=2
LYRICS_ENABLED=True
MAX_CONCURRENT_CALLS=0
AUDIO_QUALITY=HIGH
```

## Not done / deliberately scoped out
- Haven't touched the 13 locale JSON files' existing translated strings (too
  risky to hand-edit 13 languages safely in one pass) — new headers/labels
  are injected in code instead, so translations you already have stay intact.
- /lyrics, /vskip, /topsongs, /topusers, /fav, /favs, /playfav, /unfav
  aren't wired into the /help menu's button grid yet, since that grid's
  layout is shared across all locale files too. Easy follow-up if wanted.

## Files touched (cumulative)
```
 anony/core/calls.py         (Now Playing header, lyrics button, audio quality, play logging)
 anony/core/mongo.py         (leaderboard + favorites collections/methods)
 anony/core/userbot.py       (auto-join channel redirect)
 anony/core/youtube.py       (prefetch thread niceness)
 anony/helpers/__init__.py   (registers pemoji)
 anony/helpers/_dataclass.py (user_id field on Track/Media)
 anony/helpers/_emoji.py     (NEW - premium emoji helper)
 anony/helpers/_inline.py    (coloured buttons, progress row, vskip/lyrics/leaderboard wiring)
 anony/helpers/_utilities.py (progress_bar helper, used by /queue)
 anony/plugins/favorites.py  (NEW - /fav, /favs, /unfav, /playfav)
 anony/plugins/leaderboard.py(NEW - /topsongs, /topusers)
 anony/plugins/lyrics.py     (NEW - /lyrics command)
 anony/plugins/misc.py       (progress bar uses new helper)
 anony/plugins/play.py       (user_id tracking, concurrency cap check)
 anony/plugins/queue.py      (queue header + live bar)
 anony/plugins/stats.py      (private-chat fix, medal icon)
 anony/plugins/start.py      (welcome message emoji, help header)
 anony/plugins/vskip.py      (NEW - /vskip command)
 config.py                   (new optional env vars, link defaults)
 pyproject.toml              (kurigram/py-tgcalls version bumps)
 emoji_pack.json              (NEW - custom emoji ID registry)
 scripts/get_emoji_ids.py    (NEW - standalone, run separately)
```
