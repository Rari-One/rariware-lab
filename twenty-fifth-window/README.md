# The Twenty-Fifth Window

A curtained shop window holds a Christmas tree, colored glass and ribboned parcels. In scene.py, overlapping tiers establish the silhouette. A seeded snowfall passes behind the window bars. Gold chains and five colors of bulbs sit over the fir, and the star brightens on each melodic attack.

In music.py, eight bars of waltz time combine struck music-box teeth, bowed downbeats and sleigh bells. The melody generator supplies the arrival times for the lights. Each beat lasts 32,000 stereo sample pairs and 16 visual frames. The 384 frames at 24 fps fill one 16-second loop. Follow connects the snow, lights and wrapping paper to the voices in the score.

## Regenerate

Use Python 3.10+ with NumPy. The package script renders both the frames and the exact-length audio track. From the repository root:

```sh
cd twenty-fifth-window
python -m pip install numpy
python pack.py
```

The result replaces [the playable package](../player/artworks/twenty-fifth-window.rwl). Relaunch the player to see your changes. Original code and artwork use the repository’s [MIT license](../LICENSE).

Made with: Astra 6.2 (OpenAI), using OpenAI Codex
