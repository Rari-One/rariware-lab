# The Long Way Round

One drop of water goes all the way round in a minute. It gathers out of vapour inside a moonlit cloud and falls through the night onto a snowy peak. Then it runs down a stream through the pines, while the moon rises over the mountains. A river carries it through a village, where lit windows shimmer in the water and the church bell tolls as it passes. At the sea it rides the swell while a whale slides by underneath and calls. Then it sinks into the deep, past jellyfish, a turning shoal and an anglerfish's lure, waking blue-green plankton in its wake. On the trench floor a hydrothermal vent lifts it back up. It breaks the surface as vapour and rises with the wind, round the world and back into the cloud it fell from. The world wraps around, so the loop has no seam.

The camera follows the drop through one continuous landscape, 2,560 Braille dots around. Captions name the seven chapters, a route line shows how far round the drop has come, and a readout gives its height above or below sea level.

The music is 28 bars at 105 BPM, and one beat is exactly eight frames. The theme belongs to the drop. A celesta finds it in the cloud, a flute carries it down the stream and through the village (with a second flute a third below), and glass bells keep it in the deep. On the way home the flute and celesta sing it together, and the drop flares on every note. Pads, plucks, bass and drums are all synthesized, with no samples. So is the world: wind, a stream, crickets, the bell, waves, the whale, a low pressure hum, bubbles, the vent and the splash as the drop breaks the surface. Underwater the music is muffled. Follow walks through all five source files with 36 markers, highlighting the code for whatever is on screen.

## Bounds

This piece was made to see how far a version 1 package can go:

| | This piece | Limit |
| --- | --- | --- |
| Length | 64 s (896 frames at 14 fps) | 900 frames |
| Audio | 12,288,000 bytes | 12 MiB (98%) |
| Decoded cells | 130 × 43 × 896 | 24 MiB (99.5%) |
| Package | about 15.6 MB | 16 MiB (93%) |
| Source listings | 6 | 8 |
| Follow markers | 36, all with line ranges | 1,024 |

Sixty-four seconds is the longest stereo loop a version 1 package can hold. The audio cap allows 65.5 seconds, and 14 fps is the lowest rate whose frame count fits under 900 and divides evenly into 48 kHz samples.

## Play it

Copy [long-way-round.rwl](long-way-round.rwl) into Lab Player's `artworks/` folder and relaunch.

## Regenerate

Use Python 3.10+ with NumPy. The packer draws all 896 frames, renders the stereo audio, and packages the six Python listings with the repository license. It takes a little over a minute and uses under 1 GB of memory, mostly for the audio. It writes `long-way-round.rwl` in this folder, or to a path given as its first argument. It needs no network and writes nothing else, apart from Python's usual `__pycache__`. From the repository root:

```sh
cd long-way-round
python -m pip install numpy
python pack.py
```

Every random choice uses a fixed seed, so the package contents come out the same on every run.

To see a single frame without the player, run `python world.py 600` in a UTF-8 terminal with 24-bit color, at least 130 × 43. A frame number between 0 and 895 picks the moment, and 600 is the whale.

## Files

- `journey.py`: the clock, the land, the drop's route and the camera
- `world.py`: sky, cloud, snow, pines, stream, village, river, sea, vent, the drop and the captions
- `deep.py`: the whale, jellyfish, shoal and anglerfish
- `score.py`: chords, bass and the theme, bar by bar
- `voices.py`: every instrument and sound, and the mix
- `pack.py`: builds the package and its Follow markers
- `long-way-round.rwl`: the playable package

Made by Claude for RariWare Lab. Original code and artwork use the repository's [MIT license](../LICENSE).
