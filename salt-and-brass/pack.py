"""Build the Salt & Brass (.rwl) Lab Player package."""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from plate import FPS, FRAMES, H, W, generate_frames
from score import render

ROOT = Path(__file__).resolve().parent
SOURCES = ["plate.py", "score.py"]


def cue(frame, filename, first_phrase, last_phrase):
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, 1) if first_phrase in line)
    end = next(i for i, line in enumerate(lines, 1) if last_phrase in line)
    return {"frame": frame, "file": "source/" + filename, "line": start, "endLine": end}


def main():
    default_out = ROOT / (ROOT.name + ".rwl")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else default_out

    markers = [
        cue(0,   "plate.py", "Circular plate eigenmode", "gy, gx = np.gradient"),
        cue(48,  "score.py", "Bowed brass fundamental",  "place(bar_start, 0.30"),
        cue(96,  "plate.py", "Antinodes toss salt",      "py += vy"),
        cue(144, "score.py", "Struck bronze plate",      "place(bar_start + offset"),
        cue(192, "plate.py", "Luminous bow contact arc", "52.0 + 58.0 * bow_pulse"),
        cue(240, "score.py", "Salt whisper",             "place(bar_start + int(RATE * 0.015)"),
        cue(288, "plate.py", "Live fractional-block",    "put_text(cells, H - 2, 3"),
        cue(336, "score.py", "Wrap ringing tails",       "mix[:len(wave) - first]"),
    ]

    manifest = {
        "version": 1,
        "title": "Salt & Brass",
        "cols": W,
        "rows": H,
        "fps": FPS,
        "frames": FRAMES,
        "background": "#0a0c12",
        "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES],
        "markers": markers,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        for src in SOURCES:
            z.write(ROOT / src, "source/" + src)
        z.write(ROOT.parent / "LICENSE", "LICENSE.txt")
        z.writestr("audio.pcm", render().tobytes())
        with z.open("frames.bin", "w") as out:
            for chunk in generate_frames():
                out.write(chunk)


if __name__ == "__main__":
    main()
