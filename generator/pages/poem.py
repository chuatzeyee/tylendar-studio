"""Tylendar page: daily Tang poem letter-paper (every ri shijian).

One poem from data/poems.json typeset vertically right-to-left on a
ruled poem sheet, one column per line, four columns for jueju and eight
for lushi. The lunar-date colophon sits below the two leftmost columns
with the red seal stamped across their shared rule; title and poet run
down a full-height aged-silk band at right. Poem picked by day ordinal
so it changes daily and never repeats two days in a row.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw

from generate import (W, H, BLACK, WHITE, RED, YELLOW, MONTH_ABBR,
                      draw_text, latin, serif, text_width)

POEMS = json.loads((Path(__file__).resolve().parent.parent / "data" /
                    "poems.json").read_text(encoding="utf-8"))

L, R = 60, 526                # ruled sheet, left and right edges
BAND_X0, BAND_X1 = 554, 610   # aged-silk band behind the title column
BOX_T, BOX_B = 150, 846       # ruled sheet, top and bottom edges

# Char box per column count; jueju columns are twice as wide, so their
# characters run larger. Vertical pitch is the grid.
POEM_SIZE = {4: 58, 8: 50}
POEM_CY0, POEM_PITCH_Y = 206, 80
SIG_CY0, SIG_PITCH_Y = 606, 33
SEAL = 78


def draw_col(img, cx, cy0, text, font, fill, pitch):
    """One vertical column on a strict grid: same box, same pitch."""
    for k, ch in enumerate(text):
        draw_text(img, (cx, cy0 + k * pitch), ch, font, fill, anchor="mm")


def fit_latin(text, size, weight, max_w):
    """Largest Canela size (floor 13) that keeps the line on the sheet."""
    while size > 13 and text_width(text, latin(size, weight)) > max_w:
        size -= 1
    return latin(size, weight)


def render(d, hl, settings):
    poem = POEMS[d.toordinal() % len(POEMS)]
    lines = poem["lines"]
    ncol = len(lines)
    pitch_x = (R - L) / ncol

    def col_cx(i):
        return R - (i + 0.5) * pitch_x

    img = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(img)

    # Aged-silk band, full height; title slip, poet, collection label.
    dr.rectangle([BAND_X0, 0, BAND_X1, H], fill=YELLOW)
    band_cx = (BAND_X0 + BAND_X1) // 2
    title = poem["title"]
    draw_col(img, band_cx, 88, title, serif(38, 600), BLACK, 54)
    poet_cy0 = 88 + (len(title) - 1) * 54 + 80
    draw_col(img, band_cx, poet_cy0, poem["author"], serif(24, 500), BLACK, 32)
    draw_col(img, band_cx, 773, "唐詩三百首", serif(22, 500), BLACK, 30)

    # Header: series title left, poem form right, over the sheet.
    draw_text(img, (L, 84), "每日詩箋", serif(26, 600), BLACK,
              anchor="lm", tracking=8)
    draw_text(img, (R, 84), "唐 " + poem["form"], serif(22, 400), BLACK,
              anchor="rm", tracking=4)

    # The ruled sheet: hairline frame plus column rules.
    dr.rectangle([L, BOX_T, R, BOX_B], outline=BLACK, width=1)
    english = poem.get("english") if settings.get("poem_lang") == "en" else None
    if english:
        # English: horizontal centered lines on the open sheet, the
        # silk band and colophon-free seal keeping the Chinese frame.
        mid = (L + R) // 2
        title_en = (poem.get("title_en") or poem["title"]).replace("'", "\u2019")
        draw_text(img, (mid, 214), title_en,
                  fit_latin(title_en, 26, 700, R - L - 36), BLACK,
                  anchor="ms", tracking=1)
        n = len(english)
        pitch = 46 if n > 6 else 62
        cy0 = 470 - (n - 1) * pitch // 2
        for k, line in enumerate(english):
            line = line.replace("'", "\u2019")
            draw_text(img, (mid, cy0 + k * pitch), line,
                      fit_latin(line, 19, 450, R - L - 28), BLACK,
                      anchor="ms", tracking=1)
    else:
        for i in range(1, ncol):
            x = round(L + i * pitch_x)
            dr.line([x, BOX_T, x, BOX_B], fill=BLACK, width=1)

        # The poem: one ruled column per line, right to left, strict grid.
        f_poem = serif(POEM_SIZE[ncol], 500)
        for i, line in enumerate(lines):
            draw_col(img, col_cx(i), POEM_CY0, line, f_poem, BLACK, POEM_PITCH_Y)

        # Colophon: lunar date below the two leftmost columns.
        f_sig = serif(22, 500)
        draw_col(img, col_cx(ncol - 2), SIG_CY0, hl["ganzhi_year"] + "年",
                 f_sig, BLACK, SIG_PITCH_Y)
        draw_col(img, col_cx(ncol - 1), SIG_CY0, hl["lunar_md"],
                 f_sig, BLACK, SIG_PITCH_Y)

    # The red moment: seal stamped across the colophon rule. Leap-month
    # lunar dates run five characters, so the seal steps down clear of
    # the longer column.
    scx = round(L + pitch_x)
    sy0 = max(741, SIG_CY0 + (len(hl["lunar_md"]) - 1) * SIG_PITCH_Y + 25)
    sx0 = scx - SEAL // 2
    dr.rectangle([sx0, sy0, sx0 + SEAL, sy0 + SEAL], fill=RED)
    draw_text(img, (scx, sy0 + 22), "泰", serif(32, 600), WHITE, anchor="mm")
    draw_text(img, (scx, sy0 + 57), "曆", serif(32, 600), WHITE, anchor="mm")

    # Footer: Latin date left, poet name and years right, sheet-aligned.
    # Canela lighter than 700 at 16px thresholds the top bowl of 3 away
    # and it reads as 5, so the footer runs heavier than the mockup.
    when = f"{d.day} {MONTH_ABBR[d.month - 1].upper()} {d.year}"
    draw_text(img, (L, 904), when, latin(16, 800), BLACK,
              anchor="ls", tracking=3)
    if poem["author_dates"]:
        byline = f"{poem['author_roman']}, {poem['author_dates']}"
        draw_text(img, (R, 904), byline, latin(16, 700), BLACK,
                  anchor="rs", tracking=2)
    else:
        draw_text(img, (R, 904), poem["author"], serif(20, 500), BLACK,
                  anchor="rs", tracking=4)

    # One line of English under the footer: the poem's gist, not a
    # translation, kept to 52 chars so it always clears the silk band.
    # Canela has no ASCII apostrophe, only U+2019; data stays ASCII.
    gist = poem["gist"].replace("'", "\u2019")
    draw_text(img, ((L + R) // 2, 938), gist, latin(15, 600), BLACK,
              anchor="ms", tracking=1)
    return img
