# Night Carol

An original carol for four voices, written across the sky as it is sung.

Handbells ring a falling peal over a snowy village at night. Then a small choir begins to sing, and every note becomes a star. Left to right is time, and up and down is pitch. Each voice draws its own constellation: the soprano in gold, the alto in white, the tenor in green and the bass in red. Four carolers stand at the church door, and each lantern brightens with its singer's voice. The words appear along the bottom like a hymn book, one syllable at a time. On the final "Noel", every star of the carol flies together into one Christmas star above the steeple. While the bells open the next round, the star melts into falling snow, and the sky is empty again for the first word.

The music and the words are original. There are no recordings anywhere in this piece: the choir, the bells, the organ and the winter air are all calculated from sine waves and noise.

Silent text art and sound together: 132 × 44 cells, 15 fps, 864 frames (57.6 s), 18 bars of 4/4 in G major at 75 BPM, so one beat is exactly 12 frames.

> *Hush, the snow on the town;*
> *lamps in the windows glow.*
> *Far on the hill, the night is still,*
> *stars over all below.*
>
> *Ring, bells, ring through the winter night;*
> *sing as the candles burn.*
> *Noel, noel, the year will turn.*
> *Noel.*

## Play it

Copy [night-carol.rwl](night-carol.rwl) into Lab Player's `artworks/` folder and relaunch, or drop it onto the open player. Sound is one stereo track at 48 kHz. Turn on **Follow** to watch the code: on each downbeat it shows that bar of the score, and halfway through the bar it shows the code that is singing, ringing or drawing at that moment.

## How the choir sings

`choir.py` makes a voice the way the body does, in two steps. This is called the **source-filter model**.

1. **The source.** Vocal folds buzz at the note's pitch, which gives a stack of **harmonics**: the pitch, twice the pitch, three times, and so on, each a little quieter.
2. **The filter.** The throat and mouth have resonances called **formants**, and their frequencies decide the vowel. "Ah" has its first two formants near 800 and 1150 Hz; "ee" has them near 270 and 2140 Hz. Harmonics close to a formant ring out, and the rest are hushed.

`sing()` adds up the harmonics one by one (**additive synthesis**), giving each the loudness that the current vowel's formants allow (`spectrum()`). The pitch glides between notes (**portamento**), the vowels melt into each other, and a gentle **vibrato** wobbles the pitch about five times a second. Three singers per part, each with their own vibrato speed, tuning and breath timing, turn one voice into a small choir. `consonant()` adds a brief puff of shaped noise for the "s", "sh", "h", "f" and "t" sounds at the start of a syllable.

The handbells are a few decaying sine waves with a strong partial at three times the pitch (a twelfth), which is what gives a handbell its clear, hollow ring. The organ is a soft flute stop: a sine and a little of its octave for each pipe. Everything finally passes through `hall()`, which **convolves** the sound with a few seconds of decaying noise to give it the echo of a stone church. The convolution runs around the whole loop, so the last chord's echo rings into the first bars of the next round.

## How the harmony is written

Only the melody and the chords are written by hand, in `SCORE` in `carol.py`. `harmonize()` finds the alto, tenor and bass with the first rule a harmony student learns, **voice leading**: for every syllable, give each lower voice the note of the chord that is closest to the note it sang last, and let the tenor fill in any chord note that is still missing. That's why the inner voices move smoothly instead of jumping. The bass takes the chord's bass note, so "D7" pulls toward G and "D/F#" walks down by step.

## Regenerate

Use Python 3.10 or newer with NumPy (tested with NumPy 2.5.3). The packer draws every frame, sings and rings the audio, and packages the four Python listings with the repository license. From the repository root:

```sh
cd night-carol
python -m pip install numpy
python pack.py
```

It writes `night-carol.rwl` in this folder, or to the path given as its first argument. It needs no network and writes nothing else, apart from Python's usual `__pycache__`. A build takes about a minute. Every random choice uses a fixed seed and the zip entries carry a fixed date, so the package comes out byte-for-byte identical on every run.

To see a single frame without the player, run `python sky.py 560` in a UTF-8 terminal with 24-bit color, at least 132 × 44. A frame number between 0 and 863 picks the moment: 560 is "Ring, bells, ring through the winter night", and 863 is the gathered star.

## Files

- `carol.py`: the words, the melody, the chords and the voice-leading rule
- `choir.py`: the singers, handbells, organ, church echo and winter air
- `sky.py`: the sky as a staff of stars, the village, the carolers and the words
- `pack.py`: builds the package and its Follow tour
- `night-carol.rwl`: the playable package

Made with: Claude (Anthropic), using Claude Code
