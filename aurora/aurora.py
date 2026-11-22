#!/usr/bin/env python3
# aurora.py - northern lights over mountains and a still lake, drawn in text.
#
# A RariWare Lab experiment. Standard library only.
#
# Run it in a terminal with 24-bit color (Ctrl+C to stop):
#     python3 aurora.py
# Other modes:
#     python3 aurora.py --still            print one frame
#     python3 aurora.py --export           print the whole loop as JSON (what rariware.com/lab/ plays)
#     python3 aurora.py --stats            print how much of the picture changes per frame
#
# The terminal needs a font with box-drawing and block characters
# (most do) and should be at least 120 columns by 41 rows.
#
# MIT License
#
# Copyright (c) 2026 Rari-One
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import json
import math
import random
import sys
import time

COLS, ROWS = 120, 40
FPS = 15
FRAMES = 180          # 12 seconds, one seamless loop
SEED = 2026
TAU = 2 * math.pi

# One palette for the terminal and the browser. Each cell stores an index into it.
PALETTE = [
    "#000000",                                                        # 0  blank
    "#0f3b2c", "#16573f", "#1f7a55", "#2fa36d", "#4fcf8b", "#8af2b8", "#d4ffe8",  # 1-7 green
    "#1b5a63", "#2b8b93", "#48c2c4",                                  # 8-10 teal
    "#2c2463", "#463a96", "#6b57c9", "#9a7ff0",                       # 11-14 violet
    "#6a2f73", "#b45bbf",                                             # 15-16 rose fringe
    "#5d6688", "#a9b3d6", "#f4f6ff",                                  # 17-19 stars
    "#121731", "#1b2246",                                             # 20-21 far range
    "#0e1229", "#131a3a", "#8d9bc4", "#d7e0f7",                       # 22-25 near range, snow
    "#123a30", "#2a7a5c", "#2c6c78", "#4b3f8c", "#4a5888",            # 26-30 water
    "#0a1511", "#14302a",                                             # 31-32 shore and pines
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

# Aurora brightness ramp: faint vertical rays, then shading, then solid.
RAYS = " ┊╎│┃"
# Lower blocks in eighths, for smooth skylines.
LOWER = " ▁▂▃▄▅▆▇█"
# Reflections on the water are horizontal strokes.
WATER = " ·┈┄╌──━"


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Aurora:
    def __init__(self, cols=COLS, rows=ROWS, seed=SEED):
        rng = random.Random(seed)
        self.cols, self.rows = cols, rows
        self.horizon = round(rows * 0.70)                 # first water row
        hz = self.horizon

        # Three curtains, far to near. Every time term is a whole number of cycles per loop,
        # so the last frame flows back into the first.
        self.curtains = []
        for depth in (0.0, 0.5, 1.0):
            self.curtains.append({
                "depth": depth,
                "edge": hz * (0.40 + 0.20 * depth),       # lower edge, in rows from the top
                "sway": [hz * (0.09 + 0.05 * depth), hz * 0.04, hz * 0.015],
                "kx": [rng.choice((0.8, 1.1, 1.4)), rng.choice((2.3, 2.9)), rng.choice((5.1, 6.3))],
                "kt": [rng.choice((-1, 1)), rng.choice((-1, 1)), rng.choice((-2, 2))],
                "reach": hz * (0.16 + 0.12 * depth),      # how high the glow climbs
                "gain": 0.75 + 0.55 * depth,
                "ph": [rng.uniform(0, TAU) for _ in range(9)],
            })

        # Stars: (x, y) -> (brightness, twinkle cycles per loop, phase).
        self.stars = {}
        for _ in range(cols * hz // 26):
            x, y = rng.randrange(cols), rng.randrange(hz - 3)
            self.stars[(x, y)] = (rng.uniform(0.25, 1.0), rng.choice((1, 1, 2)), rng.uniform(0, TAU))

        # Mountain skylines, measured in eighths of a row so the top edge can use partial blocks.
        def skyline(base, amp, k, ph):
            out = []
            for x in range(cols):
                u = x / cols
                h = base + amp[0] * math.sin(TAU * k[0] * u + ph[0]) + amp[1] * math.sin(TAU * k[1] * u + ph[1]) \
                    + amp[2] * abs(math.sin(TAU * k[2] * u + ph[2]))
                out.append(round(h * 8))
            return out
        lift = [rng.uniform(0, TAU) for _ in range(6)]
        self.far = skyline(hz - 4.0, (1.8, 0.9, 1.3), (1.1, 2.7, 4.3), lift[:3])
        self.near = skyline(hz - 0.6, (1.6, 0.6, 0.9), (0.7, 3.3, 6.1), lift[3:])
        # Snow on the highest parts of the far range.
        self.snowline = sorted(self.far)[len(self.far) // 5]

        # Glints on the water drift a little and come back each loop.
        self.glints = [(rng.randrange(cols), hz + rng.randrange(1, rows - hz), rng.uniform(0, TAU))
                       for _ in range(cols // 5)]

        # Shores and pines in the bottom corners.
        self.shore = []
        for x in range(cols):
            u = x / cols
            s = max(0.0, 1 - u / 0.20) ** 1.6 * 2.6 + max(0.0, 1 - (1 - u) / 0.16) ** 1.6 * 2.2
            self.shore.append(round(s * 2))
        self.pines = []
        for x0, x1 in ((1, round(cols * 0.17)), (round(cols * 0.86), cols - 2)):
            x = x0
            while x <= x1:
                self.pines.append((x, rng.randint(4, 8)))
                x += rng.randint(4, 7)

    # -- aurora ------------------------------------------------------------------------------
    def _columns(self, c, t):
        """Per-column edge height and brightness of one curtain at loop phase t."""
        cols = self.cols
        p, kx, kt, sw = c["ph"], c["kx"], c["kt"], c["sway"]
        edges, bright = [], []
        for x in range(cols):
            u = x / cols
            e = c["edge"] + sum(sw[i] * math.sin(TAU * (kx[i] * u + kt[i] * t) + p[i]) for i in range(3))
            # Rays drift along the curtain; two layers moving apart make them shimmer.
            rays = 0.62 + 0.22 * math.sin(TAU * (19 * u + 2 * t) + p[3]) + 0.16 * math.sin(TAU * (33 * u - 3 * t) + p[4])
            # The curtain brightens and fades along its length, slowly.
            env = smooth(0.30, 0.80, 0.5 + 0.5 * math.sin(TAU * (0.85 * u - kt[0] * t) + p[5]))
            pulse = 0.88 + 0.12 * math.sin(TAU * (t + 1.7 * u) + p[6])
            edges.append(e)
            bright.append(c["gain"] * rays * env * pulse)
        return edges, bright

    def sky(self, t):
        """Aurora light per cell: (level 0..1, palette index)."""
        cols, hz = self.cols, self.horizon
        level = [[0.0] * cols for _ in range(hz)]
        color = [[0] * cols for _ in range(hz)]
        for c in self.curtains:
            edges, bright = self._columns(c, t)
            reach = c["reach"]
            lean = 0.7 + 0.5 * c["depth"]
            for x in range(cols):
                e = edges[x]
                top = max(0, int(e - 2.6 * reach))
                for y in range(top, min(hz, int(e) + 2)):
                    above = e - y
                    # Folds: higher parts of the curtain lean sideways.
                    sx = x + round(lean * math.sin(TAU * (x / cols * 2 + t) + c["ph"][7]) * max(0.0, above) / reach)
                    b = bright[min(cols - 1, max(0, sx))]
                    if above >= 0:
                        glow = math.exp(-above / reach) * (1.0 + 0.35 * math.exp(-above * 1.5))
                    else:
                        glow = max(0.0, 1 + above / 1.2) * 0.55
                    v = b * glow
                    if v <= level[y][x]:
                        continue
                    level[y][x] = v
                    h = above / reach
                    if above < 0:
                        color[y][x] = 16 if (c["depth"] == 1.0 and v > 0.25) else 15
                    elif h < 0.35:
                        color[y][x] = 7 if v > 0.95 else 6 if v > 0.7 else 5 if v > 0.45 else 4
                    elif h < 1.0:
                        color[y][x] = 5 if v > 0.6 else 4 if v > 0.4 else 3 if v > 0.22 else 2
                    elif h < 1.8:
                        color[y][x] = 10 if v > 0.3 else 9 if v > 0.16 else 8
                    else:
                        color[y][x] = 14 if v > 0.26 else 13 if v > 0.15 else 12 if v > 0.08 else 11
        return level, color

    # -- one frame -----------------------------------------------------------------------------
    def frame(self, index, frames=FRAMES):
        """Return (rows of characters, rows of palette codes) for frame `index`."""
        t = index / frames
        cols, rows, hz = self.cols, self.rows, self.horizon
        ch = [[" "] * cols for _ in range(rows)]
        co = [[0] * cols for _ in range(rows)]
        level, color = self.sky(t)
        shade = [[0.0] * cols for _ in range(hz)]          # what the lake reflects
        kind = [[0] * cols for _ in range(hz)]

        for y in range(hz):
            for x in range(cols):
                v = level[y][x]
                if v >= 0.16:
                    ch[y][x] = RAYS[min(len(RAYS) - 1, 1 + int((v - 0.16) / 0.7 * (len(RAYS) - 1)))]
                    co[y][x] = color[y][x]
                    shade[y][x], kind[y][x] = v, color[y][x]
                star = self.stars.get((x, y))
                if star and v < 0.22:
                    b, n, ph = star
                    tw = b * (0.78 + 0.22 * math.cos(TAU * n * t + ph))
                    if tw > 0.72:
                        ch[y][x], co[y][x] = "•", 19
                    elif tw > 0.45:
                        ch[y][x], co[y][x] = "∙", 18
                    else:
                        ch[y][x], co[y][x] = "·", 17

        # Mountains, far range first. Heights are in eighths of a row from the top.
        for heights, fill, edge in ((self.far, 20, 21), (self.near, 22, 23)):
            for x in range(cols):
                top = heights[x]
                row, part = divmod(top, 8)
                snowy = heights is self.far and top <= self.snowline
                for y in range(row, hz):
                    if y == row and part:
                        if ch[y][x] == "█":       # in front of the far range: one color per cell
                            if part <= 4:
                                ch[y][x], co[y][x] = "█", fill
                            continue
                        ch[y][x], co[y][x] = LOWER[8 - part], (25 if snowy else edge)
                    elif y == row and not part:
                        ch[y][x], co[y][x] = "█", (25 if snowy else edge)
                    elif y == row + 1 and snowy and top <= self.snowline - 6:
                        ch[y][x], co[y][x] = "█", 24
                    else:
                        ch[y][x], co[y][x] = "█", fill
                    shade[y][x], kind[y][x] = 0.0, -1

        # The lake mirrors the sky above the horizon, darker and rippled.
        for y in range(hz, rows):
            d = y - hz
            ripple = 1 + d * 0.6
            for x in range(cols):
                sx = x + round(ripple * 0.8 * math.sin(TAU * (2 * t) + d * 1.3 + x * 0.21))
                sx = min(cols - 1, max(0, sx))
                my = hz - 1 - round(d * 1.9)    # the lake is seen at a low angle, so its reflection is squeezed
                if my < 0:
                    continue
                if kind[my][sx] == -1:
                    ch[y][x], co[y][x] = "█", 22 if self.near[sx] // 8 <= my else 20
                    if my == min(self.far[sx], self.near[sx]) // 8:
                        ch[y][x] = "▀"
                    continue
                v = shade[my][sx] * (1.0 - 0.04 * d)
                if v > 0.14:
                    k = kind[my][sx]
                    ch[y][x] = WATER[min(len(WATER) - 1, 1 + int(v * 7))]
                    co[y][x] = 27 if 1 <= k <= 7 else 28 if 8 <= k <= 10 else 29 if 11 <= k <= 16 else 26
        for gx, gy, ph in self.glints:
            x = (gx + round(2.5 * math.sin(TAU * t + ph))) % cols
            if ch[gy][x] in (" ", "·", "┈"):
                ch[gy][x], co[gy][x] = "─", 30

        # Shores and pines, darkest of all, in front.
        for x in range(cols):
            s = self.shore[x]
            if s <= 0:
                continue
            top = rows * 2 - s
            for y in range(top // 2, rows):
                ch[y][x] = "▄" if (y == top // 2 and top % 2) else "█"
                co[y][x] = 31
        for x0, h in self.pines:
            base = rows - 1 - self.shore[x0] // 2
            for i in range(h):
                y = base - h + 1 + i
                if y < 0:
                    continue
                if i == 0:
                    row = "▲"
                elif i == h - 1:
                    if ch[y][x0] == " ":
                        ch[y][x0], co[y][x0] = "┃", 32
                    continue
                else:
                    half = min(3, (i + 1) // 2)
                    row = "▟" + "█" * (2 * half - 1) + "▙" if i % 2 == 0 or half == 1 else "▗" + "█" * (2 * half - 1) + "▖"
                x = x0 - len(row) // 2
                for j, g in enumerate(row):
                    if 0 <= x + j < cols:
                        ch[y][x + j], co[y][x + j] = g, 32

        return ["".join(r) for r in ch], ["".join(CODE[c] for c in r) for r in co]


# -- output --------------------------------------------------------------------------------------
def ansi(rows, codes):
    out = []
    for text, code in zip(rows, codes):
        line, last = [], None
        for g, k in zip(text, code):
            if g != " " and k != last:
                hx = PALETTE[CODE.index(k)]
                line.append("\033[38;2;%d;%d;%dm" % (int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)))
                last = k
            line.append(g)
        out.append("".join(line) + "\033[0m")
    return "\n".join(out)


def render_all(scene):
    return [scene.frame(i) for i in range(FRAMES)]


def change_stats(frames):
    cells = len(frames[0][0]) * len(frames[0][0][0])
    rates = []
    for i in range(len(frames)):
        a, b = frames[i - 1], frames[i]
        n = sum(1 for ra, rb, ca, cb in zip(a[0], b[0], a[1], b[1]) for p, q, r, s in zip(ra, rb, ca, cb) if p != q or r != s)
        rates.append(n / cells)
    return sum(rates) / len(rates), max(rates)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Northern lights in text.")
    ap.add_argument("--seed", type=int, default=SEED)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--still", action="store_true", help="print one frame and exit")
    mode.add_argument("--export", action="store_true", help="print the whole loop as JSON")
    mode.add_argument("--stats", action="store_true", help="print per-frame change rates")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args(argv)
    scene = Aurora(seed=args.seed)

    if args.export:
        frames = render_all(scene)
        json.dump({
            "format": "rariware-lab-frames", "cols": COLS, "rows": ROWS, "fps": FPS, "loop": True,
            "palette": PALETTE,
            "frames": ["\n".join(f[0]) for f in frames],
            "colors": ["\n".join(f[1]) for f in frames],
        }, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")
        return
    if args.stats:
        avg, peak = change_stats(render_all(scene))
        print("cells changed per frame: average %.1f%%, highest %.1f%%" % (avg * 100, peak * 100))
        return
    color = not args.no_color and sys.stdout.isatty()
    if args.still or not sys.stdout.isatty():
        rows, codes = scene.frame(0)
        print(ansi(rows, codes) if color else "\n".join(rows))
        return

    out = sys.stdout
    out.write("Drawing %d frames...\n" % FRAMES)
    out.flush()
    frames = [ansi(*f) if color else "\n".join(f[0]) for f in render_all(scene)]
    out.write("\033[?25l\033[2J")
    try:
        start, shown = time.monotonic(), -1
        while True:
            i = int((time.monotonic() - start) * FPS) % FRAMES
            if i != shown:
                out.write("\033[H" + frames[i] + "\n")
                out.flush()
                shown = i
            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\033[0m\033[?25h\n")
        out.flush()


if __name__ == "__main__":
    main()
