"""Tylendar renderer.

Renders a minimalist Chinese almanac (huangli) page for a
Good Display GDEM102F91 e-paper panel: 960x640, four colors
(black, white, yellow, red), SSD2677 controller.

Outputs:
  output/preview.png   what the panel will show, portrait 640x960
  output/tylendar.bin  packed panel data, 153600 bytes, 2 bits per pixel,
                       4 pixels per byte MSB first, native 960x640 rows,
                       00 black, 01 white, 10 yellow, 11 red

Set the OUT_DIR environment variable to write both files elsewhere.
"""

import importlib
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont
from lunar_python import Solar
from opencc import OpenCC

# lunar_python emits simplified Chinese; the calendar renders in
# traditional with Hong Kong conventions. The zodiac clash character is
# fixed up because almanacs write it 沖, not OpenCC's standalone 衝.
CC = OpenCC("s2hk")


def to_traditional(value):
    if isinstance(value, str):
        return CC.convert(value).replace("衝", "沖")
    if isinstance(value, list):
        return [to_traditional(v) for v in value]
    return value

ROOT = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT_DIR", "").strip() or ROOT.parent / "output")

W, H = 640, 960
MARGIN = 52


def load_settings():
    """Editable knobs, changed from any browser at
    github.com/chuatzeyee/Tylendar/edit/main/generator/settings.json.
    A bad edit must never kill the scheduled render, so any problem
    falls back to defaults with a warning."""
    try:
        parsed = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    # ValueError covers both bad JSON and non UTF-8 bytes.
    except (ValueError, OSError) as e:
        print(f"warning: settings.json ignored ({e})", file=sys.stderr)
        return {}
    if not isinstance(parsed, dict):
        print(f"warning: settings.json ignored (expected an object, got "
              f"{type(parsed).__name__})", file=sys.stderr)
        return {}
    return parsed


SETTINGS = load_settings()
HOTSPOT = str(SETTINGS.get("hotspot") or "").strip() or "TyBatan"
PAGES = ("almanac", "poem", "character", "landscape", "weather", "month",
         "year", "joke", "photo", "flora")

BLACK = (12, 12, 12)
WHITE = (255, 255, 255)
RED = (186, 32, 41)
YELLOW = (236, 183, 15)
PALETTE = {BLACK: 0b00, WHITE: 0b01, YELLOW: 0b10, RED: 0b11}

SERIF = str(ROOT / "fonts" / "ChironSungHK.ttf")
SANS_SC = str(ROOT / "fonts" / "NotoSansSC.ttf")
LATIN = str(ROOT / "fonts" / "Fraunces.ttf")

# Licensed fonts in fonts/licensed/ take priority over the open fonts
# above; if the directory is emptied the render falls back cleanly.
LICENSED = ROOT / "fonts" / "licensed"
MTR_SUNG = LICENSED / "mtr-sung.ttf"
CANELA_BY_WEIGHT = [
    (250, LICENSED / "canelaweb-thin.ttf"),
    (450, LICENSED / "canelaweb-regular.ttf"),
    (650, LICENSED / "canelaweb-medium.ttf"),
    (800, LICENSED / "canelaweb-bold.ttf"),
    (10_000, LICENSED / "canelaweb-black.ttf"),
]


def _mtr_codepoints():
    from fontTools.ttLib import TTFont

    return set(TTFont(str(MTR_SUNG)).getBestCmap())


MTR_COVER = _mtr_codepoints() if MTR_SUNG.exists() else None


class DuoFont:
    """Primary font with per-character fallback for uncovered glyphs.
    MTR Sung is traditional only, so simplified characters fall back to
    Chiron Sung HK, which shares its Hong Kong Song style."""

    def __init__(self, primary, fallback, cover):
        self.primary = primary
        self.fallback = fallback
        self.cover = cover

    def pick(self, c):
        f = self.primary if ord(c) in self.cover else self.fallback
        return f.pick(c) if isinstance(f, DuoFont) else f

    def getlength(self, text):
        return sum(self.pick(c).getlength(c) for c in text)

LATIN_COVER = set(range(0x20, 0x7F))

TIMEZONE = "Asia/Singapore"
YI_JI_MAX = 4

# Set to False if the image shows up rotated 180 degrees on your panel.
FPC_AT_BOTTOM = True

WEEKDAY_EN = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
              "FRIDAY", "SATURDAY", "SUNDAY"]
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CN_NUM = "一二三四五六七八九十"


def serif(size, weight=400):
    font = ImageFont.truetype(SERIF, size)
    font.set_variation_by_axes([weight, 0])
    if MTR_COVER is None:
        return font
    return DuoFont(ImageFont.truetype(str(MTR_SUNG), size), font, MTR_COVER)


def sans_sc(size, weight=400):
    font = ImageFont.truetype(SANS_SC, size)
    font.set_variation_by_axes([weight])
    return font


def latin(size, weight=400, opsz=32, soft=0):
    for max_weight, path in CANELA_BY_WEIGHT:
        if path.exists() and weight <= max_weight:
            return ImageFont.truetype(str(path), size)
    font = ImageFont.truetype(LATIN, size)
    font.set_variation_by_axes([opsz, weight, soft, 0])
    return font


# Mask cutoff for text. 128 drops Song hairline strokes that render
# under one pixel wide (the bottom bar of 日 vanished on the panel);
# 60 clogs dense glyphs at small sizes. 80 keeps both.
TEXT_THRESHOLD = 80


def draw_text(img, xy, text, font, fill, anchor="la", tracking=0):
    """Draw text through a thresholded mask so every pixel is an exact
    palette color. Anti-aliased edge pixels would otherwise quantize into
    speckle on the panel."""
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    duo = isinstance(font, DuoFont)
    if tracking or duo:
        total = sum(font.getlength(c) for c in text) + tracking * (len(text) - 1)
        x, y = xy
        if anchor[0] == "m":
            x -= total / 2
        elif anchor[0] == "r":
            x -= total
        for c in text:
            f = font.pick(c) if duo else font
            d.text((x, y), c, font=f, fill=255, anchor="l" + anchor[1])
            x += font.getlength(c) + tracking
    else:
        d.text(xy, text, font=font, fill=255, anchor=anchor)
    mask = layer.point(lambda p: 255 if p >= TEXT_THRESHOLD else 0)
    img.paste(fill, (0, 0), mask)


def text_width(text, font, tracking=0):
    return sum(font.getlength(c) for c in text) + tracking * (len(text) - 1)


def huangli(d):
    """Collect everything the layout needs for one Gregorian date."""
    solar = Solar.fromYmd(d.year, d.month, d.day)
    lunar = solar.getLunar()
    prev_jq = lunar.getPrevJieQi(True)
    next_jq = lunar.getNextJieQi(True)
    jq_today = prev_jq.getSolar().toYmd() == d.isoformat()
    days_into = (d - date.fromisoformat(prev_jq.getSolar().toYmd())).days
    festivals = list(lunar.getFestivals()) + list(solar.getFestivals())
    data = {
        "solar": solar,
        "day": d.day,
        "month_abbr": MONTH_ABBR[d.month - 1],
        "year": d.year,
        "weekday_cn": "星期" + solar.getWeekInChinese(),
        "weekday_en": WEEKDAY_EN[d.weekday()].capitalize(),
        "is_sunday": d.weekday() == 6,
        "lunar_md": lunar.getMonthInChinese() + "月" + lunar.getDayInChinese(),
        "ganzhi_year": lunar.getYearInGanZhi(),
        "ganzhi_month": lunar.getMonthInGanZhi(),
        "ganzhi_day": lunar.getDayInGanZhi(),
        "zodiac": lunar.getYearShengXiao(),
        "yi": list(lunar.getDayYi())[:YI_JI_MAX],
        "ji": list(lunar.getDayJi())[:YI_JI_MAX],
        "jieqi_today": prev_jq.getName() if jq_today else None,
        "jieqi_line": (prev_jq.getName() + " 第" + cn_number(days_into + 1) + "天"
                       if not jq_today else None),
        "next_jieqi": next_jq.getName(),
        "chong": "冲" + lunar.getDayChongShengXiao(),
        "sha": "煞" + lunar.getDaySha(),
        "nayin": lunar.getDayNaYin(),
        "festivals": festivals,
    }
    return {k: to_traditional(v) for k, v in data.items()}


def event_time(dt):
    h = dt.hour % 12 or 12
    ap = "am" if dt.hour < 12 else "pm"
    return f"{h}.{dt.minute:02d}{ap}" if dt.minute else f"{h}{ap}"


def calendar_events(d):
    """The day's first two events as (time, title, venue) tuples from
    the ICS feed named by the ICS_URL environment variable (a URL or a
    local file path), or None. Any failure falls back to the almanac
    rows; a broken calendar fetch must never cost the day's render."""
    url = os.environ.get("ICS_URL", "").strip()
    if not url:
        return None
    try:
        import icalendar
        import recurring_ical_events

        if url.startswith(("http://", "https://")):
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read()
        else:
            data = Path(url).read_bytes()
        cal = icalendar.Calendar.from_ical(data)
        tz = ZoneInfo(TIMEZONE)
        day_start = datetime(d.year, d.month, d.day, tzinfo=tz)
        found = []
        for ev in recurring_ical_events.of(cal).between(day_start, day_start + timedelta(days=1)):
            title = str(ev.get("SUMMARY", "")).strip()
            if not title:
                continue
            venue = str(ev.get("LOCATION", "")).strip()
            start = ev["DTSTART"].dt
            if isinstance(start, datetime):
                start = start.astimezone(tz)
                found.append((1, start, (event_time(start), title, venue)))
            else:
                found.append((0, day_start, ("", title, venue)))
        found.sort(key=lambda e: (e[0], e[1]))
        return [row for _, _, row in found[:2]] or None
    except Exception as e:
        print(f"calendar fetch failed, using almanac lines: {e}", file=sys.stderr)
        return None


def cn_number(n):
    if n <= 10:
        return CN_NUM[n - 1]
    if n < 20:
        return "十" + CN_NUM[n - 11]
    return CN_NUM[n // 10 - 1] + "十" + (CN_NUM[n % 10 - 1] if n % 10 else "")


def render(d, dark=False):
    hl = huangli(d)
    special = hl["is_sunday"] or hl["festivals"] or hl["jieqi_today"]
    weekend = d.weekday() >= 5
    # Dark theme: black page on weekdays, red page on weekends, white
    # ink. Accents shift to stay legible: yellow on black, plain white
    # on red, and red fields invert to white fields with red text.
    if dark and weekend:
        bg, ink, accent = RED, WHITE, WHITE
        seal_bg, seal_fg = WHITE, RED
        yi_chip, ji_chip = (WHITE, RED), (BLACK, WHITE)
    elif dark:
        bg, ink, accent = BLACK, WHITE, (YELLOW if special else WHITE)
        seal_bg, seal_fg = RED, WHITE
        yi_chip, ji_chip = (RED, WHITE), (WHITE, BLACK)
    else:
        bg, ink, accent = WHITE, BLACK, (RED if special else BLACK)
        seal_bg, seal_fg = RED, WHITE
        yi_chip, ji_chip = (RED, WHITE), (BLACK, WHITE)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    left, right = 120, W - 40

    # Hotspot label, top right corner above the seal. 16px at low
    # optical size: high contrast Fraunces hairlines drop out of the
    # threshold mask any smaller.
    f_spot = latin(16, 600, opsz=9)
    draw_text(img, (right, 38), HOTSPOT, f_spot, ink, anchor="rs")
    cx, cy = right - text_width(HOTSPOT, f_spot) - 18, 36
    for r in (9, 5):
        draw.arc([cx - r, cy - r, cx + r, cy + r], 225, 315, fill=ink, width=2)
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=ink)

    # Header: Aug 2026 left, horizontal ganzhi seal right
    draw_text(img, (left, 78), f"{hl['month_abbr']} {hl['year']}", latin(48, 800), ink, anchor="lm")
    sw, sh = 88, 40
    draw.rectangle([right - sw, 50, right, 50 + sh], fill=seal_bg)
    draw_text(img, (right - sw / 2, 50 + sh / 2 + 1), hl["ganzhi_year"], serif(26, 600), seal_fg,
              anchor="mm", tracking=6)

    # Hairline under header
    draw.rectangle([left, 118, right, 119], fill=ink)

    # The day: huge, flush left
    # Flush the numeral ink, not the pen position, to the left margin.
    # Side bearings vary per digit and getbbox does not report them, so
    # render to a scratch layer, measure the ink, then paste shifted.
    size, day = 430, str(hl["day"])
    while True:
        f_day = latin(size, 200, opsz=144)
        layer = Image.new("L", img.size, 0)
        ImageDraw.Draw(layer).text((40, 448), day, font=f_day, fill=255, anchor="ls")
        mask = layer.point(lambda p: 255 if p >= TEXT_THRESHOLD else 0)
        bb = mask.getbbox()
        if bb[2] - bb[0] <= right - left or size < 200:
            break
        size = int(size * (right - left) / (bb[2] - bb[0]))
    img.paste(accent, (left - bb[0], 0), mask)

    # Hairline above the weekday row
    draw.rectangle([left, 552, right, 553], fill=ink)

    # Weekday band: English left in accent color, Chinese right,
    # enclosed by hairlines above and below
    draw_text(img, (left, 586), hl["weekday_en"], latin(46, 800), accent, anchor="lm")
    draw_text(img, (right, 586), hl["weekday_cn"], serif(28, 500), ink, anchor="rm", tracking=8)
    draw.rectangle([left, 630, right, 631], fill=ink)

    # Lunar date and ganzhi pillars
    draw_text(img, (left, 690), hl["lunar_md"], serif(58, 600), ink, anchor="lm", tracking=6)
    sub = f"{hl['ganzhi_year']}{hl['zodiac']}年  {hl['ganzhi_month']}月  {hl['ganzhi_day']}日"
    draw_text(img, (left, 758), sub, serif(25, 400), ink, anchor="lm", tracking=2)

    # Festival (red tag) or solar term (yellow tag) or day count line
    line3, tag_bg, tag_fg = None, YELLOW, BLACK
    if hl["jieqi_today"]:
        line3 = hl["jieqi_today"]
    if hl["festivals"]:
        line3, tag_bg, tag_fg = hl["festivals"][0], seal_bg, seal_fg
    if line3:
        f_tag = serif(24, 600)
        tw = text_width(line3, f_tag, tracking=4)
        pad = 12
        y0, y1 = 788, 826
        draw.rectangle([left, y0, left + tw + 2 * pad, y1], fill=tag_bg)
        draw_text(img, (left + pad, (y0 + y1) / 2 + 1), line3, f_tag, tag_fg, anchor="lm", tracking=4)
    elif hl["jieqi_line"]:
        draw_text(img, (left, 807), hl["jieqi_line"], serif(24, 400), ink, anchor="lm", tracking=3)

    # Bottom block: the day's calendar events as a three column table
    # (time, title, venue with a map pin) when the ICS feed has events
    # today, the yi ji almanac rows otherwise. No rules between the
    # columns, alignment does the work.
    def fit(s, f, maxw):
        if text_width(s, f) <= maxw:
            return s
        while s and text_width(s + "..", f) > maxw:
            s = s[:-1]
        return s.rstrip() + ".."

    events = calendar_events(d)
    if events:
        # Latin set in the Latin face, CJK in the serif, on a shared
        # baseline. 22px CJK minimum: dense glyphs clog any smaller.
        f_when = DuoFont(latin(22, 700), serif(23, 500), LATIN_COVER)
        f_title = DuoFont(latin(22, 400), serif(23, 400), LATIN_COVER)
        f_venue = DuoFont(latin(19, 400), serif(22, 400), LATIN_COVER)
        title_x = left + 96
        # Hairline separating the almanac block from the events table
        draw.rectangle([left, 862, right, 863], fill=ink)
        # Bottom anchored: tighter leading closes the gap upward so the
        # last baseline keeps the 942 ink bound.
        for i, (when, title, venue) in enumerate(events):
            base = 892 + i * 40
            if when:
                draw_text(img, (left, base), when, f_when, ink, anchor="ls")
            venue = fit(venue, f_venue, 170) if venue else ""
            venue_w = text_width(venue, f_venue)
            title_max = right - title_x - (venue_w + 34 if venue else 0)
            draw_text(img, (title_x, base), fit(title, f_title, title_max),
                      f_title, ink, anchor="ls")
            if venue:
                draw_text(img, (right, base), venue, f_venue, ink, anchor="rs")
                px = right - venue_w - 16
                cy = base - 11
                draw.ellipse([px - 6, cy - 6, px + 6, cy + 6], fill=ink)
                draw.polygon([(px - 5, cy + 3), (px + 5, cy + 3), (px, base)], fill=ink)
                draw.ellipse([px - 2, cy - 2, px + 2, cy + 2], fill=bg)
        return img

    f_chip = sans_sc(21, 700)
    f_items = serif(23, 400)
    # 22px minimum: dense nayin glyphs (the rain radical pair) clog
    # into blobs any smaller.
    f_aside = DuoFont(latin(20, 500), serif(22, 400), LATIN_COVER)
    asides = [f"{hl['chong']}  {hl['sha']}", hl["nayin"]]
    rows = [("宜", hl["yi"], yi_chip, asides[0]), ("忌", hl["ji"], ji_chip, asides[1])]
    chip = 32

    def aside_room(items_line):
        return right - (left + chip + 18 + text_width(items_line, f_items)) - 24

    for i, (label, items, (chip_bg, chip_fg), aside) in enumerate(rows):
        ry = 856 + i * 52
        draw.rectangle([left, ry, left + chip, ry + chip], fill=chip_bg)
        draw_text(img, (left + chip / 2, ry + chip / 2 + 1), label, f_chip, chip_fg, anchor="mm")
        # The aside outranks the almanac list: shed yi ji items, never
        # below two, before resorting to truncating the aside.
        while aside and len(items) > 2 and text_width(aside, f_aside) > aside_room("  ".join(items)):
            items = items[:-1]
        line = "  ".join(items)
        draw_text(img, (left + chip + 18, ry + chip / 2 + 1), line, f_items, ink, anchor="lm")
        aside = fit(aside, f_aside, aside_room(line))
        draw_text(img, (right, ry + chip / 2 + 7), aside, f_aside, ink, anchor="rs")
    return img


def pick_page():
    """Which page to render: the PAGE environment variable (one shot,
    for testing) beats "page" in settings.json. Unknown values fall
    back to the almanac so a bad edit never blanks the wall."""
    page = (os.environ.get("PAGE", "").strip()
            or str(SETTINGS.get("page", "")).strip()).lower()
    if page in PAGES or not page:
        return page or "almanac"
    print(f"warning: unknown page {page!r}, using almanac", file=sys.stderr)
    return "almanac"


def render_page(page, d, dark):
    """Non-almanac pages live in pages/<name>.py, each exposing
    render(date, hl, settings) -> Image, imported lazily so a missing
    or broken page module can never kill the render; any failure falls
    back to the almanac. Non-almanac pages always render light."""
    if page != "almanac":
        try:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            module = importlib.import_module(f"pages.{page}")
            return module.render(d, huangli(d), SETTINGS), page
        except Exception as e:
            print(f"warning: page {page} failed ({e}), using almanac",
                  file=sys.stderr)
    return render(d, dark), "almanac"


def pack(img):
    """Portrait 640x960 to native 960x640 2bpp stream."""
    native = img.transpose(Image.ROTATE_90 if FPC_AT_BOTTOM else Image.ROTATE_270)
    px = native.load()
    data = bytearray(960 * 640 // 4)
    i = 0
    for y in range(640):
        for x in range(0, 960, 4):
            b = 0
            for k in range(4):
                p = px[x + k, y]
                if p not in PALETTE:
                    raise ValueError(f"non palette pixel {p} at {x + k},{y}")
                b = (b << 2) | PALETTE[p]
            data[i] = b
            i += 1
    return bytes(data)


def main():
    now = datetime.now(ZoneInfo(TIMEZONE))
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else now.date()
    # The evening render (18:35 SGT cron) goes dark until the midnight
    # render flips it back. Overrides, strongest first: DARK=1/DARK=0
    # (one shot, set by the Run workflow button or locally), then
    # "mode": "dark"/"light" in settings.json (persistent), then clock.
    forced = os.environ.get("DARK", "").strip()
    mode_setting = str(SETTINGS.get("mode", "")).strip().lower()
    if forced:
        dark = forced == "1"
    elif mode_setting in ("dark", "light"):
        dark = mode_setting == "dark"
    else:
        dark = now.hour >= 18
    img, page = render_page(pick_page(), d, dark)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / "preview.png")
    (OUT / "tylendar.bin").write_bytes(pack(img))
    mode = ("dark" if dark else "light") if page == "almanac" else page
    print(f"rendered {d} ({mode}) -> {OUT / 'tylendar.bin'} ({(OUT / 'tylendar.bin').stat().st_size} bytes)")


if __name__ == "__main__":
    main()
