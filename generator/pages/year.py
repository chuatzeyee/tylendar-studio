"""Year page: memento mori year-progress grid.

One square per day of the shown year in a strict 14 column lattice.
FILL means the day has passed, OUTLINE means it is still to come;
black is an ordinary day, yellow marks a festival, red is today.
Milestone labels sit on a left rail with hairline leaders pointing at
their square's row.
"""

import os
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont
from lunar_python import Lunar

from pages.month import HOLIDAY_CN, holidays

from generate import (W, H, BLACK, WHITE, RED, YELLOW, draw_text, text_width,
                      latin, serif, DuoFont, LATIN, LATIN_COVER, TIMEZONE,
                      TEXT_THRESHOLD, MONTH_ABBR, WEEKDAY_EN, cn_number)

L, R = 60, 580
COLS, CELL, GAP = 14, 18, 4
PITCH = CELL + GAP
GRID_W = COLS * PITCH - GAP
GX0 = R - GRID_W
RULE_Y, GY0 = 244, 278
INK_TOP = 82


def fraunces(size, weight=450, opsz=32):
    """Fraunces directly: Canela has no percent glyph, and small-opsz
    Fraunces carries the italic-feel footer line."""
    font = ImageFont.truetype(LATIN, size)
    font.set_variation_by_axes([opsz, weight, 0, 0])
    return font


def ink(img, parts, color, left=None, right=None, top=None):
    """Paste baseline-set text so the ink bbox itself lands on the given
    page coordinates (optical alignment, not font-metric alignment)."""
    layer = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer)
    for x, text, font in parts:
        d.text((x, 300), text, font=font, fill=255, anchor="ls")
    mask = layer.point(lambda p: 255 if p >= TEXT_THRESHOLD else 0)
    b = mask.getbbox()
    w, h = b[2] - b[0], b[3] - b[1]
    dst_x = left if left is not None else right - w
    dst_y = top if top is not None else b[1]
    img.paste(color, (dst_x, dst_y), mask.crop(b))
    return (dst_x, dst_y, dst_x + w, dst_y + h)


def cell_xy(doy):
    row, col = divmod(doy - 1, COLS)
    return GX0 + col * PITCH, GY0 + row * PITCH


# lunar_python returns simplified zodiac names; map both scripts.
ZODIAC_EN = {"鼠": "RAT", "牛": "OX", "虎": "TIGER", "兔": "RABBIT",
             "龍": "DRAGON", "龙": "DRAGON", "蛇": "SNAKE",
             "馬": "HORSE", "马": "HORSE", "羊": "GOAT", "猴": "MONKEY",
             "雞": "ROOSTER", "鸡": "ROOSTER", "狗": "DOG",
             "豬": "PIG", "猪": "PIG"}
MILESTONE_EN = {"元旦": "NEW YEAR", "春節": "LUNAR NEW YEAR",
                "中秋": "MID AUTUMN", "今日": "TODAY"}


def next_event(d):
    """First upcoming ICS_URL event after today, (date, summary) or
    None. No feed or a broken fetch means the holiday countdown."""
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
        start = datetime(d.year, d.month, d.day, tzinfo=tz) + timedelta(days=1)
        best = None
        for ev in recurring_ical_events.of(cal).between(start, start + timedelta(days=365)):
            s = ev["DTSTART"].dt
            if isinstance(s, datetime):
                s = s.astimezone(tz).date()
            name = str(ev.get("SUMMARY", "")).strip()
            if name and (best is None or s < best[0]):
                best = (s, name)
        return best
    except Exception as e:
        print(f"calendar fetch failed, holiday countdown instead: {e}", file=sys.stderr)
        return None


def footer_line(d, hols, lang, source):
    """The footer under the chosen source; any source that cannot
    deliver falls back to the public holiday countdown."""
    if source == "weather":
        try:
            from pages.weather import forecast_24h, outlook_cn
            high, low, text = forecast_24h()
            if lang == "cn":
                return f"日{high}度 夜{low}度 {outlook_cn(text)}"
            return f"{high} / {low} C, {text.upper()}"
        except Exception as e:
            print(f"weather fetch failed, holiday countdown instead: {e}", file=sys.stderr)
    if source == "event":
        ev = next_event(d)
        if ev:
            n = (ev[0] - d).days
            name = ev[1][:28]
            if lang == "cn":
                return f"距{name}尚有{n}日"
            return f"{n} {'DAY' if n == 1 else 'DAYS'} TO {name.upper()}"
    future = sorted(k for k in hols if date.fromisoformat(k) > d)
    if not future:
        return None
    n = (date.fromisoformat(future[0]) - d).days
    name = hols[future[0]].replace(" (Observed)", "")
    if lang == "cn":
        return f"距{HOLIDAY_CN.get(name, name)}尚有{n}日"
    return f"{n} {'DAY' if n == 1 else 'DAYS'} TO {name.upper()}"


def milestones(year):
    """(day of year, label) for yuandan, chunjie, and mid autumn."""
    out = [(1, "元旦")]
    for lm, ld, label in ((1, 1, "春節"), (8, 15, "中秋")):
        s = Lunar.fromYmd(year, lm, ld).getSolar()
        doy = date(s.getYear(), s.getMonth(), s.getDay()).timetuple().tm_yday
        out.append((doy, label))
    return out


def render(d, hl, settings):
    lang = settings.get("year_lang", "bilingual")
    if lang not in ("en", "cn"):
        lang = "bilingual"
    total = date(d.year, 12, 31).timetuple().tm_yday
    today = d.timetuple().tm_yday
    fests = milestones(d.year)
    hols = holidays()

    img = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(img)

    # Eyebrows: date left, ordinal right, tiny tracked caps. 17px at
    # 650: any smaller and the 3 loses its top curve in the threshold
    # mask, so 365 reads 565.
    f_brow = latin(17, 650)
    f_brow_cn = DuoFont(f_brow, serif(18, 600), LATIN_COVER)
    if lang == "cn":
        brow = cn_number(d.month) + "月" + cn_number(d.day) + "日 " + hl["weekday_cn"]
        draw_text(img, (L, 44), brow, f_brow_cn, BLACK, anchor="ls", tracking=2)
        draw_text(img, (R, 44), f"第{today}日 共{total}日", f_brow_cn, BLACK,
                  anchor="rs", tracking=2)
    else:
        brow = f"{WEEKDAY_EN[d.weekday()][:3]} {d.day} {hl['month_abbr'].upper()}"
        draw_text(img, (L, 44), brow, f_brow, BLACK, anchor="ls", tracking=2)
        draw_text(img, (R, 44), f"DAY {today} OF {total}", f_brow, BLACK,
                  anchor="rs", tracking=2)

    # Giant year left and the one red statistic right, ink tops matched.
    f_year = latin(120, 250, opsz=144)
    ink(img, [(0, str(d.year), f_year)], BLACK, left=L, top=INK_TOP)

    pct = round(today / total * 100)
    f_num, f_sign = latin(92, 250), fraunces(46, 500, opsz=144)
    nw = text_width(str(pct), f_num)
    pct_bb = ink(img, [(0, str(pct), f_num), (nw + 8, "%", f_sign)], RED,
                 right=R, top=INK_TOP)

    # Stacked counts under the statistic, right-aligned as a block; the
    # ganzhi year on the left shares the block's last baseline.
    f_count = DuoFont(latin(18, 500), serif(19, 500), LATIN_COVER)
    b1 = pct_bb[3] + 34
    cx = R + 3          # the closing "day" glyph carries 3px of side bearing
    if lang == "en":
        draw_text(img, (cx, b1), f"{today} DAYS PAST", f_count, BLACK,
                  anchor="rs", tracking=2)
        draw_text(img, (cx, b1 + 28), f"{total - today} DAYS LEFT", f_count, BLACK,
                  anchor="rs", tracking=2)
        zodiac = ZODIAC_EN.get(hl["zodiac"])
        if zodiac:
            draw_text(img, (L, b1 + 28), f"YEAR OF THE {zodiac}", f_brow, BLACK,
                      anchor="ls", tracking=2)
    else:
        draw_text(img, (cx, b1), f"已過 {today} 日", f_count, BLACK, anchor="rs", tracking=2)
        draw_text(img, (cx, b1 + 28), f"餘 {total - today} 日", f_count, BLACK,
                  anchor="rs", tracking=2)
        draw_text(img, (L, b1 + 28), hl["ganzhi_year"] + "年", serif(24, 500), BLACK,
                  anchor="ls", tracking=6)

    dr.rectangle([L, RULE_Y, R - 1, RULE_Y + 1], fill=BLACK)

    # The grid, flush right; the label rail owns the left half.
    fest_days = {doy for doy, _ in fests}
    fest_days |= {date.fromisoformat(k).timetuple().tm_yday
                  for k in hols if int(k[:4]) == d.year}
    for n in range(1, total + 1):
        x, y = cell_xy(n)
        box = [x, y, x + CELL - 1, y + CELL - 1]
        past = n <= today
        if n == today:
            dr.rectangle(box, fill=RED)
        elif n in fest_days and past:
            dr.rectangle(box, fill=YELLOW)
        elif n in fest_days:
            dr.rectangle(box, outline=YELLOW, width=2)
        elif past:
            dr.rectangle(box, fill=BLACK)
        else:
            dr.rectangle(box, outline=BLACK, width=1)

    # Left rail: label then a hairline tick, both dead-centred on the
    # target square's row. When two labels land on one row the later
    # one drops a full pitch (half a row still overlaps 18px glyphs);
    # the push is monotone so label chains never collide either.
    f_label = latin(15, 650) if lang == "en" else serif(18, 500)
    last_ty = None
    labels = sorted(fests + [(today, "今日")], key=lambda m: (m[0], m[1] == "今日"))
    for n, label in labels:
        _, y = cell_xy(n)
        ty = y + CELL // 2 - 1            # 2px tick, centred on the cell
        if last_ty is not None and ty - last_ty < PITCH:
            ty = last_ty + PITCH
        last_ty = ty
        color = RED if label == "今日" else BLACK
        text = MILESTONE_EN.get(label, label) if lang == "en" else label
        draw_text(img, (L, ty + 1), text, f_label, color, anchor="lm", tracking=2)
        tx = L + text_width(text, f_label, tracking=2) + 10
        dr.rectangle([tx, ty, GX0 - 10, ty + 1], fill=color)

    # The lone last square of the year gets its bookend label, cap-height
    # optically centred on the square (12px caps in an 18px cell).
    xe, ye = cell_xy(total)
    if lang == "cn":
        draw_text(img, (xe + CELL + 12, ye + CELL - 3), "12月31日", f_brow_cn,
                  BLACK, anchor="ls", tracking=2)
    else:
        draw_text(img, (xe + CELL + 12, ye + CELL - 3), "31 DEC", f_brow, BLACK,
                  anchor="ls", tracking=2)

    # Footer countdown under the chosen source. 20px at 450: at 19px
    # the small-opsz glyphs clog in the threshold mask.
    line = footer_line(d, hols, lang, settings.get("year_footer", "holidays"))
    if line:
        f_foot = fraunces(20, 450, opsz=9)
        if any(ord(ch) > 126 for ch in line):
            f_foot = DuoFont(f_foot, serif(20, 500), LATIN_COVER)
        draw_text(img, ((L + R) / 2, 934), line, f_foot, BLACK, anchor="ms")
    return img
