# The Moon in the Pond

A full moon lies reflected in a still, dark pond between three lily pads. Rain begins: a single large drop lands in the middle of the moon, then the shower thickens, and every drop throws out a ring that breaks the reflection into slivers and scatters cool glints across the water. In the last bars the rain stops, the rings fade, and the moon pulls itself back together just as the 24-second loop begins again.

Each drop also sounds. A small rising "plink" rings out where it lands, panned left or right to match, tuned to a D major pentatonic scale so the rain plays a tune over a soft four-chord pad (D, B minor, G, A) and a hiss that swells with the shower.

## Run it

Use Python 3.10 or newer. No other packages are needed. From the repository root:

```sh
cd the-moon-in-the-pond
python pack.py
```

This takes about half a minute and writes one file, `the-moon-in-the-pond.rwl`, next to the script. Nothing is downloaded. Copy the file into Lab Player's `artworks/` folder and relaunch to watch and hear it. For a quick look without the player, `python pond.py` prints the first frame as plain text.

The rain is seeded (`SEED = 1907` in `pond.py`), so every build is identical. Change the seed for a different shower.

## Where to look

- **The wave equation** (`wave_step` in `pond.py`). The water is a grid of heights. Each step pulls every point toward the average of its four neighbours, the *discrete Laplacian*, using a leapfrog finite-difference scheme. A damping factor makes old rings fade. Try changing `C2` (wave speed) or `DAMPING`.
- **Displacement-mapped reflection** (`light` in `pond.py`). To find what a point of water reflects, the code looks up the sky at a position nudged by the water's slope there. Flat water mirrors the moon exactly; rippled water bends it apart.
- **Brightness ramps** (`water_cell` in `pond.py`). Each character cell picks a glyph from `" .·-~≈=≡▒▓█"` and a colour by how bright it is.
- **Raindrop sounds** (`plink` in `score.py`). A real drop traps a tiny air bubble that rings like a bell and rises in pitch, which is called *Minnaert resonance*. Here the chirp is pulled onto a musical scale.
- **A seamless loop.** The rain stops before the end, so the pond is calm when the loop restarts. The breeze `swell` has a period that divides the loop. In `score.py`, sounds that run past the end are wrapped to the start, and the rain hiss filter runs around the loop twice so its end matches its beginning.

In Lab Player, turn on **Follow** to watch the source jump to each of these sections as the shower grows and fades.

## Details

112 × 36 cells, 15 frames per second, 360 frames, one 24-second loop with stereo sound at 48 kHz. Original code, artwork and audio use the repository's [MIT license](../LICENSE).

Made with: Claude Opus 5.5 (Anthropic), using Claude Code
