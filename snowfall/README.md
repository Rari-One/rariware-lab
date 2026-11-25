# Snowfall

Snow falling over pines on a winter night, drawn in text.

A full moon hangs over two treelines receding into haze, and a
snowfield catches the moonlight in the middle distance. Two big
snow-loaded pines frame the view, and a lantern on a post burns warm
on the right, the one warm thing in the cold. Snow falls in three
depths — far flakes small and slow, near flakes big and fast, swaying
wide in a slow gust that breathes once per loop.

One standalone Python file, one seamless loop, no input, no network,
no sound, no dependencies beyond Python 3.

## Run it yourself

Needs Python 3 and nothing else. Run in a terminal with 24-bit color,
at least 120 columns by 41 rows, and press Ctrl+C to stop.

```
python3 snowfall.py
python3 snowfall.py --still    # one frame
python3 snowfall.py --export   # whole loop as JSON (what rariware.com/lab/ plays)
python3 snowfall.py --stats    # how much changes per frame
python3 snowfall.py --seed 42  # a different, still seamless, night
```

The animation runs on the alternate screen, so it leaves nothing in
the scrollback, and your screen and cursor come back when it exits.
If the terminal is too small it says so and waits for a resize; a
larger terminal centers the artwork, and resizing mid-animation
re-centers it.

## How it is built

- Canvas: 120 × 40, 15 fps, 180 frames = 12 seconds, one seamless loop.
- Seed: 2028 by default, so the same night is reproducible.
- Every time term is a whole number of cycles per loop, so frame 179
  flows back into frame 0. Measured loop seam: 5.50% of cells change
  from frame 179 to frame 0, inside the normal per-frame range below,
  so the snow just keeps falling — there is no still point to jump from.
- Change rate: average 3.5% of cells per frame, highest 5.6% — busier
  than Fireflies, as falling snow should be, still calm.
- Export: `rariware-lab-frames` JSON
  (`cols`, `rows`, `fps`, `loop`, `palette`, `frames`, `colors`).
  2.7 MB raw, 138 KB gzipped, 33 colours.
- The moon is drawn as an ellipse in cell space, because cells are
  taller than they are wide — a circle in cells renders as a tall pill.

## License

MIT License, Copyright (c) 2026 Rari-One. The full license text is at
the top of `snowfall.py`.

## Files

- `snowfall.py` — the whole piece
- `manifest.json` — title, description, and display settings
- `frames.json` — the exported loop, generated with `python3 snowfall.py --export`
- `README.md` — this file

Made with: Muse (Meta)
