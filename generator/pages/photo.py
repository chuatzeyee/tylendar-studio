"""Photo page: a photo a day from generator/photos/, dithered to the
four panel colors and matted like a small gallery print.

Photos rotate by date through the folder in filename order; drop any
jpg or png in. EXIF rotation is honored and the mat opening is a cover
crop, so any aspect works. An empty folder raises, which generate.py
turns into the almanac fallback.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from generate import W, H, BLACK, WHITE, RED, YELLOW, draw_text, latin, serif

LEFT, RIGHT = 60, W - 60
TOP, BOTTOM = 60, 844

PHOTOS = Path(__file__).resolve().parent.parent / "photos"

PAL = Image.new("P", (1, 1))
PAL.putpalette(list(BLACK) + list(WHITE) + list(YELLOW) + list(RED)
               + list(BLACK) * 252)


def render(d, hl, settings):
    files = sorted(p for p in PHOTOS.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not files:
        raise ValueError("no photos in generator/photos")
    photo = ImageOps.exif_transpose(
        Image.open(files[d.toordinal() % len(files)])).convert("RGB")
    photo = ImageOps.fit(photo, (RIGHT - LEFT, BOTTOM - TOP), Image.LANCZOS)
    photo = photo.quantize(palette=PAL,
                           dither=Image.FLOYDSTEINBERG).convert("RGB")

    img = Image.new("RGB", (W, H), WHITE)
    img.paste(photo, (LEFT, TOP))
    dr = ImageDraw.Draw(img)
    dr.rectangle([LEFT - 1, TOP - 1, RIGHT, BOTTOM], outline=BLACK)

    # collector's stamp on the print, lower right corner
    sx, sy = RIGHT - 24 - 40, BOTTOM - 24 - 40
    dr.rectangle([sx, sy, sx + 40, sy + 40], fill=RED)
    draw_text(img, (sx + 20, sy + 21), "泰", serif(26, 600), WHITE, anchor="mm")

    # footer: hairline rule, one shared baseline
    dr.rectangle([LEFT, 884, RIGHT, 885], fill=BLACK)
    en = f"{hl['weekday_en']}, {hl['day']} {hl['month_abbr']} {hl['year']}"
    draw_text(img, (LEFT, 922), en, latin(21, 500), BLACK, anchor="ls")
    cn = f"{hl['ganzhi_year']}{hl['zodiac']}年 {hl['lunar_md']} {hl['ganzhi_day']}日"
    draw_text(img, (RIGHT + 4, 920), cn, serif(19, 500), BLACK, anchor="rs",
              tracking=2)
    return img
