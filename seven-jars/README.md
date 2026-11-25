# Seven Jars

Rain at night. A broken gutter drips into seven glass vessels on a wooden shelf: a wine bottle, a mason jar, a flask, a vase, a crock, a milk bottle and a jam jar. Each holds a different depth of water, so each sings a different note. Left to right they climb D major pentatonic, D4 to E5. Every note you hear is a drop you can watch swell at a rusted seam, fall, and strike the water. The jar lights up in its own glass color as it rings. Late in the sixth bar, lightning shows a ridge of firs and turns the jars to dark silhouettes. The thunder arrives a second later and rolls across the loop seam into the first bar.

In score.py, the melody is written as a drip schedule: eight bars of eighth notes, one digit per jar. That same list drives the glass tones, the bubble "plip" of each drop, the falling drops, the splashes, the rocking surfaces and the light. Under it are a soft two-bar chord hum, a seamless rain bed with thousands of tiny droplet ticks, and the thunder. In garden.py, the glass, rain and spray are Braille dots. The water is solid and fractional blocks, so a ripple can lift a surface by an eighth of a cell. 512 frames at 24 fps make one 21⅓-second loop at 90 BPM. Follow moves through the vessels, the score, the falling drops, the glass voice, the splash, the ripples, the lightning, the thunder and the rain.

## Play it

Copy [seven-jars.rwl](seven-jars.rwl) into Lab Player's `artworks/` folder and relaunch. Sound is a single stereo track at 48 kHz.

## Regenerate

Use Python 3.10+ with NumPy. The packer draws every frame, renders the stereo audio, and packages both Python listings with the repository license. It writes `seven-jars.rwl` in this folder, or to a path given as its first argument. It needs no network and writes nothing else, apart from Python's usual `__pycache__`. From the repository root:

```sh
cd seven-jars
python -m pip install numpy
python pack.py
```

The build is deterministic. Every random choice uses a fixed seed, so the package contents come out identical on every run.

To see a single frame without the player, run `python garden.py 360` in a UTF-8 terminal with 24-bit color, at least 120 × 44. A frame number between 0 and 511 picks the moment, and 360 is the lightning.

## Files

- `score.py`: the jars' tuning, the melody, and the audio renderer
- `garden.py`: the vessels, gutter, rain, drops, splashes, lightning and puddle
- `pack.py`: builds the Lab Player package and its Follow markers
- `seven-jars.rwl`: the playable package

Made by Claude for RariWare Lab. Original code and artwork use the repository's [MIT license](../LICENSE).

Made with: Claude Opus 5.5 (Anthropic), using Claude Code
