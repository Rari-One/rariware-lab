"""Night Carol — the voices. A choir, handbells and an organ, built from sine waves.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

There are no recordings in this piece. A singing voice is made the way the body
makes one, in two steps. This is called the source-filter model:

1. The source. Vocal folds buzz at the note's pitch, which gives a stack of
   harmonics: the pitch itself, twice it, three times it, and so on, each
   quieter than the last.
2. The filter. The throat and mouth make resonances called formants. Their
   frequencies decide the vowel: "ah" has its first two formants near 800 and
   1150 Hz, "ee" near 270 and 2140 Hz. Harmonics near a formant ring out;
   the rest are hushed.

So every harmonic here gets its loudness from the formants of the vowel being
sung (additive synthesis). Three slightly different singers per part, each
with their own vibrato and timing, make a choir instead of one voice.
"""
import numpy as np

from carol import (FPS, FRAMES, PARTS, PEAL, RATE, SECONDS_PER_BEAT, SUNG, frame_of, hz,
                   seconds)

N = FRAMES * RATE // FPS          # 2,764,800 stereo sample pairs: 57.6 seconds
HOP = 96                          # control rate: 500 updates per second
TAU = 2 * np.pi
rng = np.random.default_rng(1225)

# Formant tables: frequency (Hz), level (dB) and bandwidth (Hz) of the first
# five formants for each vowel, per voice type. These are standard acoustic
# measurements of trained singers, rounded.
FORMANTS = {
    "soprano": {"a": ([800, 1150, 2900, 3900, 4950], [0, -6, -32, -20, -50]),
                "e": ([350, 2000, 2800, 3600, 4950], [0, -20, -15, -40, -56]),
                "i": ([270, 2140, 2950, 3900, 4950], [0, -12, -26, -26, -44]),
                "o": ([450, 800, 2830, 3800, 4950], [0, -11, -22, -22, -50]),
                "u": ([325, 700, 2700, 3800, 4950], [0, -16, -35, -40, -60])},
    "alto": {"a": ([800, 1150, 2800, 3500, 4950], [0, -4, -20, -36, -60]),
             "e": ([400, 1600, 2700, 3300, 4950], [0, -24, -30, -35, -60]),
             "i": ([350, 1700, 2700, 3700, 4950], [0, -20, -30, -36, -60]),
             "o": ([450, 800, 2830, 3500, 4950], [0, -9, -16, -28, -55]),
             "u": ([325, 700, 2530, 3500, 4950], [0, -12, -30, -40, -64])},
    "tenor": {"a": ([650, 1080, 2650, 2900, 3250], [0, -6, -7, -8, -22]),
              "e": ([400, 1700, 2600, 3200, 3580], [0, -14, -12, -14, -20]),
              "i": ([290, 1870, 2800, 3250, 3540], [0, -15, -18, -20, -30]),
              "o": ([400, 800, 2600, 2800, 3000], [0, -10, -12, -12, -26]),
              "u": ([350, 600, 2700, 2900, 3300], [0, -20, -17, -14, -26])},
    "bass": {"a": ([600, 1040, 2250, 2450, 2750], [0, -7, -9, -9, -20]),
             "e": ([400, 1620, 2400, 2800, 3100], [0, -12, -9, -12, -18]),
             "i": ([250, 1750, 2600, 3050, 3340], [0, -30, -16, -22, -28]),
             "o": ([400, 750, 2400, 2600, 2900], [0, -11, -21, -20, -40]),
             "u": ([350, 600, 2400, 2675, 2950], [0, -20, -32, -28, -36])},
}
BANDWIDTHS = [80, 90, 120, 130, 140]

# The vowel each syllable is held on. Singers sustain vowels; consonants are
# only brief touches at the start (see consonant() below).
VOWELS = {"hush": "u", "the": "a", "snow": "o", "on": "o", "town": "a", "lamps": "a",
          "in": "i", "win": "i", "dows": "o", "glow": "o", "far": "a", "hill": "i",
          "night": "a", "is": "i", "still": "i", "stars": "a", "o": "o", "ver": "e",
          "all": "o", "be": "i", "low": "o", "ring": "i", "bells": "e", "through": "u",
          "ter": "e", "sing": "i", "as": "a", "can": "a", "dles": "e", "burn": "e",
          "no": "o", "el": "e", "year": "i", "will": "i", "turn": "e"}
PAN = {"soprano": -0.45, "alto": -0.15, "tenor": 0.15, "bass": 0.45}
LEVEL = {"soprano": 1.0, "alto": 0.8, "tenor": 0.8, "bass": 0.95}


def word(syllable):
    return "".join(c for c in syllable.lower() if c.isalpha())


def spectrum(part, vowel_weights, freqs):
    """How loud a vocal tract shaped like this vowel makes each frequency."""
    gain = np.zeros_like(freqs)
    for vowel, weight in vowel_weights.items():
        centres, levels = FORMANTS[part][vowel]
        for centre, level, width in zip(centres, levels, BANDWIDTHS):
            gain += weight * 10 ** (level / 20) / np.sqrt(1 + ((freqs - centre) / (width / 2)) ** 2)
    return gain


def sing(part, singer):
    """One singer's whole line: pitch, loudness and vowel, then additive synthesis."""
    steps = N // HOP + 2
    t = np.arange(steps) * HOP / RATE
    f0 = np.zeros(steps)
    loud = np.zeros(steps)
    vowel = {v: np.zeros(steps) for v in "aeiou"}
    active = np.zeros(steps, bool)
    late = rng.uniform(-0.012, 0.012)                  # each singer breathes in a little differently
    for i, note in enumerate(SUNG):
        start = seconds(note["bar"], note["beat"]) + late
        end = start + note["beats"] * SECONDS_PER_BEAT
        span = (t >= start) & (t < end)
        f0[span] = hz(note["notes"][part])
        active |= span
        # Each syllable swells in over 70 ms and lets go 80 ms before the next,
        # which is where the consonants sit.
        swell = np.clip((t[span] - start) / 0.07, 0, 1) * np.clip((end - 0.08 - t[span]) / 0.05, 0, 1)
        loud[span] = np.maximum(loud[span], swell * (0.85 + 0.15 * (note["beat"] == 0)))
        vowel[VOWELS[word(note["syllable"])]][span] = 1.0
    # Glide between notes (portamento) and between vowels, as real singers do:
    # a one-pole smoother, the simplest low-pass filter.
    # Through the silences, every curve simply keeps its last value.
    last = np.maximum.accumulate(np.where(active, np.arange(steps), 0))
    for curve, speed in ((f0, 0.12),) + tuple((vowel[v], 0.08) for v in "aeiou"):
        curve[:] = curve[last]
        smooth = np.empty_like(curve)
        level = curve[0]
        for k in range(steps):
            level += speed * (curve[k] - level)
            smooth[k] = level
        curve[:] = smooth
    f0[f0 <= 0] = hz(60)
    # Vibrato: about 5.4 wobbles a second, half a percent wide, plus a slow drift.
    rate = 5.4 + 0.25 * singer
    f0 *= 1 + 0.005 * np.sin(TAU * rate * t + rng.uniform(0, TAU)) * np.clip(loud * 1.3, 0, 1)
    f0 *= 2 ** ((rng.normal(0, 4) + 3 * np.sin(TAU * 0.11 * t + singer)) / 1200)
    sample_f0 = np.interp(np.arange(N), np.arange(steps) * HOP, f0)
    phase = TAU * np.cumsum(sample_f0) / RATE
    weights = {v: vowel[v] / np.maximum(sum(vowel.values()), 1e-9) for v in "aeiou"}
    out = np.zeros(N)
    for k in range(1, int(5200 / hz(min(n["notes"][part] for n in SUNG))) + 1):
        amp = spectrum(part, weights, k * f0) / k * (k * f0 < 6000)   # source falls 6 dB per octave
        if amp.max() < 1e-4:
            continue
        out += np.interp(np.arange(N), np.arange(steps) * HOP, amp * loud) * np.sin(k * phase + k * singer)
    return out


def consonant(syllable):
    """A short burst of shaped noise for the sounds that start a syllable."""
    w = word(syllable)
    t = np.arange(int(RATE * 0.09)) / RATE
    noise = rng.standard_normal(len(t))
    spectrum_ = np.fft.rfft(noise)
    f = np.fft.rfftfreq(len(t), 1 / RATE)
    if w[:2] in ("sh", "th") or w[0] in "sfh":
        band = (f > 2500) & (f < 9000) if w[0] == "s" else (f > 1200) & (f < 6000)
        hiss = np.fft.irfft(spectrum_ * band, len(t))
        return hiss / np.abs(hiss).max() * np.sin(np.pi * t / t[-1]) ** 2 * 0.025
    if w[0] in "bdtkcgp":
        burst = np.fft.irfft(spectrum_ * ((f > 800) & (f < 5000)), len(t))
        return burst / np.abs(burst).max() * np.clip(t / 0.002, 0, 1) * np.exp(-t / 0.008) * 0.012
    return np.zeros(0)


def handbell(note, loud=1.0):
    """A handbell: a clear fundamental with a strong twelfth (three times the pitch)."""
    t = np.arange(int(RATE * 3.5)) / RATE
    f = hz(note)
    tone = sum(a * np.sin(TAU * f * r * t) * np.exp(-t / d)
               for r, a, d in ((1, 1.0, 2.2), (3.0, 0.42, 0.9), (4.2, 0.12, 0.35), (5.4, 0.07, 0.2)))
    return 0.16 * loud * tone * np.clip(t / 0.003, 0, 1)


def church_bell():
    t = np.arange(int(RATE * 6)) / RATE
    f = hz(50)                                          # D3
    partials = ((0.5, .5, 5), (1, .8, 4), (1.19, .5, 3), (1.5, .3, 2.2), (2, .6, 2.2), (2.52, .25, 1.4))
    return 0.13 * sum(a * np.sin(TAU * f * r * t) * np.exp(-t / d) for r, a, d in partials)


def organ(notes, length):
    """A soft flute stop: each pipe is a sine and a little of its octave."""
    t = np.arange(int(RATE * (length + 0.6))) / RATE
    env = np.clip(t / 0.25, 0, 1) * np.clip((length + 0.6 - t) / 0.6, 0, 1)
    tone = sum(np.sin(TAU * hz(n) * t) + 0.18 * np.sin(TAU * 2 * hz(n) * t) for n in notes)
    return 0.018 * tone * env


def place(bus, start, wave, pan=0.0):
    """Mix a sound into the loop, panned, wrapping anything that runs past the end."""
    if not len(wave):
        return
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    at = int(round(start * RATE)) % N
    idx = (at + np.arange(len(wave))) % N
    np.add.at(bus[0], idx, left * wave)
    np.add.at(bus[1], idx, right * wave)


def hall(dry):
    """A stone church: decaying noise as the room's echo, convolved around the loop."""
    t = np.arange(int(RATE * 3.2)) / RATE
    wet = np.zeros_like(dry)
    for ch in range(2):
        ir = np.zeros(N)
        ir[:len(t)] = rng.standard_normal(len(t)) * np.exp(-t / 0.85) * (t > 0.02)
        ir[:len(t)] *= 1 / (1 + (np.arange(len(t)) / RATE / 0.6))   # darker as it fades
        ir /= np.sqrt((ir ** 2).sum())
        wet[ch] = np.fft.irfft(np.fft.rfft(dry[ch]) * np.fft.rfft(ir), N)
    return wet


def render():
    """The whole carol as int16 stereo, left then right."""
    choir = np.zeros((2, N))
    # The choir: three singers on each of the four parts.
    for part in PARTS:
        for singer in range(3):
            line = sing(part, singer) * LEVEL[part] * 0.05
            spread = PAN[part] + (singer - 1) * 0.12
            place(choir, 0, line, spread)
        for note in SUNG:
            place(choir, seconds(note["bar"], note["beat"]) - 0.03, consonant(note["syllable"]) * LEVEL[part],
                  PAN[part])

    band = np.zeros((2, N))
    # The organ holds each chord quietly under the voices, with a pedal below.
    for note in SUNG:
        notes = list(note["notes"].values())
        length = note["beats"] * SECONDS_PER_BEAT
        place(band, seconds(note["bar"], note["beat"]), organ(notes + [note["notes"]["bass"] - 12], length))
    for bar, chord in ((0, [55, 59, 62, 67, 43]), (1, [60, 64, 67, 48]), (1.5, [62, 66, 69, 50])):
        place(band, seconds(0, bar * 4), organ(chord, 4 * SECONDS_PER_BEAT * (1 if bar < 1 else 0.5) + 0.2))
    # Handbells: the falling peal before the singing starts...
    for bar, beat, note in PEAL:
        place(band, seconds(bar, beat), handbell(note, 0.9), pan=-0.6 + (note % 12) / 10)
    # ...then a ring on the first and third beats through the refrain, high above the choir.
    for note in SUNG:
        if note["bar"] >= 10 and note["beat"] in (0, 2):
            place(band, seconds(note["bar"], note["beat"]), handbell(note["notes"]["soprano"] + 12, 0.45),
                  pan=0.55)
    # A last cascade over the final "Noel", falling into the bells that open the loop.
    for i, n in enumerate([79, 74, 71, 67, 74, 71, 67, 62]):
        place(band, seconds(17, 2 + i / 4), handbell(n, 0.5), pan=0.6 - i * 0.15)
    # A church bell far off, once at the start.
    place(band, seconds(0), church_bell(), pan=-0.3)
    # Winter air: a very soft, slow wind.
    f = np.fft.rfftfreq(N, 1 / RATE)
    wind = np.array([np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) / (1 + (f / 500) ** 2) * (f > 80), N)
                     for _ in range(2)])
    wind *= 0.012 / wind.std() * (0.6 + 0.4 * np.sin(TAU * 3 * np.arange(N) / N))

    dry = choir + band
    mix = dry + 0.55 * hall(0.8 * choir + band) + wind
    mix /= np.percentile(np.abs(mix), 99.99) / 0.8
    mix = np.tanh(1.1 * mix)                           # a soft limiter that never passes full scale
    return (mix.T * 0.98 * 32767).round().astype("<i2")


def presence():
    """How strongly each part is singing on each frame, for the lanterns in the picture."""
    glow = {part: np.zeros(FRAMES) for part in PARTS}
    for note in SUNG:
        first = frame_of(note["bar"], note["beat"])
        last = frame_of(note["bar"], note["beat"] + note["beats"])
        for part in PARTS:
            glow[part][first:last] = np.linspace(1.0, 0.75, last - first)
    return glow
