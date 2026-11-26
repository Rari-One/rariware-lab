# Lab Player packages

Extract the whole portable release. To try a package once, drop its `.rwl` file onto the open player. To include it every time you launch the player, put it in `artworks/` beside `LabPlayer.exe`. At startup the library lists accepted packages in filename order and shows how many files it skipped.

## Your first two frames

From `player/`, save this as `first_art.py` and run `python first_art.py` with Python 3.10 or newer. The script uses the Python standard library. It reads its own source and writes `artworks/passing-light.rwl`, replacing that file if it exists. Drop the result onto the player to open **Passing light**. One amber light moves between two positions each second. Change the two strings or the RGB values to give it a different rhythm or color.

```python
import json
import struct
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

pictures = ["●   ", "   ●"]
header = dict(version=1, title="Passing light", cols=4, rows=1,
              fps=1, frames=len(pictures), background="#101418",
              sources=["source/first_art.py"])
cells = b"".join(struct.pack("<HBBB", ord(ch), 247, 184, 98)
                 for picture in pictures for ch in picture)
Path("artworks").mkdir(exist_ok=True)
with ZipFile("artworks/passing-light.rwl", "w", ZIP_DEFLATED) as artwork:
    artwork.writestr("manifest.json", json.dumps(header))
    artwork.writestr("frames.bin", cells)
    artwork.write(__file__, "source/first_art.py")
```

## Convert an existing gallery export

From the player folder, use Python 3.10+ on the authoring machine:

```sh
python convert_gallery.py ../snowfall artworks/snowfall.rwl --license ../LICENSE
```

Point the first argument at a gallery folder containing its manifest.json, declared frames JSON, and original source. Supply the applicable license file. The output directory must exist. The helper replaces the destination only after conversion succeeds. It reads the existing export, translates each base-36 color index through its palette, preserves the character and frame order, and uses the gallery stage background. The original source bytes go in source/. Relaunch the player to discover the package. Playback needs no Python. For pieces with a different export layout, follow the binary format below.

## Let the repository build it

If you cannot produce a `.rwl` file yourself, bundle its contents in an `rwl/` folder inside your experiment directory and open a pull request:

```text
my-piece/
  my_piece.py            source listed as "source/my_piece.py" in the manifest
  NOTICE.txt             optional; otherwise the repository LICENSE is included
  rwl/manifest.json      a version 1 manifest, described below
  rwl/frames.json        frames as text, or rwl/frames.bin in the binary layout below
  rwl/audio.pcm          only if the manifest declares "audio"
```

`frames.json` uses the gallery text format: `{"format":"rariware-lab-frames","cols":…,"rows":…,"palette":["#rrggbb",…],"frames":[…],"colors":[…]}`. Each frame is one string of `rows` lines joined by `\n`, each exactly `cols` characters wide. Each entry in `colors` has the same shape, with one base-36 digit (`0`–`9`, `a`–`z`) per cell choosing a palette color. Listed sources are read from `rwl/source/` first, then from the experiment directory.

The **Lab Player packages** check on every pull request assembles the package, checks it with the player's own loader and attaches the result to the run as `rwl-packages`. It never runs your experiment's code. A maintainer can commit the finished package by running the workflow from the **Actions** tab on your branch with your folder name. To build or check packages locally, run `python player/build_package.py my-piece` or `python player/build_package.py --check` from the repository root.

## Make a package

Create an ordinary ZIP with manifest.json and frames.bin at its root, plus the original UTF-8 source files you want to share. Use stored or deflated entries, regular files only, relative paths with forward slashes, and no explicit directory entries. Rename the ZIP to .rwl. No authoring language or SDK is required.

Required fields are `version`, `title`, `cols`, `rows`, `fps`, `frames`, and `background` (six hexadecimal RGB digits with a leading #). Dimensions, rate, and count are positive integers. The optional fields are `sources`, `markers`, and `audio`.

Example manifest for a two-frame piece with a source annotation:

```json
{"version":1,"title":"Two dots","cols":2,"rows":1,"fps":1,"frames":2,"background":"#101418","sources":["source/dots.c"],"markers":[{"frame":0,"file":"source/dots.c","line":1}]}
```

Write frames in playback order. Each cell occupies exactly five bytes: a little-endian unsigned 16-bit Unicode character followed by red, green and blue bytes (0–255). Walk left to right, top to bottom, with no row separators or padding. For a space in white, write 20 00 FF FF FF in hex. Use single-cell printable BMP characters. Braille and fractional blocks have dedicated drawing rules; other characters use the bundled JetBrains Mono face. Each cell has a 9:18 aspect ratio. The player loops frames at the declared FPS.

List source files in desired browsing order under source/. Include applicable notices. Markers are optional editorial annotations. Each marker begins at its zero-based frame and stays active up to the next marker or loop end. Use strictly increasing frame numbers, exact listed source paths, and one-based line numbers. For a work with markers, Follow starts on. Click a timeline tick to see the frame and source line together. Scrolling the source or switching files returns you to manual browsing. The player displays the source as text.

## Limits in version 1

Up to 128 candidate packages, 16 MiB per archive, 12 regular entries, 64 KiB manifest, 80 UTF-8 bytes per title, 160 columns, 60 rows, 60 FPS, 900 frames and 24 MiB of decoded cells per piece. Up to eight source files of 256 KiB and 12,000 lines each, and 1,024 markers. Unknown format versions are skipped. The loader reads the manifest, listed source, frame data and declared audio directly from the archive.

## Optional sound and source ranges

An artwork can add one stereo track. Set `"audio":"audio.pcm"` and include that ZIP member as headerless signed little-endian 16-bit PCM, left then right, at 48,000 samples per second per channel. Its length must equal exactly one visual loop: 48,000 × frame count ÷ FPS stereo sample pairs, four bytes per pair, up to 12 MiB. Bake mixing and the loop seam into the asset. Playback, pause, restart and the source timeline share the audio position. Omit audio for silent work.

A source marker may add an inclusive one-based `endLine`, in the same file and at or after `line`. For example, `{"frame":64,"file":"source/score.py","line":31,"endLine":38}` spreads the highlight evenly from line 31 to 38 through the frame before the next marker (or the last frame of the loop). A one-frame interval shows its starting line. Short intervals may skip intermediate lines. Omit endLine for a fixed annotation. Follow uses the middle third of the source pane and yields immediately to manual browsing.
