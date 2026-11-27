"""Build the Night Carol (.rwl) Lab Player package.

MIT License. Copyright (c) 2026 Rari-One.
Writes night-carol.rwl beside this file, or to the path given as the first argument.

Follow walks through the carol bar by bar: on each downbeat it shows that bar
of the score in carol.py, and halfway through the bar it shows the code that
is singing, ringing or drawing at that moment.
"""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from carol import FPS, FRAMES
from choir import render
from sky import H, W, image

ROOT = Path(__file__).resolve().parent
SOURCES = ["carol.py", "choir.py", "sky.py", "pack.py"]

# Follow: (frame, file, where the passage starts). One bar is 48 frames.
TOUR = [
    (0, "sky.py", "# Once gathered, the star shines"), (24, "choir.py", "# Handbells: the falling peal"),
    (48, "carol.py", "PEAL = "), (72, "choir.py", "# A church bell far off"),
    (96, "carol.py", "# bar 3"), (120, "sky.py", "def pitch_y"),
    (144, "carol.py", "# bar 4"), (168, "choir.py", "# Formant tables"),
    (192, "carol.py", "# bar 5"), (216, "choir.py", "def spectrum"),
    (240, "carol.py", "# bar 6"), (264, "choir.py", "# Vibrato:"),
    (288, "carol.py", "# bar 7"), (312, "carol.py", "def harmonize"),
    (336, "carol.py", "# bar 8"), (360, "choir.py", "# Glide between notes"),
    (384, "carol.py", "# bar 9"), (408, "sky.py", "# A star is a little plus sign"),
    (432, "carol.py", "# bar 10"), (456, "choir.py", "def consonant"),
    (480, "carol.py", "# bar 11"), (504, "choir.py", "# ...then a ring on the first"),
    (528, "carol.py", "# bar 12"), (552, "sky.py", "# Four carolers by the door"),
    (576, "carol.py", "# bar 13"), (600, "choir.py", "# The organ holds each chord"),
    (624, "carol.py", "# bar 14"), (648, "sky.py", "# The words, like a hymn book"),
    (672, "carol.py", "# bar 15"), (696, "choir.py", "def hall"),
    (720, "carol.py", "# bar 16"), (744, "choir.py", "# The choir: three singers"),
    (768, "carol.py", "# bar 17"), (792, "choir.py", "# A last cascade"),
    (816, "carol.py", "# bar 18"), (836, "sky.py", "# Each star's place in the final shape"),
]


def passage(filename, phrase):
    """The lines to highlight: a whole bar of the score, or the passage a comment opens."""
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    tags = [i for i, line in enumerate(lines, 1) if line.rstrip().endswith("# bar " + phrase[6:])] \
        if phrase.startswith("# bar ") else []
    if tags:
        bars = [i for i, line in enumerate(lines, 1) if "# bar " in line and line.rstrip()[-1].isdigit()]
        before = [i for i in bars if i < tags[0]]
        return (before[-1] + 1 if before else tags[0]), tags[0]
    start = next(i for i, line in enumerate(lines, 1) if line.strip().startswith(phrase))
    indent = len(lines[start - 1]) - len(lines[start - 1].lstrip())
    end, code = start, False
    for i in range(start, min(len(lines), start + 30)):
        text = lines[i]
        depth = len(text) - len(text.lstrip())
        comment = text.strip().startswith("#")
        if not text.strip() or (comment and depth <= indent and code):
            break                     # stop at the next comment once the code has begun
        code = code or not comment
        end = i + 1
    return start, end


def info(name):
    """A zip entry with a fixed date, so the package rebuilds byte for byte."""
    entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    entry.compress_type = ZIP_DEFLATED
    return entry


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / (ROOT.name + ".rwl")
    markers = []
    for frame, filename, phrase in TOUR:
        line, end = passage(filename, phrase)
        markers.append({"frame": frame, "file": "source/" + filename, "line": line, "endLine": end})
    manifest = {
        "version": 1, "title": "Night Carol", "cols": W, "rows": H, "fps": FPS,
        "frames": FRAMES, "background": "#060916", "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES], "markers": markers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(info("manifest.json"), json.dumps(manifest))
        for src in SOURCES:
            z.writestr(info("source/" + src), (ROOT / src).read_bytes())
        z.writestr(info("LICENSE.txt"), (ROOT.parent / "LICENSE").read_bytes())
        z.writestr(info("audio.pcm"), render().tobytes())
        with z.open(info("frames.bin"), "w") as out:
            for n in range(FRAMES):
                out.write(image(n))
    print(f"{output.name}: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
