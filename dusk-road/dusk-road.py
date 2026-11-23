#!/usr/bin/env python3
"""Dusk Road — a road home through the woods at dusk.

The road runs away from you to a small warm light on the horizon, pines
sliding past on either side in layered perspective, fireflies drifting
over the grass, mist lying low over the road. Silent. 120x40, 15 fps,
180 frames (12 s).

Gallery export: --export writes frames.json + manifest.json (stdlib only).
Player package: --package writes dusk-road.rwl beside this file —
manifest.json, frames.bin (five-byte cells: LE uint16 char + RGB), and
this source.
"""
import argparse
import json
import math
import random
import struct
import sys
import time
import zipfile
from pathlib import Path

COLS, ROWS, FPS, FRAMES = 120, 40, 15, 180
SEED = 4117
CELL_W, CELL_H = 8, 15
HORIZON_Y = 16
VP_X = 60

PALETTE = [
    "#05070d", "#0a0e1e", "#141b33", "#232a4a", "#4a3a5e",
    "#7a5238", "#f5e9c8", "#d8c9a0", "#8a93b8", "#c8d4e8",
    "#0e1a12", "#16281c", "#1e3a26", "#2e5238", "#a87e42",
    "#3a2f28", "#4a3a30", "#5d4a3c", "#7a6248", "#2a2118",
    "#1c2416", "#243020", "#c9a86a", "#6a4a28", "#b8a8d8",
    "#8a7ab0", "#d8e6a0", "#7a9a4a", "#3a2a1a", "#241a12",
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

_rng = random.Random(SEED)

# The moon, drawn in pixel space so it reads round: cells are taller
# than wide, so the ellipse is wider in cells than in rows.
MOON_X, MOON_Y, MOON_RY = 86, 5, 3

# Stars above the horizon. A few twinkle, the rest hold still.
STARS = []
while len(STARS) < 60:
    x = _rng.randrange(COLS)
    y = _rng.randrange(0, 14)
    if (x - MOON_X) ** 2 + (y - MOON_Y) ** 2 < 64:
        continue
    STARS.append((x, y, _rng.random() < 0.25, _rng.random() * 2 * math.pi))
TWINKLERS = {i for i, s in enumerate(STARS) if s[2]}

# The distant treeline: a jagged silhouette along the horizon.
TREELINE = {}
for x in range(COLS):
    TREELINE[x] = 1 + (1 if (x * 13) % 3 == 0 else 0) + (1 if (x * 7) % 5 == 0 else 0)

# Pines beside the road. Each has a side, a lane offset, and a phase;
# the phase runs one whole cycle per loop, so a tree travels from the
# horizon to beside the viewer and the loop closes cleanly.
TREES = []
for side in (-1, 1):
    for i in range(5):
        TREES.append((side, _rng.random(), i / 5 + _rng.random() * 0.06))

# Fireflies over the grass, each on its own rhythm.
FLIES = []
for _ in range(14):
    FLIES.append((
        _rng.randrange(8, 112), _rng.randrange(19, 37),
        _rng.random() * 2 * math.pi, _rng.random() * 2 * math.pi,
        _rng.random() * 2 * math.pi,
    ))


def road_half(y):
    """Half-width of the road in cells at row y."""
    if y <= HORIZON_Y:
        return 2
    u = (y - HORIZON_Y) / (ROWS - 1 - HORIZON_Y)
    return 2 + 24 * u ** 1.6


def road_color(y):
    if y < 22:
        return 15
    if y < 30:
        return 16
    return 17


def render_frame(f):
    """Return (chars, colors): two lists of 40 strings, 120 cells each."""
    t = f / FRAMES
    chars = [[" "] * COLS for _ in range(ROWS)]
    cols = [[0] * COLS for _ in range(ROWS)]

    # Sky: dark overhead, warming toward the horizon. The horizon band
    # itself is drawn, the rest is empty dark.
    for y in range(HORIZON_Y):
        for x in range(COLS):
            cols[y][x] = 1 if y < 6 else (2 if y < 11 else 3)
    for x in range(COLS):
        chars[HORIZON_Y - 1][x] = "░"
        cols[HORIZON_Y - 1][x] = 5 if (x * 3) % 4 else 4

    # The moon, an ellipse in pixel space. @marker moon
    rx = MOON_RY * CELL_H / CELL_W
    for dy in range(-MOON_RY - 1, MOON_RY + 2):
        for dx in range(-8, 9):
            x, y = MOON_X + dx, MOON_Y + dy
            if not (0 <= x < COLS and 0 <= y < HORIZON_Y):
                continue
            r = (dx / rx) ** 2 + (dy / MOON_RY) ** 2
            if r <= 1.0:
                chars[y][x] = "█"
                cols[y][x] = 6

    # Stars.
    for i, (x, y, bright, phase) in enumerate(STARS):
        if i in TWINKLERS:
            glow = 0.65 + 0.35 * math.sin(2 * math.pi * (t * 2 + phase))
            chars[y][x] = "*" if glow > 0.8 else "·"
            cols[y][x] = 9 if glow > 0.8 else 8
        else:
            chars[y][x] = "*" if bright else "·"
            cols[y][x] = 9 if bright else 8

    # The distant treeline, and the small warm light the road leads to.
    # @marker home
    for x, h in TREELINE.items():
        for y in range(HORIZON_Y - h, HORIZON_Y):
            chars[y][x] = "█"
            cols[y][x] = 10 if (x + y) % 2 else 11
    for y in (12, 13, 14, 15):
        for x in range(56, 65):
            chars[y][x] = "█"
            cols[y][x] = 29
    for x in range(57, 64):
        chars[12][x] = "▄"
        cols[12][x] = 29
    for x in (58, 62):
        chars[15][x] = "█"
        cols[15][x] = 22

    # Grass and road below the horizon. @marker road
    for y in range(HORIZON_Y + 1, ROWS):
        half = road_half(y)
        for x in range(COLS):
            if VP_X - half <= x <= VP_X + half:
                chars[y][x] = "░"
                cols[y][x] = road_color(y)
            else:
                v = (x * 5 + y * 7) % 3
                if v == 0:
                    chars[y][x] = "·"
                    cols[y][x] = 20 if (x + y) % 2 else 21
                else:
                    cols[y][x] = 19

    # Centre dashes, travelling toward the viewer. Two whole cycles per
    # loop, so the loop closes cleanly.
    for k in range(4):
        d = (k / 4 + t * 2) % 1.0
        y0 = HORIZON_Y + int((ROWS - HORIZON_Y) * d ** 2.2)
        tall = max(1, int(3 * d))
        wide = 1 if d < 0.5 else 2
        for y in range(y0, min(ROWS, y0 + tall)):
            for x in range(VP_X - wide + 1, VP_X + 1):
                chars[y][x] = "█"
                cols[y][x] = 18

    # Pines, far first so near ones overlap them. @marker trees
    placed = []
    for side, lane, p0 in TREES:
        p = (p0 + t) % 1.0
        y_base = HORIZON_Y + int((ROWS - 1 - HORIZON_Y) * p ** 1.7)
        h = max(2, int(2 + 28 * p ** 2.0))
        half = road_half(y_base)
        # Near the viewer the tree slides sideways off the frame, so by
        # the time its phase wraps back to the horizon it is already
        # out of sight — no pop.
        cx = VP_X + side * int(half + 5 + lane * 26 * (0.25 + 0.75 * p) + 30 * p ** 3)
        placed.append((p, side, cx, y_base, h))
    placed.sort(key=lambda z: z[0])
    for p, side, cx, y_base, h in placed:
        top_y = y_base - h + 1
        for r in range(h):
            y = top_y + r
            if y < HORIZON_Y or y >= ROWS:
                continue
            frac = r / max(1, h - 1)
            hw = max(0, int(frac * h * 0.45))
            for x in range(cx - hw, cx + hw + 1):
                if 0 <= x < COLS:
                    chars[y][x] = "▓" if (x + y) % 2 else "█"
                    rim = (x == cx + hw) if side < 0 else (x == cx - hw)
                    cols[y][x] = 14 if (rim and frac > 0.2) else (12 if frac < 0.5 else 11)
        for y in range(max(HORIZON_Y, y_base - 2), y_base + 1):
            if 0 <= cx < COLS:
                chars[y][cx] = "█"
                cols[y][cx] = 28

    # Mist lying low over the road, breathing slowly. It only tints
    # road and grass glyphs, never the trees, so the landscape stays
    # continuous — no solid blocks. Every time term runs whole cycles
    # per loop. @marker mist
    for y in range(HORIZON_Y + 1, HORIZON_Y + 7):
        for x in range(COLS):
            inten = (0.5 + 0.5 * math.sin(2 * math.pi * (x / 45 + t * 2))
                     * math.sin(2 * math.pi * (x / 23 - t)))
            if inten > 0.82 and chars[y][x] in ("░", "·"):
                cols[y][x] = 24 if inten > 0.92 else 25

    # Fireflies over the grass. @marker fireflies
    for x0, y0, ph1, ph2, ph3 in FLIES:
        x = int(x0 + 6 * math.sin(2 * math.pi * (t + ph1)))
        y = int(y0 + 2 * math.sin(2 * math.pi * (t * 2 + ph2)))
        if not (0 <= x < COLS and HORIZON_Y < y < ROWS):
            continue
        if VP_X - road_half(y) <= x <= VP_X + road_half(y):
            continue
        b = math.sin(2 * math.pi * (t * 3 + ph3))
        if b > 0.55:
            chars[y][x] = "*"
            cols[y][x] = 26
        elif b > 0.2:
            chars[y][x] = "·"
            cols[y][x] = 27

    return (["".join(r) for r in chars], ["".join(CODE[c] for c in r) for r in cols])


def build_frames():
    return [render_frame(f) for f in range(FRAMES)]


def stats(frames):
    def changed(a, b):
        n = sum(1 for ra, rb in zip(a[0], b[0]) for ca, cb in zip(ra, rb) if ca != cb)
        n += sum(1 for ra, rb in zip(a[1], b[1]) for ca, cb in zip(ra, rb) if ca != cb)
        return n / (COLS * ROWS) * 100
    ds = [changed(frames[i], frames[(i + 1) % FRAMES]) for i in range(FRAMES)]
    return sum(ds) / len(ds), max(ds), ds[-1], sum(ds) / len(ds) * COLS * ROWS * FPS / 100


def export(frames, here):
    palette = PALETTE
    data = {
        "format": "rariware-lab-frames",
        "cols": COLS, "rows": ROWS, "fps": FPS, "loop": True,
        "palette": palette,
        "frames": ["\n".join(c) for c, _ in frames],
        "colors": ["\n".join(k) for _, k in frames],
    }
    raw = json.dumps(data, separators=(",", ":")).encode()
    (here / "frames.json").write_bytes(raw)
    manifest = {
        "format": "rariware-lab-manifest",
        "id": "dusk-road", "title": "Dusk Road",
        "description": "A road home through the woods at dusk, drawn in text. Pines slide past on either side, fireflies drift over the grass, mist lies low over the road, and a small warm light waits on the horizon.",
        "alt": "A road running away through dark pines at dusk toward a small warm light on the horizon, under a low moon.",
        "source": "dusk-road.py", "frames": "frames.json",
        "cols": COLS, "rows": ROWS, "fps": FPS, "frameCount": FRAMES,
        "stillFrame": 0, "license": "MIT",
        "copyright": "Copyright (c) 2026 Rari-One",
        "featured": False, "order": 6,
    }
    (here / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return len(raw)


def markers():
    """Source annotations, found by their @marker comments in this file."""
    out = []
    lines = Path(__file__).read_text().splitlines()
    want = [("road", 0), ("moon", 30), ("trees", 60),
            ("home", 90), ("fireflies", 120), ("mist", 150)]
    for name, frame in want:
        for i, line in enumerate(lines, 1):
            if f"@marker {name}" in line:
                out.append({"frame": frame, "file": "source/dusk-road.py", "line": i})
                break
    return out


def package(frames, here):
    cells = bytearray()
    for chars, keys in frames:
        for y in range(ROWS):
            for x in range(COLS):
                rgb = PALETTE[CODE.index(keys[y][x])]
                r, g, b = int(rgb[1:3], 16), int(rgb[3:5], 16), int(rgb[5:7], 16)
                cells += struct.pack("<HBBB", ord(chars[y][x]), r, g, b)
    manifest = {
        "version": 1, "title": "Dusk Road", "cols": COLS, "rows": ROWS,
        "fps": FPS, "frames": FRAMES, "background": "#05070d",
        "sources": ["source/dusk-road.py"], "markers": markers(),
    }
    out = here / "dusk-road.rwl"
    fixed = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("manifest.json", json.dumps(manifest).encode()),
                           ("frames.bin", bytes(cells))):
            info = zipfile.ZipInfo(name, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        info = zipfile.ZipInfo("source/dusk-road.py", date_time=fixed)
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, Path(__file__).read_bytes())
    return out.stat().st_size


def run_terminal(frames):
    import shutil
    need_cols, need_rows = COLS, ROWS + 1
    print(f"Drawing {FRAMES} frames...")
    sys.stdout.write("\033[?1049h\033[?25l")
    try:
        while True:
            w, h = shutil.get_terminal_size()
            if w < need_cols or h < need_rows:
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.write(f"Dusk Road needs {need_cols} columns by {need_rows} rows.\n")
                sys.stdout.flush()
                time.sleep(0.5)
                continue
            pad_x, pad_y = (w - COLS) // 2, (h - ROWS - 1) // 2
            start = time.time()
            for f in range(FRAMES):
                chars, keys = frames[f]
                buf = ["\033[H"]
                for y in range(ROWS):
                    buf.append("\033[%d;%dH" % (pad_y + y + 1, pad_x + 1))
                    for x in range(COLS):
                        g = chars[y][x]
                        if g == " ":
                            continue
                        rgb = PALETTE[CODE.index(keys[y][x])]
                        r, gg, b = int(rgb[1:3], 16), int(rgb[3:5], 16), int(rgb[5:7], 16)
                        buf.append(f"\033[38;2;{r};{gg};{b}m{g}")
                buf.append("\033[%d;%dH\033[0mDusk Road — Ctrl+C to stop" % (pad_y + ROWS + 1, pad_x + 1))
                sys.stdout.write("".join(buf))
                sys.stdout.flush()
                time.sleep(max(0, 1 / FPS - (time.time() - start - f / FPS)))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[?1049l")
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description="Dusk Road — a road home through the woods at dusk.")
    ap.add_argument("--still", action="store_true")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--package", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()
    here = Path(__file__).parent
    frames = build_frames()
    if args.stats:
        avg, mx, seam, redraw = stats(frames)
        print(f"change avg {avg:.2f}% max {mx:.2f}% seam {seam:.2f}% redraw ~{redraw:.0f} cells/s")
        print(f"colors: {len(PALETTE)} palette entries")
    if args.export:
        size = export(frames, here)
        print(f"frames.json: {size} bytes")
    if args.package:
        size = package(frames, here)
        print(f"dusk-road.rwl: {size} bytes")
    if args.still:
        chars, keys = frames[args.frame % FRAMES]
        for y in range(ROWS):
            line = ""
            for x in range(COLS):
                g = chars[y][x]
                if args.no_color or g == " ":
                    line += g
                else:
                    rgb = PALETTE[CODE.index(keys[y][x])]
                    r, gg, b = int(rgb[1:3], 16), int(rgb[3:5], 16), int(rgb[5:7], 16)
                    line += f"\033[38;2;{r};{gg};{b}m{g}\033[0m"
            print(line)
        return
    if not (args.export or args.package or args.stats):
        run_terminal(frames)


if __name__ == "__main__":
    main()
