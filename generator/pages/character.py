"""Character page: one character a day (yi ri yi zi).

A single giant character from data/characters.json fills the page,
optically centered between two hairlines. Below, a dictionary-style
table: pinyin + gloss, then two compound rows, all sharing one gutter
column and per-row baselines. A red seal sits lower right; a radical
and stroke-count line closes the page as fine print. Character picked
by day ordinal so it changes daily and never repeats two days in a row.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

from generate import (W, H, BLACK, WHITE, RED, YELLOW, DuoFont,
                      TEXT_THRESHOLD, cn_number, draw_text, text_width,
                      latin, serif)

CHARS = json.loads((Path(__file__).resolve().parent.parent / "data" /
                    "characters.json").read_text(encoding="utf-8"))

LEFT, RIGHT = 60, W - 60

RULE_A, RULE_B, RULE_C = 668, 778, 900   # hairlines of the bottom apparatus
PY_BASE, ROW1, ROW2, FOOT = 738, 826, 874, 932
SEAL = 80


def char_mask(ch, size, weight=600):
    """Render one CJK glyph to a page-sized mask and return (mask, bbox).
    Huge sizes clip getbbox-style metrics, so measure the actual ink."""
    f = serif(size, weight)
    pil_font = f.pick(ch) if isinstance(f, DuoFont) else f
    layer = Image.new("L", (W, H), 0)
    ImageDraw.Draw(layer).text((W // 2, H // 2), ch, font=pil_font,
                               anchor="mm", fill=255)
    mask = layer.point(lambda p: 255 if p >= TEXT_THRESHOLD else 0)
    return mask, mask.getbbox()


def fit_char(ch, max_w, max_h, start=560, weight=600):
    size = start
    while True:
        mask, bb = char_mask(ch, size, weight)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if (w <= max_w and h <= max_h) or size < 100:
            return mask, bb
        size = int(size * min(max_w / w, max_h / h))


def ink_centroid(mask):
    """Center of ink mass, via exact box-filtered row/column averages."""
    w, h = mask.size
    cols = mask.resize((w, 1), Image.BOX).tobytes()
    rows = mask.resize((1, h), Image.BOX).tobytes()
    cx = sum(x * v for x, v in enumerate(cols)) / max(1, sum(cols))
    cy = sum(y * v for y, v in enumerate(rows)) / max(1, sum(rows))
    return cx, cy


def place_char(img, ch, zone_top, zone_bot):
    """Fit the glyph, then center it optically: blend the ink bounding
    box center with the ink centroid so thin extenders do not push the
    dense body off balance. Nudge is capped."""
    mask, bb = fit_char(ch, RIGHT - LEFT, zone_bot - zone_top - 52)
    bcx, bcy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    mcx, mcy = ink_centroid(mask)
    ax = bcx + max(-12, min(12, 0.4 * (mcx - bcx)))
    ay = bcy + max(-12, min(12, 0.4 * (mcy - bcy)))
    ox, oy = W / 2 - ax, (zone_top + zone_bot) / 2 - ay
    shifted = mask.transform(mask.size, Image.AFFINE,
                             (1, 0, -ox, 0, 1, -oy), fillcolor=0)
    img.paste(BLACK, (0, 0), shifted)


def render(d, hl, settings):
    entry = CHARS[d.toordinal() % len(CHARS)]
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Header: series title left, date right, hairline under.
    draw_text(img, (LEFT, 78), "一日一字", serif(28, 600), BLACK,
              anchor="lm", tracking=8)
    when = f"{hl['day']} {hl['month_abbr'].upper()}"
    draw_text(img, (RIGHT, 80), when, latin(30, 650), BLACK,
              anchor="rm", tracking=2)
    draw.rectangle([LEFT, 118, RIGHT, 119], fill=BLACK)

    # The character, optically centered between the hairlines.
    place_char(img, entry["zi"], 119, RULE_A)
    draw.rectangle([LEFT, RULE_A, RIGHT, RULE_A + 1], fill=BLACK)

    # Shared gutter: one x for every English cell.
    f_py, f_tone = latin(56, 450), latin(26, 500)
    f_word, f_gl1, f_gl2 = serif(32, 500), latin(26, 450), latin(22, 450)
    w_pin = text_width(entry["pinyin"], f_py) + 6 + text_width(entry["tone"], f_tone)
    w_word = max(text_width(w, f_word, 4) for w, _ in entry["words"])
    x_gloss = LEFT + max(w_pin, w_word) + 56

    # Row 1: pinyin with a yellow underline under the descenders, tone
    # as a superscript numeral, then the main gloss.
    draw.rectangle([LEFT, PY_BASE + 16, LEFT + w_pin, PY_BASE + 19], fill=YELLOW)
    draw_text(img, (LEFT, PY_BASE), entry["pinyin"], f_py, BLACK, anchor="ls")
    tone_x = LEFT + text_width(entry["pinyin"], f_py) + 6
    draw_text(img, (tone_x, PY_BASE - 30), entry["tone"], f_tone, BLACK, anchor="ls")
    draw_text(img, (x_gloss, PY_BASE), entry["gloss"], f_gl1, BLACK, anchor="ls")

    # Rows 2-3: compounds and glosses, plus the red seal.
    draw.rectangle([LEFT, RULE_B, RIGHT, RULE_B + 1], fill=BLACK)
    for base, (word, gloss) in zip((ROW1, ROW2), entry["words"]):
        draw_text(img, (LEFT, base), word, f_word, BLACK, anchor="ls", tracking=4)
        draw_text(img, (x_gloss, base), gloss, f_gl2, BLACK, anchor="ls")

    sx0, sy0 = RIGHT - SEAL, (RULE_B + RULE_C - SEAL) // 2
    draw.rectangle([sx0, sy0, sx0 + SEAL, sy0 + SEAL], fill=RED)
    draw_text(img, (sx0 + SEAL / 2, sy0 + 23), "泰", serif(32, 600), WHITE, anchor="mm")
    draw_text(img, (sx0 + SEAL / 2, sy0 + 58), "曆", serif(32, 600), WHITE, anchor="mm")

    # Footer: radical and stroke count, fine print.
    draw.rectangle([LEFT, RULE_C, RIGHT, RULE_C + 1], fill=BLACK)
    f_foot = serif(22, 500)
    radical = "部首 " + entry["radical"]
    draw_text(img, (LEFT, FOOT), radical, f_foot, BLACK, anchor="ls", tracking=2)
    dot_x = LEFT + text_width(radical, f_foot, 2) + 14
    draw.ellipse([dot_x - 2, FOOT - 10, dot_x + 2, FOOT - 6], fill=BLACK)
    draw_text(img, (dot_x + 14, FOOT), cn_number(entry["strokes"]) + "畫",
              f_foot, BLACK, anchor="ls", tracking=2)
    # Canela lighter than 700 at this size thresholds the top bowl of 3
    # away and it reads as 5, so the line runs heavier than the mockup.
    en = f"RADICAL {entry['radical_no']}, {entry['strokes']} STROKES"
    draw_text(img, (RIGHT, FOOT), en, latin(16, 700), BLACK, anchor="rs", tracking=2)
    return img
