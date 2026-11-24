"""The Long Way Round — the voices. Every instrument and sound is synthesized here.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

No samples: pads, celesta, flute, glass, plucks, bass and drums are built from
sine partials and shaped noise. The world adds wind, a stream, crickets, a
church bell, waves, a whale, the deep and a vent. Everything lands on one
circular timeline, so tails that ring past the end wrap into the beginning.
"""
import numpy as np

from journey import (BELLS, BREACH, FPS, FRAMES, LANDING, N, RATE, SEA, VENT, WHALE,
                     WHALE_AGAIN, drop)
from score import SCORE, SPB, bar_time, chord, hz, melody, midi, scene, third_below

rng = np.random.default_rng(2560)
TAU = 2 * np.pi


def secs(length):
    return np.arange(int(length * RATE)) / RATE


class Bus:
    """A stereo loop. place() pans, and wraps anything that runs past the end."""

    def __init__(self):
        self.dry = np.zeros((2, N))
        self.send = np.zeros((2, N))

    def place(self, at, wave, pan=0.0, gain=1.0, wet=0.25):
        wave = np.atleast_2d(wave) * gain
        if wave.shape[0] == 1:
            angle = (np.clip(pan, -1, 1) + 1) * np.pi / 4
            wave = np.vstack([wave[0] * np.cos(angle), wave[0] * np.sin(angle)])
        start = int(round(at * RATE)) % N
        for dst, share in ((self.dry, 1.0), (self.send, wet)):
            if share:
                first = min(wave.shape[1], N - start)
                dst[:, start:start + first] += share * wave[:, :first]
                rest = wave.shape[1] - first
                while rest > 0:
                    chunk = min(rest, N)
                    dst[:, :chunk] += share * wave[:, wave.shape[1] - rest:wave.shape[1] - rest + chunk]
                    rest -= chunk


def shaped(length, low, high, seed=None):
    """Noise between two corner frequencies, normalized; circular, so seamless."""
    noise = (np.random.default_rng(seed) if seed is not None else rng).standard_normal(length)
    f = np.fft.rfftfreq(length, 1 / RATE)
    gain = (f / low) ** 2 / (1 + (f / low) ** 2) / (1 + (f / high) ** 2)
    out = np.fft.irfft(np.fft.rfft(noise) * gain, length)
    return out / (out.std() + 1e-12)


def envelope(t, attack, length, release):
    return np.clip(t / attack, 0, 1) * np.clip((length + release - t) / release, 0, 1)


# The pad: detuned partials, wide in stereo, one chord per bar.
def pad(notes, length, bright):
    t = secs(length + 1.4)
    env = envelope(t, 0.45, length, 1.4)
    out = np.zeros((2, len(t)))
    for note in notes:
        for side, cents in ((0, -7), (1, 7)):
            f = hz(note) * 2 ** (cents / 1200)
            for k in range(1, 7):
                if f * k < 9000:
                    out[side] += bright ** (k - 1) / k * np.sin(TAU * f * k * t + k * side)
    return out * env * 0.035


def celesta(note, loud=1.0):
    t = secs(1.8)
    f = hz(note)
    tone = sum(a * np.sin(TAU * f * r * t) * np.exp(-t / d)
               for r, a, d in ((1, 1, 1.3), (3.0, 0.22, 0.35), (4.07, 0.14, 0.22), (6.2, 0.05, 0.08)))
    return 0.16 * loud * tone * np.clip(t / 0.002, 0, 1)


def flute(note, beats, loud=1.0):
    length = beats * SPB * 0.96
    t = secs(length + 0.3)
    f = hz(note) * (1 + 0.004 * np.sin(TAU * 5.2 * t) * np.clip((t - 0.25) / 0.3, 0, 1))
    phase = TAU * np.cumsum(f) / RATE
    tone = np.sin(phase) + 0.22 * np.sin(2 * phase) + 0.08 * np.sin(3 * phase)
    breath = shaped(len(t), 1500, 5000) * 0.05
    return 0.13 * loud * (tone + breath) * envelope(t, 0.06, length, 0.25)


def glass(note, loud=1.0):
    t = secs(4.0)
    f = hz(note)
    tone = sum(a * np.sin(TAU * f * r * t) * np.exp(-t / d)
               for r, a, d in ((1, 1, 2.6), (1.003, 0.6, 2.2), (2.76, 0.18, 0.7), (5.4, 0.05, 0.2)))
    return 0.14 * loud * tone * np.clip(t / 0.004, 0, 1)


def pluck(note, loud=1.0, ring=0.9):
    t = secs(1.6)
    f = hz(note)
    tone = sum(np.sin(TAU * f * k * t) * np.exp(-t * (1 + 0.6 * k) / ring) / k ** 1.2
               for k in range(1, 9) if f * k < 12000)
    return 0.11 * loud * tone * np.clip(t / 0.002, 0, 1)


def bass(note, beats, loud=1.0, short=False):
    length = beats * SPB * (0.5 if short else 0.95)
    t = secs(length + 0.2)
    f = hz(note)
    tone = np.sin(TAU * f * t) + 0.3 * np.sin(TAU * 2 * f * t) + 0.12 * np.sin(TAU * 3 * f * t)
    return 0.2 * loud * tone * envelope(t, 0.01, length, 0.2)


def kick(loud=1.0):
    t = secs(0.4)
    phase = TAU * np.cumsum(50 + 70 * np.exp(-t / 0.04)) / RATE
    return 0.5 * loud * np.sin(phase) * np.exp(-t / 0.16)


def brush(loud=1.0):
    t = secs(0.3)
    return 0.1 * loud * shaped(len(t), 1800, 7000) * np.exp(-t / 0.09)


def shaker(loud=1.0):
    t = secs(0.08)
    return 0.05 * loud * shaped(len(t), 5000, 12000) * np.exp(-t / 0.02)


def tom(loud=1.0):
    t = secs(0.7)
    phase = TAU * np.cumsum(70 + 30 * np.exp(-t / 0.1)) / RATE
    return 0.35 * loud * np.sin(phase) * np.exp(-t / 0.3)


def church_bell():
    t = secs(7.0)
    f = hz(midi("D3"))
    partials = ((0.5, .5, 6), (1, .8, 4.5), (1.19, .6, 3.5), (1.5, .3, 2.5), (2, .7, 2.5),
                (2.52, .3, 1.5), (3.01, .2, 1.2))
    tone = sum(a * np.sin(TAU * f * r * t) * np.exp(-t / d) for r, a, d in partials)
    strike = shaped(len(t), 800, 4000) * np.exp(-t / 0.01) * 0.4
    return 0.16 * (tone + strike)


def whale_song(low=1.0):
    t = secs(3.6)
    glide = 140 + 70 * np.sin(np.pi * t / 3.6) ** 2 - 20 * t / 3.6
    phase = TAU * np.cumsum(glide * low) / RATE
    formant = 0.5 + 0.5 * np.sin(np.pi * t / 1.8)
    tone = sum((formant if k > 2 else 1) * np.sin(k * phase) / k for k in range(1, 7))
    return 0.22 * tone * np.sin(np.pi * t / 3.6) ** 2


def bloop(freq, decay, loud):
    t = secs(decay * 6)
    phase = TAU * np.cumsum(freq * (1 + 0.6 * (1 - np.exp(-t / decay)))) / RATE
    return loud * np.sin(phase) * np.exp(-t / decay)


def splash(bright=1.0):
    t = secs(0.8)
    hiss = shaped(len(t), 400 * bright, 3500 * bright)
    hiss /= np.abs(hiss).max()                    # peak-normalized: a splash, never a crackle
    return 0.22 * (hiss * np.exp(-t / 0.12) + 0.6 * np.sin(TAU * 90 * t) * np.exp(-t / 0.08))


def curve(points):
    """A gain that follows (frame, gain) points around the loop, sample by sample."""
    frames = [p[0] for p in points] + [points[0][0] + FRAMES]
    gains = [p[1] for p in points] + [points[0][1]]
    return np.interp(np.arange(N) * FPS / RATE, frames, gains)


def render():
    """Return the 64-second loop as int16 stereo, left then right."""
    music, world = Bus(), Bus()

    # The harmony: a pad on every bar, bass from the end of the fall onward.
    for bar, (_, root, _) in enumerate(SCORE):
        where = scene(bar)
        t0 = bar_time(bar)
        bright = {"cloud": .5, "fall": .55, "snowmelt": .4, "river": .45, "sea": .6,
                  "deep": .25, "return": .5}[where]
        loud = {"cloud": 1.0, "fall": 1.1, "snowmelt": .6, "river": .7, "sea": 1.2,
                "deep": .9, "return": .9}[where]
        music.place(t0, pad(chord(bar), 4 * SPB, bright), gain=loud, wet=0.5)
        low = midi(root)
        if where == "snowmelt":
            for beat in (0, 2):
                music.place(bar_time(bar, beat), bass(low, 2), wet=0.1)
        elif where == "river":
            for beat, step in enumerate((0, 7, 12, 7)):
                music.place(bar_time(bar, beat), bass(low + step, 1, short=True), wet=0.1)
        elif where == "return":
            for eighth in range(8):
                music.place(bar_time(bar, eighth / 2), bass(low + 12 * (eighth % 2), .5, .8, True),
                            wet=0.1)
        elif bar >= 6:
            music.place(t0, bass(low, 4, 0.8 if where != "deep" else 1.1), wet=0.2)

        # Plucks: falling sixteenths in the fall, a running figure by the
        # stream and river, rising sixteenths on the way home.
        tones = sorted(n + 12 for n in chord(bar))
        if where == "fall":
            for s in range(16):
                note = tones[::-1][s % len(tones)] + 12 * (1 - s // 8)
                music.place(bar_time(bar, s / 4), pluck(note, 0.5 + 0.03 * s), pan=0.5 - s / 16)
        elif where in ("snowmelt", "river"):
            figure = [tones[0], tones[2], tones[1], tones[2]]
            for e in range(8):
                music.place(bar_time(bar, e / 2), pluck(figure[e % 4], 0.6 if e % 2 else 0.8),
                            pan=-0.4 if e % 2 else 0.3)
        elif where == "return" and bar > 24:
            for s in range(16):
                music.place(bar_time(bar, s / 4), pluck(tones[s % len(tones)] + 12 * (s // 8), 0.45),
                            pan=-0.6 + s / 13)

        # Drums: a light groove by the water, a pulse on the way home.
        if where in ("snowmelt", "river"):
            for beat in (0, 2):
                music.place(bar_time(bar, beat), kick(0.8), wet=0.05)
            for e in range(8):
                music.place(bar_time(bar, e / 2), shaker(1.0 if e % 2 else 0.6), pan=0.35, wet=0.1)
            if where == "river":
                for beat in (1, 3):
                    music.place(bar_time(bar, beat), brush(), pan=-0.2, wet=0.2)
        if where == "sea" and bar == 19:
            for s in range(8):
                music.place(bar_time(bar, 2 + s / 4), tom(0.3 + s * 0.08), pan=-0.5 + s / 8, wet=0.4)
        if where == "return" and bar > 24:
            for beat in range(4 if bar < 27 else 3):
                music.place(bar_time(bar, beat), kick(0.9), wet=0.05)
            for s in range(16 if bar < 27 else 12):
                music.place(bar_time(bar, s / 4), shaker(0.5 + 0.5 * (s % 2)), pan=0.4, wet=0.1)

    # The theme, in whichever voice the chapter gives it.
    for start, note, beats, bar in melody():
        where = scene(bar)
        if where in ("cloud", "fall"):
            music.place(start, celesta(note + 12 if where == "fall" else note), pan=0.15, wet=0.45)
        elif where == "deep":
            music.place(start, glass(note), pan=-0.1, wet=0.7)
        else:
            music.place(start, flute(note, beats, 1.0 if where != "sea" else 1.15), pan=-0.05, wet=0.35)
            if where == "river" and third_below(note):
                music.place(start, flute(third_below(note), beats, 0.55), pan=0.35, wet=0.35)
            if where == "return":
                music.place(start, celesta(note + 12, 0.7), pan=0.3, wet=0.45)

    # Sparkles: vapour glinting as it gathers, and again as it rises home.
    sparkle = [midi(n) for n in "D6 E6 F#6 A6 B6 D7".split()]
    for bar, chance in ((0, .55), (1, .4), (2, .25), (3, .12), (26, .25), (27, .5)):
        for s in range(16):
            if rng.uniform() < chance:
                music.place(bar_time(bar, s / 4), celesta(rng.choice(sparkle), 0.35),
                            pan=rng.uniform(-0.8, 0.8), wet=0.6)

    # The landing: a soft thump into snow on the downbeat of the stream.
    world.place(LANDING / FPS, splash(0.6), wet=0.3)
    # The church bell tolls twice as the drop passes the tower.
    for frame in BELLS:
        world.place(frame / FPS, church_bell(), pan=-0.3, wet=0.9)
    # The whale calls as it passes, and answers itself from far away.
    world.place(WHALE / FPS, whale_song(), pan=0.2, wet=0.9)
    world.place(WHALE_AGAIN / FPS, whale_song(0.8) * 0.45, pan=-0.6, wet=1.0)
    # The vent wakes with a low roar, and the drop breaks the surface.
    t = secs(4.0)
    world.place(VENT / FPS, shaped(len(t), 30, 180) * np.sin(np.pi * t / 4.0) * 0.25, wet=0.4)
    world.place(BREACH / FPS, splash(1.6), wet=0.5)
    # Riser: wind sweeps upward over the last two bars, then the cloud shimmers.
    t = secs(8 * SPB)
    sweep = shaped(len(t), 300, 6000) * (t / t[-1]) ** 2 * 0.09
    world.place(bar_time(26), np.vstack([sweep, np.roll(sweep, 300)]), wet=0.4)
    t = secs(5.0)
    shimmer = sum(np.sin(TAU * hz(midi(n)) * t + i) for i, n in enumerate("D6 F#6 A6 E7".split()))
    world.place(bar_time(27, 3), 0.035 * shimmer * np.sin(np.pi * t / 5.0) ** 2, wet=0.8)

    # Ambience: each place on the road has its own sound, crossfading by chapter.
    layers = []
    # Cloud air: a high, soft hiss.
    layers.append((shaped(N, 2500, 9000), [(0, .02), (100, .02), (140, 0), (860, 0), (885, .02)]))
    # Wind for the fall and the climb home.
    gust = 0.6 + 0.4 * np.sin(TAU * 6 * np.arange(N) / N)
    layers.append((shaped(N, 300, 1800) * gust,
                   [(0, 0), (120, 0), (150, .06), (215, .07), (232, 0), (820, 0), (870, .07), (895, 0)]))
    # Stream babble and river flow.
    layers.append((shaped(N, 500, 3000), [(0, 0), (220, 0), (236, .03), (380, .03), (400, .02),
                                            (530, .02), (556, 0)]))
    # Waves on the open sea.
    swell = 0.3 + 0.7 * np.sin(np.pi * 9 * np.arange(N) / N) ** 2
    layers.append((shaped(N, 120, 2500) * swell, [(0, 0), (530, 0), (556, .07), (612, .07),
                                                   (632, .02), (BREACH - 4, .02), (BREACH + 6, .05),
                                                   (BREACH + 30, 0)]))
    # The deep: a low pressure hum.
    layers.append((shaped(N, 30, 220), [(0, 0), (612, 0), (640, .08), (760, .08), (790, .1),
                                         (BREACH, 0)]))
    ambience = np.zeros((2, N))
    for noise, points in layers:
        gain = curve(points)
        ambience[0] += noise * gain
        ambience[1] += np.roll(noise, 2400) * gain
    # Stream bloops, river bloops, crickets in the village, bubbles in the deep.
    for first, last, rate, low, high, decay, loud in ((224, 384, 40, 500, 1500, .025, .05),
                                                      (384, 544, 16, 300, 800, .04, .04),
                                                      (640, BREACH, 7, 600, 1600, .03, .05)):
        for _ in range(int((last - first) / FPS * rate)):
            at = rng.uniform(first, last) / FPS
            world.place(at, bloop(rng.uniform(low, high), decay, loud), pan=rng.uniform(-.7, .7), wet=0.2)
    for side, pitch in ((-0.7, 4600), (0.6, 5100)):
        at = 384 / FPS + rng.uniform(0, 0.5)
        while at < 540 / FPS:
            t = secs(0.075)
            chirp = np.sin(TAU * pitch * t) * (np.sin(TAU * 40 * t) > 0) * 0.018
            for k in range(3):
                world.place(at + k * 0.09, chirp, pan=side, wet=0.3)
            at += rng.uniform(0.6, 1.1)

    # Underwater, the music is muffled: a low-passed copy fades in while the drop is submerged.
    under = np.array([max(0.0, min(1.0, (drop(f)[1] - SEA) / 12)) for f in range(FRAMES)])
    muffle = np.interp(np.arange(N) * FPS / RATE, np.arange(FRAMES + 1), np.append(under, under[0]))
    f = np.fft.rfftfreq(N, 1 / RATE)
    low_pass = 1 / (1 + (f / 650) ** 4)
    for bus in (music.dry, music.send):
        muted = np.fft.irfft(np.fft.rfft(bus, axis=1) * low_pass, N, axis=1)
        bus *= 1 - 0.55 * muffle
        bus += 0.55 * muffle * muted

    # One stone-and-water hall for everything, convolved around the loop.
    rt = secs(2.4)
    wet = np.zeros((2, N))
    for ch in range(2):
        ir = np.zeros(N)
        ir[:len(rt)] = rng.standard_normal(len(rt)) * np.exp(-rt / 0.7) * (rt > 0.018)
        ir /= np.sqrt((ir ** 2).sum())
        wet[ch] = np.fft.irfft(np.fft.rfft(music.send[ch] + world.send[ch]) * np.fft.rfft(ir), N)

    mix = music.dry + world.dry + 0.6 * wet + ambience
    mix /= np.percentile(np.abs(mix), 99.99) / 0.8
    mix = np.tanh(1.15 * mix)                     # a soft limiter that can never pass full scale
    return (mix.T * 0.98 * 32767).round().astype("<i2")
