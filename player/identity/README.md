# Lab Player identity

Eight lavender cells and one teal cell form the play mark. The [flat master](lab-player-master.svg) defines its geometry. The [application icon master](lab-player-icon.svg) adds a rounded dark background. Edit these two SVG files when changing the design.

The library shows the flat mark at 24 pixels. Its leading cell uses the Lab theme’s mint accent or the IDE theme’s blue accent. Windows and Linux use the application icon in its original colors.

## Regenerate the exports

From the repository root, run `python player/identity/generate.py` with Python 3 and Pillow 13.0.0. The script reads both masters, draws their rounded rectangles at a larger scale, then reduces each image to smooth the edges. It replaces the PNG and ICO files in this directory. The player embeds the PNGs at build time.

The Windows ICO contains nine sizes from 16 to 256 pixels. Follow the [Windows build instructions](../README.md#build-and-share) to include it in the executable.

## Linux desktop integration

The player supplies its icon directly to desktop windows that accept it. For desktop environments that look up the application by name, the supplied desktop entry pairs the window class `lab-player` with the same icon. When packaging a Linux build, make the executable available on PATH as `lab-player` and keep its collection beside the executable. Install these files under the package’s data prefix (typically `/usr/share`):

| Source | Destination under the data prefix |
| --- | --- |
| `lab-player.desktop` | `applications/lab-player.desktop` |
| `lab-player-icon.svg` | `icons/hicolor/scalable/apps/lab-player.svg` |
| `icon-16.png`, `icon-32.png`, `icon-48.png`, `icon-256.png` | `icons/hicolor/<size>x<size>/apps/lab-player.png` for each size |
