# Fireflies

Fireflies over a still pond on a summer night, drawn in text.

A full moon hangs over a low treeline. Below it, a still pond mirrors
the moon in a shimmering column. Thirty-six fireflies drift and blink
over the water, each on its own rhythm, with dim reflections below
them. Ripples expand and fade on the pond. Reeds and cattails stand
in the foreground corners.

One standalone Python file, one seamless loop, no input, no network,
no sound, no dependencies beyond Python 3.

## Run it yourself

Needs Python 3 and nothing else. Run in a terminal with 24-bit color,
at least 120 columns by 41 rows, and press Ctrl+C to stop.

```
python3 fireflies.py
python3 fireflies.py --still    # one frame
python3 fireflies.py --export   # whole loop as JSON (what rariware.com/lab/ plays)
python3 fireflies.py --stats    # how much changes per frame
python3 fireflies.py --seed 42  # a different, still seamless, night
```

## How it is built

- Canvas: 120 × 40, 15 fps, 180 frames = 12 seconds, one seamless loop.
- Seed: 2027 by default, so the same night is reproducible.
- Every time term is a whole number of cycles per loop, so frame 179
  flows back into frame 0. Measured loop seam: 0.27% of cells change
  from frame 179 to frame 0, against 0.8% average per frame.
- Change rate: average 0.8% of cells per frame, highest 2.4% — a calm
  piece, not a flashing one.
- Export: `rariware-lab-frames` JSON
  (`cols`, `rows`, `fps`, `loop`, `palette`, `frames`, `colors`).
  1.9 MB raw, under 250 KB compressed.

## License

MIT License, Copyright (c) 2026 Rari-One. The full license text is at
the top of `fireflies.py`.

## Files

- `fireflies.py` — the whole piece
- `manifest.json` — title, description, and display settings
- `frames.json` — the exported loop, generated with `python3 fireflies.py --export`
- `README.md` — this file
