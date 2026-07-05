# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


import os
import re
import time
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from anony import config
from anony.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        self.font1 = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 30)
        self.font2 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 30)
        self.card_title_font = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 52)
        self.card_sub_font = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 34)
        self.card_brand_font = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 40)
        self.card_time_font = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 28)
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()
    async def close(self) -> None:
        await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f: f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            thumb = Image.open(temp).convert("RGBA").resize(
                size, Image.Resampling.LANCZOS,
            )
            blur = thumb.filter(ImageFilter.GaussianBlur(25))
            image = ImageEnhance.Brightness(blur).enhance(.40)

            _rect = ImageOps.fit(
                thumb, self.rect,
                method=Image.LANCZOS, centering=(0.5, 0.5),
            )
            ImageDraw.Draw(self.mask).rounded_rectangle(
                (0, 0, self.rect[0], self.rect[1]),
                radius=15,
                fill=255,
            )
            _rect.putalpha(self.mask)
            image.paste(_rect, (183, 30), _rect)

            draw = ImageDraw.Draw(image)
            draw.text(
                xy=(50, 560),
                text=f"{song.channel_name[:25]} | {song.view_count}",
                font=self.font2, fill=self.fill,
            )
            draw.text((50, 600), song.title[:50], font=self.font1, fill=self.fill)
            draw.text((40, 650), "0:01", font=self.font1)
            draw.line([(140, 670), (1160, 670)], fill=self.fill, width=5, joint="curve")
            draw.text((1185, 650), song.duration, font=self.font1, fill=self.fill)

            image.save(output)
            try: os.remove(temp)
            except Exception: pass
            return output
        except Exception:
            return config.DEFAULT_THUMB

    async def generate_share_card(
        self,
        song: Track,
        bot_name: str,
        bot_username: str,
        elapsed: int = 0,
    ) -> str:
        """
        A dedicated vertical (story-friendly, 1080x1920) shareable card --
        unlike the in-chat Now Playing thumbnail, this bakes bot branding
        directly into the image pixels, not just the message caption. That
        way it still promotes the bot even if someone forwards/reposts just
        the photo with no caption attached (e.g. onto a Telegram Story).
        """
        W, H = 1080, 1920
        temp = f"cache/share_temp_{song.id}.jpg"
        output = f"cache/share_{song.id}.png"

        def centered(draw, y, text, font, fill=(255, 255, 255)):
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (W - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), text, font=font, fill=fill)

        def truncate(draw, text, font, max_width):
            while draw.textbbox((0, 0), text, font=font)[2] > max_width and len(text) > 1:
                text = text[:-2] + "…"
            return text

        try:
            await self.save_thumb(temp, song.thumbnail)
            cover = Image.open(temp).convert("RGBA")

            # Full-bleed blurred background
            bg = ImageOps.fit(cover, (W, H), method=Image.LANCZOS, centering=(0.5, 0.5))
            bg = bg.filter(ImageFilter.GaussianBlur(40))
            bg = ImageEnhance.Brightness(bg).enhance(0.35)
            card = bg.convert("RGBA")

            # Large, near-edge-to-edge album art
            margin = 40
            art_size = W - margin * 2  # 1000px -- fills almost the full width
            art_top = 90
            art = ImageOps.fit(
                cover, (art_size, art_size), method=Image.LANCZOS, centering=(0.5, 0.5)
            )
            art_mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(art_mask).rounded_rectangle(
                (0, 0, art_size, art_size), radius=40, fill=255
            )
            art.putalpha(art_mask)
            card.paste(art, (margin, art_top), art)

            draw = ImageDraw.Draw(card)

            # "NOW PLAYING" badge -- fills the gap under the art and sets context
            badge_y = art_top + art_size + 40
            badge_text = "NOW PLAYING"
            badge_bbox = draw.textbbox((0, 0), badge_text, font=self.card_sub_font)
            badge_w = (badge_bbox[2] - badge_bbox[0]) + 60
            badge_h = 60
            badge_x = (W - badge_w) // 2
            draw.rounded_rectangle(
                (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
                radius=30, fill=(15, 15, 25, 200),
            )
            centered(draw, badge_y + 14, badge_text, self.card_sub_font)

            title_y = badge_y + badge_h + 45
            title = truncate(draw, song.title, self.card_title_font, W - 120)
            centered(draw, title_y, title, self.card_title_font)

            subtitle_y = title_y + 85
            subtitle = truncate(
                draw, song.channel_name or "", self.card_sub_font, W - 160
            )
            centered(draw, subtitle_y, subtitle, self.card_sub_font, fill=(210, 210, 210))

            # Progress line
            bar_y = subtitle_y + 110
            pos = min(elapsed / song.duration_sec, 1.0) if song.duration_sec else 0
            bar_x1, bar_x2 = 140, W - 140
            fill_x = bar_x1 + int((bar_x2 - bar_x1) * pos)
            draw.line([(bar_x1, bar_y), (bar_x2, bar_y)], fill=(255, 255, 255, 90), width=8)
            draw.line([(bar_x1, bar_y), (fill_x, bar_y)], fill=(255, 255, 255), width=8)
            draw.ellipse(
                (fill_x - 12, bar_y - 12, fill_x + 12, bar_y + 12), fill=(255, 255, 255)
            )
            elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
            draw.text((bar_x1, bar_y + 25), elapsed_str, font=self.card_time_font, fill=(230, 230, 230))
            dur_bbox = draw.textbbox((0, 0), song.duration, font=self.card_time_font)
            draw.text(
                (bar_x2 - (dur_bbox[2] - dur_bbox[0]), bar_y + 25),
                song.duration, font=self.card_time_font, fill=(230, 230, 230),
            )

            if song.user:
                # song.user is a Pyrogram mention string with raw HTML
                # (e.g. '<a href="tg://user?id=...">Name</a>') -- PIL draws
                # literal characters, it doesn't parse HTML, so this must be
                # stripped down to plain text before drawing.
                plain_name = re.sub(r"<[^>]+>", "", song.user).strip() or "Someone"
                centered(
                    draw, bar_y + 90, f"Requested by {plain_name}",
                    self.card_sub_font, fill=(200, 200, 200),
                )

            # Bottom branding bar -- more padding, better vertical centering
            brand_h = 190
            brand_y = H - brand_h - 70
            draw.rounded_rectangle(
                (60, brand_y, W - 60, brand_y + brand_h), radius=30, fill=(20, 20, 30, 235)
            )
            centered(draw, brand_y + 48, bot_name, self.card_brand_font)
            centered(
                draw, brand_y + 108, f"t.me/{bot_username} — stream music together",
                self.card_sub_font, fill=(190, 190, 190),
            )

            card.convert("RGB").save(output)
            try: os.remove(temp)
            except Exception: pass
            return output
        except Exception:
            try: os.remove(temp)
            except Exception: pass
            return config.DEFAULT_THUMB
