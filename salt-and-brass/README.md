# Salt & Brass

A bowed circular brass plate gathers 5,400 grains of salt into eight harmonic standing-wave figures. In plate.py, circular Bessel eigenmodes set the plate in motion while a tangent bow stroke glides across the rim. Grains resting on vibrating antinodes leap in molten gold before settling along quiet porcelain-ivory nodal curves, framed by engraved corner markings and live partial meters.

In score.py, eight bars in D Dorian pair a bowed brass fundamental, struck bronze partials, an off-beat harmonic answer, and a filtered crystalline whisper of leaping salt. Both the bow contact point and the stereo image orbit the rim by 45° per bar. The 384 frames at 24 fps fill one 16-second loop with ringing tails wrapped seamlessly into the opening. Follow moves between the eigenmodes, salt migration, bow contact arc, bronze tones, salt whisper, partial meters, and wrapping tails.

## Regenerate

Use Python 3.10+ with NumPy. The packer simulates the grains, renders the stereo audio, and packages both Python listings. From the repository root:

```sh
cd salt-and-brass
python -m pip install numpy
python pack.py
```

The result writes [salt-and-brass.rwl](salt-and-brass.rwl). Copy it into Lab Player’s `artworks/` folder and relaunch to play it. Original code and artwork use the repository’s [MIT license](../LICENSE).
