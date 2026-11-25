# Chamber Music

A silent, ten-second score for an imaginary shell instrument. Read it from the coil outward. A copper glow travels along the partitions, the five gauges catch it in succession, and the trace at the lip rings briefly after the light reaches the mouth.

[Watch one breath](preview.gif)

## Run

Use Python 3.10 or newer in a UTF-8 terminal. The animation uses the Python standard library. Allow at least 112 columns and 38 rows. A monospace font with Unicode Braille glyphs and a terminal with 24-bit color give the clearest engraving.

```sh
python3 chamber_music.py
```

Press Ctrl+C to leave the animation. For a still, even in a smaller window, use either command below. Redirected output is a plain-text still.

```sh
python3 chamber_music.py --still
python3 chamber_music.py --still --no-color --frame 124
```

## Inside the shell

Imagine taking a print from a shell sliced open along its coil. The edge of each whorl is a logarithmic spiral. The partitions bow across it, packed so close at the core that they print almost solid. Eight samples in each character cell pick out those walls as Braille dots. Between the walls, a second set of curved marks suggests the grain of nacre.

The lighting supplies the score. Every point on the spiral receives the same quick attack and slow decay, delayed by its distance along the winding angle. A damped oscillation at the lip writes the last few moments onto the trace. The instrument is imaginary and the scale is relative.

One loop is 160 frames at 16 frames per second. Frame numbers wrap, and the piece uses no randomness. The GIF records the same character grids in color. No sound, network access, or external assets are needed to run the source.

MIT License. Copyright (c) 2026 Rari-One. The full license is in the source.

Made with: Astra 6.2 (OpenAI), using OpenAI Codex
