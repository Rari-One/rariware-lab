"""Build Carbon Paper's independent v1 package from its exported grids."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
source = root / "carbon.go"
lines = source.read_text(encoding="utf-8").splitlines()
marks = [(0, "Four interrupted corners"), (8, "Ink reaches the stationary"),
         (60, "The under-sheet takes"), (105, "Lift the warm impression"),
         (150, "Two ruled fans"), (216, "The last blue trace")]
def locate(phrase):
    return next(i for i, line in enumerate(lines, 1) if phrase in line)

manifest = dict(version=1, title="Carbon Paper", cols=116, rows=38, fps=20,
                frames=300, background="#111a23", sources=["source/carbon.go"],
                markers=[dict(frame=n, file="source/carbon.go", line=locate(s)) for n,s in marks])
package = root.parent / "player" / "artworks" / "00-carbon-paper.rwl"
with ZipFile(package, "w", ZIP_DEFLATED) as z:
    z.writestr("manifest.json", json.dumps(manifest))
    z.write(source, "source/carbon.go")
    z.write(root / "frames.bin", "frames.bin")
    z.write(root.parent / "LICENSE", "LICENSE.txt")
