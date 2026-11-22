#!/usr/bin/env python3
"""Beacon — a lonely lighthouse of the North Sea keeps its slow watch.

A single lamp turns once per loop, sweeping a warm beam across the sky and
the water. Stars twinkle, a few shoot across the dark, and a faint wash of
aurora breathes high overhead. The sea shimmers, and the light finds its own
reflection and carries it home. Silent. 120x40, 15 fps, 180 frames (12 s).

Gallery export: --export writes frames.json + manifest.json (stdlib only).
Player package: --package writes beacon.rwl beside this file — manifest.json,
frames.bin (five-byte cells: LE uint16 char + RGB), and this source.
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
SEED = 2031
CELL_W, CELL_H = 8, 15

PALETTE = [
    "#000000", "#05070d", "#0a1224", "#101a30", "#1b2b47",
    "#16273d", "#0e1a2c", "#c8d4e8", "#7d8aa5", "#f2ede0",
    "#8e2f2a", "#3a3f46", "#5b5648", "#ffd98a", "#ffb347",
    "#e8a54d", "#b97e33", "#ffe9b8", "#d8e6f5", "#f5c86e",
    "#2e5d4b", "#4a8a6d", "#7fb89a",
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

# The lamp, in cell space. Beam angles are worked out in pixel space,
# because terminal cells are taller than wide.
LAMP_X, LAMP_Y = 28, 11
TOWER_X0, TOWER_X1, TOWER_TOP, TOWER_BASE = 26, 31, 13, 26
ROCK_Y = 27
SEA_Y = 28

_rng = random.Random(SEED)

# Stars: (x, y, bright, twinkle_phase). A few twinkle, the rest hold still.
STARS = []
while len(STARS) < 90:
    x = _rng.randrange(COLS)
    y = _rng.randrange(0, 25)
    if TOWER_X0 - 2 <= x <= TOWER_X1 + 2 and y >= TOWER_TOP - 4:
        continue
    STARS.append((x, y, _rng.random() < 0.25, _rng.random() * 2 * math.pi))
TWINKLERS = {i for i, s in enumerate(STARS) if s[2]}

# Rock skyline: the top edge of the outcrop, one height per column.
ROCK_TOP = {}
for x in range(18, 41):
    ROCK_TOP[x] = ROCK_Y - (1 if _rng.random() < 0.3 else 0)

# Sea shimmer: a few drifting sparkle positions per row.
SPARKLE = {}
for y in range(SEA_Y, ROWS):
    SPARKLE[y] = [_rng.randrange(COLS) for _ in range(3)]

# Shooting stars: (start frame, x0, y0, dx, dy, life in frames). Three per
# loop, each crossing the open sky and fading out.
METEORS = [
    (18, 95, 3, -2, 1, 14),
    (78, 45, 5, 2, 1, 12),
    (132, 105, 6, -2, 1, 13),
]

# The aurora: two slow curtains drifting overhead, strongest high up and
# fading toward the horizon. (center, drift, phase)
AURORA = [(42, 18, 0.0), (88, 22, 0.4)]


def _sky_color(y):
    if y < 10:
        return 1
    if y < 20:
        return 2
    return 3


def _sea_color(y):
    return 4 if y % 3 == 0 else (5 if y % 3 == 1 else 6)


def _beam_index(intensity):
    if intensity > 0.6:
        return 17
    if intensity > 0.35:
        return 14
    if intensity > 0.15:
        return 15
    return 16


def render_frame(f):
    """Return (chars, colors): two lists of 40 strings, 120 cells each."""
    t = f / FRAMES
    chars = [[" "] * COLS for _ in range(ROWS)]
    cols = [[0] * COLS for _ in range(ROWS)]

    # Sky and stars.
    for y in range(SEA_Y):
        for x in range(COLS):
            cols[y][x] = _sky_color(y)
    # A faint wash of aurora: two narrow curtains hanging down from the
    # sky, their edges meandering as they breathe. Brightest along the
    # lower edge, fading upward. Every time term runs a whole number of
    # cycles per loop, so the loop has no seam. @marker aurora
    for y in range(2, 17):
        vfall = (y - 2) / 14
        for x in range(COLS):
            inten = 0.0
            for center, drift, phase in AURORA:
                cx = (center + drift * math.sin(2 * math.pi * (t + phase))
                      + 5 * math.sin(2 * math.pi * (y / 9 + 2 * t + phase)))
                inten += math.exp(-((x - cx) / 5.5) ** 2)
            inten *= 0.45 * vfall * (0.7 + 0.3 * math.sin(2 * math.pi * (x / 25 + t * 2)))
            if inten > 0.5:
                chars[y][x] = "░"
                cols[y][x] = 22
            elif inten > 0.3:
                chars[y][x] = "░"
                cols[y][x] = 21
            elif inten > 0.15:
                chars[y][x] = "░"
                cols[y][x] = 20
    for i, (x, y, bright, phase) in enumerate(STARS):
        if i in TWINKLERS:
            glow = 0.65 + 0.35 * math.sin(2 * math.pi * (t * 2 + phase))
            chars[y][x] = "*" if glow > 0.8 else "·"
            cols[y][x] = 7 if glow > 0.8 else 8
        else:
            chars[y][x] = "*" if bright else "·"
            cols[y][x] = 7 if bright else 8

    # Sea, with a slow shimmer that drifts back and forth, not one way,
    # so the loop closes cleanly.
    for y in range(SEA_Y, ROWS):
        drift = int(6 * math.sin(2 * math.pi * (t + y * 0.05)))
        for x in range(COLS):
            cols[y][x] = _sea_color(y)
            chars[y][x] = "~"
            for sx in SPARKLE[y]:
                if (x - sx - drift) % COLS < 2:
                    cols[y][x] = 18
                    chars[y][x] = "-"

    # The beam. @marker beam
    theta = -math.pi / 2 + 2 * math.pi * t
    lx, ly = LAMP_X * CELL_W + CELL_W // 2, LAMP_Y * CELL_H + CELL_H // 2
    sin_t, cos_t = math.sin(theta), math.cos(theta)
    hit_x = None
    if sin_t > 0.05:
        sea_px = SEA_Y * CELL_H
        hit_x = lx + cos_t * (sea_px - ly) / sin_t
    for y in range(ROWS):
        for x in range(COLS):
            cx, cy = x * CELL_W + CELL_W // 2, y * CELL_H + CELL_H // 2
            dx, dy = cx - lx, cy - ly
            dist = math.hypot(dx, dy)
            if dist < 4:
                continue
            ang = math.atan2(dy, dx)
            d = (ang - theta + math.pi) % (2 * math.pi) - math.pi
            if abs(d) < 0.12:
                inten = (1 - abs(d) / 0.12) * max(0.0, 1 - dist / 1000)
                if inten > 0.12:
                    if y < SEA_Y:
                        chars[y][x] = "░"
                        cols[y][x] = _beam_index(inten)
                    else:
                        cols[y][x] = _beam_index(inten)
    # Shooting stars, bright head and a fading tail. @marker meteors
    for start, x0, y0, dx, dy, life in METEORS:
        age = f - start
        if 0 <= age < life:
            hx, hy = x0 + dx * age, y0 + dy * age
            if 0 <= hx < COLS and 0 <= hy < SEA_Y:
                chars[hy][hx] = "*"
                cols[hy][hx] = 7
            tail_char = "╲" if dx > 0 else "╱"
            for k in range(1, 5):
                tx, ty = hx - dx * k, hy - dy * k
                if 0 <= tx < COLS and 0 <= ty < SEA_Y:
                    chars[ty][tx] = tail_char
                    cols[ty][tx] = 8
    # Where the beam meets the water, it lays a road of light. @marker reflection
    if hit_x is not None:
        for y in range(SEA_Y, ROWS):
            for x in range(COLS):
                cx = x * CELL_W + CELL_W // 2
                spread = 26 + (y - SEA_Y) * 4
                glow = math.exp(-((cx - hit_x) / spread) ** 2)
                glow *= 0.75 + 0.25 * math.sin(2 * math.pi * (t * 3 + x * 0.13))
                if glow > 0.55:
                    cols[y][x] = 19
                    chars[y][x] = "~"
                elif glow > 0.3 and cols[y][x] in (4, 5, 6):
                    cols[y][x] = 15

    # Rocks, drawn over the sea. @marker rocks
    for x, top in ROCK_TOP.items():
        for y in range(top, SEA_Y + 2):
            chars[y][x] = "█" if (x + y) % 3 else "▓"
            cols[y][x] = 11 if (x + y) % 3 else 12

    # The tower, drawn over the beam. @marker tower
    for y in range(TOWER_TOP, TOWER_BASE + 1):
        for x in range(TOWER_X0, TOWER_X1 + 1):
            chars[y][x] = "█"
            cols[y][x] = 10 if y in (17, 18, 19, 22, 23, 24) else 9
    # The lamp room. @marker lamp
    for y in (10, 11, 12):
        for x in range(27, 31):
            chars[y][x] = "█"
            cols[y][x] = 13
    for x in range(27, 31):
        chars[9][x] = "▄"
        cols[9][x] = 11

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
        "id": "beacon", "title": "Beacon",
        "description": "A lonely lighthouse of the North Sea keeps its slow watch, drawn in text. Its lamp turns once per loop, sweeping a warm beam across the sky and laying a road of light on the water, while shooting stars cross overhead and a faint aurora breathes high above.",
        "alt": "A lighthouse on rocks at night, its beam sweeping across a dark North Sea under stars, shooting stars, and a faint aurora.",
        "source": "beacon.py", "frames": "frames.json",
        "cols": COLS, "rows": ROWS, "fps": FPS, "frameCount": FRAMES,
        "stillFrame": 0, "license": "MIT",
        "copyright": "Copyright (c) 2026 Rari-One",
        "featured": False, "order": 4,
    }
    (here / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return len(raw)


def markers():
    """Source annotations, found by their @marker comments in this file."""
    out = []
    lines = Path(__file__).read_text().splitlines()
    want = [("beam", 0), ("aurora", 22), ("lamp", 45),
            ("meteors", 78), ("reflection", 90), ("tower", 135)]
    for name, frame in want:
        for i, line in enumerate(lines, 1):
            if f"@marker {name}" in line:
                out.append({"frame": frame, "file": "source/beacon.py", "line": i})
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
        "version": 1, "title": "Beacon", "cols": COLS, "rows": ROWS,
        "fps": FPS, "frames": FRAMES, "background": "#05070d",
        "sources": ["source/beacon.py"], "markers": markers(),
    }
    out = here / "beacon.rwl"
    # Fixed entry dates, so the package is byte-identical on every build.
    fixed = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("manifest.json", json.dumps(manifest).encode()),
                           ("frames.bin", bytes(cells))):
            info = zipfile.ZipInfo(name, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        info = zipfile.ZipInfo("source/beacon.py", date_time=fixed)
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
                sys.stdout.write(f"Beacon needs {need_cols} columns by {need_rows} rows.\n")
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
                buf.append("\033[%d;%dH\033[0mBeacon — Ctrl+C to stop" % (pad_y + ROWS + 1, pad_x + 1))
                sys.stdout.write("".join(buf))
                sys.stdout.flush()
                time.sleep(max(0, 1 / FPS - (time.time() - start - f / FPS)))
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[?1049l")
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description="Beacon — a lighthouse keeps its slow watch.")
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
        print(f"beacon.rwl: {size} bytes")
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
