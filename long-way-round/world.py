"""The Long Way Round — the world. Sky, land, water and the drop, seen through a moving camera.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

Each frame starts from the camera's place on the route. Every screen dot is
given a world position, and the world decides what is there: stars, cloud,
snow, pines, a stream, a village, the sea and the deep. Textures are hashed
from world positions, so they stay put while the camera travels. Finally the
dots fold into Braille cells, and two letterbox rows carry the captions.

Preview a still in a 24-bit color terminal:  python world.py [frame]
"""
import math
import sys

import numpy as np

import deep
from journey import (BELLS, CAMERA, CHAPTERS, DH, DW, FRAMES, H, PERIOD, SEA, VENT, W,
                     chapter, drop, ground, surface)
from score import pulse

TAU = 2 * math.pi
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint16)
BG = np.array([7, 9, 16], float)
yy, xx = np.mgrid[:DH, :DW]
GLINT = pulse()
PATH = np.array([drop(f)[:2] for f in range(FRAMES)])


def hashed(x, y, salt=0.0):
    """A steady pseudo-random number in [0, 1) for each world position, wrapping with the world."""
    v = np.sin(np.mod(x, PERIOD) * 12.9898 + y * 78.233 + salt * 37.719) * 43758.5453
    return v - np.floor(v)


class Canvas:
    """The screen as Braille dots, addressed in world coordinates."""

    def __init__(self, cx, cy):
        self.cx, self.cy = cx, cy
        self.lit = np.zeros((DH, DW), bool)
        self.ink = np.zeros((DH, DW, 3))
        self.hero = []

    def screen(self, x, y):
        sx = (np.asarray(x, float) - self.cx + PERIOD / 2) % PERIOD - PERIOD / 2 + DW // 2
        return sx, np.asarray(y, float) - self.cy + DH // 2

    def dot(self, x, y, color):
        sx, sy = self.screen(x, y)
        r, c = int(round(float(sy))), int(round(float(sx)))
        if 0 <= r < DH and 0 <= c < DW:
            self.lit[r, c] = True
            self.ink[r, c] = np.clip(color, 0, 255)

    def paint(self, mask, color):
        self.lit |= mask
        self.ink[mask] = color if np.ndim(color) == 1 else color[mask]


rng = np.random.default_rng(1)
# The cloud: blobs of vapour around the place the journey begins and ends.
CLOUD = [(150 + rng.normal(0, 70), -150 + rng.normal(0, 28), rng.uniform(26, 50), rng.uniform())
         for _ in range(22)]
CLOUD += [(rng.uniform(220, 620), rng.uniform(30, 70), rng.uniform(10, 18), rng.uniform()) for _ in range(9)]
# Pines down the slope, and a few on the cliff.
PINES = [(x + rng.uniform(-3, 3), rng.uniform(9, 22)) for x in range(380, 1180, 8) if rng.uniform() < .8]
PINES += [(x, rng.uniform(8, 16)) for x in range(2515, 2560, 9)]
# The village on the far bank: (x, width, height, windows).
HOUSES = [(1250, 16, 12, 2), (1278, 12, 15, 1), (1300, 18, 11, 2), (1338, 14, 16, 2),
          (1366, 20, 12, 3), (1404, 12, 14, 1), (1424, 16, 18, 2), (1508, 14, 13, 2),
          (1530, 18, 11, 2), (1612, 14, 14, 1), (1640, 16, 12, 2), (1668, 12, 10, 1)]
CHURCH = 1470
KELP = [(x, rng.uniform(18, 48), rng.uniform()) for x in list(range(1742, 1900, 9)) + list(range(2380, 2490, 8))]
RAIN = [(rng.uniform(60, 420), int(rng.integers(8, 15)), rng.uniform()) for _ in range(70)]
PLUME = [(rng.uniform(), int(rng.integers(14, 24)), rng.uniform(-1, 1)) for _ in range(46)]
VENT_X = 2178


def windows():
    """Every lit window in the village as (x, y, width, height)."""
    out = []
    for x, w, h, count in HOUSES:
        base = float(ground(x + w / 2)) - 3
        for k in range(count):
            out.append((x + 3 + k * (w - 6) / max(1, count), base - h + 4, 2, 3))
    return out


WINDOWS = windows()


def frame(n):
    cx, cy = CAMERA[n]
    canvas = Canvas(cx, cy)
    wx = cx - DW // 2 + xx
    wy = cy - DH // 2 + yy
    col = wx[0]
    g = ground(col)[None, :]
    sea = g > SEA
    s = np.where(sea, surface(col, n)[None, :], np.inf)
    land = wy >= g
    water = (wy >= s) & ~land
    air = ~land & ~water
    x, y, vapour = drop(n)
    mx, my = 205 - 0.05 * cx, 30 - 0.22 * (cy - 660)

    # Stars, with a little parallax, twinkling a whole number of times per loop.
    sx, sy = (xx + int(0.1 * cx)) % 256, yy + int(0.1 * cy)
    star = air & (hashed(sx, sy, 1) < 0.0045)
    twinkle = 0.55 + 0.45 * np.sin(TAU * (hashed(sx, sy, 2) + (10 + (hashed(sx, sy, 3) * 20).astype(int))
                                          * n / FRAMES))
    canvas.paint(star, np.array([200, 210, 235])[None, None, :] * twinkle[..., None])

    # The moon rises as the drop comes down from the mountains.
    d = np.hypot(xx - mx, yy - my)
    moonlight = float(np.clip((cy - 220) / 120, 0, 1))
    if moonlight > 0:
        crater = (1 - 0.18 * (hashed(xx - int(mx), yy - int(my), 4) < 0.25))[..., None]
        canvas.paint(air & (d < 11), np.array([236, 226, 192]) * crater * moonlight)
        canvas.paint(air & (d >= 11) & (d < 22) & (hashed(wx, wy, 5) < 0.12 * (22 - d) / 11),
                     np.array([96, 98, 122]) * moonlight)

    # The cloud, made of soft blobs; inside it everything is fog.
    near = abs((cx - 150 + PERIOD / 2) % PERIOD - PERIOD / 2) < 520 and cy < 200
    if near:
        dx0 = (wx - 150 + PERIOD / 2) % PERIOD - PERIOD / 2 + 150
        dens = np.zeros((DH, DW))
        for bx, by, r, ph in CLOUD:
            bx = bx + 5 * math.sin(TAU * (2 * n / FRAMES + ph))
            by = by + 3 * math.cos(TAU * (3 * n / FRAMES + ph))
            dens += np.exp(-((dx0 - bx) ** 2 + (wy - by) ** 2) / r ** 2)
        fog = air & (hashed(wx, wy, 6) < np.clip((dens - 0.35) * 0.9, 0, 0.52))
        canvas.lit[air & (dens > 0.5)] = False
        shade = np.clip(0.4 + (-100 - wy) / 110, 0.3, 1.15)[..., None]
        canvas.paint(fog, np.array([150, 160, 188])[None, None, :] * shade)

    # Rain from the cloud: the drop's companions fall with it.
    for rx, cycles, ph in RAIN:
        bottom = float(ground(rx))
        ry = -110 + ((ph + cycles * n / FRAMES) % 1) * (bottom + 110)
        for k in range(4):
            canvas.dot(rx + 0.15 * (ry - k + 110) * 0.2, ry - k, np.array([110, 140, 180]) * (1 - 0.2 * k))

    # Snow, rock and meadow: textures keyed to depth below the surface.
    depth = wy - g
    soil = 0.5 * np.exp(-depth / 12) + 0.07
    canvas.paint(land & (hashed(wx, wy, 7) < soil), np.array([70, 64, 74]) * np.clip(1 - depth / 120, .45, 1)[..., None])
    canvas.paint(land & (depth < 1.5), (112, 108, 120))
    meadow = land & (depth < 4) & ((wx % PERIOD) > 820) & ((wx % PERIOD) < 1700) & (hashed(wx, wy, 8) < .7)
    canvas.paint(meadow, (52, 86, 60))
    snow = land & (depth < 7) & (g < 430) & (hashed(wx, wy, 9) < .9)
    canvas.paint(snow, np.array([206, 216, 236]) - (depth * 9)[..., None])
    sand = land & (depth < 4) & (((wx % PERIOD) > 1680) & ((wx % PERIOD) < 1730) | ((wx % PERIOD) > 2488) & ((wx % PERIOD) < 2512))
    canvas.paint(sand & (hashed(wx, wy, 10) < .8), (156, 136, 96))
    canvas.lit[land & sea] = False
    canvas.paint(land & sea & (hashed(wx, wy, 11) < soil), (46, 54, 70))
    canvas.paint(land & sea & (depth < 1.5), (70, 82, 98))

    # Pines down the slope, dusted with snow up high.
    for tx, h in PINES:
        base = float(ground(tx))
        px, py = canvas.screen(tx, base)
        if -20 < px < DW + 20 and -30 < py < DH + 30:
            for t in range(int(h)):
                half = t * 0.34
                for u in np.arange(-half, half + 0.5, 1):
                    if hashed(tx + u, t, 12) < 0.75:
                        white = base < 440 and t < h * 0.35 and hashed(tx + u, t, 13) < .45
                        canvas.dot(tx + u, base - h + t, (196, 206, 226) if white else (30, 68, 52))
            canvas.dot(tx, base, (58, 44, 36))

    # The stream: glitter runs downhill along the surface.
    stream = ((wx % PERIOD) >= 300) & ((wx % PERIOD) < 1150) & (wy >= g - 2) & (wy < g)
    glitter = 0.5 + 0.5 * np.sin(0.45 * wx - TAU * 44 * n / FRAMES + 2 * hashed(wx, 0, 14))
    canvas.paint(stream, np.array([110, 160, 220])[None, None, :] * (0.45 + 0.65 * glitter)[..., None])

    # The village: houses on the far bank, lit windows, and the church.
    for hx, w, h, _ in HOUSES:
        base = float(ground(hx + w / 2)) - 3
        hx0, _ = canvas.screen(hx, base)
        if -30 < hx0 < DW + 30:
            for u in range(w + 1):
                roof = h + (w / 2 - abs(u - w / 2)) * 0.6
                canvas.dot(hx + u, base - roof, (86, 72, 74))
                if u in (0, w):
                    for t in range(int(h)):
                        canvas.dot(hx + u, base - t, (70, 66, 82))
    for wx0, wy0, ww, wh in WINDOWS:
        flicker = 0.85 + 0.15 * math.sin(TAU * 9 * n / FRAMES + wx0)
        for u in range(ww):
            for v in range(wh):
                canvas.dot(wx0 + u, wy0 + v, np.array([252, 194, 104]) * flicker)
    cb = float(ground(CHURCH + 5)) - 3
    for t in range(48):
        for u in (0, 10):
            canvas.dot(CHURCH + u, cb - t, (78, 74, 90))
    for t in range(16):
        canvas.dot(CHURCH + 5 - t * 5 / 16, cb - 48 - 16 + t, (90, 84, 98))
        canvas.dot(CHURCH + 5 + t * 5 / 16, cb - 48 - 16 + t, (90, 84, 98))
    # The church bell: the belfry flashes on each toll.
    ring = sum(math.exp(-((n - b) % FRAMES) / 6) for b in BELLS)
    for u in range(3, 8):
        for v in range(4):
            canvas.dot(CHURCH + u, cb - 42 + v, np.array([120, 90, 50]) + np.array([135, 140, 120]) * ring)

    # The river: dark moving water with ripples and the village's lights in it.
    river = ((wx % PERIOD) >= 1150) & ((wx % PERIOD) < 1712) & (wy >= g - 3) & (wy < g + 3)
    canvas.paint(river & (hashed(wx, wy, 15) < .85), (28, 56, 106))
    ripple = river & (np.sin(0.3 * wx + TAU * 24 * n / FRAMES + 3 * wy) > 0.86)
    canvas.paint(ripple, (128, 168, 220))
    for wx0, _, ww, _ in WINDOWS:
        band = river & (wx >= wx0 - 1) & (wx < wx0 + ww + 1)
        canvas.paint(band & (np.sin(0.9 * wy + TAU * 30 * n / FRAMES + wx) > 0.1), (196, 146, 82))
    for bx in range(1580, 1641):
        deck = float(ground(1610)) - 12
        canvas.dot(bx, deck, (118, 108, 104))
        arch = float(ground(1610)) - 2 - 9 * math.sin(math.pi * (bx - 1580) / 60)
        canvas.dot(bx, arch, (96, 88, 86))
    for lx in (1584, 1636):
        canvas.dot(lx, float(ground(1610)) - 14, np.array([255, 200, 110]) * (0.8 + 0.2 * math.sin(TAU * 7 * n / FRAMES)))

    # The sea: light fades with depth, and moonbeams slant through the top.
    under = wy - SEA
    beams = 0.12 * np.clip(np.sin(0.045 * (wx + 0.6 * wy) - TAU * 6 * n / FRAMES), 0, 1) * np.exp(-under / 90)
    density = 0.3 * np.exp(-np.clip(under, 0, None) / 110) + 0.03 + beams
    tone = np.clip(under / 320, 0, 1)[..., None]
    sea_ink = (1 - tone) * np.array([46, 110, 150]) + tone * np.array([14, 30, 72])
    canvas.paint(water & (hashed(wx, wy, 16) < density), sea_ink)
    crest = water & (wy - s < 1.2)
    canvas.paint(crest, (126, 176, 214))
    canvas.paint(crest & (np.abs(xx - mx) < 20) & (hashed(wx, 7, n % 997) < 0.5), (240, 232, 196))

    # Plankton glow where the drop has just passed.
    plankton = water & (under > 140) & (hashed(wx, wy, 17) < 0.006)
    wake = np.zeros((DH, DW))
    for k in range(0, 12, 2):
        px, py = PATH[(n - k) % FRAMES]
        wake = np.maximum(wake, np.exp(-((wx - px) ** 2 + (wy - py) ** 2) / 500) * (1 - k / 12))
    canvas.paint(plankton, np.array([40, 70, 90])[None, None, :] + np.array([60, 190, 160])[None, None, :] * wake[..., None])
    canvas.paint(water & (under > 100) & (hashed(wx, wy, 18) < 0.06 * wake), (90, 230, 210))

    # Kelp sways on the shelves either side of the trench.
    for kx, h, ph in KELP:
        base = float(ground(kx))
        px, py = canvas.screen(kx, base)
        if -10 < px < DW + 10 and -60 < py < DH + 10:
            for t in range(int(h)):
                sway = 3 * math.sin(0.09 * t + TAU * (2 * n / FRAMES + ph)) * t / h
                canvas.dot(kx + sway, base - t, np.array([60, 105, 70]) * (0.6 + 0.4 * t / h))
                if t % 5 == 2:
                    canvas.dot(kx + sway + (1 if t % 10 == 2 else -1), base - t, (74, 128, 84))

    # The vent: a black chimney on the trench floor, breathing warm water.
    base = float(ground(VENT_X))
    px, py = canvas.screen(VENT_X, base)
    if -40 < px < DW + 40 and -60 < py < DH + 40:
        for t in range(28):
            half = 7 - t * 5 / 28
            for u in np.arange(-half, half + 0.5, 1):
                if hashed(VENT_X + u, t, 19) < 0.8:
                    canvas.dot(VENT_X + u, base - t, (70, 58, 56))
        burst = math.exp(-((n - VENT) % FRAMES) / 14)
        for ph, cycles, drift in PLUME:
            age = (ph + cycles * n / FRAMES) % 1
            rise = age * (60 + 120 * burst)
            heat = np.array([240, 130, 60]) * (1 - age) + np.array([90, 90, 100]) * age
            canvas.dot(VENT_X + drift * 4 * age + 2 * math.sin(TAU * age * 2 + ph * 9), base - 28 - rise,
                       heat * (0.4 + 0.6 * burst) * (1 - 0.6 * age))
        for u in range(-2, 3):
            canvas.dot(VENT_X + u, base - 28, np.array([250, 150, 70]) * (0.6 + 0.4 * burst))

    # The living sea.
    deep.draw(canvas, n)

    # The drop itself: a bright bead that flares with the theme, or a
    # spiral of vapour while it is still becoming one.
    flare = 0.75 + 0.25 * GLINT[n]
    body = (1 - vapour) * flare
    for k in range(1, 14):
        tx, ty = PATH[(n - k) % FRAMES]
        if abs(tx - x) < 120:
            canvas.dot(tx, ty, np.array([90, 150, 210]) * (1 - k / 14) * (1 - 0.7 * vapour))
    if body > 0.02:
        # Braille dots are small, so the drop is drawn as whole cells: a block
        # with a half-block tip above it, the brightest thing on the screen.
        sx, sy = canvas.screen(x, y)
        r, c = int(sy) // 4, int(sx) // 2
        color = np.array([150, 200, 245]) + np.array([90, 50, 15]) * GLINT[n]
        canvas.hero = [(r, c, "█", color * body), (r - 1, c, "▄", color * body * 0.9)]
        for k in range(14):
            a = TAU * k / 14 + n * 0.3
            r = 6 + 2.5 * GLINT[n]
            canvas.dot(x + r * math.cos(a), y - 1 + 0.9 * r * math.sin(a),
                       np.array([120, 180, 240]) * body * (0.35 + 0.65 * GLINT[n]))
    if vapour > 0.02:
        for k in range(32):
            a = TAU * k / 16 + n * 0.35 * (1 + k // 16)
            r = 1.5 + vapour * (8 + 5 * (k // 16)) + 1.5 * math.sin(3 * a + n * 0.2)
            canvas.dot(x + r * math.cos(a), y + 0.8 * r * math.sin(a), np.array([180, 214, 250]) * (0.45 + 0.55 * vapour))

    return cells(canvas, n, y)


def caption(solid, paint, row, col, text, color):
    for k, ch in enumerate(text):
        if 0 <= col + k < W:
            solid[row, col + k] = ord(ch)
            paint[row, col + k] = np.clip(color, 0, 255)


def cells(canvas, n, height):
    """Fold the dots into Braille cells, then add the letterbox and captions."""
    l = canvas.lit.reshape(H, 4, W, 2)
    bits = (l * BITS[None, :, None, :]).sum(axis=(1, 3))
    count = np.maximum(1, l.sum(axis=(1, 3)))
    rgb = (canvas.ink * canvas.lit[..., None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3)) / count[..., None]
    ch = np.where(bits > 0, 0x2800 + bits, 32).astype(np.uint16)
    solid = np.zeros((H, W), np.uint16)
    paint = np.zeros((H, W, 3))
    for r, c, glyph, color in canvas.hero:
        if 0 <= r < H - 2 and 0 <= c < W and max(color) > 12:
            solid[r, c] = ord(glyph)
            paint[r, c] = np.clip(color, 0, 255)
    solid[H - 2:] = 32

    # Captions: the chapter fades in and out; a route line shows the way round.
    i = chapter(n)
    start, number, name = CHAPTERS[i]
    age = n - start
    fade = np.clip(min(age / 8, (60 - age) / 14), 0, 1)
    if fade > 0.05:
        caption(solid, paint, H - 2, 3, f"{number}  " + " ".join(name), np.array([176, 190, 212]) * fade)
    metres = int(round((SEA - height) * 4.5, -1))
    level = f"▲ {metres:,} m" if metres > 0 else (f"▼ {-metres:,} m" if metres < 0 else "sea level")
    caption(solid, paint, H - 2, W - 3 - len(level), level, (120, 132, 156))
    span = W - 6
    caption(solid, paint, H - 1, 3, "─" * span, (46, 54, 68))
    for first, _, _ in CHAPTERS:
        caption(solid, paint, H - 1, 3 + int(first / FRAMES * span), "┴", (76, 88, 108))
    caption(solid, paint, H - 1, 3 + int(n / FRAMES * span), "●", (204, 220, 240))

    ch = np.where(solid > 0, solid, ch)
    rgb = np.where((solid > 0)[..., None], paint, rgb)
    return ch, np.clip(rgb, 0, 255).round().astype(np.uint8)


def image(n):
    """One frame in the player's five-byte cells: UTF-16 code unit, then RGB."""
    ch, rgb = frame(n)
    out = np.zeros((H, W), dtype=[("c", "<u2"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
    out["c"], out["r"], out["g"], out["b"] = ch, rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return out.tobytes()


if __name__ == "__main__":
    ch, rgb = frame(int(sys.argv[1]) % FRAMES if len(sys.argv) > 1 else 0)
    back = "\x1b[48;2;%d;%d;%dm" % tuple(BG.astype(int))
    for r in range(H):
        print(back + "".join("\x1b[38;2;%d;%d;%dm%s" % (*rgb[r, c], chr(ch[r, c])) for c in range(W))
              + "\x1b[0m")
