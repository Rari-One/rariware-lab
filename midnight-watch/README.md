# The Midnight Watch

One minute inside an antique pocket watch, from `11:59:00` to the stroke of twelve. It opens on a gold-and-ivory dial resting in midnight velvet, with a crescent moon at six o'clock and blued-steel hands nearing midnight. Then the camera dives straight through the central skeleton aperture into the mechanism beneath.

Inside the gearworks, seven interlocking brass, copper, and steel wheels turn in exact tooth ratios while an anchor escapement clicks on the beat, ruby jewel bearings pulse crimson, and a golden balance hairspring breathes in and out. Beyond the train lies a receding perspective vault of Gothic brass arches where three golden pendulums swing through shafts of moonlight. At the end of the hall, the chamber opens into a 3D brass armillary orrery turning around a blazing sun, carrying orbiting worlds, a ringed turquoise Saturn, and a silver comet. Rising out of the cosmos brings us into the bronze belfry as an articulated brass hammer strikes the cathedral bell on the beat, shaking the air with golden shockwaves and sparks before the camera pulls back through the sapphire crystal onto the dial at midnight.

The stereo score runs 30 bars at 120 BPM (`2.0 s` per bar, `30` frames per bar). One recurring watchmaker motif in E minor / G major transforms across every chamber—intimate music box on the dial, bright harpsichord arpeggios in the gearworks, bowed cello and cathedral organ under stereo pendulum air whooshes, a soaring woodwind and celesta theme in the orrery, and grand inharmonic bronze chimes whose ringing tails wrap seamlessly across the 60-second seam. Live fractional-block voice meters track the escapement, bells, melody, and bass while 36 `Follow` markers tour all seven source listings.

## Bounds

Built to explore the ceiling of a version 1 Lab Player package:

| | This piece | Limit |
| --- | --- | --- |
| Frames & duration | 900 frames at 15 fps (60.0 s) | 900 frames |
| Decoded cells | 124 × 45 × 900 (25,110,000 B) | 24 MiB (99.8%) |
| Audio | 11,520,000 B (48 kHz stereo) | 12 MiB (91.6%) |
| Package | ~14.4 MB | 16 MiB (~86%) |
| Source listings | 7 | 8 |
| Follow markers | 36, all with line ranges | 1,024 |

## Play it

Copy [midnight-watch.rwl](midnight-watch.rwl) into Lab Player's `artworks/` folder and relaunch.

## Regenerate

Requires Python 3.10+ and NumPy (`numpy`). Generation runs offline with fixed RNG seeds, writes `midnight-watch.rwl` beside `pack.py` (or to the path given as its first argument), and needs no external samples, fonts, or network access. From the repository root:

```sh
cd midnight-watch
python -m pip install numpy
python pack.py
```

To inspect a single frame directly in a 24-bit UTF-8 terminal (at least 124 × 45), pass `--frame` with a frame number from `0` to `899` (for example, `525` for the orrery or `666` for a bell strike):

```sh
python pack.py --frame 525
```

## Files

- `clock.py` — master 60-second timeline, chapters, easing, and vectorized Braille canvas
- `dial.py` — antique pocket watch dial, moon phase, hands, and zoom portal (Chapters I & VI)
- `gears.py` — meshing gear train, anchor escapement, hairspring, and 3D pendulum vault (Chapters II & III)
- `cosmos.py` — 3D brass armillary orrery, orbiting worlds, and midnight bronze belfry (Chapters IV & V)
- `score.py` — 30-bar harmonic score, bell strike schedule, and live voice meter envelopes
- `synth.py` — 48 kHz stereo synthesizer with wrapped hall reflections
- `pack.py` — chapter crossfades, HUD engravings, terminal preview, and `.rwl` packager
- `midnight-watch.rwl` — the playable Lab Player package

Original code and artwork use the repository's [MIT license](../LICENSE).

Made with: Neon 4 (Google), using Google Antigravity
