"""Build the Flyway (.rwl) Lab Player package.

MIT License. Copyright (c) 2026 Rari-One.
Writes flyway.rwl beside this file, or to the path given as its first argument.
"""
import json
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from flyway import H, W, image
from score import FPS, FRAMES, render

ROOT = Path(__file__).resolve().parent
SOURCES = ["flyway.py", "score.py"]
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


def cue(frame, filename, first_phrase, last_phrase):
    lines = (ROOT / filename).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines, 1) if first_phrase in line)
    end = next(i for i, line in enumerate(lines[start - 1:], start) if last_phrase in line)
    return {"frame": frame, "file": "source/" + filename, "line": start, "endLine": end}


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / (ROOT.name + ".rwl")
    markers = [
        cue(0, "flyway.py", "The sky: a dot gradient", "still reads against it"),
        cue(11, "score.py", "The wingbeat", "low-passed noise swelling"),
        cue(64, "flyway.py", "@marker fireflies", "glow > 0.4"),
        cue(128, "flyway.py", "Open country", "hedgerows, a river"),
        cue(192, "score.py", "The flute", "gentle fall"),
        cue(256, "flyway.py", "The sea: glittering water", "horizon light"),
        cue(320, "score.py", "The sea: waves breathing", "0.05 * lp * swell"),
        cue(384, "flyway.py", "Stars fade in over dusk", "strength * (0.6"),
        cue(448, "flyway.py", "The bird, drawn over the sky", "drop = max"),
    ]
    manifest = {
        "version": 1, "title": "Flyway", "cols": W, "rows": H, "fps": FPS,
        "frames": FRAMES, "background": "#0b0e1a", "audio": "audio.pcm",
        "sources": ["source/" + s for s in SOURCES], "markers": markers,
    }
    license_path = ROOT.parent.parent / "LICENSE"
    license_text = (license_path.read_text(encoding="utf-8") if license_path.exists()
                    else LICENSE_TEXT)
    # Fixed entry dates, so the package rebuilds byte-identical. ZipInfo
    # defaults to storing entries uncompressed, so set the method here.
    def info(name):
        zi = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        zi.compress_type = ZIP_DEFLATED
        return zi

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as z:
        z.writestr(info("manifest.json"), json.dumps(manifest))
        for src in SOURCES:
            z.writestr(info("source/" + src), (ROOT / src).read_bytes())
        z.writestr(info("LICENSE.txt"), license_text)
        z.writestr(info("audio.pcm"), render().tobytes())
        with z.open(info("frames.bin"), "w") as out:
            for n in range(FRAMES):
                out.write(image(n))
    print(f"{output.name}: {output.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
