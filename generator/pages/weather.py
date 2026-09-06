"""Tylendar weather page: Singapore island weather broadsheet.

Masthead, sun-cloud-rain glyph, giant Canela day high and night low,
outlook row with quiet UV and PM2.5 lines, 12 hour rain chance strip.
Live data from NEA (data.gov.sg) and open-meteo at render time; any
fetch failure raises and generate.py falls back to the almanac.
"""

import json
import math
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw

from generate import W, H, BLACK, WHITE, RED, YELLOW, draw_text, text_width, latin, serif

LEFT, RIGHT = 60, W - 60
TIMEOUT = 10

NEA_24H = "https://api-open.data.gov.sg/v2/real-time/api/twenty-four-hr-forecast"
NEA_UV = "https://api-open.data.gov.sg/v2/real-time/api/uv"
NEA_PM25 = "https://api-open.data.gov.sg/v2/real-time/api/pm25"
OPEN_METEO = ("https://api.open-meteo.com/v1/forecast?latitude=1.29&longitude=103.85"
              "&hourly=precipitation_probability&timezone=Asia%2FSingapore")

# NEA standard forecast phrases in traditional Chinese. Keys are
# lowercase with the (Day)/(Night) suffix already stripped.
FORECAST_CN = {
    "fair": "天晴",
    "fair and warm": "晴暖",
    "partly cloudy": "少雲",
    "cloudy": "多雲",
    "overcast": "天陰",
    "hazy": "煙霞",
    "slightly hazy": "輕微煙霞",
    "windy": "有風",
    "mist": "薄霧",
    "fog": "大霧",
    "drizzle": "毛毛雨",
    "light rain": "小雨",
    "moderate rain": "中雨",
    "heavy rain": "大雨",
    "passing showers": "短暫陣雨",
    "light showers": "小陣雨",
    "showers": "陣雨",
    "heavy showers": "大陣雨",
    "thundery showers": "雷陣雨",
    "heavy thundery showers": "大雷雨",
    "heavy thundery showers with gusty winds": "狂風雷暴",
    "morning thundery showers": "早晨雷陣雨",
    "afternoon thundery showers": "午後雷陣雨",
    "late afternoon thundery showers": "傍晚雷陣雨",
    "early morning thundery showers": "清晨雷陣雨",
    "pre-dawn thundery showers": "凌晨雷陣雨",
}


def fetch_json(url):
    # data.gov.sg rejects the default Python-urllib User-Agent with 403.
    req = urllib.request.Request(url, headers={"User-Agent": "Tylendar/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def forecast_24h():
    general = fetch_json(NEA_24H)["data"]["records"][0]["general"]
    text = general["forecast"]["text"].replace("(Day)", "").replace("(Night)", "").strip()
    return round(general["temperature"]["high"]), round(general["temperature"]["low"]), text


def outlook_cn(text):
    key = text.lower()
    if key in FORECAST_CN:
        return FORECAST_CN[key]
    wet = any(w in key for w in ("rain", "shower", "thunder"))
    return "今日有雨" if wet else "天氣多變"


def uv_index():
    entries = fetch_json(NEA_UV)["data"]["records"][0]["index"]
    return int(max(entries, key=lambda e: e["hour"])["value"])


def uv_band(v):
    if v <= 2:
        return "LOW"
    if v <= 5:
        return "MODERATE"
    if v <= 7:
        return "HIGH"
    if v <= 10:
        return "VERY HIGH"
    return "EXTREME"


def pm25_average():
    readings = fetch_json(NEA_PM25)["data"]["items"][0]["readings"]["pm25_one_hourly"]
    return round(sum(readings.values()) / len(readings))


def pm25_band(v):
    if v <= 55:
        return "NORMAL"
    if v <= 150:
        return "ELEVATED"
    return "HIGH"


def rain_next_12h(now):
    """Hourly rain probability for the render hour plus twelve, so the
    strip spans 12 hours with a bar on both ends."""
    hourly = fetch_json(OPEN_METEO)["hourly"]
    i = hourly["time"].index(now.strftime("%Y-%m-%dT%H:00"))
    pct = hourly["precipitation_probability"][i:i + 13]
    if len(pct) < 13 or any(p is None for p in pct):
        raise ValueError("incomplete rain probabilities")
    hours = [datetime.fromisoformat(t).hour for t in hourly["time"][i:i + 13]]
    return hours, [int(p) for p in pct]


def hour_label(h):
    return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"


def cap_height(text, font):
    return -font.getbbox(text, anchor="ls")[1]


def pct_sign(draw, x, top, h, color, stroke=2):
    """Hand-drawn percent sign; the Canela subset has no % glyph."""
    r = round(h * 0.30)
    draw.ellipse([x, top, x + 2 * r, top + 2 * r], outline=color, width=stroke)
    draw.ellipse([x + h * 0.62 - 2 * r + 4, top + h - 2 * r,
                  x + h * 0.62 + 4, top + h], outline=color, width=stroke)
    draw.line([x + h * 0.60, top + 1, x + 2, top + h - 1], fill=color, width=stroke)


def sky_glyph(draw):
    """Sun behind cloud with two rows of rain dashes, centered alone."""
    scx, scy, sr = 380, 232, 52  # sun sits low enough that no ray grazes the rule
    for k in (0, 1, 2, 3, 5, 6, 7):  # no left ray: it would graze the cloud
        a = math.radians(k * 45)
        draw.line([scx + math.cos(a) * (sr + 14), scy + math.sin(a) * (sr + 14),
                   scx + math.cos(a) * (sr + 36), scy + math.sin(a) * (sr + 36)],
                  fill=YELLOW, width=9)
    draw.ellipse([scx - sr, scy - sr, scx + sr, scy + sr], fill=YELLOW)
    cloud = [(186, 217, 310, 341), (290, 246, 386, 342), (173, 282, 428, 356)]
    st = 5  # heavier icon stroke, uniform with the rain dashes
    for fill, s in ((BLACK, 0), (WHITE, st)):
        for x0, y0, x1, y1 in cloud:
            draw.ellipse([x0 + s, y0 + s, x1 - s, y1 - s], fill=fill)
    for y0, xs in ((366, range(221, 402, 60)), (394, range(251, 372, 60))):
        for x in xs:
            draw.line([x, y0, x - 8, y0 + 20], fill=BLACK, width=st)


def draw_temps(img, draw, hi, lo):
    """Giant high and low on a shared baseline, degree rings at cap
    height, hand-drawn slash centered in the gap."""
    base = 592
    f_hi, f_lo = latin(215, 250), latin(125, 250)
    hi_s, lo_s = str(hi), str(lo)
    hi_w, lo_w = text_width(hi_s, f_hi), text_width(lo_s, f_lo)
    draw_text(img, (LEFT, base), hi_s, f_hi, RED, anchor="ls")
    r1x = LEFT + hi_w + 10
    cap_hi = cap_height(hi_s, f_hi)
    draw.ellipse([r1x, base - cap_hi, r1x + 28, base - cap_hi + 28], outline=RED, width=5)
    hi_end = r1x + 28
    lo_x = RIGHT - 18 - 8 - lo_w
    draw_text(img, (lo_x, base), lo_s, f_lo, BLACK, anchor="ls")
    cap_lo = cap_height(lo_s, f_lo)
    draw.ellipse([lo_x + lo_w + 8, base - cap_lo, lo_x + lo_w + 8 + 18,
                  base - cap_lo + 18], outline=BLACK, width=4)
    s_cx = (hi_end + lo_x) / 2
    s_h, s_dx, s_w = 125, 30, 7
    draw.polygon([(s_cx - s_dx / 2 - s_w / 2, base), (s_cx - s_dx / 2 + s_w / 2, base),
                  (s_cx + s_dx / 2 + s_w / 2, base - s_h),
                  (s_cx + s_dx / 2 - s_w / 2, base - s_h)], fill=BLACK)
    f_lab = latin(15, 600, opsz=9)
    draw_text(img, ((LEFT + hi_end) / 2, base + 36), "DAY HIGH", f_lab, BLACK,
              anchor="ms", tracking=3)
    draw_text(img, ((lo_x + RIGHT) / 2, base + 36), "NIGHT LOW", f_lab, BLACK,
              anchor="ms", tracking=3)


def draw_rain_strip(img, draw, hours, pct):
    f_eyebrow = latin(16, 600, opsz=9)
    draw_text(img, (LEFT, 818), "CHANCE OF RAIN", f_eyebrow, BLACK, anchor="ls", tracking=3)
    draw_text(img, (RIGHT, 818), "NEXT 12 HOURS", f_eyebrow, BLACK, anchor="rs", tracking=3)
    bar_base, bar_w, pitch, scale = 910, 24, 40, 0.64
    for i, p in enumerate(pct):
        cx, h = 80 + i * pitch, max(4, round(p * scale))
        draw.rectangle([cx - bar_w / 2, bar_base - h, cx + bar_w / 2, bar_base], fill=BLACK)
    draw.rectangle([LEFT, bar_base, RIGHT, bar_base + 1], fill=BLACK)

    peak_i = pct.index(max(pct))
    peak_cx = 80 + peak_i * pitch
    lab_base = bar_base - round(max(pct) * scale) - 12  # clearance above bar
    f_pk = latin(18, 700)
    pk = str(max(pct))
    pk_w = text_width(pk, f_pk)
    sx = peak_cx - (pk_w + 3 + 14 * 0.62 + 4) / 2
    draw_text(img, (sx, lab_base), pk, f_pk, BLACK, anchor="ls")
    pct_sign(draw, sx + pk_w + 3, lab_base - 14, 14, BLACK)

    f_hour = latin(15, 500, opsz=9)
    for i in (0, 12):
        if i != peak_i:
            draw_text(img, (80 + i * pitch, 936), hour_label(hours[i]), f_hour,
                      BLACK, anchor="ms")
    f_pkc = latin(15, 700, opsz=9)
    chip = hour_label(hours[peak_i])
    cw = text_width(chip, f_pkc, tracking=1) + 18
    ccx = min(max(peak_cx, LEFT + cw / 2), RIGHT - cw / 2)  # keep chip in margins
    draw.rectangle([ccx - cw / 2, 918, ccx + cw / 2, 942], fill=YELLOW)
    draw_text(img, (ccx, 930), chip, f_pkc, BLACK, anchor="mm", tracking=1)


def render(d, hl, settings):
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    hi, lo, outlook_en = forecast_24h()
    uv = uv_index()
    pm = pm25_average()
    hours, pct = rain_next_12h(now)

    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    def hairline(y):
        draw.rectangle([LEFT, y, RIGHT, y + 1], fill=BLACK)

    draw_text(img, (LEFT, 86), f"{hl['day']} {hl['month_abbr']} {hl['year']}",
              latin(48, 800), BLACK, anchor="lm")
    draw_text(img, (RIGHT, 70), hl["weekday_cn"], serif(24, 500), BLACK,
              anchor="rm", tracking=8)
    draw_text(img, (RIGHT, 104), hl["lunar_md"], serif(19, 400), BLACK,
              anchor="rm", tracking=4)
    hairline(126)

    sky_glyph(draw)
    draw_temps(img, draw, hi, lo)
    hairline(656)

    draw_text(img, (LEFT, 705), outlook_cn(outlook_en), serif(44, 600), BLACK,
              anchor="lm", tracking=5)
    draw_text(img, (LEFT, 753), outlook_en, latin(21, 400), BLACK, anchor="lm")
    f_stats = latin(17, 600, opsz=9)
    draw_text(img, (RIGHT, 705), f"UV {uv} {uv_band(uv)}", f_stats, BLACK,
              anchor="rm", tracking=2)
    draw_text(img, (RIGHT, 753), f"PM2.5 {pm} {pm25_band(pm)}", f_stats, BLACK,
              anchor="rm", tracking=2)
    hairline(792)

    draw_rain_strip(img, draw, hours, pct)
    return img
