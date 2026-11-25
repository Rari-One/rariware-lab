"""Build and check Lab Player packages from bundled data (Python 3.10+, standard library only).

This tool never runs an experiment's own code. It only reads files that are
already in the experiment directory, assembles them into a .rwl package and
checks the result with the same rules the Lab Player's loader applies.

An experiment can be packaged in either of two ways:

1. A bundle folder named rwl/ inside the experiment directory:

       my-piece/
         rwl/manifest.json     version 1 player manifest (see PACKAGES.md)
         rwl/frames.bin        binary frames, or
         rwl/frames.json       frames in the text gallery format (palette, frames, colors)
         rwl/audio.pcm         optional, when the manifest declares "audio"
         my_piece.py           sources listed as "source/my_piece.py" are read from
                               rwl/source/ first, then from the experiment directory
         NOTICE.txt            optional; otherwise the repository LICENSE is included

2. A gallery export (manifest.json with "format": "rariware-lab-manifest" and
   its frames JSON), which becomes a silent package.

Usage, from the repository root:

    python player/build_package.py my-piece            # writes my-piece/my-piece.rwl
    python player/build_package.py --all --out dist    # every buildable experiment
    python player/build_package.py --check             # check every committed .rwl
"""
import argparse
import json
import re
import struct
import sys
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
PALETTE_CODES = "0123456789abcdefghijklmnopqrstuvwxyz"


class PackageError(Exception):
    pass


def fail(message):
    raise PackageError(message)


def is_control(text):
    return any(unicodedata.category(ch) == "Cc" for ch in text)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def valid_member_name(name):
    # Mirrors Go's fs.ValidPath plus the loader's extra checks.
    if not name or name.startswith("/") or name.endswith("/") or "\\" in name or ":" in name:
        return False
    return all(part not in ("", ".", "..") for part in name.split("/"))


# ---------------------------------------------------------------- checking

def check_package(path):
    """Apply the Lab Player loader's rules (player/packages.go) to a .rwl file."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 << 20:
        fail("package missing, not a regular file, or larger than 16 MiB")
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        fail("not a ZIP archive")
    with archive:
        infos = archive.infolist()
        if len(infos) > 12:
            fail("more than 12 entries")
        files = {}
        for info in infos:
            if not valid_member_name(info.filename) or info.filename in files or info.is_dir():
                fail(f"invalid or duplicate entry {info.filename!r}")
            files[info.filename] = info

        def read(name, limit):
            info = files.get(name)
            if info is None or info.file_size > limit:
                fail(f"{name} missing or too large")
            return archive.read(info)

        try:
            m = json.loads(read("manifest.json", 65536))
        except ValueError:
            fail("manifest.json is not valid JSON")
        if not isinstance(m, dict):
            fail("manifest.json must be an object")
        for key in ("version", "cols", "rows", "fps", "frames"):
            if not is_int(m.get(key)):
                fail(f"manifest {key} must be an integer")
        title = m.get("title")
        if m["version"] != 1:
            fail("manifest version must be 1")
        if not isinstance(title, str) or len(title.encode()) > 80 or not title.strip() or is_control(title):
            fail("title must be 1-80 bytes of printable text")
        if not (1 <= m["cols"] <= 160 and 1 <= m["rows"] <= 60 and 1 <= m["fps"] <= 60 and 1 <= m["frames"] <= 900):
            fail("cols, rows, fps or frames outside player limits")
        sources = m.get("sources") or []
        markers = m.get("markers") or []
        if not isinstance(sources, list) or len(sources) > 8 or not isinstance(markers, list) or len(markers) > 1024:
            fail("too many sources or markers")
        background = m.get("background")
        if not isinstance(background, str) or not re.fullmatch(r"#?[0-9a-fA-F]{6}", background):
            fail("background must be six hexadecimal digits")

        size = m["cols"] * m["rows"] * m["frames"] * 5
        if size > 24 << 20:
            fail("decoded frames exceed 24 MiB")
        raw = read("frames.bin", size)
        if len(raw) != size:
            fail(f"frames.bin is {len(raw)} bytes; expected {size}")
        for (code,) in struct.iter_unpack("<H", b"".join(raw[i:i + 2] for i in range(0, size, 5))):
            if unicodedata.category(chr(code)) == "Cc" or 0xD800 <= code <= 0xDFFF:
                fail(f"frames.bin contains an unusable character U+{code:04X}")

        audio = m.get("audio") or ""
        if audio:
            if audio != "audio.pcm":
                fail('audio must be "audio.pcm"')
            samples = 48000 * m["frames"]
            if samples % m["fps"]:
                fail("audio length cannot match the loop exactly at this frame rate")
            length = samples // m["fps"] * 4
            if length > 12 << 20:
                fail("audio exceeds 12 MiB")
            if len(read("audio.pcm", length)) != length:
                fail(f"audio.pcm must be exactly {length} bytes (one visual loop)")

        counts = {}
        for s in sources:
            if not isinstance(s, str) or not s.startswith("source/") or s in counts or len(s) > 160 or is_control(s):
                fail(f"invalid source entry {s!r}")
            data = read(s, 256 << 10)
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                fail(f"{s} is not UTF-8")
            if "\0" in text:
                fail(f"{s} contains NUL bytes")
            lines = text.replace("\r\n", "\n").split("\n")
            if len(lines) > 12000:
                fail(f"{s} has more than 12,000 lines")
            counts[s] = len(lines)

        previous = None
        for mk in markers:
            if not isinstance(mk, dict):
                fail("markers must be objects")
            frame, line, end = mk.get("frame", 0), mk.get("line", 0), mk.get("endLine", 0)
            limit = counts.get(mk.get("file"), 0)
            if not (is_int(frame) and is_int(line) and is_int(end)):
                fail("marker fields must be integers")
            if not (0 <= frame < m["frames"] and 1 <= line <= limit) or (end and not line <= end <= limit) \
                    or (previous is not None and frame <= previous):
                fail(f"invalid marker {mk}")
            previous = frame
    return m


# ---------------------------------------------------------------- building

def local_file(folder, name):
    if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in (".", ".."):
        fail(f"expected a plain filename, got {name!r}")
    path = folder / name
    if path.is_symlink() or not path.is_file():
        fail(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} not found")
    return path


def frames_from_json(path, cols, rows, count):
    data = json.loads(path.read_bytes())
    if data.get("format") != "rariware-lab-frames":
        fail(f"{path.name} must use the rariware-lab-frames format")
    if (data.get("cols"), data.get("rows")) != (cols, rows):
        fail(f"{path.name} is {data.get('cols')}x{data.get('rows')}; manifest says {cols}x{rows}")
    frames, colors, palette = data.get("frames"), data.get("colors"), data.get("palette")
    if not isinstance(frames, list) or not isinstance(colors, list) or len(frames) != count or len(colors) != count:
        fail(f"{path.name} must hold exactly {count} frames and color maps")
    if not isinstance(palette, list) or not 1 <= len(palette) <= 36:
        fail("palette must list 1-36 colors")
    lookup = {}
    for code, rgb in zip(PALETTE_CODES, palette):
        if not isinstance(rgb, str) or not re.fullmatch("#[0-9a-fA-F]{6}", rgb):
            fail(f"invalid palette color {rgb!r}")
        lookup[code] = bytes.fromhex(rgb[1:])
    out = bytearray()
    for number, (glyphs, codes) in enumerate(zip(frames, colors)):
        grid, shades = glyphs.split("\n"), codes.split("\n")
        if len(grid) != rows or len(shades) != rows:
            fail(f"frame {number} has {len(grid)} rows; expected {rows}")
        for row, shade in zip(grid, shades):
            if len(row) != cols or len(shade) != cols:
                fail(f"frame {number} has a row that is not {cols} cells wide")
            for ch, c in zip(row, shade):
                if ord(ch) > 0xFFFF or c not in lookup:
                    fail(f"frame {number} uses a character outside the BMP or an unknown color code {c!r}")
                out += struct.pack("<H", ord(ch)) + lookup[c]
    return bytes(out)


def notice_member(folder):
    notice = folder / "NOTICE.txt"
    if notice.is_file() and not notice.is_symlink():
        return "NOTICE.txt", notice.read_bytes()
    return "LICENSE.txt", (ROOT / "LICENSE").read_bytes()


def bundle_members(folder):
    bundle = folder / "rwl"
    manifest = json.loads(local_file(bundle, "manifest.json").read_bytes())
    if not isinstance(manifest, dict):
        fail("rwl/manifest.json must be an object")
    cols, rows, count = manifest.get("cols"), manifest.get("rows"), manifest.get("frames")
    if (bundle / "frames.bin").is_file():
        frames = local_file(bundle, "frames.bin").read_bytes()
    elif (bundle / "frames.json").is_file():
        frames = frames_from_json(local_file(bundle, "frames.json"), cols, rows, count)
    else:
        fail("rwl/ needs frames.bin or frames.json")
    members = {"manifest.json": json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).encode(),
               "frames.bin": frames}
    if manifest.get("audio"):
        members["audio.pcm"] = local_file(bundle, "audio.pcm").read_bytes()
    for entry in manifest.get("sources") or []:
        if not isinstance(entry, str) or not entry.startswith("source/") or entry.count("/") != 1:
            fail(f"sources must look like source/NAME, got {entry!r}")
        name = entry.split("/", 1)[1]
        place = bundle / "source" if (bundle / "source" / name).is_file() else folder
        members[entry] = local_file(place, name).read_bytes()
    name, data = notice_member(folder)
    members.setdefault(name, data)
    return members


def gallery_members(folder):
    manifest = json.loads(local_file(folder, "manifest.json").read_bytes())
    if manifest.get("format") != "rariware-lab-manifest":
        fail("manifest.json is not a gallery export")
    cols, rows, count = manifest.get("cols"), manifest.get("rows"), manifest.get("frameCount")
    frames = frames_from_json(local_file(folder, manifest.get("frames")), cols, rows, count)
    fps = json.loads(local_file(folder, manifest["frames"]).read_bytes()).get("fps")
    source = manifest.get("source")
    header = dict(version=1, title=manifest.get("title"), cols=cols, rows=rows, fps=fps,
                  frames=count, background="#07070e", sources=["source/" + source])
    members = {"manifest.json": json.dumps(header, ensure_ascii=False, separators=(",", ":")).encode(),
               "frames.bin": frames,
               "source/" + source: local_file(folder, source).read_bytes()}
    name, data = notice_member(folder)
    members[name] = data
    return members


def buildable(folder):
    if (folder / "rwl" / "manifest.json").is_file():
        return "bundle"
    manifest = folder / "manifest.json"
    if manifest.is_file():
        try:
            if json.loads(manifest.read_bytes()).get("format") == "rariware-lab-manifest":
                return "gallery"
        except (ValueError, AttributeError):
            pass
    return None


def build(folder, out_dir=None):
    folder = folder.resolve()
    kind = buildable(folder)
    if kind is None:
        fail("no rwl/ bundle or gallery export found")
    members = bundle_members(folder) if kind == "bundle" else gallery_members(folder)
    target = (out_dir.resolve() if out_dir else folder) / f"{folder.name}.rwl"
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".rwl.tmp")
    with zipfile.ZipFile(temp, "w") as archive:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    try:
        check_package(temp)
    except PackageError:
        temp.unlink()
        raise
    temp.replace(target)
    return kind, target


def experiments():
    return sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".") and buildable(p))


def main():
    parser = argparse.ArgumentParser(description="Build or check Lab Player packages without running experiment code.")
    parser.add_argument("experiments", nargs="*", type=Path, help="experiment directories to package")
    parser.add_argument("--all", action="store_true", help="package every experiment with a bundle or gallery export")
    parser.add_argument("--out", type=Path, help="write packages here instead of beside each experiment")
    parser.add_argument("--check", action="store_true", help="check every committed .rwl file in the repository")
    args = parser.parse_args()
    if not (args.experiments or args.all or args.check):
        parser.error("name an experiment, or use --all or --check")

    problems = 0
    if args.check:
        for package in sorted(ROOT.rglob("*.rwl")):
            if ".git" in package.parts:
                continue
            try:
                m = check_package(package)
                print(f"ok    {package.relative_to(ROOT)}  {m['title']!r}")
            except PackageError as error:
                problems += 1
                print(f"FAIL  {package.relative_to(ROOT)}: {error}")
    for folder in (experiments() if args.all else args.experiments):
        try:
            kind, target = build(folder, args.out)
            print(f"built {target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}  (from {kind})")
        except (PackageError, ValueError, KeyError, TypeError) as error:
            problems += 1
            print(f"FAIL  {folder}: {error}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
