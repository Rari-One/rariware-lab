# Aurora

Northern lights over mountains and a still lake, drawn in text.

Green and violet curtains of light ripple above snowy mountains under a
starry sky, and the still lake below mirrors them, darker and rippled.
Dark pines stand on the shores in the bottom corners. This is the first
piece shown on rariware.com/lab/.

One standalone Python file, one seamless loop, no input, no network,
no sound, no dependencies beyond Python 3.

## Run it yourself

Needs Python 3 and nothing else. Run in a terminal with 24-bit color,
at least 120 columns by 41 rows, and press Ctrl+C to stop.

```
python3 aurora.py
python3 aurora.py --still              # one frame
python3 aurora.py --still --no-color   # one frame, plain text
python3 aurora.py --export             # whole loop as JSON (what rariware.com/lab/ plays)
python3 aurora.py --stats              # how much changes per frame
python3 aurora.py --seed 42            # a different, still seamless, sky
```

The terminal needs a font with box-drawing and block characters.

## How it is built

- Canvas: 120 × 40, 15 fps, 180 frames = 12 seconds, one seamless loop.
- Seed: 2026 by default, so the same sky is reproducible.
- Every time term is a whole number of cycles per loop, so frame 179
  flows back into frame 0. Measured loop seam: 5.92% of cells change
  from frame 179 to frame 0, inside the normal per-frame range below.
- Change rate: average 5.5% of cells per frame, highest 7.1%.
- Export: `rariware-lab-frames` JSON
  (`cols`, `rows`, `fps`, `loop`, `palette`, `frames`, `colors`).
  2.6 MB raw, 179 KB gzipped, 33 colours.

## License

MIT License, Copyright (c) 2026 Rari-One. The full license text is at
the top of `aurora.py`.

## Files

- `aurora.py` — the whole piece
- `manifest.json` — title, description, and display settings
- `frames.json` — the exported loop, generated with `python3 aurora.py --export`
- `README.md` — this file

Made with: Rari-One (original version), then improved by a Grok agent (xAI) using Cursor; exact model not recorded
