#!/usr/bin/env python3
# snowfall.py - snow falling over pines on a winter night, drawn in text.
#
# A RariWare Lab experiment. Standard library only. Original work, written
# for the Lab in the same contract as aurora.py: one standalone file, one
# seamless loop, no input, no network, no sound.
#
# The scene is layered like a painting, near to far: two big snow-loaded
# pines frame the view, a lantern burns warm on the right, a snowfield
# catches the moonlight in the middle, and behind it two treelines recede
# into haze under a full moon. Snow falls in three depths — far flakes
# drift small and slow, near flakes are big, fast, and sway wide in the
# wind. Nothing here is random per run: one seed makes one night.
#
# Terminal presentation: the animation runs on the alternate screen, so it
# leaves no frames in the scrollback, and the original screen and cursor
# come back when it exits. It checks the terminal size first — it needs
# 120 columns by 41 rows — and waits politely for a resize if the window
# is too small. A larger terminal centers the artwork, and resizing
# mid-animation re-centers it.
#
# Run it in a terminal with 24-bit color (Ctrl+C to stop):
#     python3 snowfall.py
# Other modes:
#     python3 snowfall.py --still            print one frame
#     python3 snowfall.py --export           print the whole loop as JSON (what rariware.com/lab/ plays)
#     python3 snowfall.py --stats            print how much of the picture changes per frame
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
SEED = 2028
TAU = 2 * math.pi
NEED_COLS, NEED_ROWS = COLS, ROWS + 1   # the artwork, plus one footer line

# One palette for the terminal and the browser. Each cell stores an index into it.
# 33 colours, inside the gallery's 36-colour limit.
PALETTE = [
    "#000000",                                                        # 0  blank
    "#0a0f1e", "#101a2e", "#182742", "#1e2f52",                      # 1-4 sky, horizon haze
    "#5d6688", "#a9b3d6", "#f4f6ff",                                  # 5-7 stars, near flakes
    "#e8e6c8", "#f7f3d8", "#8a8f6a", "#3a4666",                      # 8-11 moon, halo, glow
    "#1c2b45", "#2a3d5c",                                            # 12-13 far treeline
    "#0a1512", "#12241c", "#1a2f24",                                  # 14-16 near treeline
    "#0d1f16", "#16301f",                                            # 17-18 foreground pines
    "#dfe8f2", "#b9c9de", "#8fa5c2",                                  # 19-21 snow, snow caps
    "#5a6a8a", "#6a7a96",                                            # 22-23 ground shadow, moonlit snow
    "#3a2a12", "#6a4a1e",                                            # 24-25 lantern post
    "#ffb84d", "#ff9a1e", "#ffe9b8", "#2a2118",                      # 26-29 lantern flame, frame
    "#c98a2e", "#7a5a28",                                            # 30-31 lantern glow
    "#c9d6ea",                                                        # 32 mid flakes
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

LOWER = " ▁▂▃▄▅▆▇█"


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


class Snowfall:
    def __init__(self, cols=COLS, rows=ROWS, seed=SEED):
        rng = random.Random(seed)
        self.cols, self.rows = cols, rows
        self.ground = round(rows * 0.75)              # first snow-ground row
        gr = self.ground

        # Moon: a small full disc, high on the left.
        self.moon = (24, 5)

        # Stars: (x, y) -> (brightness, twinkle cycles per loop, phase).
        # Kept out of the moon's disc and above the treeline.
        self.stars = {}
        for _ in range(cols * gr // 22):
            x, y = rng.randrange(cols), rng.randrange(gr - 8)
            if (x - self.moon[0]) ** 2 + (y - self.moon[1]) ** 2 < 36:
                continue
            self.stars[(x, y)] = (rng.uniform(0.25, 1.0), rng.choice((1, 1, 2)), rng.uniform(0, TAU))

        # Two skylines: a far ridge, dim and hazy, and a near treeline,
        # dark and tall. Heights in eighths of a row so the top edge can
        # use partial blocks.
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
        self.far = skyline(gr - 9.0, (0.8, 0.4, 0.5), (0.9, 2.3, 4.1), lift)
        lift = [rng.uniform(0, TAU) for _ in range(3)]
        self.trees = skyline(gr - 4.0, (1.2, 0.6, 0.7), (0.8, 2.7, 5.3), lift)
        self.pines = []
        for _ in range(6):
            x = rng.randrange(4, cols - 4)
            self.pines.append((x, rng.randint(4, 6)))

        # Snow drifts on the ground: a gentle height per column, at most
        # one row either way so the ground never gaps from the treeline.
        self.drifts = []
        for x in range(cols):
            u = x / cols
            h = 0.8 * math.sin(TAU * 1.1 * u + 0.7) + 0.5 * math.sin(TAU * 3.3 * u + 2.1)
            self.drifts.append(min(0, round(h)))

        # Glints on the snow: faint points of light that come and go.
        self.glints = [(rng.randrange(cols), gr + rng.randrange(1, rows - gr), rng.uniform(0, TAU))
                       for _ in range(cols // 5)]

        # Snowflakes in three depths. Each falls at a whole number of
        # drops per loop and sways side to side on whole cycles too, so
        # the last frame flows back into the first.
        # (x0, y0, fall cycles, sway cycles, phase, size, base sway)
        self.flakes = []
        for _ in range(60):   # far: small, slow, dim
            self.flakes.append((rng.randrange(cols), rng.randrange(rows),
                                2, 1, rng.uniform(0, TAU), 0, 1.0))
        for _ in range(50):   # middle: the bulk of the fall
            self.flakes.append((rng.randrange(cols), rng.randrange(rows),
                                3, rng.choice((1, 2)), rng.uniform(0, TAU), 1, 1.5))
        for _ in range(25):   # near: big, fast, wide in the wind
            self.flakes.append((rng.randrange(cols), rng.randrange(rows),
                                rng.choice((4, 5)), 2, rng.uniform(0, TAU), 2, 2.5))

        # A lantern on a post in the right foreground, the one warm thing
        # in the scene. Its flame flickers on whole cycles per loop.
        self.lantern = (102, gr - 7)

        # Two big foreground pines framing the view, snow on their boughs.
        self.big_pines = [(7, 13), (113, 11)]

    # -- one frame -----------------------------------------------------------------------------
    def frame(self, index, frames=FRAMES):
        """Return (rows of characters, rows of palette codes) for frame `index`."""
        t = index / frames
        cols, rows, gr = self.cols, self.rows, self.ground
        ch = [[" "] * cols for _ in range(rows)]
        co = [[0] * cols for _ in range(rows)]

        # Sky haze: a faint, static dust of shade cells, thickening toward
        # the horizon. It costs nothing per frame and gives the sky depth.
        # The hash keeps it irregular, not a woven pattern.
        for y in range(gr):
            for x in range(cols):
                h = (x * 73 + y * 149 + x * y * 7) % 47
                if y > gr - 12 and h < 2:
                    ch[y][x], co[y][x] = "░", 4
                elif h == 0:
                    ch[y][x], co[y][x] = "░", 2

        # Stars, twinkling slowly.
        for (x, y), (b, n, ph) in self.stars.items():
            tw = b * (0.78 + 0.22 * math.cos(TAU * n * t + ph))
            if tw > 0.72:
                ch[y][x], co[y][x] = "•", 7
            elif tw > 0.45:
                ch[y][x], co[y][x] = "∙", 6
            else:
                ch[y][x], co[y][x] = "·", 5

        # Moon: a small full disc, a soft glow around it, a faint halo ring.
        # Cells are taller than they are wide, so the disc is measured in
        # an ellipse — a circle in cell space would render as a tall pill.
        mx, my = self.moon
        for y in range(my - 6, my + 7):
            for x in range(mx - 6, mx + 7):
                if not (0 <= x < cols and 0 <= y < gr):
                    continue
                d = math.hypot((x - mx) * 0.53, y - my)
                if d <= 2.8:
                    ch[y][x], co[y][x] = "█", 9 if d > 1.7 else 8
                elif 2.8 < d <= 4.2 and (x + 2 * y) % 2 == 0 and ch[y][x] == " ":
                    ch[y][x], co[y][x] = "░", 11
                elif 4.2 < d <= 5.6 and (x + y) % 4 == 0 and ch[y][x] == " ":
                    ch[y][x], co[y][x] = "·", 11
                elif 3.5 < d <= 4.3 and (x + 2 * y) % 3 == 0 and ch[y][x] == " ":
                    ch[y][x], co[y][x] = "·", 10

        # Far treeline: a dim, hazy ridge behind everything, snow on top.
        for x in range(cols):
            top = self.far[x]
            row, part = divmod(top, 8)
            for y in range(row, gr):
                if y == row and part:
                    ch[y][x], co[y][x] = LOWER[8 - part], 13
                elif y == row + 1:
                    ch[y][x], co[y][x] = "█", 13
                else:
                    ch[y][x], co[y][x] = "█", 12

        # Near treeline, with taller pines on top. The top edge carries a
        # cap of snow.
        for x in range(cols):
            top = self.trees[x]
            row, part = divmod(top, 8)
            for y in range(row, gr):
                if y == row and part:
                    ch[y][x], co[y][x] = LOWER[8 - part], 19
                elif y == row + 1:
                    ch[y][x], co[y][x] = "█", 19
                elif y == row + 2:
                    ch[y][x], co[y][x] = "█", 16
                else:
                    ch[y][x], co[y][x] = "█", 15 if y == row + 3 else 14
        for x0, h in self.pines:
            base = self.trees[x0] // 8
            for i in range(h):
                y = base - h + 1 + i
                if y < 0 or y >= gr:
                    continue
                if i == 0:
                    ch[y][x0], co[y][x0] = "▲", 19
                else:
                    half = 1 if i >= 2 else 0
                    for dx in range(-half, half + 1):
                        if 0 <= x0 + dx < cols and ch[y][x0 + dx] == " ":
                            ch[y][x0 + dx], co[y][x0 + dx] = "█", 19 if i == 1 else 15

        # The snow ground: drifts rising and falling, paler where the
        # moonlight catches it, with a sparse scatter of shadowed cells
        # so the field is not one flat slab.
        for x in range(cols):
            top = gr + self.drifts[x]
            for y in range(gr - 1, rows):
                if y < top:
                    continue
                if y == top:
                    ch[y][x], co[y][x] = "█", 19
                elif y == top + 1:
                    ch[y][x], co[y][x] = "█", 20
                elif (x * 73 + y * 149 + x * y * 7) % 23 < 2:
                    ch[y][x], co[y][x] = "█", 22
                else:
                    ch[y][x], co[y][x] = "█", 20

        # Moonlight dappling the snow in a band under the moon.
        for x in range(mx - 12, mx + 13):
            if not (0 <= x < cols):
                continue
            for y in range(gr, rows):
                if ch[y][x] != " " and (x * 73 + y * 149 + x * y * 7) % 4 < 2:
                    co[y][x] = 23

        # Two big foreground pines, snow on each tier of boughs, trunks
        # standing in the snow. They frame the view and give the scene
        # its foreground.
        for x0, height in self.big_pines:
            base = gr + self.drifts[x0]
            tiers, per = 3, max(2, height // 3)
            y = base - height
            if 0 <= y < rows:
                ch[y][x0], co[y][x0] = "▲", 19
            for tier in range(tiers):
                for r in range(per):
                    row = y + 1 + tier * per + r
                    if row >= base:
                        break
                    half = r + tier
                    for dx in range(-half, half + 1):
                        xx = x0 + dx
                        if 0 <= xx < cols and 0 <= row < rows:
                            if r == 0:
                                # Snow sitting on the bough: an upper-half
                                # block, a thin line over the dark branch
                                # below, not a solid white bar.
                                ch[row][xx], co[row][xx] = "▀", 19
                            else:
                                ch[row][xx], co[row][xx] = "█", 18 if tier == 0 else 17
            for row in range(base - 2, base + 2):
                if 0 <= row < rows:
                    ch[row][x0], co[row][x0] = "┃", 24

        # Faint glints on the snow, coming and going.
        for gx, gy, ph in self.glints:
            tw = 0.5 + 0.5 * math.cos(TAU * 2 * t + ph)
            if tw > 0.7 and ch[gy][gx] != " ":
                ch[gy][gx], co[gy][gx] = "·", 19

        # The lantern post and its warm light, flickering gently.
        lx, ly = self.lantern
        flick = 0.85 + 0.15 * math.sin(TAU * 3 * t + 1.2)
        # Warm pool on the snow below it, fading with distance — wide and
        # shallow, a small bright core and a faint wash around it.
        for y in range(gr, rows):
            for x in range(lx - 7, lx + 8):
                if not (0 <= x < cols) or ch[y][x] == " ":
                    continue
                d = ((x - lx) / 7.0) ** 2 + ((y - (gr + 2)) / 2.0) ** 2
                if d <= 0.25:
                    co[y][x] = 30
                elif d <= 1.0:
                    co[y][x] = 31
        # The post stands in front of the treeline and the snow, so it
        # draws over whatever is behind it; the lantern body, drawn next,
        # draws over the post in turn.
        for y in range(ly + 2, rows):
            ch[y][lx], co[y][lx] = "┃", 25
        # Crossbar the lantern hangs from.
        for dx in (-2, -1, 0, 1, 2):
            if 0 <= lx + dx < cols:
                ch[ly + 1][lx + dx], co[ly + 1][lx + dx] = "─", 25
        # Lantern body: frame around a warm flame.
        for dy in range(3):
            y = ly + 2 + dy
            for dx in (-1, 0, 1):
                if 0 <= lx + dx < cols:
                    if dx == 0 and dy == 1:
                        ch[y][lx + dx], co[y][lx + dx] = "●", 27 if flick > 0.9 else 26
                    elif dx == 0:
                        ch[y][lx + dx], co[y][lx + dx] = "█", 28
                    else:
                        ch[y][lx + dx], co[y][lx + dx] = "█", 29
        # A soft halo around the lantern, brighter when the flame is up.
        if flick > 0.88:
            for dx, dy in ((2, 2), (-2, 2), (2, 3), (-2, 3), (0, 1), (0, 5)):
                nx, ny = lx + dx, ly + dy
                if 0 <= nx < cols and 0 <= ny < rows and ch[ny][nx] == " ":
                    ch[ny][nx], co[ny][nx] = "·", 28

        # Snowflakes, falling through the whole frame and wrapping back
        # to the top. Larger flakes fall faster and sway wider, and the
        # whole fall breathes with one slow gust per loop.
        gust = 1.0 + 0.5 * math.sin(TAU * t)
        for x0, y0, fall, sway, ph, size, amp in self.flakes:
            y = (y0 + fall * t * rows) % rows
            x = x0 + round(amp * gust * math.sin(TAU * sway * t + ph))
            xi, yi = int(x) % cols, int(y)
            if size == 2:
                glyph, col = "*", 7
            elif size == 1:
                glyph, col = "•", 32
            else:
                glyph, col = "·", 21
            ch[yi][xi], co[yi][xi] = glyph, col

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
        msg = ("Snowfall needs a terminal at least %d columns by %d rows — yours is "
               "%d by %d. Resize the window and it will start when it fits "
               "(Ctrl+C to quit)." % (NEED_COLS, NEED_ROWS, c, l))
        sys.stdout.write("\r" + msg[:c].ljust(c))
        sys.stdout.flush()
        warned = True
        time.sleep(0.25)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Snow falling over pines on a winter night, in text.")
    ap.add_argument("--seed", type=int, default=SEED)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--still", action="store_true", help="print one frame and exit")
    mode.add_argument("--export", action="store_true", help="print the whole loop as JSON")
    mode.add_argument("--stats", action="store_true", help="print per-frame change rates")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args(argv)
    scene = Snowfall(seed=args.seed)

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
    footer = ("\033[38;2;93;102;136mSnowfall - Ctrl+C to stop\033[0m"
              if color else "Snowfall - Ctrl+C to stop")

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
