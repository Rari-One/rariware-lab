"""Build the-moon-in-the-pond.rwl for Lab Player (Python 3.10+, standard library only).

    python pack.py

Writes one file next to this script: the-moon-in-the-pond.rwl, a ZIP holding the manifest, the
frames, the stereo soundtrack, these three sources and the license. Nothing else is written and
nothing is downloaded. It takes about a minute.
"""
import json
import struct
import zipfile
from pathlib import Path

import pond
import score

HERE = Path(__file__).resolve().parent
SOURCES = ["pond.py", "score.py", "pack.py"]
FIXED_TIME = (1980, 1, 1, 0, 0, 0)  # fixed ZIP timestamps make rebuilds byte-identical


def find(file, text):
    """One-based line number of the first line containing text, for the Follow markers."""
    for number, line in enumerate((HERE / file).read_text(encoding="utf-8").splitlines(), 1):
        if text in line:
            return number
    raise ValueError(f"{text!r} not found in {file}")


def span(file, start, end):
    return {"file": f"source/{file}", "line": find(file, start), "endLine": find(file, end)}


def markers():
    """Point Follow at the code behind what is on screen, as the rain grows and fades."""
    at = lambda seconds: round(seconds * pond.FPS)
    return [
        {"frame": at(0), **span("pond.py", "def strike", "def wave_step")},
        {"frame": at(1.5), **span("pond.py", "def wave_step", "return nxt")},
        {"frame": at(4.5), **span("pond.py", "# ── 2. Displacement", "return min(b, 1.0)")},
        {"frame": at(8), **span("score.py", "def plink", "def drops")},
        {"frame": at(11), **span("pond.py", "def rain_schedule", "return drops")},
        {"frame": at(14), **span("pond.py", "# ── 3. Brightness", "def pad_cell")},
        {"frame": at(17), **span("score.py", "def hiss", "channel[i] +=")},
        {"frame": at(20), **span("pond.py", "def swell", "return 0.03")},
    ]


def frames_bin():
    """Five bytes per cell: a little-endian UTF-16 code unit, then red, green and blue."""
    out = bytearray()
    for picture in pond.frames():
        for line in picture:
            for glyph, (r, g, b) in line:
                out += struct.pack("<HBBB", ord(glyph), r, g, b)
    return bytes(out)


def main():
    manifest = {
        "version": 1, "title": "The Moon in the Pond",
        "cols": pond.COLS, "rows": pond.ROWS, "fps": pond.FPS, "frames": pond.FRAMES,
        "background": pond.BACKGROUND, "audio": "audio.pcm",
        "sources": [f"source/{name}" for name in SOURCES], "markers": markers(),
    }
    members = {"manifest.json": json.dumps(manifest, ensure_ascii=False).encode(),
               "frames.bin": frames_bin(), "audio.pcm": score.render()}
    for name in SOURCES:
        members[f"source/{name}"] = (HERE / name).read_bytes()
    members["LICENSE.txt"] = (HERE.parent / "LICENSE").read_bytes()
    target = HERE / "the-moon-in-the-pond.rwl"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as rwl:
        for name, data in members.items():
            rwl.writestr(zipfile.ZipInfo(name, FIXED_TIME), data, zipfile.ZIP_DEFLATED)
    print(f"wrote {target.name}: {pond.FRAMES} frames, {len(members['audio.pcm'])} bytes of audio")


if __name__ == "__main__":
    main()
