"""Build The Midnight Watch (.rwl) Lab Player package, or preview any frame in a terminal.

MIT License. Copyright (c) 2026 Rari-One.
Writes midnight-watch.rwl beside this file, or to the path given as the first argument.

Exercises the version 1 Lab Player specification near its ceiling: 900 frames at 15 fps
(60.0 s exact), 124 x 45 cells (99.8% of the 24 MiB decoded-cell budget), 11.52 MB of
48 kHz stereo PCM (91.6% of the 12 MiB audio cap), 7 source listings, and 36 Follow markers.
"""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from clock import BG_HEX, BLOCKS, FRAMES, FPS, H, W, chapter_info, put_text, smoothstep
from cosmos import render_bell_tower, render_orrery
from dial import render_dial
from gears import render_escapement, render_pendulum_hall
from score import meter_levels
from synth import render as render_audio

ROOT = Path(__file__).resolve().parent
SOURCES = ["clock.py", "dial.py", "gears.py", "cosmos.py", "score.py", "synth.py", "pack.py"]

# 36 Follow markers touring every visual chamber and synthesized voice across the minute.
TOUR = [
    (0,   "dial.py",   "# Smooth zoom curve",            "zoom = 1.0 + 4.8"),
    (24,  "dial.py",   "# Visible clockwork glimpses",   "central ruby jewel bearing"),
    (48,  "synth.py",  "# Escapement click",             "return (0.75 * body"),
    (72,  "dial.py",   "# Moon-phase sub-window",        "(158, 124, 68))"),
    (96,  "synth.py",  "# Music box / celesta",          "return tone * env"),
    (120, "dial.py",   "# Blued-steel hour and minute",  "(245, 206, 126))"),
    (150, "gears.py",  "# Exact meshing gear train",     "w2 = -w_main"),
    (176, "clock.py",  "def gear(self",                  "sub_c[metal] ="),
    (200, "synth.py",  "# Harpsichord pluck",            "return tone * env"),
    (224, "gears.py",  "# Escape wheel at top-center",   "esc_ang = esc_step"),
    (248, "gears.py",  "# Rocking anchor escapement",    "cv.disc(piv_x, piv_y"),
    (272, "gears.py",  "# Breathing gold balance",       "(236, 192, 112))"),
    (300, "gears.py",  "# Receding 3D-perspective",      "depth_fade = smoothstep"),
    (326, "gears.py",  "# Pointed cathedral arch curve", "cv.points(rx, ay"),
    (352, "synth.py",  "# Bowed cello bass",             "return np.column_stack"),
    (376, "gears.py",  "# Three golden pendulums",       "pendulums = ["),
    (400, "synth.py",  "# Soft filtered air swoosh",     "return (0.65 * low"),
    (424, "gears.py",  "# Luminous motion trail",        "cv.disc(bx - bob_r"),
    (450, "cosmos.py", "def _project(pts",               "return CX + pts[:, 0]"),
    (476, "cosmos.py", "# Build four counter-rotating",  "rings_spec = ["),
    (500, "synth.py",  "# Celestial woodwind",           "return tone * attack"),
    (524, "cosmos.py", "# Orbiting worlds in true 3D",   "worlds_spec = ["),
    (548, "cosmos.py", "# Blazing golden clockwork Sun", "(255, 248, 218))"),
    (574, "cosmos.py", "# Sweeping silver-cyan comet",   "cv.disc(comet_x"),
    (600, "cosmos.py", "# Authentic flared cathedral",   "bell_mask = (v >="),
    (626, "synth.py",  "# Grand bronze midnight chime",  "return wave * attack"),
    (652, "cosmos.py", "# 3D cylindrical bronze",        "cv.paint(bands"),
    (676, "cosmos.py", "# Articulated gilded brass",     "cv.disc(h_piv_x"),
    (702, "cosmos.py", "# Concentric golden acoustic",   "cv.add_glow(ring_m"),
    (726, "cosmos.py", "# Molten brass sparks",          "radius=0.7)"),
    (750, "score.py",  "# Exact bronze bell strike",     "BELL_STRIKES = ["),
    (776, "dial.py",   "# Expanding golden chime aura",  "chime * 0.95)"),
    (800, "pack.py",   "# Smooth crossfades between",    "cv.composite_over"),
    (826, "pack.py",   "# Live timepiece readout",       "put_text(cells, 1, W"),
    (852, "pack.py",   "# Fractional-block voice",       "put_text(cells, H - 2"),
    (876, "synth.py",  "# 4. Subtle stereo hall",        "return np.round(25600.0"),
]


def _render_chapter(ch_idx, frame, local):
    if ch_idx == 0:
        return render_dial(frame, local, returning=False)
    if ch_idx == 1:
        return render_escapement(frame, local)
    if ch_idx == 2:
        return render_pendulum_hall(frame, local)
    if ch_idx == 3:
        return render_orrery(frame, local)
    if ch_idx == 4:
        return render_bell_tower(frame, local)
    return render_dial(frame, local, returning=True)


def render_frame(frame):
    """Render one complete 124 x 45 frame with seamless chapter dissolves and HUD."""
    ch_idx, local, title, depth = chapter_info(frame)
    cv, overlays = _render_chapter(ch_idx, frame, local)

    # Smooth crossfades between adjacent chambers over the final 16 frames of each chapter.
    fade_len = 16
    ch_frame = frame % 150
    if ch_idx < 5 and ch_frame >= 150 - fade_len:
        alpha = smoothstep(0.0, 1.0, (ch_frame - (150 - fade_len) + 1) / (fade_len + 1))
        nxt_cv, nxt_ov = _render_chapter(ch_idx + 1, frame, 0.0)
        cv.composite_over(nxt_cv, alpha)
        if alpha > 0.5:
            overlays = nxt_ov

    cells = cv.to_cells()
    for row, col, text, rgb in overlays:
        put_text(cells, row, col, text, rgb)

    # Corner engravings: chapter title, live 11:59:SS timepiece, voice meters, and minute bar.
    brass_hi = (224, 186, 114)
    brass_mid = (148, 126, 92)
    brass_dim = (98, 86, 68)

    put_text(cells, 1, 2, "THE MIDNIGHT WATCH", brass_hi)
    put_text(cells, 2, 2, title, brass_mid)

    # Live timepiece readout ticking second by second from 11:59:00 to 11:59:59.
    sec = frame // FPS
    clock_str = f"11:59:{sec:02d}"
    put_text(cells, 1, W - 2 - len(clock_str), clock_str, brass_hi)
    put_text(cells, 2, W - 2 - len(depth), depth, brass_dim)

    # Fractional-block voice meters tracking escapement, bells, melody, and bass.
    levels = meter_levels(frame)
    colors = ((232, 166, 96), (248, 212, 126), (168, 214, 248), (192, 146, 94))
    for i, lvl in enumerate(levels):
        idx = max(1, min(8, int(round(lvl * 8.0))))
        put_text(cells, H - 3, 2 + i * 3, BLOCKS[idx] * 2, colors[i])
    put_text(cells, H - 2, 2, "TK BL ML BS", brass_dim)

    # Minute progress hairline in the lower-right corner.
    bar_w = 18
    filled = int(round((frame / (FRAMES - 1)) * bar_w))
    prog = "━" * filled + "─" * (bar_w - filled)
    put_text(cells, H - 2, W - 2 - bar_w, prog, brass_mid)

    return cells


def _locate(filename, first_phrase, last_phrase):
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, 1) if first_phrase in line)
    end = next(i for i, line in enumerate(lines[start - 1:], start) if last_phrase in line)
    return start, end


def show_terminal_frame(frame):
    """Print a single frame to a 24-bit UTF-8 terminal."""
    cells = render_frame(max(0, min(FRAMES - 1, frame)))
    lines = []
    for r in range(H):
        row_out = []
        for c in range(W):
            g = chr(int(cells[r, c]["glyph"]))
            rv, gv, bv = (int(x) for x in cells[r, c]["ink"])
            row_out.append(f"\x1b[38;2;{rv};{gv};{bv}m{g}")
        lines.append("".join(row_out) + "\x1b[0m")
    print("\n".join(lines))


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--frame":
        show_terminal_frame(int(sys.argv[2]))
        return

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / (ROOT.name + ".rwl")
    markers = []
    for frame, filename, first_p, last_p in TOUR:
        start, end = _locate(filename, first_p, last_p)
        markers.append({"frame": frame, "file": "source/" + filename, "line": start, "endLine": end})

    manifest = {
        "version": 1,
        "title": "The Midnight Watch",
        "cols": W,
        "rows": H,
        "fps": FPS,
        "frames": FRAMES,
        "background": BG_HEX,
        "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES],
        "markers": markers,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        for src in SOURCES:
            z.write(ROOT / src, "source/" + src)
        z.write(ROOT.parent / "LICENSE", "LICENSE.txt")
        z.writestr("audio.pcm", render_audio().tobytes())
        with z.open("frames.bin", "w") as out:
            for n in range(FRAMES):
                out.write(render_frame(n).tobytes())

    size = output.stat().st_size
    print(f"Wrote {output} ({size:,} bytes, {size / (16 << 20):.1%} of 16 MiB limit)")


if __name__ == "__main__":
    main()
