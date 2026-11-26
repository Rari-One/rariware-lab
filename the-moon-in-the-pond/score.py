"""The sound of The Moon in the Pond: one 24-second stereo loop, standard library only.

Three layers are mixed into a single loop the exact length of the animation:

1. Drop plinks. Every drop in pond.DROPS makes a short rising tone, the way a real raindrop does
   when it traps a tiny air bubble (Minnaert resonance: a small bubble rings like a bell and its
   pitch climbs as it shrinks). Here the pitch is pulled onto a D major pentatonic scale so the
   rain plays a tune, and it is panned to where the drop lands.
2. A soft pad. Four chords, D, B minor, G and A, two bars each, built from additive sine partials.
3. A rain hiss. Filtered white noise whose level follows how hard it is raining.

Every sound that runs past the end of the loop is wrapped around to the start (modular time), so
the seam is silent to the ear.
"""
import math
import random

from pond import BEAT, DROPS, LOOP_SECONDS, W

RATE = 48000
LENGTH = round(LOOP_SECONDS * RATE)    # 1,152,000 stereo sample pairs
SEED = 1907


def note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def add(left, right, start, samples, pan):
    """Mix a mono list into the stereo loop at a start sample, wrapping past the end.

    pan runs from 0 (left) to 1 (right) with an equal-power law, so loudness stays even.
    """
    gl, gr = math.cos(pan * math.pi / 2), math.sin(pan * math.pi / 2)
    for k, s in enumerate(samples):
        i = (start + k) % LENGTH
        left[i] += s * gl
        right[i] += s * gr


# ── 1. Drop plinks ────────────────────────────────────────────────────────────────────────────
PENTATONIC = [74, 76, 78, 81, 83, 86, 88, 90, 93]   # D5 E5 F#5 A5 B5 D6 E6 F#6 A6


def plink(freq, size):
    """A bubble-like chirp: a sine that glides up about a semitone while it rings away."""
    out, phase = [], 0.0
    for k in range(int(0.45 * RATE)):
        t = k / RATE
        f = freq * (0.94 + 0.06 * (1 - math.exp(-t / 0.025)))
        phase += 2 * math.pi * f / RATE
        envelope = min(1.0, t / 0.002) * math.exp(-t / (0.07 + 0.06 * size))
        out.append(0.16 * size * envelope * (math.sin(phase) + 0.18 * math.sin(2 * phase)))
    return out


def drops(left, right):
    rng = random.Random(SEED)
    for t, x, y, size in DROPS:
        # Bigger drops sing lower; the rest choose a scale tone near their size.
        top = len(PENTATONIC) - 1
        index = max(0, min(top, round((1 - size) * top * 1.6 + rng.randint(-2, 2))))
        add(left, right, round(t * RATE), plink(note(PENTATONIC[index]), size), x / W)


# ── 2. The pad ────────────────────────────────────────────────────────────────────────────────
CHORDS = [[50, 57, 66, 69], [47, 54, 62, 66], [43, 50, 59, 62], [45, 52, 61, 64]]  # D Bm G A


def pad(left, right):
    span = 8 * BEAT                    # two bars per chord
    fade = 2.0                          # seconds of crossfade into the next chord
    for c, chord in enumerate(CHORDS):
        start = c * span
        n = int((span + fade) * RATE)
        for v, midi in enumerate(chord):
            f = note(midi)
            tone = []
            for k in range(n):
                t = k / RATE
                # A raised-cosine swell in and out keeps every chord change smooth.
                env = min(1.0, t / fade, (span + fade - t) / fade)
                env = 0.5 - 0.5 * math.cos(math.pi * max(0.0, env))
                w = 2 * math.pi * f * t
                tone.append(0.035 * env * (math.sin(w) + 0.3 * math.sin(2 * w) + 0.1 * math.sin(3 * w)))
            add(left, right, round((start - fade / 2) * RATE), tone, 0.3 + 0.4 * v / 3)


# ── 3. Rain hiss ──────────────────────────────────────────────────────────────────────────────
def rain_level(t):
    """How hard it is raining at time t: count drops in a soft window, measured around the loop."""
    total = 0.0
    for dt, _, _, size in DROPS:
        d = (t - dt + LOOP_SECONDS / 2) % LOOP_SECONDS - LOOP_SECONDS / 2
        total += size * math.exp(-(d / 1.2) ** 2)
    return min(1.0, total / 5)


def hiss(left, right):
    rng = random.Random(SEED + 1)
    levels = [rain_level(i * 0.05) for i in range(int(LOOP_SECONDS / 0.05) + 1)]
    for channel in (left, right):
        noise = [rng.uniform(-1, 1) for _ in range(LENGTH)]
        # A band-pass from two one-pole filters. Running them over the loop twice and keeping the
        # second pass makes the filter state at the end match the start, so the loop is seamless.
        low = high = 0.0
        for lap in range(2):
            for i in range(LENGTH):
                low += 0.35 * (noise[i] - low)
                high += 0.02 * (low - high)
                if lap:
                    level = levels[int(i / RATE / 0.05)]
                    channel[i] += 0.05 * (0.15 + level) * (low - high)


def render():
    """Return the loop as headerless signed 16-bit little-endian stereo PCM."""
    left, right = [0.0] * LENGTH, [0.0] * LENGTH
    pad(left, right)
    hiss(left, right)
    drops(left, right)
    pcm = bytearray()
    gain = 2.2  # master level, chosen so the loudest moment peaks near two-thirds of full scale
    for l, r in zip(left, right):
        l, r = l * gain, r * gain
        # A gentle tanh limiter keeps chance pile-ups of drops from clipping.
        pcm += int(32767 * math.tanh(l)).to_bytes(2, "little", signed=True)
        pcm += int(32767 * math.tanh(r)).to_bytes(2, "little", signed=True)
    return bytes(pcm)
