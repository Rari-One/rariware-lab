#!/usr/bin/env python3
"""Logon Wink — a little greeter winks at you when you log on.

A small original character with teal twin-tails stands on a dark screen,
like the ASCII pranks left on a buddy's computer. She mostly watches you
with both eyes open, then winks — twice per loop — with a sparkle at the
corner of her eye. Stars twinkle, a shooting star crosses, the headphones
pulse with the music, and the prompt below backspaces and retypes itself
mid-loop: > logon. A music-box chime rings with every wink, soft key clicks
with every keystroke. Silent no longer. 120x40, 15 fps, 180 frames (12 s).

Gallery export: --export writes frames.json + manifest.json (stdlib only).
Player package: --package writes logon-wink.rwl beside this file, with the
score rendered by score.py (stdlib only) as audio.pcm when it is available.
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
SEED = 2033
CELL_W, CELL_H = 8, 15

PALETTE = [
    "#000000",  # 0 blank
    "#0a0e14",  # 1 background
    "#111a28",  # 2 background 2
    "#1a2638",  # 3 background 3
    "#39c5bb",  # 4 teal hair
    "#2a9d97",  # 5 teal dark
    "#1f7a76",  # 6 teal shadow
    "#f2d5c4",  # 7 skin
    "#e8b89a",  # 8 skin shadow
    "#20242e",  # 9 eyes / outline
    "#ff8fa3",  # a blush pink
    "#ffd98a",  # b warm sparkle
    "#c8d4e8",  # c pale stars
    "#7d8aa5",  # d dim stars
    "#f5f0e6",  # e prompt text
    "#8e6fb8",  # f soft violet note
    "#ff6b8a",  # g deep blush (winks)
    "#5ce8e0",  # h bright teal (headphone pulse)
]
CODE = "0123456789abcdefghijklmnopqrstuvwxyz"

_rng = random.Random(SEED)
STARS = []
while len(STARS) < 70:
    x = _rng.randrange(COLS)
    y = _rng.randrange(0, 32)
    if 40 <= x <= 82 and 5 <= y <= 30:
        continue
    STARS.append((x, y, _rng.random() < 0.3, _rng.random() * 2 * math.pi))
SPARKLES = [( _rng.randrange(20, 100), _rng.randrange(2, 30),
              _rng.random() * 2 * math.pi) for _ in range(14)]
NOTES = [(34, 12, 0.0), (86, 9, 0.33), (92, 16, 0.66)]

# The melody is the beat grid the picture reads: every chime lights the
# headphones for two frames, so each note has a glow you can watch.
try:
    import score as _score
    _MELODY_FRAMES = {f for f, _, _ in _score.MELODY}
except Exception:
    _MELODY_FRAMES = set()
_PULSE = {f for m in _MELODY_FRAMES for f in (m, m + 1)}

PROMPT = "> logon"


def _prompt_text(f):
    """Return (text, cursor_x) for the prompt at frame f. @marker typing

    Full text most of the loop; it backspaces (frames 90-103) and retypes
    (104-131) mid-loop, so the loop seam stays clean.
    """
    if 90 <= f < 104:
        step = (f - 90) // 2          # 0..6
        shown = 6 - step              # 6..0
        return PROMPT[:shown], 10 + shown
    if 104 <= f < 132:
        step = (f - 104) // 4         # 0..6
        shown = step + 1              # 1..7
        return PROMPT[:shown], 10 + shown
    return PROMPT, 17


def _eye_state(f):
    """Return (left_closed, right_closed). Two winks per loop, one quick blink."""
    if 36 <= f < 54 or 126 <= f < 144:
        return False, True
    if 84 <= f < 89:  # @marker blink
        return True, True
    return False, False


def render_frame(f):
    """Return (chars, colors): two lists of 40 strings, 120 cells each."""
    t = f / FRAMES
    chars = [[" "] * COLS for _ in range(ROWS)]
    cols = [[0] * COLS for _ in range(ROWS)]

    def put(x, y, ch, ci):
        if 0 <= x < COLS and 0 <= y < ROWS:
            chars[y][x] = ch
            cols[y][x] = ci

    def text(x, y, s, ci):
        for i, ch in enumerate(s):
            put(x + i, y, ch, ci)

    # Background gradient.
    for y in range(ROWS):
        for x in range(COLS):
            cols[y][x] = 1 if y < 14 else (2 if y < 28 else 3)

    # Stars. @marker sparkles
    for x, y, tw, ph in STARS:
        if tw:
            bright = 0.5 + 0.5 * math.sin(2 * math.pi * (3 * t + ph / (2 * math.pi)))
            ci = 12 if bright > 0.6 else 13
        else:
            ci = 13
        put(x, y, ".", ci)
    for x, y, ph in SPARKLES:
        if math.sin(2 * math.pi * (2 * t + ph / (2 * math.pi))) > 0.4:
            put(x, y, "*", 11)

    # Shooting star, once per loop, high up where the hair never reaches.
    # @marker star
    if 150 <= f < 165:
        k = f - 150
        hx = 8 + 3 * k
        hy = 2 + k // 8
        for i in range(4):
            put(hx - i, hy, "*" if i == 0 else ".", 14 if i == 0 else 13)

    # Twin tails, swaying. Every time term runs whole cycles per loop,
    # so the loop has no seam. @marker hair
    for side in (-1, 1):
        base = 47 if side < 0 else 72
        for y in range(9, 30):
            dx = int(round(math.sin(2 * math.pi * (2 * t + y / 30.0))))
            w = 4 if y < 27 else 2
            for i in range(w):
                x = base + dx + i if side < 0 else base + dx + i
                # left tail occupies base..base+3, right tail base..base+3
                put(x, y, "#", 4 if i in (1, 2) else 5)
        # tail tie
        put(base + 1, 9, "o", 10)

    # Head: skin, with shadowed edges. @marker face
    for y in range(11, 20):
        for x in range(53, 68):
            if (y == 11 and x in (53, 67)) or (y == 19 and x in (53, 67)):
                continue
            put(x, y, " ", 7)
            cols[y][x] = 7
    # Fill skin as blocks so the face reads in the gallery render.
    for y in range(11, 20):
        for x in range(53, 68):
            if chars[y][x] == " " and cols[y][x] == 7:
                chars[y][x] = "#"
    for y in range(11, 20):
        put(53, y, "#", 8)
        put(67, y, "#", 8)

    # Hair top and bangs.
    for x in range(50, 71):
        put(x, 7, "#", 4)
        put(x, 8, "#", 4)
    for x in range(51, 70):
        put(x, 9, "#", 4)
        put(x, 10, "#", 5)
    for x in range(53, 68, 3):
        put(x, 11, "#", 4)
        put(x + 1, 11, "#", 4)
    # Ahoge.
    put(60, 5, "/", 4)
    put(61, 6, "/", 4)
    # Headphone band and cups. The cups light up on every chime beat.
    for x in range(52, 69):
        put(x, 8, "#", 6)
    pulse = f in _PULSE
    for y in range(13, 17):
        put(51, y, "#", 17 if pulse else 4)
        put(52, y, "#", 4 if pulse else 5)
        put(68, y, "#", 4 if pulse else 5)
        put(69, y, "#", 17 if pulse else 4)

    # Eyes. @marker wink
    left_closed, right_closed = _eye_state(f)
    for (ex, closed) in ((56, left_closed), (63, right_closed)):
        if closed:
            put(ex, 15, "^", 9)
            put(ex + 1, 15, "^", 9)
        else:
            put(ex, 15, "#", 9)
            put(ex + 1, 15, "#", 9)
    # Wink sparkle at the winking eye. @marker wink2
    if right_closed:
        put(68, 13, "*", 11)
        put(69, 14, "+", 11)
        text(72, 11, "hi!", 14)
        if f in range(36, 42) or f in range(126, 132):
            put(70, 12, "*", 11)
            put(71, 13, "+", 11)
    # Blush and smile. The blush deepens while she winks.
    blush = 16 if right_closed else 10
    put(54, 16, "o", blush)
    put(55, 16, "o", blush)
    put(65, 16, "o", blush)
    put(66, 16, "o", blush)
    put(59, 18, "\\", 9)
    put(60, 18, "_", 9)
    put(61, 18, "/", 9)

    # Shoulders and collar.
    for y in range(20, 28):
        for x in range(54, 67):
            put(x, y, "#", 5 if y < 22 else 6)
    for x in range(58, 63):
        put(x, 20, "#", 14)
    put(59, 21, "o", 10)
    put(60, 21, "o", 10)
    put(61, 21, "o", 10)

    # Drifting notes. They light up warm on the second wink. @marker notes
    for x0, y0, ph in NOTES:
        dy = int(round(2 * math.sin(2 * math.pi * (t + ph))))
        if 126 <= f < 144:
            put(x0, y0 + dy - 1, "*", 11)
        else:
            put(x0, y0 + dy, "*", 15 if ph == 0.0 else 11)

    # Logon prompt, typing itself mid-loop, cursor blinking. @marker prompt
    ptext, cursor_x = _prompt_text(f)
    text(10, 36, ptext, 14)
    if (90 <= f < 132) or (f // 15) % 2 == 0:
        put(cursor_x, 36, "#", 14)
    text(10, 37, "a little greeter, winking at you.", 13)

    return (["".join(r) for r in chars],
            ["".join(CODE[c] for c in r) for r in cols])


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
    data = {
        "format": "rariware-lab-frames",
        "cols": COLS, "rows": ROWS, "fps": FPS, "loop": True,
        "palette": PALETTE,
        "frames": ["\n".join(c) for c, _ in frames],
        "colors": ["\n".join(k) for _, k in frames],
    }
    raw = json.dumps(data, separators=(",", ":")).encode()
    (here / "frames.json").write_bytes(raw)
    manifest = {
        "format": "rariware-lab-manifest",
        "id": "logon-wink", "title": "Logon Wink",
        "description": "A little greeter winks at you when you log on, drawn in text. Teal twin-tails, a blinking prompt below, stars twinkling overhead — and now a music-box chime that rings with every wink. The old logon prank, kept friendly.",
        "alt": "A small teal-haired character with twin-tails winking on a dark screen above a blinking logon prompt.",
        "source": "logon-wink.py", "frames": "frames.json",
        "cols": COLS, "rows": ROWS, "fps": FPS, "frameCount": FRAMES,
        "stillFrame": 0, "license": "MIT",
        "copyright": "Copyright (c) 2026 Rari-One",
        "featured": False, "order": 5,
    }
    (here / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return len(raw)


LICENSE_TEXT = """MIT License

Copyright (c) 2026 Rari-One

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def markers():
    out = []
    here = Path(__file__).parent
    files = [("source/logon-wink.py", Path(__file__)),
             ("source/score.py", here / "score.py")]
    want = [("hair", 0), ("face", 1), ("sparkles", 2), ("notes", 3),
            ("prompt", 4), ("melody", 5), ("pad", 6), ("wink", 40),
            ("blink", 84), ("clicks", 90), ("typing", 104),
            ("wink2", 126), ("star", 150)]
    for name, frame in want:
        for fname, path in files:
            if not path.exists():
                continue
            for i, line in enumerate(path.read_text().splitlines(), 1):
                if f"@marker {name}" in line:
                    out.append({"frame": frame, "file": fname, "line": i})
                    break
            else:
                continue
            break
    out.sort(key=lambda m: m["frame"])
    deduped = []
    for m in out:
        if deduped and m["frame"] <= deduped[-1]["frame"]:
            continue
        deduped.append(m)
    return deduped


def package(frames, here):
    cells = bytearray()
    for chars, keys in frames:
        for y in range(ROWS):
            for x in range(COLS):
                rgb = PALETTE[CODE.index(keys[y][x])]
                r, g, b = int(rgb[1:3], 16), int(rgb[3:5], 16), int(rgb[5:7], 16)
                cells += struct.pack("<HBBB", ord(chars[y][x]), r, g, b)
    sources = ["source/logon-wink.py"]
    audio = None
    try:
        import score as _score
        audio = _score.render()
        (here / "audio.pcm").write_bytes(audio)
        sources.append("source/score.py")
        print(f"audio.pcm: {len(audio)} bytes")
    except Exception as e:
        print(f"note: no audio ({e}); packaging silent")
    manifest = {
        "version": 1, "title": "Logon Wink", "cols": COLS, "rows": ROWS,
        "fps": FPS, "frames": FRAMES, "background": "#0a0e14",
        "sources": sources, "markers": markers(),
    }
    if audio is not None:
        manifest["audio"] = "audio.pcm"
    out = here / "logon-wink.rwl"
    fixed = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        members = [("manifest.json", json.dumps(manifest).encode()),
                   ("frames.bin", bytes(cells))]
        if audio is not None:
            members.append(("audio.pcm", audio))
        members.append(("LICENSE", LICENSE_TEXT.encode()))
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
        for src, arc in (("logon-wink.py", "source/logon-wink.py"),
                         ("score.py", "source/score.py")):
            p = here / src
            if not p.exists():
                continue
            info = zipfile.ZipInfo(arc, date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return out.stat().st_size


def main():
    ap = argparse.ArgumentParser(description="Logon Wink — a little greeter winks at you.")
    ap.add_argument("--still", action="store_true")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--package", action="store_true")
    ap.add_argument("--stats", action="store_true")
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
        print(f"logon-wink.rwl: {size} bytes")
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


if __name__ == "__main__":
    main()
