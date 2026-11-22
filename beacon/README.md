# Beacon

A lonely lighthouse of the North Sea keeps its slow watch. Its lamp turns
once per loop, sweeping a warm beam across the sky and laying a road of light
on the water. Stars twinkle, a few shoot across the dark, and a faint wash of
aurora breathes high overhead. The sea shimmers, and the light finds its own
reflection and carries it home.

Silent. 120 × 40, 15 fps, 180 frames (12 s loop).

## Regenerate

Python 3.10+, standard library only. From the repository root:

```sh
cd beacon
python beacon.py --export --package
```

`--export` writes the gallery `frames.json` and `manifest.json`;
`--package` writes the playable `beacon.rwl` for the Lab Player.
Original code and artwork use the repository's [MIT license](../LICENSE).
