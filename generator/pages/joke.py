"""Joke page: one Singlish profanity a day (yi ri yi ma).

The character page's dictionary apparatus, deadpan, but the headword
is a Hokkien vulgarity spelled out in Chinese characters, the
romanization sits where the pinyin would, and the gloss is the polite
English pun. The "joke_word" setting pins one entry by key; any other
value rotates through data/jokes.json by day ordinal.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

from generate import (W, H, BLACK, WHITE, RED, YELLOW, DuoFont,
                      TEXT_THRESHOLD, cn_number, draw_text, text_width,
                      latin, serif)
from pages.character import ink_centroid

JOKES = json.loads((Path(__file__).resolve().parent.parent / "data" /
                    "jokes.json").read_text(encoding="utf-8"))

LEFT, RIGHT = 60, W - 60

RULE_A, RULE_B, RULE_C = 668, 778, 900   # hairlines of the bottom apparatus
PY_BASE, ROW1, ROW2, FOOT = 738, 826, 874, 932
SEAL = 80


def word_mask(word, size, weight=600):
    """Like character.char_mask but for a whole headword: the deck is
    all traditional characters, so one font pick covers the string."""
    f = serif(size, weight)
    pil_font = f.pick(word[0]) if isinstance(f, DuoFont) else f
    layer = Image.new("L", (W, H), 0)
    ImageDraw.Draw(layer).text((W // 2, H // 2), word, font=pil_font,
                               anchor="mm", fill=255)
    mask = layer.point(lambda p: 255 if p >= TEXT_THRESHOLD else 0)
    return mask, mask.getbbox()


def fit_word(word, max_w, max_h, start=560):
    size = start
    while True:
        mask, bb = word_mask(word, size)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        if (w <= max_w and h <= max_h) or size < 60:
            return mask, bb
        size = int(size * min(max_w / w, max_h / h))


def place_word(img, word, zone_top, zone_bot):
    mask, bb = fit_word(word, RIGHT - LEFT, zone_bot - zone_top - 52)
    bcx, bcy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    mcx, mcy = ink_centroid(mask)
    ax = bcx + max(-12, min(12, 0.4 * (mcx - bcx)))
    ay = bcy + max(-12, min(12, 0.4 * (mcy - bcy)))
    ox, oy = W / 2 - ax, (zone_top + zone_bot) / 2 - ay
    shifted = mask.transform(mask.size, Image.AFFINE,
                             (1, 0, -ox, 0, 1, -oy), fillcolor=0)
    img.paste(BLACK, (0, 0), shifted)


def pick_entry(d, settings):
    key = str(settings.get("joke_word", "")).strip().lower()
    for e in JOKES:
        if e["key"] == key:
            return e
    return JOKES[d.toordinal() % len(JOKES)]


def render(d, hl, settings):
    entry = pick_entry(d, settings)
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Header: series title left, date right, hairline under.
    draw_text(img, (LEFT, 78), "一日一罵", serif(28, 600), BLACK,
              anchor="lm", tracking=8)
    when = f"{hl['day']} {hl['month_abbr'].upper()}"
    draw_text(img, (RIGHT, 80), when, latin(30, 650), BLACK,
              anchor="rm", tracking=2)
    draw.rectangle([LEFT, 118, RIGHT, 119], fill=BLACK)

    # The headword, optically centered between the hairlines.
    place_word(img, entry["zi"], 119, RULE_A)
    draw.rectangle([LEFT, RULE_A, RIGHT, RULE_A + 1], fill=BLACK)

    # Shared gutter: one x for every English cell.
    f_py = latin(56, 450)
    f_word, f_gl1, f_gl2 = serif(32, 500), latin(26, 450), latin(22, 450)
    w_rom = text_width(entry["roman"], f_py)
    w_word = max(text_width(w, f_word, 4) for w, _ in entry["words"])
    x_gloss = LEFT + max(w_rom, w_word) + 56

    # Row 1: romanization with the yellow underline, then the pun.
    draw.rectangle([LEFT, PY_BASE + 16, LEFT + w_rom, PY_BASE + 19], fill=YELLOW)
    draw_text(img, (LEFT, PY_BASE), entry["roman"], f_py, BLACK, anchor="ls")
    draw_text(img, (x_gloss, PY_BASE), entry["gloss"], f_gl1, BLACK, anchor="ls")

    # Rows 2-3: usage and glosses, plus the red seal.
    draw.rectangle([LEFT, RULE_B, RIGHT, RULE_B + 1], fill=BLACK)
    for base, (word, gloss) in zip((ROW1, ROW2), entry["words"]):
        draw_text(img, (LEFT, base), word, f_word, BLACK, anchor="ls", tracking=4)
        draw_text(img, (x_gloss, base), gloss, f_gl2, BLACK, anchor="ls")

    sx0, sy0 = RIGHT - SEAL, (RULE_B + RULE_C - SEAL) // 2
    draw.rectangle([sx0, sy0, sx0 + SEAL, sy0 + SEAL], fill=RED)
    draw_text(img, (sx0 + SEAL / 2, sy0 + 23), "泰", serif(32, 600), WHITE, anchor="mm")
    draw_text(img, (sx0 + SEAL / 2, sy0 + 58), "曆", serif(32, 600), WHITE, anchor="mm")

    # Footer: radical and stroke count of the first character.
    draw.rectangle([LEFT, RULE_C, RIGHT, RULE_C + 1], fill=BLACK)
    f_foot = serif(22, 500)
    radical = "部首 " + entry["radical"]
    draw_text(img, (LEFT, FOOT), radical, f_foot, BLACK, anchor="ls", tracking=2)
    dot_x = LEFT + text_width(radical, f_foot, 2) + 14
    draw.ellipse([dot_x - 2, FOOT - 10, dot_x + 2, FOOT - 6], fill=BLACK)
    draw_text(img, (dot_x + 14, FOOT), cn_number(entry["strokes"]) + "畫",
              f_foot, BLACK, anchor="ls", tracking=2)
    en = f"RADICAL {entry['radical_no']}, {entry['strokes']} STROKES"
    draw_text(img, (RIGHT, FOOT), en, latin(16, 700), BLACK, anchor="rs", tracking=2)
    return img
