# Endpaper Tide

A silent piece of marbled paper moves inside a stationary deckled edge. The JavaScript generator traces each cell backward through a sideways current and alternating comb teeth. The resulting position selects an ink ribbon. Four samples per cell soften tight curls; solid block characters carry the mixed color.

One turn of the phase takes 240 frames at 20 fps. The four source ranges follow the pull of the bath, the teeth, the eddies and the final color sampling. Try changing the tooth spacing in tide.mjs and comparing the regenerated print.

## Regenerate

Install Node.js and Python 3.10+. Node writes the frame stream; the Python standard library packages it with the JavaScript listing. From the repository root:

```sh
cd endpaper-tide
node tide.mjs frames.bin
python pack.py
```

The result replaces [the playable package](../player/artworks/endpaper-tide.rwl). Relaunch the player to see your changes. Original code and artwork use the repository’s [MIT license](../LICENSE).
