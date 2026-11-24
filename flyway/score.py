"""Flyway — the score. A heron's journey in sound.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

The picture flies on wingbeats, so the sound does too: sixteen soft
whooshes, one per downstroke, set by the same flap schedule flyway.py
draws from. Under them a flute line in D Dorian changes with the country
— high and sparse at dawn, flowing over the fields, long and low over
the sea, and the dawn theme coming home an octave down at dusk. A dawn
chorus chatters over the reeds, waves breathe under the sea act, and a
low drone holds one chord per act. Everything wraps into one seamless
loop — tails that ring past the end come back around to the opening bars.
"""
import math

import numpy as np

FPS, FRAMES, RATE = 24, 512, 48000
SPF = RATE // FPS              # 2,000 stereo sample pairs per frame
N = FRAMES * SPF               # 1,024,000 pairs: one 21 1/3-second loop

# The flap schedule, mirroring flyway.py: hard beats for the takeoff, a
# steady cruise, then a long silent glide into the landing.
_RATE = np.ones(FRAMES) / 32.0
_RATE[:64] = 1 / 24.0
_RATE[448:] = np.linspace(1 / 32.0, 0.0, FRAMES - 448)
_PHASE = (np.cumsum(_RATE) + 0.5) % 1.0


def beats():
    """Frames where the wings reach the bottom of a stroke."""
    out = []
    prev = _PHASE[0]
    for n in range(1, FRAMES):
        if _PHASE[n] < prev:
            out.append(n)
        prev = _PHASE[n]
    return out


# The melody: (frame, MIDI note, length in frames). D Dorian throughout.
# @marker melody
MELODY = [
    # Dawn wetlands: high and sparse.
    (0, 74, 12), (16, 76, 12), (32, 77, 16), (56, 81, 16),
    (80, 79, 12), (96, 77, 12), (112, 76, 16),
    # Open country: flowing.
    (128, 69, 12), (144, 72, 12), (160, 74, 12), (176, 76, 16),
    (192, 77, 12), (208, 76, 12), (224, 74, 16), (240, 72, 16),
    # The sea: long and low.
    (256, 62, 24), (288, 65, 24), (320, 69, 24), (352, 67, 24),
    # Dusk home: the dawn theme returns, an octave down, slower.
    (384, 62, 16), (408, 64, 16), (432, 65, 20), (456, 69, 20),
    (480, 67, 16), (496, 62, 16),
]
# One low chord per act, in D Dorian: Dm, F, C, Am.
CHORDS = [(50, 53, 57), (53, 57, 60), (48, 52, 55), (45, 48, 52)]
# Dawn chorus: small birds chattering over the reeds.
CHIRPS = [12, 44, 76, 108]


def midi_hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def render():
    """Return the loop as int16 stereo, left then right."""
    rng = np.random.default_rng(417)
    wing_bus = np.zeros((2, N))
    tune_bus = np.zeros((2, N))
    air_bus = np.zeros((2, N))

    def place(bus, at, wave, pan):
        # Equal-power pan, and anything that rings past the loop end
        # wraps around into the opening bars.
        gains = (np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4))
        at %= N
        first = min(len(wave), N - at)
        for ch, gain in enumerate(gains):
            bus[ch, at:at + first] += gain * wave[:first]
            bus[ch, :len(wave) - first] += gain * wave[first:]

    # The wingbeat: a soft deep whoosh, low-passed noise swelling and
    # falling over half a second. @marker wingbeat
    for i, b in enumerate(beats()):
        loud = 1.0 if b < 64 else 0.8
        length = int(RATE * 0.6)
        tt = np.arange(length) / RATE
        noise = rng.standard_normal(length)
        lp = np.zeros(length)
        a = 0.06
        for k in range(1, length):
            lp[k] = lp[k - 1] + a * (noise[k] - lp[k - 1])
        env = np.sin(np.pi * tt / 0.6) ** 2
        pan = 0.12 * math.sin(2 * math.pi * b / FRAMES)
        place(wing_bus, b * SPF, 0.30 * loud * lp * env, pan)

    # The flute: a soft sine with a breath of second harmonic, slow
    # attack, gentle fall. @marker flute
    def flute(hz, seconds):
        m = int(seconds * RATE)
        tt = np.arange(m) / RATE
        atk = np.minimum(1.0, tt / 0.08)
        rel = np.clip((seconds - tt) / 0.25, 0, 1)
        return (np.sin(2 * np.pi * hz * tt)
                + 0.25 * np.sin(4 * np.pi * hz * tt)) * atk * rel

    for frame, midi, length in MELODY:
        pan = -0.3 + 0.6 * (midi - 62) / (81 - 62)
        place(tune_bus, frame * SPF, 0.16 * flute(midi_hz(midi), length / FPS), pan)

    # Dawn chorus: quick three-syllable chirps, each a small frequency
    # sweep. @marker chorus
    for start in CHIRPS:
        m = int(RATE * 0.22)
        tt = np.arange(m) / RATE
        freqs = np.concatenate([
            np.linspace(3400, 2800, m // 3),
            np.linspace(3600, 3000, m // 3),
            np.linspace(3300, 2900, m - 2 * (m // 3)),
        ])
        ph = 2 * np.pi * np.cumsum(freqs) / RATE
        env = np.minimum(1.0, tt / 0.01) * np.exp(-tt / 0.09)
        place(tune_bus, start * SPF, 0.05 * np.sin(ph) * env,
              -0.4 + 0.8 * (start % 3) / 2)

    # The drone: one low chord per act, crossfading at the boundaries.
    # @marker drone
    span = 128 * SPF
    ht = np.arange(span + RATE) / RATE
    swell = np.minimum(1, ht / 1.2) * np.clip((span / RATE + 1.0 - ht) / 1.2, 0, 1)
    for i, chord in enumerate(CHORDS):
        for side, detune in ((-0.5, 0.9985), (0.5, 1.0015)):
            voice = np.zeros_like(ht)
            for note in chord:
                hz = midi_hz(note) * detune
                voice += np.sin(2 * np.pi * hz * ht) + 0.15 * np.sin(4 * np.pi * hz * ht)
            place(air_bus, i * span - RATE // 2, 0.014 * voice * swell, side)

    # The sea: waves breathing under the third act, slow filtered swells.
    # @marker sea
    sea_len = 128 * SPF
    st = np.arange(sea_len) / RATE
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * st / 4.2)
    noise = rng.standard_normal(sea_len)
    lp = np.zeros(sea_len)
    a = 0.02
    for k in range(1, sea_len):
        lp[k] = lp[k - 1] + a * (noise[k] - lp[k - 1])
    lp /= np.abs(lp).max()
    place(air_bus, 256 * SPF, 0.05 * lp * swell, 0.0)

    # The wind bed: soft filtered noise under the whole loop, circular so
    # it has no seam. @marker wind
    freqs = np.fft.rfftfreq(N, 1 / RATE)
    hiss = (freqs / (freqs + 400)) ** 2 / (1 + (freqs / 5000) ** 2)
    wind = np.array([np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) * hiss, N)
                     for _ in range(2)])
    wind *= 0.012 / wind.std()
    air_bus += wind

    # A small open sky: decaying noise as a room, convolved around the loop.
    rt = np.arange(int(RATE * 1.4)) / RATE

    def room(bus, wet):
        out = np.zeros_like(bus)
        for ch in range(2):
            ir = np.zeros(N)
            ir[:len(rt)] = rng.standard_normal(len(rt)) * np.exp(-rt / 0.35) * (rt > 0.01)
            ir /= np.sqrt((ir ** 2).sum())
            out[ch] = np.fft.irfft(np.fft.rfft(bus[ch]) * np.fft.rfft(ir), N)
        return bus + wet * out

    mix = room(wing_bus + tune_bus, 0.4) + room(air_bus, 0.25)
    mix *= 0.89 / np.abs(mix).max()
    return (mix.T * 32767).round().astype("<i2")


if __name__ == "__main__":
    import sys
    print("beats:", beats())
    print("melody notes:", len(MELODY))
    audio = render()
    print("audio:", audio.shape, audio.dtype, "peak:", np.abs(audio).max())
    if "--write" in sys.argv:
        from pathlib import Path
        Path(__file__).with_name("audio.pcm").write_bytes(audio.tobytes())
        print("wrote audio.pcm")
