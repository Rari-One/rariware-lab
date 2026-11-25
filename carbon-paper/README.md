# Carbon Paper

A mechanical swallow lifts away from its blue impression. The Go generator samples curved feather strokes onto the eight dots of each Braille cell. It draws two copies of the bird on 116 × 38 cells. One holds still in blue while the warm copy rotates, beats its wings and leaves the sheet. A moving cut across the geometry makes the ink appear from tail to beak.

Six fixed source markers point to the registration corners, cut, carbon deposit, lift, ruled feathers and final trace. The 300 frames run at 20 fps for 15 seconds in silence.

## Regenerate

Install Go and Python 3.10+. Go draws the entire piece. The small Python script wraps the cells and their Go source in a ZIP. From the repository root:

```sh
cd carbon-paper
go run carbon.go frames.bin
python package.py
```

The result replaces [the playable package](../player/artworks/00-carbon-paper.rwl). Relaunch the player to see your changes. Original code and artwork use the repository’s [MIT license](../LICENSE).

Made with: Astra 6.2 (OpenAI), using OpenAI Codex
