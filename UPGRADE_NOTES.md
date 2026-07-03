# AnonXMusic Upgrade Pack

Changes on top of upstream `AnonymousX1025/AnonXMusic`. Everything here is additive —
no existing commands, DB schema, or config were removed, so it's a drop-in update.

## 1. Colour-coded control buttons
`anony/helpers/_inline.py` → `Inline.controls()`

Telegram's Bot API has **no way to set actual colours on inline buttons** — that's
entirely up to the user's client theme. What we can do (and now do) is prefix each
button with a coloured-circle emoji so the row reads visually at a glance:

```
🟢 ▶️   🟠 ⏸   🔁   ⏭ 🔵   ⏹ 🔴
resume  pause  replay  skip   stop
```

## 2. Live progress bar
`anony/helpers/_utilities.py` → `Utilities.progress_bar()`
Used in `anony/plugins/misc.py` (the existing `update_timer` loop) and in `/queue`.

Replaced the old `——◉———` ASCII bar with a coloured block-emoji bar:
`🟪🟪🟪🔘⬜⬜⬜⬜⬜⬜⬜⬜`. It already updates live every ~12s via the pre-existing
`update_timer` task — no new background loop needed, just a nicer renderer.

## 3. Custom premium emoji branding
`anony/helpers/_emoji.py` (new) — `PremiumEmoji` class, exposed as `pemoji` from
`anony.helpers`.

**Important limitation:** custom/premium emoji can only appear in message
**text/captions** (via Pyrogram's `<emoji id="...">` HTML tag) — Telegram does not
support entities inside inline button labels, so buttons stay on plain unicode
emoji (see #1). `pemoji.tag("music")` is now used to brand the "Now Streaming"
header in the play card and the "Queue" header in `/queue`. If no emoji ID is
configured for a given key, or your account isn't Premium, it silently falls back
to a plain unicode emoji — nothing breaks either way.

**Setup:** run `scripts/get_emoji_ids.py` once, using your Premium account's
session string (full instructions are in the script's docstring — set
`API_ID`/`API_HASH`/`PREMIUM_SESSION` env vars, run it, then send yourself a
template message in Saved Messages with your chosen custom emoji). It writes
`emoji_pack.json` in the project root, which `pemoji` reads on startup. This
script is standalone — it's never imported by the bot itself, so it's safe to
run from anywhere with network access to Telegram.

## 4. `/lyrics` (new)
`anony/plugins/lyrics.py`

- `/lyrics <song name>` or just `/lyrics` while something is playing.
- A "🎤 Lyrics" button is now added under the controls row whenever a
  YouTube-searched track (not a replied-file/M3U8 stream) starts playing.
- Pulls plain lyrics from [lrclib.net](https://lrclib.net) — free, keyless API.
  If nothing is found it says so instead of guessing.
- Toggle with `LYRICS_ENABLED=False` in your `.env`.

## 5. `/vskip` — vote to skip (new)
`anony/plugins/vskip.py`

Lets regular members (not just admins/auth users) start a vote to skip the
current track — useful for open groups where `/skip` is admin-only.
- Needed votes = `max(VOTE_SKIP_MIN, ceil(group_member_count * VOTE_SKIP_RATIO))`.
- Votes are tracked per currently-playing track ID, so they auto-reset on
  track change — no manual cleanup needed.
- Config: `VOTE_SKIP_ENABLED` (default True), `VOTE_SKIP_RATIO` (default 0.5),
  `VOTE_SKIP_MIN` (default 2).

## New config keys (all optional, sane defaults, add to `.env` if you want to change them)
```
VOTE_SKIP_ENABLED=True
VOTE_SKIP_RATIO=0.5
VOTE_SKIP_MIN=2
LYRICS_ENABLED=True
```

## Not done / deliberately scoped out
- Didn't touch the 13 locale JSON files' existing translated strings (too risky
  to hand-edit 13 languages safely in one pass) — new headers/labels are
  injected in code instead, so translations you already have stay intact.
- Didn't wire `/lyrics` or `/vskip` into the `/help` menu's button grid, since
  that grid's layout is shared across all locale files too. Easy 10-minute
  follow-up if you want it — just say the word.
- No literal "coloured buttons" since Telegram doesn't support that — see #1.

## Files touched
```
 anony/core/calls.py         (Now Playing header + lyrics button)
 anony/helpers/__init__.py   (registers `pemoji`)
 anony/helpers/_emoji.py     (NEW — premium emoji helper)
 anony/helpers/_inline.py    (coloured buttons, vskip markup, lyrics button row)
 anony/helpers/_utilities.py (progress_bar helper)
 anony/plugins/lyrics.py     (NEW — /lyrics command)
 anony/plugins/misc.py       (progress bar uses new helper)
 anony/plugins/queue.py      (queue header + live bar)
 anony/plugins/vskip.py      (NEW — /vskip command)
 config.py                   (new optional env vars)
 scripts/get_emoji_ids.py    (NEW — standalone, run separately)
```
