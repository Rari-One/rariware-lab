# Flyway

A grey heron lifts out of a reedbed at dawn, crosses open fields and the
sea, and comes down again at dusk to the same reeds. Four acts, one loop:
dawn wetlands, open country, the sea, dusk home. The light travels with
her — gold, blue, pale haze, violet — and the ground scrolls beneath her
wings.

In flyway.py, the bird is drawn on a dot canvas (two dots across, four
down per cell) and folded into Braille, so she keeps her curves, while
the sky is a dithered dot gradient that lets her read against it. Her
wings beat hard for the takeoff, settle to a cruise, and go quiet for the
long glide home; her legs drop for the landing. In score.py, the same
flap schedule sets sixteen soft wingbeats, a flute line in D Dorian
changes with the country, a dawn chorus chatters over the reeds, waves
breathe under the sea act, and the dawn theme comes home an octave down.
512 frames at 24 fps make one 21⅓-second loop. Follow moves through the
sky, the wingbeats, the fireflies, the fields, the flute, the sea, the
gulls, the stars, and the landing.

## Play it

Copy [flyway.rwl](flyway.rwl) into Lab Player's `artworks/` folder and
relaunch. Sound is a single stereo track at 48 kHz.

## Regenerate

Use Python 3.10+ with NumPy. The packer draws every frame, renders the
stereo audio, and packages both Python listings with the repository
license. It writes `flyway.rwl` in this folder, or to a path given as its
first argument. It needs no network and writes nothing else, apart from
Python's usual `__pycache__`. From the repository root:

```sh
cd flyway
python -m pip install numpy
python pack.py
```

The build is deterministic. Every random choice uses a fixed seed, so
the package contents come out identical on every run.

To see a single frame without the player, run `python flyway.py 160` in
a UTF-8 terminal with 24-bit color, at least 120 × 44. A frame number
between 0 and 511 picks the moment, and 160 is the open fields.

## Files

- `flyway.py`: the heron, the sky, the scrolling ground, and the light
- `score.py`: the wingbeats, the flute, the chorus, the sea, and the drone
- `pack.py`: builds the Lab Player package and its Follow markers
- `flyway.rwl`: the playable package

Made by Atlas for RariWare Lab. Original code and artwork use the
repository's [MIT license](../LICENSE).

Made with: Muse (Meta)
