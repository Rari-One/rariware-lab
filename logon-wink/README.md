# Logon Wink

A little greeter winks at you when you log on. Teal twin-tails, stars
twinkling overhead, a shooting star, and a blinking prompt below — the old
logon prank, kept friendly. She watches with both eyes open, then winks
twice per loop, with a sparkle at the corner of her eye. The prompt
backspaces and retypes itself mid-loop, the headphones pulse with the music,
and a music-box chime rings with every wink.

With sound. 120 × 40, 15 fps, 180 frames (12 s loop).

## Regenerate

Python 3.10+, standard library only. From the repository root:

```sh
cd logon-wink
python logon-wink.py --export --package
```

`--export` writes the gallery `frames.json` and `manifest.json`;
`--package` renders the score with `score.py` (writing `audio.pcm`) and
writes the playable `logon-wink.rwl` for the Lab Player. `score.py` on its
own writes `audio.pcm`; `score.py --check` validates its length against the
loop. Original code and artwork use the repository's [MIT license](../LICENSE).
