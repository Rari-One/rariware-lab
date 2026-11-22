#!/usr/bin/env python3
# fireflies.py - fireflies over a still pond on a summer night, drawn in text.
#
# A RariWare Lab experiment. Standard library only. Original work, written
# for the Lab in the same contract as aurora.py: one standalone file, one
# seamless loop, no input, no network, no sound.
#
# Terminal presentation: the animation runs on the alternate screen, so it
# leaves no frames in the scrollback, and the original screen and cursor
# come back when it exits. It checks the terminal size first — it needs
# 120 columns by 41 rows — and waits politely for a resize if the window
# is too small. A larger terminal centers the artwork, and resizing
# mid-animation re-centers it.
#
# Run it in a terminal with 24-bit color (Ctrl+C to stop):
#     python3 fireflies.py
# Other modes:
#     python3 fireflies.py --still            print one frame
#     python3 fireflies.py --export           print the whole loop as JSON (what rariware.com/lab/ plays)
#     python3 fireflies.py --stats            print how much of the picture changes per frame
#
# The terminal needs a font with box-drawing and block characters —
# JetBrains Mono, the gallery font, covers them — and should be at least
# 120 columns by 41 rows.
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
import shutil
import signal
import sys
import time

COLS, ROWS = 120, 40
FPS = 15
FRAMES = 180          # 12 seconds, one seamless loop
SEED = 2027
TAU = 2 * math.pi
NEED_COLS, NEED_ROWS = COLS, ROWS + 1   # the artwork, plus one footer line

# One palette for the terminal and the browser. Each cell stores an index into it.
PALETTE = [
    "#000000",                                                        # 0  blank
    "#0a0f1e", "#101a2e", "#182742",                                  # 1-3 sky
    "#5d6688", "#a9b3d6", "#f4f6ff",                                  # 4-6 stars
    "#e8e6c8", "#f7f3d8", "#8a8f6a",                                  # 7-9 moon, moon halo
    "#0a1511", "#12241a", "#1a2f22",                                  # 10-12 treeline
    "#0a1a22", "#0e2430", "#12303e", "#1a4a5a",                       # 13-16 pond
    "#c9c49a",                                                        # 17 moon reflection
    "#3a5a1a", "#6a8a2a", "#a8d838", "#d8f758", "#f8ffb8",             # 18-22 fireflies
    "#0d1f14", "#17301f",                                             # 23-24 reeds
    "#4a3520", "#6a4a28",                                             # 25-26 cattails
    "#2a4a3a",                                                        # 27 grass
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

LOWER = " ▁▂▃▄▅▆▇█"
WATER = " ·┈┄╌──━"


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Fireflies:
    def __init__(self, cols=COLS, rows=ROWS, seed=SEED):
        rng = random.Random(seed)
        self.cols, self.rows = cols, rows
        self.horizon = round(rows * 0.65)                 # first pond row
        hz = self.horizon

        # Moon: a small crescent, high on the right, clear of the fireflies.
        self.moon = (96, 5)

        # Stars: (x, y) -> (brightness, twinkle cycles per loop, phase).
        # Kept out of the moon's disc and below the treeline.
        self.stars = {}
        for _ in range(cols * hz // 22):
            x, y = rng.randrange(cols), rng.randrange(hz - 4)
            if (x - self.moon[0]) ** 2 + (y - self.moon[1]) ** 2 < 36:
                continue
            self.stars[(x, y)] = (rng.uniform(0.25, 1.0), rng.choice((1, 1, 2)), rng.uniform(0, TAU))

        # Treeline: a low, uneven silhouette, heights in eighths of a row
        # so the top edge can use partial blocks. A few pines poke above it.
        def skyline(base, amp, k, ph):
            out = []
            for x in range(cols):
                u = x / cols
                h = base + amp[0] * math.sin(TAU * k[0] * u + ph[0]) \
                    + amp[1] * math.sin(TAU * k[1] * u + ph[1]) \
                    + amp[2] * abs(math.sin(TAU * k[2] * u + ph[2]))
                out.append(round(h * 8))
            return out
        lift = [rng.uniform(0, TAU) for _ in range(3)]
        self.trees = skyline(hz - 1.2, (1.1, 0.6, 0.8), (0.9, 2.9, 5.7), lift)
        self.pines = []
        for _ in range(5):
            x = rng.randrange(4, cols - 4)
            self.pines.append((x, rng.randint(3, 4)))

        # Glints on the pond: faint, slow points of light that drift
        # and come back each loop.
        self.glints = [(rng.randrange(cols), hz + rng.randrange(1, rows - hz), rng.uniform(0, TAU))
                       for _ in range(cols // 6)]

        # Fireflies: each one drifts in a slow, closed wander and blinks
        # on its own rhythm. Every time term is a whole number of cycles
        # per loop, so the last frame flows back into the first.
        # (base_x, base_y, drift_x, drift_y, blink cycles, phase, height)
        self.flies = []
        for _ in range(36):
            self.flies.append((
                rng.randrange(6, cols - 6),
                rng.randrange(7, hz - 3),
                rng.uniform(1.5, 4.0),
                rng.uniform(0.8, 2.2),
                rng.choice((2, 3, 3, 4, 5, 6)),
                rng.uniform(0, TAU),
                rng.uniform(0.7, 1.0),
            ))

        # Ripples on the pond: expanding rings that fade out, then start
        # again. (x, y, cycles per loop, phase, max radius)
        self.ripples = []
        for _ in range(6):
            self.ripples.append((
                rng.randrange(12, cols - 12),
                hz + rng.randrange(2, rows - hz - 1),
                rng.choice((1, 1, 2)),
                rng.uniform(0, 1),
                rng.uniform(4.0, 8.0),
            ))

        # Reeds and cattails in the bottom corners, in front of the pond.
        self.reeds = []
        for side in (0, 1):
            for _ in range(7):
                if side == 0:
                    x = rng.randrange(1, 18)
                else:
                    x = rng.randrange(cols - 18, cols - 1)
                self.reeds.append((x, rng.randint(5, 9), rng.random() < 0.45))

    # -- one frame -----------------------------------------------------------------------------
    def frame(self, index, frames=FRAMES):
        """Return (rows of characters, rows of palette codes) for frame `index`."""
        t = index / frames
        cols, rows, hz = self.cols, self.rows, self.horizon
        ch = [[" "] * cols for _ in range(rows)]
        co = [[0] * cols for _ in range(rows)]

        # Stars, twinkling slowly.
        for (x, y), (b, n, ph) in self.stars.items():
            tw = b * (0.78 + 0.22 * math.cos(TAU * n * t + ph))
            if tw > 0.72:
                ch[y][x], co[y][x] = "•", 6
            elif tw > 0.45:
                ch[y][x], co[y][x] = "∙", 5
            else:
                ch[y][x], co[y][x] = "·", 4

        # Moon: a small full disc, with a faint halo ring. A crescent
        # read as a thin sliver at this size, so the disc stays whole.
        mx, my = self.moon
        for y in range(my - 5, my + 6):
            for x in range(mx - 5, mx + 6):
                if not (0 <= x < cols and 0 <= y < hz):
                    continue
                d = math.hypot(x - mx, y - my)
                if d <= 3.0:
                    ch[y][x], co[y][x] = "█", 8 if d > 1.8 else 7
                elif 3.8 < d <= 4.6 and (x + 2 * y) % 3 == 0 and ch[y][x] == " ":
                    ch[y][x], co[y][x] = "·", 9

        # Treeline, far to near in one silhouette, with pines on top.
        for x in range(cols):
            top = self.trees[x]
            row, part = divmod(top, 8)
            for y in range(row, hz):
                if y == row and part:
                    ch[y][x], co[y][x] = LOWER[8 - part], 12
                else:
                    ch[y][x], co[y][x] = "█", 11 if y == row + 1 else 10
        for x0, h in self.pines:
            base = self.trees[x0] // 8
            for i in range(h):
                y = base - h + 1 + i
                if y < 0 or y >= hz:
                    continue
                if i == 0:
                    ch[y][x0], co[y][x0] = "▲", 12
                else:
                    half = 1 if i >= 2 else 0
                    for dx in range(-half, half + 1):
                        if 0 <= x0 + dx < cols and ch[y][x0 + dx] == " ":
                            ch[y][x0 + dx], co[y][x0 + dx] = "█", 11

        # The pond: the moon's reflection, one shimmering column that
        # wobbles as it runs down the water, fading with depth.
        for y in range(hz, rows):
            d = y - hz
            fade = max(0.0, 1.0 - d / (rows - hz + 2))
            if fade < 0.2:
                continue
            center = mx + round(1.5 * math.sin(TAU * (1 * t) + d * 0.8))
            width = 2 if d < 5 else 1
            glyph = "─" if fade > 0.55 else "┄" if fade > 0.35 else "·"
            for x in range(center - width, center + width + 1):
                if 0 <= x < cols and ch[y][x] == " ":
                    ch[y][x], co[y][x] = glyph, 17

        # Faint glints drifting on the pond, so the water is not empty.
        for gx, gy, ph in self.glints:
            x = (gx + round(2.0 * math.sin(TAU * t + ph))) % cols
            if ch[gy][x] == " ":
                ch[gy][x], co[gy][x] = "─", 16

        # Ripples, expanding and fading.
        for x0, y0, cyc, ph, rmax in self.ripples:
            p = (t * cyc + ph) % 1.0
            r = 1 + p * rmax
            alpha = 1.0 - p
            if alpha < 0.15:
                continue
            glyph = "─" if alpha > 0.6 else "┄" if alpha > 0.35 else "·"
            col = 16 if alpha > 0.6 else 15 if alpha > 0.35 else 14
            for dx in (-round(r), round(r)):
                x = x0 + dx
                if 0 <= x < cols and ch[y0][x] == " ":
                    ch[y0][x], co[y0][x] = glyph, col
            for dx in (-round(r * 0.6), round(r * 0.6)):
                for dy in (-1, 1):
                    x, y = x0 + dx, y0 + dy
                    if 0 <= x < cols and hz <= y < rows and ch[y][x] == " " and alpha > 0.5:
                        ch[y][x], co[y][x] = "·", 14

        # Fireflies and their reflections. A fly is drawn only when its
        # blink is on; the reflection is dimmer, squeezed, and rippled.
        for bx, by, ax, ay, n, ph, hgt in self.flies:
            x = bx + round(ax * math.sin(TAU * (1 * t) + ph) + 1.2 * math.sin(TAU * (3 * t) + ph * 2))
            y = by + round(ay * math.sin(TAU * (2 * t) + ph) + 0.7 * math.sin(TAU * (5 * t) + ph))
            x = min(cols - 2, max(1, x))
            y = min(hz - 2, max(2, y))
            blink = 0.5 + 0.5 * math.sin(TAU * n * t + ph)
            blink = smooth(0.35, 0.75, blink) * hgt
            if blink < 0.12:
                continue
            if blink > 0.75:
                glyph, col = "*", 22
            elif blink > 0.5:
                glyph, col = "•", 21
            elif blink > 0.3:
                glyph, col = "•", 20
            else:
                glyph, col = "·", 19
            ch[y][x], co[y][x] = glyph, col
            # A faint halo on the brightest blinks.
            if blink > 0.75:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < cols and 0 <= ny < hz and ch[ny][nx] == " ":
                        ch[ny][nx], co[ny][nx] = "·", 18
            # Reflection in the pond, below the horizon.
            ry = hz + round((hz - y) * 0.55)
            if ry < rows:
                rx = x + round(1.0 * math.sin(TAU * (2 * t) + ph + y))
                if 0 <= rx < cols and ch[ry][rx] == " ":
                    ch[ry][rx], co[ry][rx] = "·" if blink < 0.5 else "∙", 19 if blink > 0.5 else 18

        # Reeds and cattails in the foreground corners, darkest of all.
        for x0, h, cattail in self.reeds:
            base = rows - 1
            for i in range(h):
                y = base - i
                if y < hz:
                    break
                if ch[y][x0] == " ":
                    ch[y][x0], co[y][x0] = "┃", 24
                # A leaning leaf or two.
                if i in (2, 4):
                    dx = -1 if x0 < cols // 2 else 1
                    if 0 <= x0 + dx < cols and ch[y][x0 + dx] == " ":
                        ch[y][x0 + dx], co[y][x0 + dx] = "╱" if dx < 0 else "╲", 27
            if cattail:
                y = base - h
                if hz <= y < rows:
                    ch[y][x0], co[y][x0] = "█", 26
                    if y + 1 < rows:
                        ch[y + 1][x0], co[y + 1][x0] = "█", 25

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


def term_size():
    s = shutil.get_terminal_size()
    return s.columns, s.lines


def wait_for_room():
    """Wait until the terminal fits the artwork, saying so plainly."""
    warned = False
    while True:
        c, l = term_size()
        if c >= NEED_COLS and l >= NEED_ROWS:
            if warned:
                sys.stdout.write("\n")
            return c, l
        msg = ("Fireflies needs a terminal at least %d columns by %d rows — yours is "
               "%d by %d. Resize the window and it will start when it fits "
               "(Ctrl+C to quit)." % (NEED_COLS, NEED_ROWS, c, l))
        sys.stdout.write("\r" + msg[:c].ljust(c))
        sys.stdout.flush()
        warned = True
        time.sleep(0.25)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fireflies over a still pond, in text.")
    ap.add_argument("--seed", type=int, default=SEED)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--still", action="store_true", help="print one frame and exit")
    mode.add_argument("--export", action="store_true", help="print the whole loop as JSON")
    mode.add_argument("--stats", action="store_true", help="print per-frame change rates")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args(argv)
    scene = Fireflies(seed=args.seed)

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
    footer = ("\033[38;2;93;102;136mFireflies - Ctrl+C to stop\033[0m"
              if color else "Fireflies - Ctrl+C to stop")

    def _term(*_args):
        raise KeyboardInterrupt
    try:
        old_term = signal.signal(signal.SIGTERM, _term)
    except (AttributeError, ValueError, OSError):
        old_term = None
    try:
        while True:
            wait_for_room()
            cols, lines = term_size()
            pad_left = (cols - COLS) // 2
            pad_top = (lines - NEED_ROWS) // 2
            out.write("\033[?1049h\033[?25l\033[2J")
            try:
                start, shown = time.monotonic(), -1
                size = (cols, lines)
                while True:
                    c, l = term_size()
                    if c < NEED_COLS or l < NEED_ROWS:
                        break
                    if (c, l) != size:
                        size = (c, l)
                        pad_left = (c - COLS) // 2
                        pad_top = (l - NEED_ROWS) // 2
                        out.write("\033[2J")
                        shown = -1
                    i = int((time.monotonic() - start) * FPS) % FRAMES
                    if i != shown:
                        body = "\n".join(" " * pad_left + ln for ln in frames[i].split("\n"))
                        out.write("\033[H" + "\n" * pad_top + body + "\n" + " " * pad_left + footer + "\n")
                        out.flush()
                        shown = i
                    time.sleep(0.005)
            finally:
                out.write("\033[0m\033[?25h\033[?1049l\n")
                out.flush()
    except KeyboardInterrupt:
        pass
    finally:
        if old_term is not None:
            try:
                signal.signal(signal.SIGTERM, old_term)
            except (AttributeError, ValueError, OSError):
                pass


if __name__ == "__main__":
    main()
