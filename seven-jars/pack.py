"""Build the Seven Jars (.rwl) Lab Player package.

MIT License. Copyright (c) 2026 Rari-One.
Writes seven-jars.rwl beside this file, or to the path given as the first argument.
"""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from garden import H, W, image
from score import FPS, FRAMES, LIGHTNING, THUNDER, render

ROOT = Path(__file__).resolve().parent
SOURCES = ["garden.py", "score.py"]


def cue(frame, filename, first_phrase, last_phrase):
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, 1) if first_phrase in line)
    end = next(i for i, line in enumerate(lines[start - 1:], start) if last_phrase in line)
    return {"frame": frame, "file": "source/" + filename, "line": start, "endLine": end}


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / (ROOT.name + ".rwl")
    markers = [
        cue(0, "garden.py", "Blow each vessel from its profile", "clear = core & ~near"),
        cue(64, "score.py", "The score: one bar per line", '"3 . 2 . 1 . . ."'),
        cue(128, "garden.py", "A drop gathers at the seam", "dot(x + side"),
        cue(192, "score.py", "The glass voice", "return 0.2 * loud"),
        cue(256, "garden.py", "The splash: a crown", "dot(x, level_y - 6"),
        cue(320, "garden.py", "The surface rocks", "ink[water] = color"),
        cue(LIGHTNING, "garden.py", "Lightning shows the sky", "(236, 234, 255)"),
        cue(THUNDER, "score.py", "Thunder: a short crack", "place(storm_bus, THUNDER"),
        cue(448, "score.py", "The rain bed", "rain += patter"),
    ]
    manifest = {
        "version": 1, "title": "Seven Jars", "cols": W, "rows": H, "fps": FPS,
        "frames": FRAMES, "background": "#090c13", "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES], "markers": markers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        for src in SOURCES:
            z.write(ROOT / src, "source/" + src)
        z.write(ROOT.parent / "LICENSE", "LICENSE.txt")
        z.writestr("audio.pcm", render().tobytes())
        with z.open("frames.bin", "w") as out:
            for n in range(FRAMES):
                out.write(image(n))
    print(f"{output.name}: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
