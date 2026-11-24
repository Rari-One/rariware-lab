"""Build The Long Way Round (.rwl) Lab Player package.

MIT License. Copyright (c) 2026 Rari-One.
Writes long-way-round.rwl beside this file, or to the path given as the first argument.

The package sits close to several version 1 limits on purpose: 64 seconds of
stereo (98% of the audio cap), 130 x 43 cells over 896 frames (99.5% of the
decoded-cell budget), six source listings and three dozen Follow markers.
"""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from journey import FPS, FRAMES, H, W
from voices import render
from world import image

ROOT = Path(__file__).resolve().parent
SOURCES = ["journey.py", "world.py", "deep.py", "score.py", "voices.py", "pack.py"]

# Follow: (frame, file, the comment that opens the passage to highlight).
TOUR = [
    (0, "journey.py", "# The cloud: vapour gathers"), (24, "world.py", "# The cloud, made of soft blobs"),
    (56, "voices.py", "# Sparkles:"), (96, "score.py", "# bar 4"),
    (128, "journey.py", "# The fall:"), (150, "world.py", "# Rain from the cloud"),
    (176, "voices.py", "# Plucks:"), (208, "score.py", "# bar 7"),
    (224, "voices.py", "# The landing:"), (240, "journey.py", "# Snowmelt:"),
    (264, "world.py", "# Snow, rock and meadow"), (288, "world.py", "# The stream:"),
    (320, "world.py", "# Pines down the slope, dusted"), (352, "voices.py", "# Drums:"),
    (384, "journey.py", "# The river carries"), (408, "world.py", "# The village:"),
    (440, "world.py", "# The church bell:"), (452, "voices.py", "# The church bell tolls"),
    (480, "world.py", "# The river:"), (512, "score.py", "# bar 17"),
    (544, "journey.py", "# The sea: it rides"), (560, "world.py", "# The sea: light fades"),
    (596, "deep.py", "# The whale:"), (612, "voices.py", "# The whale calls"),
    (640, "journey.py", "# The deep: it sinks"), (656, "voices.py", "# Underwater, the music"),
    (680, "deep.py", "# Jellyfish:"), (710, "deep.py", "# Fish:"),
    (736, "world.py", "# Plankton glow"), (752, "deep.py", "# Anglerfish:"),
    (768, "world.py", "# The vent:"), (780, "voices.py", "# The vent wakes"),
    (800, "journey.py", "# The return:"), (822, "voices.py", "# Wind for the fall"),
    (840, "voices.py", "# Riser:"), (864, "world.py", "# The drop itself"),
]


def passage(filename, phrase):
    """The passage a comment opens, up to the next comment or blank line at its depth."""
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    tagged = [i for i, line in enumerate(lines, 1) if line.rstrip().endswith(phrase)]
    if tagged:                                    # a bar of the score: just that line
        return tagged[0], tagged[0]
    start = next(i for i, line in enumerate(lines, 1) if line.strip().startswith(phrase))
    indent = len(lines[start - 1]) - len(lines[start - 1].lstrip())
    end = start
    for i in range(start, min(len(lines), start + 30)):
        text = lines[i]
        depth = len(text) - len(text.lstrip())
        if not text.strip() or (text.strip().startswith("#") and depth <= indent and i > start):
            break
        end = i + 1
    return start, end


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / (ROOT.name + ".rwl")
    markers = []
    for frame, filename, phrase in TOUR:
        line, end = passage(filename, phrase)
        markers.append({"frame": frame, "file": "source/" + filename, "line": line, "endLine": end})
    manifest = {
        "version": 1, "title": "The Long Way Round", "cols": W, "rows": H, "fps": FPS,
        "frames": FRAMES, "background": "#070910", "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES], "markers": markers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        for src in SOURCES:
            z.write(ROOT / src, "source/" + src)
        z.write(ROOT.parent / "LICENSE", "LICENSE.txt")
        z.writestr("audio.pcm", render().tobytes())
        with z.open("frames.bin", "w") as out:
            for n in range(FRAMES):
                out.write(image(n))
    size = output.stat().st_size
    print(f"{output.name}: {size:,} bytes ({size / (16 << 20):.0%} of the 16 MiB package limit)")


if __name__ == "__main__":
    main()
