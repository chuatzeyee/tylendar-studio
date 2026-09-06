"""Month page: full-month planning grid.

Monday-first calendar for the shown month. Every cell carries the day
numeral and a lunar day label; Sundays and Singapore public holidays
set in red, a red frame on today. Solar terms, festivals, and holiday
names replace the lunar label on their days, major festivals earn a
small yellow chip, ICS events show as dots. Footer: the month's lunar
span and a next-month preview.
"""

import calendar
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw
from lunar_python import Solar

from generate import (W, H, BLACK, WHITE, RED, YELLOW, draw_text, text_width,
                      latin, serif, DuoFont, LATIN_COVER, TIMEZONE,
                      cn_number, to_traditional)

L, R = 60, 580
XS = [round(L + i * (R - L) / 7) for i in range(8)]
BASE_Y = 150
SEAL_Y = 60
RULE_Y = 180
WD_BASE = 208
GRID_TOP = 222
GRID_BOT = 810
SPAN_BASE = GRID_BOT + 34
FOOT_RULE = SPAN_BASE + 23
FOOT_BASE = FOOT_RULE + 37

WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Major festivals earn a quiet yellow chip and keep their lunar label;
# any other lunar festival replaces the label in red.
MAJOR = ("除夕", "春節", "元宵", "端午", "中元", "中秋", "重陽")
HOLIDAY_CN = {
    "New Year's Day": "元旦",
    "Chinese New Year": "新年",
    "Hari Raya Puasa": "開齋節",
    "Good Friday": "受難節",
    "Labour Day": "勞動節",
    "Vesak Day": "衛塞節",
    "Hari Raya Haji": "哈芝節",
    "National Day": "國慶日",
    "Deepavali": "屠妖節",
    "Christmas Day": "聖誕節",
}


def holidays():
    """Gazetted Singapore public holidays, ISO date -> official name.
    A missing or bad file costs the red marks, never the render."""
    path = Path(__file__).resolve().parent.parent / "data" / "sg_holidays.json"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, OSError) as e:
        print(f"warning: sg_holidays.json ignored ({e})", file=sys.stderr)
        return {}


def holiday_label(name):
    if name.endswith(" (Observed)"):
        return "補假"
    return HOLIDAY_CN.get(name)


def short(fest):
    return fest[:-1] if len(fest) > 2 and fest.endswith("節") else fest


def day_facts(y, m, day):
    """(lunar label, jieqi, major chip, minor festival) for one day.
    The label is the lunar day, or the lunar month name on chuyi."""
    lunar = Solar.fromYmd(y, m, day).getLunar()
    fests = [short(to_traditional(f)) for f in lunar.getFestivals()]
    if "中元節" in to_traditional(list(lunar.getOtherFestivals())):
        fests.append("中元")
    chip = next((f for f in fests if f in MAJOR), None)
    minor = next((f for f in fests if f not in MAJOR), None)
    day_cn = to_traditional(lunar.getDayInChinese())
    if day_cn == "初一":
        day_cn = to_traditional(lunar.getMonthInChinese()) + "月"
    return day_cn, to_traditional(lunar.getJieQi()) or None, chip, minor


def lunar_md(y, m, day):
    lunar = Solar.fromYmd(y, m, day).getLunar()
    return to_traditional(lunar.getMonthInChinese() + "月" + lunar.getDayInChinese())


def next_highlight(y, m, hols):
    """Next month's headline: the first public holiday, else the first
    major festival, else the first solar term."""
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    days = calendar.monthrange(y, m)[1]
    fest = jq = None
    for day in range(1, days + 1):
        name = hols.get(f"{y:04d}-{m:02d}-{day:02d}", "")
        cn = holiday_label(name) if name else None
        if cn and cn != "補假":
            return MONTHS[m - 1], f"{cn} {m}月{day}日"
        label, jieqi, chip, minor = day_facts(y, m, day)
        if chip and not fest:
            fest = f"{chip} {m}月{day}日"
        if jieqi and not jq:
            jq = f"{jieqi} {m}月{day}日"
    return MONTHS[m - 1], fest or jq or ""


def month_dots(y, m, days):
    """Events per day from the ICS_URL feed, capped at two dots. No
    feed or a broken fetch means no dots, never a broken page."""
    url = os.environ.get("ICS_URL", "").strip()
    if not url:
        return {}
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
        start = datetime(y, m, 1, tzinfo=tz)
        counts = {}
        for ev in recurring_ical_events.of(cal).between(start, start + timedelta(days=days)):
            s = ev["DTSTART"].dt
            if isinstance(s, datetime):
                s = s.astimezone(tz).date()
            if (s.year, s.month) == (y, m):
                counts[s.day] = min(counts.get(s.day, 0) + 1, 2)
        return counts
    except Exception as e:
        print(f"calendar fetch failed, no event dots: {e}", file=sys.stderr)
        return {}


def ink(text, font, tracking=0):
    """Thresholded ink mask + bbox for optical (ink edge) alignment.
    Scratch baseline sits at y=400."""
    tmp = Image.new("RGB", (W, H), WHITE)
    draw_text(tmp, (80, 400), text, font, BLACK, anchor="ls", tracking=tracking)
    mask = tmp.convert("L").point(lambda p: 255 if p < 128 else 0)
    return mask, mask.getbbox()


def render(d, hl, settings):
    y, m = d.year, d.month
    first, days = calendar.monthrange(y, m)
    sunday_first = settings.get("month_week_start") == "sunday"
    off = (first + 1) % 7 if sunday_first else first
    wds = WEEKDAYS[-1:] + WEEKDAYS[:-1] if sunday_first else WEEKDAYS
    sun_col = 0 if sunday_first else 6
    n_rows = (off + days + 6) // 7
    ys = [GRID_TOP + round(k * (GRID_BOT - GRID_TOP) / n_rows) for k in range(n_rows + 1)]
    hols = holidays()
    dots = month_dots(y, m, days)

    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Masthead on one optical baseline: English month, CJK month, year.
    # Long month names shrink until the group clears the year block.
    m_cjk, bb_c = ink(cn_number(m) + "月", serif(40, 600), tracking=8)
    m_yr, bb_y = ink(str(y), latin(30, 650), tracking=6)
    fixed = 26 + (bb_c[2] - bb_c[0]) + 24 + (bb_y[2] - bb_y[0])
    size = 100
    while True:
        m_eng, bb_e = ink(MONTHS[m - 1], latin(size, 250, opsz=144))
        ew = bb_e[2] - bb_e[0]
        if ew + fixed <= R - L or size < 60:
            break
        size = int(size * (R - L - fixed) / ew)
    img.paste(BLACK, (L - bb_e[0], BASE_Y - 400), m_eng)
    img.paste(BLACK, (L + ew + 26 - bb_c[0], BASE_Y - bb_c[3]), m_cjk)
    img.paste(BLACK, (R - bb_y[2], BASE_Y - bb_y[3]), m_yr)

    # Red ganzhi seal, top right
    sw, sh = 88, 40
    draw.rectangle([R - sw, SEAL_Y, R, SEAL_Y + sh], fill=RED)
    draw_text(img, (R - sw / 2, SEAL_Y + sh / 2 + 1), hl["ganzhi_year"], serif(26, 600),
              WHITE, anchor="mm", tracking=6)

    draw.rectangle([L, RULE_Y, R, RULE_Y + 1], fill=BLACK)

    f_wd = latin(16, 650)
    for i, wd in enumerate(wds):
        draw_text(img, (XS[i] + 8, WD_BASE), wd, f_wd, RED if i == sun_col else BLACK,
                  anchor="ls", tracking=1)

    for yy in ys:
        draw.rectangle([L, yy, R, yy], fill=BLACK)

    f_num = latin(27, 450)
    # 17px/600 keeps the horizontal hairline of yi above the mask
    # threshold while leaving dense glyphs open (700 clogs them)
    f_lunar = serif(17, 600)
    f_chip = serif(15, 700)

    for day in range(1, days + 1):
        row, col = divmod(off + day - 1, 7)
        x0, x1, y0, y1 = XS[col], XS[col + 1], ys[row], ys[row + 1]
        label, jieqi, chip, minor = day_facts(y, m, day)
        hol = hols.get(f"{y:04d}-{m:02d}-{day:02d}")
        is_today = day == d.day
        color = RED if (col == sun_col or hol or is_today) else BLACK

        # today: crisp 2px red frame exactly on the cell bounds, drawn
        # over the black hairlines
        if is_today:
            draw.rectangle([x0, y0, x1, y1], outline=RED, width=2)

        hol_cn = holiday_label(hol) if hol else None
        lcolor = color
        if hol_cn and not chip:
            label = hol_cn
        elif minor:
            label, lcolor = minor, RED
        elif jieqi:
            label = jieqi
        draw_text(img, (x0 + 8, y0 + 10), str(day), f_num, color, anchor="la")
        draw_text(img, (x0 + 8, y0 + 46), label, f_lunar, lcolor, anchor="la", tracking=1)

        # chip and dots share the band above the cell's bottom rule;
        # a chip day is already marked, so the chip wins
        if chip:
            tw = text_width(chip, f_chip, tracking=2)
            cx0, cy0 = x0 + 8, y1 - 29
            draw.rectangle([cx0, cy0, cx0 + tw + 14, cy0 + 22], fill=YELLOW)
            draw_text(img, (cx0 + 7, cy0 + 12), chip, f_chip, BLACK, anchor="lm", tracking=2)
        elif dots.get(day):
            cy = y1 - 18
            for j in range(dots[day]):
                cx = x0 + 11 + j * 13
                draw.ellipse([cx - 3, cy - 3, cx + 2, cy + 2], fill=BLACK)

    # Footer: lunar span of the month as a labeled ledger line
    draw_text(img, (L, SPAN_BASE), "農曆", serif(17, 600), BLACK, anchor="ls", tracking=4)
    span = f"{lunar_md(y, m, 1)} 至 {lunar_md(y, m, days)}"
    draw_text(img, (R, SPAN_BASE), span, serif(17, 500), BLACK, anchor="rs", tracking=3)

    draw.rectangle([L, FOOT_RULE, R, FOOT_RULE], fill=BLACK)

    # Next-month preview: Latin bold lead, serif CJK, small-caps place
    nm_name, nm_line = next_highlight(y, m, hols)
    f_next = latin(21, 700)
    draw_text(img, (L, FOOT_BASE), nm_name, f_next, BLACK, anchor="ls")
    if nm_line:
        f_foot = DuoFont(latin(20, 450), serif(21, 500), LATIN_COVER)
        draw_text(img, (L + text_width(nm_name, f_next) + 16, FOOT_BASE), nm_line,
                  f_foot, BLACK, anchor="ls", tracking=1)
    return img
