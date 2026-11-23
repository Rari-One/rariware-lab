"""Seven Jars — the score. Rain drips from a broken gutter into seven glass jars.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

Every note in this piece is a raindrop. The melody below is also the drip
schedule that garden.py animates, so each sound has a drop you can watch fall,
strike the water and light its jar. Everything wraps into one seamless loop.
"""
import numpy as np

FPS, FRAMES, RATE = 24, 512, 48000
SPF = RATE // FPS              # 2,000 stereo sample pairs per frame
N = FRAMES * SPF               # 1,024,000 pairs: one 21⅓-second loop
BEAT = 16                      # frames per beat at 90 BPM
EIGHTH = BEAT // 2
BAR_FRAMES = 4 * BEAT

# More water leaves a shorter column of air, so a fuller jar sings higher.
# Left to right the jars climb D major pentatonic.
JARS = [("D4", 62), ("E4", 64), ("F#4", 66), ("A4", 69),
        ("B4", 71), ("D5", 74), ("E5", 76)]

# The score: one bar per line, eight eighth notes per bar.
# A digit names the jar a drop lands in; a dot is a dry moment.
MELODY = [
    "0 . 2 . 3 . . 5",   # D
    ". 6 . 5 3 . 2 .",   # D
    "4 . . 5 . 4 2 .",   # Bm
    ". 3 . 2 1 . 0 .",   # Bm
    "0 . 4 . 5 . 6 5",   # G
    ". 4 . 3 . 4 5 .",   # G
    "1 . 3 . 6 . 5 .",   # A
    "3 . 2 . 1 . . .",   # A, falling back to the first drop
]
# The low hum under the eaves holds one chord for every two bars.
CHORDS = [(50, 54, 57), (47, 50, 54), (43, 47, 50), (45, 49, 52)]

# Lightning flashes late in bar six. Its thunder arrives 26 frames later,
# a storm about 370 metres away, and rolls across the loop seam.
LIGHTNING = 360
THUNDER = LIGHTNING + 26


def midi_hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def drops():
    """Every note as (impact frame, jar, loudness), in loop order."""
    out = []
    for bar, line in enumerate(MELODY):
        for slot, mark in enumerate(line.split()):
            if mark != ".":
                loud = 1.0 if slot == 0 else (0.84 if slot % 2 == 0 else 0.68)
                out.append((bar * BAR_FRAMES + slot * EIGHTH, int(mark), loud))
    return out


def render():
    """Return the loop as int16 stereo, left then right, one pass of the picture."""
    rng = np.random.default_rng(1907)
    t = np.arange(int(RATE * 3.2)) / RATE
    glass_bus = np.zeros((2, N))
    hum_bus = np.zeros((2, N))
    storm_bus = np.zeros((2, N))

    def place(bus, at, wave, pan):
        # Equal-power pan, and anything that rings past the loop end
        # wraps around into the opening bars.
        gains = (np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4))
        at %= N
        first = min(len(wave), N - at)
        for ch, gain in enumerate(gains):
            bus[ch, at:at + first] += gain * wave[:first]
            bus[ch, :len(wave) - first] += gain * wave[first:]

    # The glass voice: a struck jar rings with a few slightly inharmonic
    # partials, and the drop itself makes a quick rising bubble "plip".
    def glass(hz, loud):
        tone = np.zeros_like(t)
        for ratio, amp, decay in ((1.0, 1.0, 1.9), (2.004, 0.30, 0.85),
                                  (2.76, 0.15, 0.42), (5.40, 0.05, 0.15)):
            tone += amp * np.sin(2 * np.pi * hz * ratio * t) * np.exp(-t / decay)
        tone *= np.minimum(1.0, t / 0.002)
        bubble_hz = 2.3 * hz * (1 + 0.35 * (1 - np.exp(-t / 0.03)))
        plip = np.sin(2 * np.pi * np.cumsum(bubble_hz) / RATE) * np.exp(-t / 0.045) * 0.32
        tick = rng.standard_normal(len(t)) * np.exp(-t / 0.0015) * 0.12
        return 0.2 * loud * (tone + plip + tick)

    for frame, jar, loud in drops():
        pan = -0.65 + 1.3 * jar / (len(JARS) - 1)
        place(glass_bus, frame * SPF, glass(midi_hz(JARS[jar][1]), loud), pan)

    # The hum: soft sustained chords, each fading in and out across two bars.
    span = 2 * BAR_FRAMES * SPF
    ht = np.arange(span + RATE) / RATE
    swell = np.minimum(1, ht / 0.8) * np.clip((span / RATE + 1.0 - ht) / 1.0, 0, 1)
    for i, chord in enumerate(CHORDS):
        for side, detune in ((-0.6, 0.9985), (0.6, 1.0015)):
            voice = np.zeros_like(ht)
            for note in chord + (chord[0] - 12,):
                hz = midi_hz(note) * detune
                voice += np.sin(2 * np.pi * hz * ht) + 0.18 * np.sin(4 * np.pi * hz * ht)
            place(hum_bus, i * span - RATE // 2, 0.012 * voice * swell, side)

    # The rain bed: noise shaped in the frequency domain. Filtering the whole
    # loop at once is circular, so the hiss has no seam.
    freqs = np.fft.rfftfreq(N, 1 / RATE)
    hiss = (freqs / (freqs + 600)) ** 2 / (1 + (freqs / 7000) ** 2)
    rain = np.array([np.fft.irfft(np.fft.rfft(rng.standard_normal(N)) * hiss, N) for _ in range(2)])
    rain *= 0.022 / rain.std()
    # Thousands of tiny droplets ticking on leaves and stone.
    patter = np.zeros((2, N))
    for ch in range(2):
        spots = rng.integers(0, N, 5200)
        np.add.at(patter[ch], spots, rng.uniform(0.15, 1.0, len(spots)) ** 2 * rng.choice([-1, 1], len(spots)))
    kt = np.arange(240) / RATE
    kernel = np.zeros(N)
    kernel[:240] = rng.standard_normal(240) * np.exp(-kt / 0.0012)
    patter = np.fft.irfft(np.fft.rfft(patter) * np.fft.rfft(kernel), N)
    rain += patter * 0.07 / np.abs(patter).max()   # soft, never a click

    # Thunder: a short crack, then brown-noise rumble in slow swells.
    length = int(RATE * 6.5)
    tt = np.arange(length) / RATE
    tf = np.fft.rfftfreq(length, 1 / RATE)
    swells = sum(a * np.exp(-((tt - c) / w) ** 2) for a, c, w in
                 ((1.0, 0.35, 0.3), (0.8, 1.2, 0.5), (0.55, 2.3, 0.7), (0.3, 3.6, 0.9)))
    for side in (-0.5, 0.5):
        rumble = np.fft.irfft(np.fft.rfft(rng.standard_normal(length)) / (1 + (tf / 90) ** 2) /
                              np.maximum(tf, 20) * 40, length)
        crack = np.fft.irfft(np.fft.rfft(rng.standard_normal(length)) / (1 + (tf / 2500) ** 2), length)
        wave = rumble / np.abs(rumble).max() * swells * np.exp(-tt / 2.8) * 0.5
        wave += crack / np.abs(crack).max() * np.exp(-tt / 0.06) * 0.18
        place(storm_bus, THUNDER * SPF, wave * np.minimum(1, tt / 0.01), side)

    # A small stone courtyard: decaying noise as a room, convolved around the loop.
    rt = np.arange(int(RATE * 1.8)) / RATE
    def room(bus, wet):
        out = np.zeros_like(bus)
        for ch in range(2):
            ir = np.zeros(N)
            ir[:len(rt)] = rng.standard_normal(len(rt)) * np.exp(-rt / 0.42) * (rt > 0.012)
            ir /= np.sqrt((ir ** 2).sum())
            out[ch] = np.fft.irfft(np.fft.rfft(bus[ch]) * np.fft.rfft(ir), N)
        return bus + wet * out

    # Wrap ringing tails: the buses already hold them, so the mix is one loop.
    mix = room(glass_bus + hum_bus, 0.45) + room(storm_bus, 0.3) + rain
    mix *= 0.89 / np.abs(mix).max()
    return (mix.T * 32767).round().astype("<i2")
