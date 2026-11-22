"""Convert a trusted RariWare gallery export to a v1 player package (Python 3.10+)."""
import argparse
import json
import re
import struct
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


def local_asset(folder, name):
    path = (folder / name).resolve()
    if path.parent != folder or path.name != name:
        raise ValueError("Expected an asset filename inside the experiment directory")
    return path


def convert(folder, output, notice):
    folder = folder.resolve()
    manifest = json.loads((folder / "manifest.json").read_bytes())
    data = json.loads(local_asset(folder, manifest["frames"]).read_bytes())
    if (manifest["format"], data["format"], data["loop"]) != (
        "rariware-lab-manifest", "rariware-lab-frames", True
    ):
        raise ValueError("Expected a looping Lab gallery export")
    for key, limit in (("cols", 160), ("rows", 60), ("fps", 60)):
        if manifest[key] != data[key] or not 1 <= data[key] <= limit:
            raise ValueError(f"Invalid {key}")
    cols, rows = data["cols"], data["rows"]
    count = manifest["frameCount"]
    if not 1 <= count <= 900 or count * rows * cols * 5 > 24 << 20:
        raise ValueError("Frame count or decoded size exceeds player limits")
    if len(data["frames"]) != count or len(data["colors"]) != count:
        raise ValueError("Frame count mismatch")
    if not 1 <= len(data["palette"]) <= 36:
        raise ValueError("Invalid palette size")
    palette = {}
    for code, rgb in zip("0123456789abcdefghijklmnopqrstuvwxyz", data["palette"]):
        if not re.fullmatch("#[0-9a-fA-F]{6}", rgb):
            raise ValueError("Invalid palette color")
        palette[code] = bytes.fromhex(rgb[1:])
    source = local_asset(folder, manifest["source"])
    member = "source/" + source.name
    header = dict(version=1, title=manifest["title"], cols=cols, rows=rows,
                  fps=data["fps"], frames=count, background="#07070e", sources=[member])
    source_bytes = source.read_bytes()
    listing = source_bytes.decode("utf-8")
    if len(source_bytes) > 256 * 1024 or len(listing.split("\n")) > 12000 or "\0" in listing:
        raise ValueError("Source exceeds player limits")
    with TemporaryDirectory(dir=output.parent) as temp:
        archive = Path(temp) / "package.zip"
        with ZipFile(archive, "w", ZIP_DEFLATED) as package:
            package.writestr("manifest.json", json.dumps(header))
            package.writestr(member, source_bytes)
            if notice:
                package.write(notice, "LICENSE.txt")
            with package.open("frames.bin", "w") as frames:
                for glyphs, colors in zip(data["frames"], data["colors"], strict=True):
                    grid, indices = glyphs.split("\n"), colors.split("\n")
                    if len(grid) != rows or len(indices) != rows:
                        raise ValueError("Row count mismatch")
                    for row, codes in zip(grid, indices):
                        if len(row) != cols or len(codes) != cols:
                            raise ValueError("Column count mismatch")
                        frames.write(b"".join(struct.pack("<H", ord(ch)) + palette[c]
                                              for ch, c in zip(row, codes)))
        if archive.stat().st_size > 16 << 20:
            raise ValueError("Compressed package exceeds player limit")
        archive.replace(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--license", type=Path, help="applicable notice to include")
    args = parser.parse_args()
    convert(args.experiment, args.output, args.license)
