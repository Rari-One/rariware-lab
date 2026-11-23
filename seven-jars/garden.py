"""Seven Jars — the picture. Seven glass vessels catch the drips from a gutter.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

Glass, drops, rain and splashes are drawn as Braille dots, two across and four
down in every cell. Water, wood and zinc are solid or fractional blocks. Every
drop comes from score.py, so the picture and the sound share one timeline.

Preview a still in a 24-bit color terminal:  python garden.py [frame]
"""
import math
import sys

import numpy as np

from score import FRAMES, JARS, LIGHTNING, drops

W, H = 120, 44
DW, DH = W * 2, H * 4                     # 240 x 176 Braille dots
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint16)
BG = np.array([9, 12, 19], float)
SEAM_Y = 12                               # beads hang from the gutter lip here
FLOOR = 155                               # lowest dot row of every jar
GRAVITY = 0.9                             # dots per frame, per frame
GLOW = 26.0                               # a struck jar's light fades with its ring

# name, glass tint, height in dots, fill, profile of (fraction of height, half-width)
VESSELS = [
    ("wine bottle", (196, 128, 52), 96, .20, [(0, 9), (.52, 9), (.66, 5), (.74, 3), (.97, 3), (1, 4)]),
    ("mason jar", (120, 176, 214), 62, .30, [(0, 10), (.06, 11), (.84, 11), (.92, 9), (1, 9.5)]),
    ("flask", (98, 190, 120), 78, .36, [(0, 8), (.08, 12), (.25, 13.5), (.42, 12), (.56, 6),
                                       (.64, 3.5), (.97, 3.5), (1, 4.5)]),
    ("vase", (70, 186, 178), 88, .48, [(0, 7), (.1, 8), (.85, 8), (.95, 9.5), (1, 10)]),
    ("crock", (150, 120, 214), 50, .58, [(0, 10), (.12, 12.5), (.6, 13), (.9, 12), (1, 12.5)]),
    ("milk bottle", (222, 128, 150), 74, .70, [(0, 8.5), (.55, 9), (.78, 5.5), (.9, 5), (1, 6)]),
    ("jam jar", (226, 196, 96), 46, .82, [(0, 8.5), (.85, 9), (.9, 8), (1, 8.5)]),
]

yy, xx = np.mgrid[:DH, :DW]


def cells_all(mask):
    return mask.reshape(H, 4, W, 2).all(axis=(1, 3))


def cells_any(mask):
    return mask.reshape(H, 4, W, 2).any(axis=(1, 3))


# Blow each vessel from its profile: inside, a one-dot glass wall, an open mouth.
jars = []
for j, (name, tint, height, fill, profile) in enumerate(VESSELS):
    cx = 25 + 32 * j
    above = FLOOR - yy
    hw = np.interp(above / height, [p for p, _ in profile], [w for _, w in profile])
    dx = xx + 0.5 - cx
    inside = (above >= 0) & (above <= height) & (np.abs(dx) <= hw)
    core = inside.copy()
    for shift, axis in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
        core &= np.roll(inside, shift, axis)
    mouth = (above >= height - 1) & (np.abs(dx) < hw - 1.2)
    wall = inside & ~core & ~mouth
    near = wall.copy()
    for shift, axis in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
        near |= np.roll(wall, shift, axis)
    clear = core & ~near                  # water never touches the wall dots
    glint = inside & (np.abs(dx + hw * 0.55) < 0.6) & (above > height * .15) & \
        (above < height * .62) & (yy % 2 == 0)
    tint = np.array(tint, float)
    hits = [f for f, jar, _ in drops() if jar == j]
    jars.append(dict(
        cx=cx, dx=dx, core=core, wall=wall, glint=glint, tint=tint, hits=hits,
        water_tint=0.55 * tint + 0.45 * np.array([60, 120, 170]),
        clear=clear, inside=inside, level=fill * height, solid=cells_all(clear), zone=cells_any(inside),
        span=np.abs(dx) <= hw * 0.8))
zone = np.any([jar["zone"] for jar in jars], axis=0)
for jar in jars:
    jar["box"] = np.repeat(np.repeat(jar["zone"], 4, axis=0), 2, axis=1)


def sky_dots(light):
    return BG + light * (np.array([70, 76, 110]) + (yy[..., None] / 4 / 38) * np.array([80, 84, 96]))

# A ridge of firs far beyond the yard. It stays hidden until lightning shows it.
rng = np.random.default_rng(360)
across = np.arange(DW)
hill = 86 + 5 * np.sin(across * 0.031) + 3 * np.sin(across * 0.083 + 1.3)
ridge = hill.copy()
for tx in range(-4, DW + 4, 7):
    tx += int(rng.integers(-2, 3))
    peak = hill[int(np.clip(tx, 0, DW - 1))] - rng.uniform(8, 21)
    ridge = np.minimum(ridge, peak + np.abs(across - tx) * 2.6)
tree_cell = ridge.reshape(W, 2).mean(axis=1)
bolt, col = [], 62
for row in range(3, 40):
    if 4 * row + 2 > tree_cell[col]:
        break
    bolt.append((row, col))
    col += int(rng.choice([-1, -1, 0, 1, 1, 1]))
fork, col = [], bolt[len(bolt) // 2][1]
for row in range(bolt[len(bolt) // 2][0] + 1, 40):
    col -= int(rng.choice([1, 1, 2]))
    if 4 * row + 2 > tree_cell[col] or len(fork) > 7:
        break
    fork.append((row, col))

# Rain behind the jars: each streak falls a whole number of times per loop.
streaks = [(rng.uniform(0, DW), int(rng.integers(16, 29)), rng.uniform(), rng.uniform(.3, 1))
           for _ in range(170)]
rings = [(rng.uniform(4, DW - 4), rng.uniform(165, 170), int(rng.integers(6, 13)), rng.uniform())
         for _ in range(40)]


def flash(n):
    """Lightning: a double flicker, then a fading sky."""
    return {0: 1.0, 1: .35, 2: .85, 3: .55, 4: .3, 5: .15, 6: .07}.get((n - LIGHTNING) % FRAMES, 0.0)


def ages(hits, n):
    return [(n - f) % FRAMES for f in hits]


def frame(n):
    lit = np.zeros((DH, DW), bool)
    ink = np.zeros((DH, DW, 3))
    solid = np.zeros((H, W), np.uint16)
    paint = np.zeros((H, W, 3))
    light = flash(n)

    def dot(x, y, color):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < DW and 0 <= y < DH:
            lit[y, x] = True
            ink[y, x] = color

    def cell(row, col, ch, color):
        solid[row, col] = ord(ch)
        paint[row, col] = np.clip(color, 0, 255)

    # Rain falls behind everything, softer where the ridge stands.
    for x0, cycles, phase, depth in streaks:
        top = SEAM_Y + 4
        y = top + ((phase + cycles * n / FRAMES) % 1) * (FLOOR - top)
        for k in range(3 + int(depth * 4)):
            yk = y - k
            xk = (x0 + 0.18 * (yk - top)) % DW
            r, c = int(yk) // 4, int(xk) // 2
            if yk < top or zone[r, c]:
                continue
            behind = 0.45 if yk > ridge[int(xk)] else 1.0
            dot(xk, yk, np.array([88, 114, 154]) * depth * behind * (1 - k * .1) + light * 120)

    # Lightning shows the sky and the dark ridge of firs beneath it.
    if light > 0:
        for r in range(3, 39):
            for c in range(W):
                if zone[r, c]:
                    continue
                top = tree_cell[c]
                sky = BG + light * (np.array([70, 76, 110]) + (r / 38) * np.array([80, 84, 96]))
                if top >= 4 * r + 4:
                    cell(r, c, "█", sky)
                elif top > 4 * r + 2:
                    cell(r, c, "▀", sky)
        if light in (1.0, .85, .55):
            for r, c in bolt + fork:
                if not zone[r, c]:
                    cell(r, c, "█", (236, 234, 255))

    # The puddle in front of the shelf: wavering reflections and rain rings.
    for jar in jars:
        glow = min(1.0, sum(math.exp(-a / GLOW) for a in ages(jar["hits"], n)))
        jar["glow"] = glow
        wave = np.sin(0.7 * xx + 2 * math.pi * 48 * n / FRAMES + yy * 1.7)
        mask = jar["span"] & (yy >= 164) & (yy < 172) & (yy % 2 == 0) & (wave > 0.1 - 0.5 * glow)
        lit[mask] = True
        ink[mask] = jar["water_tint"] * (0.18 + 0.6 * glow) + light * 60
    for x, y, cycles, phase in rings:
        age = ((phase + cycles * n / FRAMES) % 1) * FRAMES / cycles
        if age < 10:
            r = 0.6 * age
            for a in np.linspace(0, 2 * math.pi, 10, endpoint=False):
                dot(x + r * math.cos(a), y + 0.35 * r * math.sin(a),
                    np.array([84, 104, 136]) * (1 - age / 10))

    for j, jar in enumerate(jars):
        cx, dx, glow, tint = jar["cx"], jar["dx"], jar["glow"], jar["tint"]
        recent = [a for a in ages(jar["hits"], n) if a < 48]

        # The surface rocks after each drop: a dimple, a slosh, a bright ring
        # running out to the glass.
        bob = np.zeros(DW)
        ring = np.zeros(DW)
        col_dx = np.arange(DW) + 0.5 - cx
        for a in recent:
            bob += 2.2 * math.exp(-a / 10) * math.sin(0.9 * a) * np.cos(0.55 * col_dx)
            bob -= 1.6 * math.exp(-a / 3) * np.exp(-col_dx ** 2 / 6)
            ring += math.exp(-a / 14) * np.exp(-((np.abs(col_dx) - 0.9 * a) ** 2) / 6)
        surface = FLOOR - jar["level"] - bob
        water = jar["clear"] & (yy >= surface[None, :])

        # Water fills whole cells as blocks; the top cell takes a fractional
        # block in eighths, so a ripple can lift it a fraction of a cell.
        surf_cell = surface.reshape(W, 2).mean(axis=1)
        color = jar["water_tint"] * (0.42 + 0.55 * glow) + light * 40
        for r, c in zip(*np.nonzero(jar["solid"])):
            eighths = int(np.clip(round((4 * r + 4 - surf_cell[c]) * 2), 0, 8))
            if eighths:
                depth = (4 * r - surf_cell[c]) / 40
                shine = 0.35 * (eighths < 8 or 4 * r < surf_cell[c] + 4) + 0.6 * ring[2 * c]
                cell(r, c, chr(0x2580 + eighths) if eighths < 8 else "█",
                     color * (1.15 - min(depth, 0.6) + shine))
        lit[water] = True
        ink[water] = color

        if light > 0:
            # Against the flash the glass turns to a dark silhouette.
            backlit = jar["box"] & ~jar["wall"] & ~water & (yy < ridge[None, :])
            lit[backlit] = True
            ink[backlit] = sky_dots(light)[backlit]
        lit[jar["wall"]] = True
        ink[jar["wall"]] = tint * (0.38 + 0.6 * glow) + light * 60
        if light > 0:
            lit[jar["wall"] & (yy < ridge[None, :])] = False
        lit[jar["glint"]] = True
        ink[jar["glint"]] = np.array([200, 214, 226]) * (0.3 + 0.3 * glow) + light * 40

        # A drop gathers at the seam, lets go, and falls under gravity.
        level_y = FLOOR - jar["level"]
        fall = math.sqrt(2 * (level_y - SEAM_Y - 3) / GRAVITY)
        x = cx - 1
        swell = 1.0
        for hit in jar["hits"]:
            t = (n - (hit - fall)) % FRAMES
            if t < fall:
                y = SEAM_Y + 3 + 0.5 * GRAVITY * t * t
                for k in range(min(5, int(GRAVITY * t * 0.7) + 1)):
                    dot(x, y - k, np.array([196, 218, 240]) * (1 - k * 0.18))
            wait = (hit - fall - n) % FRAMES
            if wait < 20:
                swell = max(swell, 1 + 3 * (1 - wait / 20))
        for k in range(int(swell)):
            dot(x, SEAM_Y + k, np.array([150, 184, 220]) * (0.6 + swell / 10))
        if swell >= 2.5:
            for side in (-1, 1):
                dot(x + side, SEAM_Y + int(swell) - 2, np.array([150, 184, 220]) * 0.9)

        # The splash: a crown of droplets, then the jet that pops back up.
        for hit, a in zip(jar["hits"], ages(jar["hits"], n)):
            if a >= 22:
                continue
            spray = np.random.default_rng(j * 1000 + hit)
            bright = jar["water_tint"] * 1.2 + 60
            for _ in range(8):
                angle = spray.uniform(-1.1, 1.1)
                speed = spray.uniform(1.0, 2.1)
                px = cx - 0.5 + speed * math.sin(angle) * a
                py = level_y - speed * math.cos(angle) * 1.3 * a + 0.27 * a * a
                if py < level_y - 1 and jar["core"][int(np.clip(py, 0, DH - 1)), int(np.clip(px, 0, DW - 1))]:
                    dot(px, py, bright * (1 - a / 26))
            if 3 <= a <= 9:
                for k in range(int(6 * math.sin(math.pi * (a - 3) / 6)) + 1):
                    dot(x, level_y - 1 - k, bright)
            if 9 <= a <= 18:
                dot(x, level_y - 6 - 1.0 * (a - 9) + 0.27 * (a - 9) ** 2, bright)

    # The gutter overhead: eave, zinc trough, and a rusted seam above each jar.
    for c in range(W):
        cell(0, c, "█", np.array([22, 18, 15]) + light * 30)
        cell(1, c, "█", np.array([54, 60, 68]) + light * 70)
        cell(2, c, "▀", np.array([90, 98, 108]) + light * 90)
    for jar in jars:
        cell(2, (jar["cx"] - 1) // 2, "▀", (120, 74, 48))

    # The shelf, warmed by whichever jar is ringing.
    for c in range(W):
        warm = np.array([64, 45, 32]) + light * 50
        for jar in jars:
            warm = warm + jar["tint"] * jar["glow"] * 0.4 * max(0, 1 - abs(2 * c + 1 - jar["cx"]) / 22)
        cell(39, c, "█", warm)
        cell(40, c, "▀", np.array([34, 25, 19]) + light * 20)

    # Note names under the shelf.
    for jar, (note, _) in zip(jars, JARS):
        start = (jar["cx"] - 1) // 2 - len(note) // 2 + (len(note) == 3)
        for k, ch in enumerate(note):
            cell(43, start + k, ch, np.array([96, 90, 76]) + jar["tint"] * jar["glow"] * 0.7)

    return cells(lit, ink, solid, paint)


def cells(lit, ink, solid, paint):
    """Fold the dot canvas into Braille cells, then lay the solid cells over it."""
    l = lit.reshape(H, 4, W, 2)
    bits = (l * BITS[None, :, None, :]).sum(axis=(1, 3))
    count = np.maximum(1, l.sum(axis=(1, 3)))
    rgb = (ink * lit[..., None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3)) / count[..., None]
    ch = np.where(bits > 0, 0x2800 + bits, 32).astype(np.uint16)
    ch[bits == 255] = ord("█")
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
