#!/usr/bin/env python3
"""Draw a site's sharing card: sites/<site>/static/brand/og.png, 1200 by 630.

    python3 scripts/sharing_card.py stats

The card is the picture a link to the site shows in a message or on social media (chart pages share their chart
instead). It is the site's coin, its wordmark, and one line under the wordmark. The line is Jim's wording and lives
in sites/<site>/site.yml as `sharing_card_line`; change it there and run this script. Nothing else on the card is
typed: the coin and the wordmark are the brand files in sites/<site>/static/brand/.

Needs Pillow and matplotlib (for its copy of DejaVu Sans, so the card looks the same on every machine).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SIZE = (1200, 630)
NAVY = (7, 24, 41)            # #071829, the brand's band color
LINE_INK = (169, 182, 200)    # the line under the wordmark
COIN_BOX = (90, 115, 400)     # left, top, side
WORDMARK_BOX = (560, 235, 560)   # left, top, width
LINE_LEFT, LINE_TOP, LINE_PITCH, TYPE_SIZE = 562, 329, 40, 30
LINE_WIDTH = 552              # the line wraps inside the wordmark's own width


def wrap(text: str, font, width: int) -> list[str]:
    """Fill each row with as many words as fit the width; the card has room for two rows."""
    rows: list[str] = []
    for word in text.split():
        if rows and font.getlength(f"{rows[-1]} {word}") <= width:
            rows[-1] = f"{rows[-1]} {word}"
        else:
            rows.append(word)
    if len(rows) > 2 or any(font.getlength(row) > width for row in rows):
        raise SystemExit(f"the line is too long for the card: {text!r}")
    return rows


def draw_card(site: str) -> Path:
    from matplotlib import font_manager
    from PIL import Image, ImageDraw, ImageFont

    settings = yaml.safe_load((ROOT / "sites" / site / "site.yml").read_text(encoding="utf-8"))
    line = str(settings.get("sharing_card_line", "")).strip()
    if not line:
        raise SystemExit(f"sites/{site}/site.yml has no sharing_card_line; add the line the card should carry")
    brand = ROOT / "sites" / site / "static" / "brand"
    coin = Image.open(brand / "coin-512.png").convert("RGBA")
    wordmark = Image.open(brand / "wordmark.png").convert("RGBA")

    card = Image.new("RGB", SIZE, NAVY)
    left, top, side = COIN_BOX
    big = coin.resize((side, side), Image.LANCZOS)
    card.paste(big, (left, top), big)
    left, top, width = WORDMARK_BOX
    mark = wordmark.resize((width, round(wordmark.size[1] * width / wordmark.size[0])), Image.LANCZOS)
    card.paste(mark, (left, top), mark)

    font = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), TYPE_SIZE)
    pen = ImageDraw.Draw(card)
    for row, text in enumerate(wrap(line, font, LINE_WIDTH)):
        pen.text((LINE_LEFT, LINE_TOP + LINE_PITCH * row), text, font=font, fill=LINE_INK)

    out = brand / "og.png"
    card.save(out, optimize=True)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("stats", "facts", "acts"):
        print(__doc__)
        sys.exit(2)
    print("wrote", draw_card(sys.argv[1]).relative_to(ROOT))
