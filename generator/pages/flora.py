"""Flora page: the Four Gentlemen, one ink plant a season.

Plum blossom in winter, orchid in spring, bamboo in summer,
chrysanthemum in autumn, drawn procedurally with all randomness seeded
from the date, so each day grows its own plant and every render of a
day is identical. The flora_plant setting pins one plant year round.
"""

import math
import random

from PIL import Image, ImageDraw

from generate import W, H, BLACK, WHITE, RED, YELLOW, draw_text, latin, serif

LEFT, RIGHT = 60, W - 60


def bezier(p0, p1, p2, n=28):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return pts


def taper(dr, pts, w0, w1, color=BLACK):
    """Polyline whose width eases from w0 to w1, round joints so the
    stroke reads as one brush pull, not chained segments."""
    n = len(pts) - 1
    for i in range(n):
        w = w0 + (w1 - w0) * i / n
        dr.line([pts[i], pts[i + 1]], fill=color, width=max(1, round(w)))
        r = max(0.5, w / 2)
        x, y = pts[i + 1]
        dr.ellipse([x - r, y - r, x + r, y + r], fill=color)


def leaf(dr, x, y, ang, ln, wd, color=BLACK):
    """Slender pointed leaf as a four point polygon."""
    tx, ty = x + ln * math.cos(ang), y + ln * math.sin(ang)
    mx, my = x + ln * 0.42 * math.cos(ang), y + ln * 0.42 * math.sin(ang)
    px, py = -math.sin(ang) * wd, math.cos(ang) * wd
    dr.polygon([(x, y), (mx + px, my + py), (tx, ty), (mx - px, my - py)],
               fill=color)


def blossom(dr, x, y, r):
    for k in range(5):
        a = math.tau * k / 5 - 0.4
        px, py = x + r * math.cos(a), y + r * math.sin(a)
        pr = r * 0.68
        dr.ellipse([px - pr, py - pr, px + pr, py + pr], fill=RED)
    cr = max(2, r * 0.3)
    dr.ellipse([x - cr, y - cr, x + cr, y + cr], fill=YELLOW)


def scene_plum(dr, rng):
    """One old bough entering low on the left, kinked segments thinning
    as they climb, red blossoms crowding the young wood."""
    anchors = []

    def grow(x, y, ang, w, depth):
        while w > 2.4:
            ln = rng.uniform(52, 92) * (0.82 if depth else 1.0)
            ang += rng.uniform(-0.5, 0.35)
            ang = min(max(ang, -2.1), -0.15)
            nx = x + ln * math.cos(ang)
            ny = y + ln * math.sin(ang)
            if not (80 < nx < RIGHT - 16 and ny > 250):
                break
            taper(dr, [(x, y), (nx, ny)], w, w * 0.78)
            if w < 8:
                anchors.append(((x + nx) / 2, (y + ny) / 2))
                anchors.append((nx, ny))
            if depth < 2 and w > 4 and rng.random() < 0.55:
                grow(nx, ny, ang + rng.choice((-1, 1)) * rng.uniform(0.4, 0.9),
                     w * 0.5, depth + 1)
            x, y, w = nx, ny, w * 0.78

    grow(72, 830, -0.9, 18, 0)
    grow(150, 845, -0.45, 10, 1)
    rng.shuffle(anchors)
    for i, (x, y) in enumerate(anchors[:14]):
        if i % 3 == 2:
            dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=RED)  # bud
        else:
            blossom(dr, x + rng.uniform(-6, 6), y + rng.uniform(-6, 6),
                    rng.uniform(7, 10))


def scene_orchid(dr, rng):
    """A ground clump of long crossing leaves, two flower stems rising
    over them, drawn in single tapering pulls."""
    bx, by = 300 + rng.randint(-30, 30), 850
    for i in range(9):
        side = -1 if i % 2 else 1
        reach = rng.uniform(140, 300)
        lift = rng.uniform(180, 420)
        c = (bx + side * reach * rng.uniform(0.3, 0.7), by - lift * 0.9)
        tip = (bx + side * reach, by - lift + rng.uniform(-30, 30))
        taper(dr, bezier((bx + side * rng.uniform(0, 14), by), c, tip),
              rng.uniform(6, 9), 1)
    for sx, drift in ((bx - 40, -70), (bx + 70, 60)):
        top = (sx + drift + rng.uniform(-25, 25), by - rng.uniform(470, 550))
        stem = bezier((sx, by), (sx + drift * 0.2, by - 320), top)
        taper(dr, stem, 3, 1.5)
        for t in (0.7, 0.85, 1.0):
            x, y = stem[int((len(stem) - 1) * t)]
            up = -math.pi / 2 + drift / 400
            for k in range(5):
                a = up + (k - 2) * 0.5 + rng.uniform(-0.12, 0.12)
                leaf(dr, x, y, a, rng.uniform(15, 23), 1.8)
            dr.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=RED)


def scene_bamboo(dr, rng):
    """Three culms of different weights, jointed with node gaps, leaf
    bursts hanging off the upper nodes."""
    culms = ((250 + rng.randint(-20, 20), 15, 230),
             (400 + rng.randint(-20, 20), 10, 300),
             (160 + rng.randint(-15, 15), 7, 440))
    for sx, w, top in culms:
        lean = rng.uniform(-0.06, 0.06)
        y = 858
        nodes = []
        while y > top:
            y2 = max(top, y - rng.randint(78, 106))
            x1, x2 = sx + (858 - y) * lean, sx + (858 - y2) * lean
            dr.polygon([(x1 - w / 2, y), (x1 + w / 2, y),
                        (x2 + w * 0.45, y2), (x2 - w * 0.45, y2)], fill=BLACK)
            nodes.append((x2, y2))
            dr.line([(x2 - w / 2 - 2, y2 - 3), (x2 + w / 2 + 2, y2 - 3)],
                    fill=BLACK, width=2)
            y = y2 - 6
        bursts = [(x, ny) for x, ny in nodes[:-1]
                  if ny < 700 and rng.random() > 0.45] + [nodes[-1]]
        for x, ny in bursts:
            side = rng.choice((-1, 1))
            bx2, by2 = x + side * rng.uniform(14, 34), ny + rng.uniform(-22, 2)
            dr.line([(x, ny), (bx2, by2)], fill=BLACK, width=3)
            for k in range(rng.randint(3, 5)):
                a = rng.uniform(0.15, 1.25) * (1 if rng.random() < 0.75 else -0.4)
                a = a if side > 0 else math.pi - a
                leaf(dr, bx2, by2, a, rng.uniform(40, 74), rng.uniform(4, 6))


def scene_chrysanthemum(dr, rng):
    """One heavy yellow head on a bent stem, a smaller side bud, ragged
    ink leaves below."""
    bx, by = 300 + rng.randint(-20, 20), 858
    hx, hy = bx + rng.randint(30, 90), 400 + rng.randint(-30, 30)
    stem = bezier((bx, by), (bx - rng.uniform(20, 70), (by + hy) / 2), (hx, hy))
    taper(dr, stem, 8, 3)

    def head(x, y, r):
        # curled yellow strokes in three rings, rounded tips, so the
        # head reads as a mum, not a starburst
        for rr, k in ((1.0, 14), (0.7, 10)):
            off = rng.uniform(0, math.tau)
            for i in range(k):
                a = math.tau * i / k + off + rng.uniform(-0.08, 0.08)
                ln = r * rr * rng.uniform(0.82, 1.0)
                bend = rng.uniform(-0.45, 0.45)
                p0 = (x + 5 * math.cos(a), y + 5 * math.sin(a))
                mid = (x + 0.55 * ln * math.cos(a + bend),
                       y + 0.55 * ln * math.sin(a + bend))
                tip = (x + ln * math.cos(a + bend * 0.4),
                       y + ln * math.sin(a + bend * 0.4))
                taper(dr, bezier(p0, mid, tip, 10), r * 0.22, 3, color=YELLOW)
        hr = r * 0.32
        dr.ellipse([x - hr, y - hr, x + hr, y + hr], fill=YELLOW)
        cr = r * 0.08
        dr.ellipse([x - cr, y - cr, x + cr, y + cr], fill=BLACK)

    head(hx, hy - 8, rng.uniform(88, 104))
    t = 0.55
    sx, sy = stem[int((len(stem) - 1) * t)]
    ex, ey = sx - rng.uniform(60, 100), sy - rng.uniform(60, 110)
    taper(dr, bezier((sx, sy), (sx - 50, sy - 20), (ex, ey)), 4, 2)
    head(ex, ey, rng.uniform(40, 52))
    for t, side in ((0.2, 1), (0.34, -1), (0.5, 1), (0.68, -1)):
        x, y = stem[int((len(stem) - 1) * t)]
        base = math.pi * (0.5 - side * 0.28)
        for k in range(5):
            a = base + (k - 2) * 0.38 + rng.uniform(-0.1, 0.1)
            leaf(dr, x + side * 8, y, a if side > 0 else math.pi - a,
                 rng.uniform(30, 56), rng.uniform(7, 11))


SEASON = {12: "plum", 1: "plum", 2: "plum",
          3: "orchid", 4: "orchid", 5: "orchid",
          6: "bamboo", 7: "bamboo", 8: "bamboo",
          9: "chrysanthemum", 10: "chrysanthemum", 11: "chrysanthemum"}
PLANTS = {"plum": ("梅", "PLUM BLOSSOM", scene_plum),
          "orchid": ("蘭", "ORCHID", scene_orchid),
          "bamboo": ("竹", "BAMBOO", scene_bamboo),
          "chrysanthemum": ("菊", "CHRYSANTHEMUM", scene_chrysanthemum)}


def render(d, hl, settings):
    choice = str(settings.get("flora_plant", "")).strip().lower()
    plant = choice if choice in PLANTS else SEASON[d.month]
    zi, en, scene = PLANTS[plant]

    img = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(img)
    scene(dr, random.Random(d.isoformat() + ":" + plant))

    # title, top left: the plant's character with its English name
    draw_text(img, (LEFT, 128), zi, serif(96, 600), BLACK, anchor="lm")
    draw_text(img, (LEFT + 4, 196), en, latin(18, 600), BLACK, anchor="ls")
    draw_text(img, (LEFT + 4, 222), "四君子", serif(17, 500), BLACK,
              anchor="ls", tracking=4)

    # red seal, upper right, lunar day of month under it
    dr.rectangle([RIGHT - 56, 60, RIGHT, 176], fill=RED)
    draw_text(img, (RIGHT - 28, 92), "泰", serif(40, 600), WHITE, anchor="mm")
    draw_text(img, (RIGHT - 28, 144), "曆", serif(40, 600), WHITE, anchor="mm")
    lunar_day = hl["lunar_md"].split("月", 1)[1]
    draw_text(img, (RIGHT - 28, 202), lunar_day, serif(18, 500), BLACK,
              anchor="mm", tracking=6)

    # footer: hairline rule, one shared baseline
    dr.rectangle([LEFT, 884, RIGHT, 885], fill=BLACK)
    en_date = f"{hl['weekday_en']}, {hl['day']} {hl['month_abbr']} {hl['year']}"
    draw_text(img, (LEFT, 922), en_date, latin(21, 500), BLACK, anchor="ls")
    cn = f"{hl['ganzhi_year']}{hl['zodiac']}年 {hl['lunar_md']} {hl['ganzhi_day']}日"
    draw_text(img, (RIGHT + 4, 920), cn, serif(19, 500), BLACK, anchor="rs",
              tracking=2)
    return img
