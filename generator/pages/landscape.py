"""Landscape page: procedural flat-ink shanshui.

Three full-width ridge bands (far high on the page, mid crowned by a
pavilion, near shore with pines) stay continuous silhouettes; a wavy
white mist line erases their feet so mountains stand in mist and never
fragment. Below, calm hairline ripples, yellow sun glints, a fisherman
boat sitting on its own waterline, and a near bank tapering in from the
right margin. All randomness is seeded from the date, so each day gets
its own mountains and every render of a day is identical.
"""

import random

from PIL import Image, ImageDraw

from generate import W, H, BLACK, WHITE, RED, YELLOW, draw_text, latin, serif

LEFT, RIGHT = 60, W - 60


def value_noise(rng, spacing):
    knots = [rng.uniform(0.0, 1.0) for _ in range(W // spacing + 3)]
    out = []
    for x in range(W):
        i, fx = divmod(x, spacing)
        t = fx / spacing
        t = t * t * (3.0 - 2.0 * t)
        out.append(knots[i] * (1.0 - t) + knots[i + 1] * t)
    return out


def ridge(rng, mist_base, lift, p, spacings, band=16, wave=6):
    """Full-width ridge: crest stays >= band above the wavy mist line so
    the band never breaks; peaks taper near the frame edges, never
    chopped."""
    total, wgt = [0.0] * W, 1.0
    for s in spacings:
        total = [t + v * wgt for t, v in zip(total, value_noise(rng, s))]
        wgt *= 0.55
    lo, hi = min(total), max(total)
    mw1, mw2 = value_noise(rng, 300), value_noise(rng, 110)
    mist = [mist_base + (mw1[x] - 0.5) * 2 * wave + (mw2[x] - 0.5) * wave
            for x in range(W)]
    crest = []
    for x in range(W):
        e = min(x, W - 1 - x) / 150.0
        env = 0.5 + 0.5 * min(1.0, e * e * (3 - 2 * min(e, 1.0)))
        crest.append(mist[x] - band - lift * env * ((total[x] - lo) / (hi - lo)) ** p)
    return crest, mist


def fill_below(img, curve, color):
    pts = [(x, curve[x]) for x in range(W)] + [(W - 1, H), (0, H)]
    ImageDraw.Draw(img).polygon(pts, fill=color)


def pine(d, x, gy, h):
    top = gy - h
    d.line([(x, gy), (x, top + 2)], fill=BLACK, width=2)
    for i in range(3):
        f = (i + 1) / 4
        cy, span = top + f * (h - 3), 1 + f * h * 0.42
        d.polygon([(x - span, cy + 2), (x + span, cy + 2), (x, cy - h * 0.22)], fill=BLACK)


def crest_pines(d, rng, crest, count, x0, x1, hmin, hmax, avoid=(), clear=None,
                flat=0.55):
    placed, tries = [], 0
    while len(placed) < count and tries < count * 60:
        tries += 1
        x = rng.randint(x0, x1)
        if any(abs(x - a) < 50 for a in avoid) or any(abs(x - p) < 24 for p in placed):
            continue
        if abs(crest[min(x + 14, W - 1)] - crest[max(x - 14, 0)]) / 28 > flat:
            continue
        if min(crest[max(0, x - 22):x + 23]) < crest[x] - 4:   # canopy covered
            continue
        if max(crest[max(0, x - 8)], crest[min(x + 8, W - 1)]) > crest[x] + 6:
            continue                                           # sharp apex
        if clear is not None and crest[x] - hmax < clear[x] + 8:
            continue
        pine(d, x, crest[x] + 3, rng.randint(hmin, hmax))
        placed.append(x)


def pavilion(d, cx, gy):
    d.rectangle([cx - 20, gy - 3, cx + 20, gy], fill=BLACK)
    for px in (cx - 14, cx + 11):
        d.rectangle([px, gy - 20, px + 3, gy - 3], fill=BLACK)
    ry = gy - 20
    d.polygon([(cx - 27, ry - 9), (cx - 21, ry - 3), (cx - 16, ry),
               (cx + 16, ry), (cx + 21, ry - 3), (cx + 27, ry - 9),
               (cx + 10, ry - 12), (cx, ry - 15), (cx - 10, ry - 12)], fill=BLACK)
    d.rectangle([cx - 1, ry - 21, cx + 1, ry - 14], fill=BLACK)


def pavilion_spot(mid, far_m):
    """Flat local summit of the mid ridge, clear of the far band. Two
    passes: strict (must crown its own hill), then relaxed; if even
    that fails, the pavilion is simply skipped for the day."""
    for max_slope, crown in ((0.4, True), (0.7, False)):
        best, best_s = None, None
        for x in range(90, 550):
            slope = abs(mid[min(x + 12, W - 1)] - mid[max(x - 12, 0)]) / 24
            if slope > max_slope or mid[x] - 44 < far_m[x] + 6:
                continue
            if crown and mid[x] > min(mid[x - 34:x + 35]) + 3:
                continue
            s = -mid[x] - 40 * slope - 0.08 * abs(x - 320)
            if best_s is None or s > best_s:
                best, best_s = x, s
        if best is not None:
            return best
    return None


def boat(d, cx, wy):
    d.polygon([(cx - 30, wy - 6), (cx - 22, wy - 2), (cx + 20, wy - 2),
               (cx + 30, wy - 7), (cx + 23, wy + 3), (cx - 20, wy + 3)], fill=BLACK)
    fx = cx - 6
    d.ellipse([fx - 3, wy - 16, fx + 3, wy - 10], fill=BLACK)
    d.polygon([(fx - 4, wy - 10), (fx + 3, wy - 10), (fx + 2, wy - 2),
               (fx - 5, wy - 2)], fill=BLACK)
    d.line([(fx + 1, wy - 8), (fx + 24, wy - 17)], fill=BLACK, width=2)
    d.line([(fx + 24, wy - 17), (fx + 24, wy + 2)], fill=BLACK, width=1)


def scene_lake(img, dr, seed):
    dr.ellipse([124, 116, 212, 204], fill=YELLOW)          # sun, high left
    for bx, by, s in ((350, 272, 7), (382, 260, 6), (410, 276, 5)):  # birds
        dr.line([(bx - s, by), (bx, by - s * 0.6)], fill=BLACK, width=2)
        dr.line([(bx, by - s * 0.6), (bx + s, by)], fill=BLACK, width=2)

    far, far_m = ridge(random.Random(seed + ":far"), 480, 106, 1.6,
                       (240, 100, 46), band=18, wave=9)
    mid, mid_m = ridge(random.Random(seed + ":mid"), 614, 80, 1.5,
                       (210, 90, 40), wave=11)
    near, near_m = ridge(random.Random(seed + ":near"), 700, 50, 1.3,
                         (180, 80, 36), band=20, wave=4)
    for crest, mist in ((far, far_m), (mid, mid_m), (near, near_m)):
        fill_below(img, crest, BLACK)
        fill_below(img, mist, WHITE)

    spot = pavilion_spot(mid, far_m)
    if spot is not None:
        pavilion(dr, spot, mid[spot] + 2)

    crest_pines(dr, random.Random(seed + ":pines"), near, 8, 20, W - 21, 12, 16,
                clear=mid_m)

    # water: calm hairlines, sun glints, boat sitting on its own line
    for x, y, ln in ((92, 726, 74), (306, 750, 48), (452, 738, 56),
                     (96, 808, 60), (370, 810, 36), (258, 834, 44)):
        dr.line([(x, y), (x + ln, y)], fill=BLACK, width=1)
    for x, y, ln in ((136, 748, 58), (162, 764, 42)):
        dr.rectangle([x, y, x + ln, y + 2], fill=YELLOW)
    dr.line([(186, 780), (352, 780)], fill=BLACK, width=1)
    boat(dr, random.Random(seed + ":boat").randint(222, 316), 780)

    # near bank: tapers in from the right margin onto its own waterline
    bx0, ybot = 330, 856
    bn = value_noise(random.Random(seed + ":bank"), 90)
    top = {}
    for x in range(bx0, W):
        t = (x - bx0) / (W - bx0)
        top[x] = ybot - 56 * (t * t * (3 - 2 * t)) ** 0.9 - bn[x] * 14 * t
    dr.line([(150, ybot), (bx0 + 40, ybot)], fill=BLACK, width=1)
    dr.polygon([(x, top[x]) for x in range(bx0, W)] + [(W - 1, ybot), (bx0, ybot)],
               fill=BLACK)
    for px, ph in ((430, 21), (492, 26), (548, 23), (608, 26)):
        pine(dr, px, top[px] + 3, ph)


def scene_gorge(img, dr, seed):
    """Steep gorge: two tall ridge bands, banks closing in from both
    margins, a narrow channel of water with one boat threading it."""
    dr.ellipse([124, 116, 212, 204], fill=YELLOW)
    far, far_m = ridge(random.Random(seed + ":far"), 470, 160, 2.1,
                       (220, 90, 42), band=16, wave=8)
    mid, mid_m = ridge(random.Random(seed + ":mid"), 610, 130, 1.9,
                       (190, 80, 36), band=16, wave=10)
    for crest, mist in ((far, far_m), (mid, mid_m)):
        fill_below(img, crest, BLACK)
        fill_below(img, mist, WHITE)

    spot = pavilion_spot(mid, far_m)
    if spot is not None:
        pavilion(dr, spot, mid[spot] + 2)

    ybot, xl, xr = 856, 252, 388
    bl = value_noise(random.Random(seed + ":bankl"), 90)
    br = value_noise(random.Random(seed + ":bankr"), 90)
    topl, topr = {}, {}
    for x in range(0, xl):
        t = (xl - x) / xl
        topl[x] = ybot - 92 * (t * t * (3 - 2 * t)) ** 0.9 - bl[x] * 14 * t
    for x in range(xr, W):
        t = (x - xr) / (W - xr)
        topr[x] = ybot - 74 * (t * t * (3 - 2 * t)) ** 0.9 - br[x] * 14 * t
    dr.polygon([(x, topl[x]) for x in range(0, xl)] + [(xl - 1, ybot), (0, ybot)],
               fill=BLACK)
    dr.polygon([(x, topr[x]) for x in range(xr, W)] + [(W - 1, ybot), (xr, ybot)],
               fill=BLACK)
    for y, a, b in ((812, 266, 372), (838, 274, 356)):
        dr.line([(a, y), (b, y)], fill=BLACK, width=1)
    dr.line([(xl - 6, ybot), (xr + 6, ybot)], fill=BLACK, width=1)
    boat(dr, random.Random(seed + ":boat").randint(300, 336), 776)
    for px, ph in ((64, 25), (132, 22), (198, 26)):
        pine(dr, px, topl[px] + 3, ph)
    for px, ph in ((452, 24), (532, 27), (596, 22)):
        pine(dr, px, topr[px] + 3, ph)


def islet(img, dr, rng, cx, wy, w, h):
    """Low mound of an island on its own waterline; returns the crest
    so pines can stand on it."""
    n = value_noise(rng, 60)
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    top = {}
    for x in range(x0, x1 + 1):
        t = (x - x0) / (x1 - x0)
        arc = (4 * t * (1 - t)) ** 0.8
        top[x] = wy - h * arc - n[min(max(x, 0), W - 1)] * 10 * arc
    dr.polygon([(x, top[x]) for x in range(x0, x1 + 1)]
               + [(x1, wy), (x0, wy)], fill=BLACK)
    dr.line([(max(LEFT, x0 - 26), wy), (min(RIGHT, x1 + 26), wy)],
            fill=BLACK, width=1)
    return top


def scene_islands(img, dr, seed):
    """Open water: one low far ridge, then islets with pines, boats
    scattered between them."""
    dr.ellipse([124, 116, 212, 204], fill=YELLOW)
    for bx, by, s in ((350, 272, 7), (382, 260, 6), (410, 276, 5)):
        dr.line([(bx - s, by), (bx, by - s * 0.6)], fill=BLACK, width=2)
        dr.line([(bx, by - s * 0.6), (bx + s, by)], fill=BLACK, width=2)

    far, far_m = ridge(random.Random(seed + ":far"), 450, 70, 1.6,
                       (240, 100, 46), band=18, wave=8)
    fill_below(img, far, BLACK)
    fill_below(img, far_m, WHITE)

    for x, y, ln in ((80, 560, 90), (300, 585, 60), (470, 570, 70),
                     (120, 664, 70), (420, 684, 56),
                     (90, 800, 60), (380, 812, 48)):
        dr.line([(x, y), (x + ln, y)], fill=BLACK, width=1)
    for x, y, ln in ((150, 610, 52), (176, 626, 40)):
        dr.rectangle([x, y, x + ln, y + 2], fill=YELLOW)

    rng = random.Random(seed + ":isles")
    for cx, wy, w, h, pxs in (
            (150 + rng.randint(-20, 20), 648, 190, 42, (-34, 12)),
            (462 + rng.randint(-20, 20), 748, 210, 50, (-20, 30)),
            (240 + rng.randint(-20, 20), 856, 250, 56, (-46, 0, 44))):
        top = islet(img, dr, random.Random(seed + f":isle{wy}"), cx, wy, w, h)
        for off in pxs:
            x = min(max(cx + off, min(top)), max(top))
            pine(dr, x, top[x] + 3, rng.randint(18, 24))
    rb = random.Random(seed + ":boat")
    boat(dr, rb.randint(330, 420), 620)
    boat(dr, rb.randint(90, 130), 730)


def scene_night(img, dr, seed):
    """Nightfall: crescent moon, a few stars, no glints, sparser water,
    the pavilion window lit."""
    dr.ellipse([124, 116, 212, 204], fill=YELLOW)
    dr.ellipse([148, 100, 236, 188], fill=WHITE)           # the bite
    rs = random.Random(seed + ":stars")
    stars = 0
    while stars < 5:
        x, y = rs.randint(70, 570), rs.randint(56, 236)
        if abs(x - 180) < 90 and abs(y - 150) < 90:
            continue
        dr.ellipse([x - 2, y - 2, x + 2, y + 2], fill=YELLOW)
        stars += 1

    far, far_m = ridge(random.Random(seed + ":far"), 480, 106, 1.6,
                       (240, 100, 46), band=18, wave=9)
    mid, mid_m = ridge(random.Random(seed + ":mid"), 614, 80, 1.5,
                       (210, 90, 40), wave=11)
    near, near_m = ridge(random.Random(seed + ":near"), 700, 50, 1.3,
                         (180, 80, 36), band=20, wave=4)
    for crest, mist in ((far, far_m), (mid, mid_m), (near, near_m)):
        fill_below(img, crest, BLACK)
        fill_below(img, mist, WHITE)

    spot = pavilion_spot(mid, far_m)
    if spot is not None:
        gy = mid[spot] + 2
        pavilion(dr, spot, gy)
        dr.rectangle([spot - 10, gy - 18, spot + 9, gy - 4], fill=YELLOW)

    crest_pines(dr, random.Random(seed + ":pines"), near, 8, 20, W - 21, 12, 16,
                clear=mid_m)

    for x, y, ln in ((92, 726, 74), (452, 738, 56), (258, 834, 44)):
        dr.line([(x, y), (x + ln, y)], fill=BLACK, width=1)
    dr.line([(186, 780), (352, 780)], fill=BLACK, width=1)
    boat(dr, random.Random(seed + ":boat").randint(222, 316), 780)

    bx0, ybot = 330, 856
    bn = value_noise(random.Random(seed + ":bank"), 90)
    top = {}
    for x in range(bx0, W):
        t = (x - bx0) / (W - bx0)
        top[x] = ybot - 56 * (t * t * (3 - 2 * t)) ** 0.9 - bn[x] * 14 * t
    dr.line([(150, ybot), (bx0 + 40, ybot)], fill=BLACK, width=1)
    dr.polygon([(x, top[x]) for x in range(bx0, W)] + [(W - 1, ybot), (bx0, ybot)],
               fill=BLACK)
    for px, ph in ((430, 21), (492, 26), (548, 23), (608, 26)):
        pine(dr, px, top[px] + 3, ph)


SCENES = {"lake": scene_lake, "gorge": scene_gorge,
          "islands": scene_islands, "night": scene_night}


def render(d, hl, settings):
    seed = d.isoformat()
    img = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(img)
    SCENES.get(settings.get("landscape_scenery"), scene_lake)(img, dr, seed)

    # red seal, upper right, lunar day of month under it
    dr.rectangle([RIGHT - 56, 60, RIGHT, 176], fill=RED)
    draw_text(img, (RIGHT - 28, 92), "泰", serif(40, 600), WHITE, anchor="mm")
    draw_text(img, (RIGHT - 28, 144), "曆", serif(40, 600), WHITE, anchor="mm")
    lunar_day = hl["lunar_md"].split("月", 1)[1]
    draw_text(img, (RIGHT - 28, 202), lunar_day, serif(18, 500), BLACK,
              anchor="mm", tracking=6)

    # footer: hairline rule, one shared baseline
    dr.rectangle([LEFT, 884, RIGHT, 885], fill=BLACK)
    en = f"{hl['weekday_en']}, {hl['day']} {hl['month_abbr']} {hl['year']}"
    draw_text(img, (LEFT, 922), en, latin(21, 500), BLACK, anchor="ls")
    cn = f"{hl['ganzhi_year']}{hl['zodiac']}年 {hl['lunar_md']} {hl['ganzhi_day']}日"
    draw_text(img, (RIGHT + 4, 920), cn, serif(19, 500), BLACK, anchor="rs", tracking=2)
    return img
