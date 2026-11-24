#!/usr/bin/env python3
"""Logon Wink — the score. A music-box chime for a little greeter.

Stdlib only. Renders audio.pcm: headerless signed little-endian 16-bit
stereo PCM at 48,000 samples per second, exactly one visual loop
(180 frames at 15 fps = 12 seconds = 576,000 stereo sample pairs).

The melody is also the beat grid the picture reads: logon-wink.py imports
MELODY for the headphone pulse, so every chime has a glow you can watch.
Each wink gets its own chime phrase; the quick blink gets a high tick; the
prompt's backspace and retype get soft key clicks; a shooting star gets a
rising shimmer. A low pad holds one chord per half-loop, and a short echo
gives the little box a room to ring in. Everything wraps into one seamless
loop — tails that ring past the end come back around to the opening bars.

Usage: python score.py            (writes audio.pcm beside this file)
       python score.py --check    (validates an existing audio.pcm)
"""
import math
import random
import struct
import sys
from pathlib import Path

RATE = 48000
FPS, FRAMES = 15, 180
SPF = RATE // FPS            # 3,200 stereo sample pairs per frame
N = FRAMES * SPF             # 576,000 pairs: one 12-second loop

# @marker melody
# (frame, MIDI note, velocity). C major pentatonic, music-box voice.
# The wink phrases sit on the wink frames (36-54, 126-144); the high tick
# at 86 is the quick blink; the last four notes are the shooting star.
MELODY = [
    (0, 84, 0.9), (6, 81, 0.7), (12, 79, 0.7), (18, 76, 0.6),
    (24, 79, 0.7), (30, 81, 0.8),
    (36, 88, 1.0), (42, 84, 0.8), (48, 86, 0.8), (54, 84, 0.7),
    (60, 79, 0.7), (66, 76, 0.6), (72, 74, 0.6), (78, 72, 0.7),
    (86, 96, 0.25),
    (96, 76, 0.6), (104, 79, 0.7), (112, 81, 0.7), (120, 84, 0.8),
    (126, 88, 1.0), (132, 91, 1.0), (138, 88, 0.8), (144, 86, 0.7),
    (150, 84, 0.7), (154, 86, 0.7), (158, 88, 0.8), (162, 91, 0.9),
]

# @marker clicks
# Soft key clicks: the prompt backspaces (90-102) and retypes (104-128).
KEY_CLICKS = [90, 92, 94, 96, 98, 100, 102,
              104, 108, 112, 116, 120, 124, 128]

# @marker pad
# One low chord per half-loop: C major, then F major. (MIDI notes.)
CHORDS = [((48, 55, 60, 64), 0, 90), ((41, 48, 53, 57), 90, 180)]

_SEED = 2033
_TABLE = [math.sin(2 * math.pi * i / 8192) for i in range(8192)]


def _sine(phase):
    """Sine by table lookup; phase in cycles."""
    x = (phase % 1.0) * 8192.0
    i = int(x)
    frac = x - i
    return _TABLE[i] + (_TABLE[(i + 1) & 8191] - _TABLE[i]) * frac


def _hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12)


def _place(bus, at, wave, pan):
    """Add wave into bus at sample offset at, wrapping around the loop seam."""
    gains = (math.cos((pan + 1) * math.pi / 4),
             math.sin((pan + 1) * math.pi / 4))
    at %= N
    first = min(len(wave), N - at)
    for ch in range(2):
        g = gains[ch]
        b = bus[ch]
        for i in range(first):
            b[at + i] += g * wave[i]
        for i in range(first, len(wave)):
            b[i - first] += g * wave[i]


def _music_box(hz, seconds=1.6):
    """A struck music-box tine: bright partials, quick decay, soft tick."""
    n = int(seconds * RATE)
    wave = [0.0] * n
    # (ratio, amplitude, decay seconds) — the tine's voice.
    for ratio, amp, decay in ((1.0, 1.0, 1.1), (2.0, 0.28, 0.45),
                              (3.01, 0.10, 0.20), (4.2, 0.04, 0.10)):
        ph = 0.0
        step = hz * ratio / RATE
        env = 1.0
        d = 1.0 / (decay * RATE)
        for i in range(n):
            wave[i] += amp * _sine(ph) * env
            ph += step
            env *= (1.0 - d)
    # The tine's tick: the first 3 ms, tiny seeded noise.
    rng = random.Random(_SEED)
    tick = int(0.003 * RATE)
    for i in range(tick):
        wave[i] += (rng.random() * 2 - 1) * 0.05 * (1 - i / tick)
    return wave


def _pad(notes, seconds):
    """A low sustained chord: detuned pairs, slow swell in and out."""
    n = int(seconds * RATE)
    wave = [0.0] * n
    for note in notes:
        for detune in (0.9985, 1.0015):
            hz = _hz(note) * detune
            ph = 0.0
            step = hz / RATE
            for i in range(n):
                t = i / RATE
                swell = min(1.0, t / 0.8) * max(0.0, min(1.0, (seconds - t) / 1.0))
                wave[i] += (_sine(ph) + 0.18 * _sine(2 * ph)) * swell
                ph += step
    return [s * 0.012 for s in wave]


def _click():
    """A soft key click: 5 ms of noise through a one-pole lowpass."""
    rng = random.Random(_SEED)
    n = int(0.005 * RATE)
    out = [0.0] * n
    last = 0.0
    for i in range(n):
        last = 0.35 * last + 0.65 * (rng.random() * 2 - 1)
        out[i] = last * 0.05 * (1 - i / n)
    return out


def render():
    """Return the loop as int16 stereo bytes, left then right."""
    bus = ([0.0] * N, [0.0] * N)
    cache = {}

    def tine(midi):
        if midi not in cache:
            cache[midi] = _music_box(_hz(midi))
        return cache[midi]

    for frame, midi, vel in MELODY:
        pan = -0.3 + 0.6 * (midi - 72) / (91 - 72)
        wave = [s * 0.22 * vel for s in tine(midi)]
        _place(bus, frame * SPF, wave, pan)

    for notes, start, end in CHORDS:
        span = (end - start) * SPF
        wave = _pad(notes, span / RATE + 1.0)
        _place(bus, start * SPF, wave, 0.0)

    click = _click()
    for frame in KEY_CLICKS:
        _place(bus, frame * SPF, click, 0.0)

    # A short echo: two repeats of the mix, wrapped around the loop so
    # the seam stays clean. The box gets a room to ring in.
    delay = int(0.18 * RATE)
    out = ([0.0] * N, [0.0] * N)
    for ch in range(2):
        b = bus[ch]
        o = out[ch]
        for i in range(N):
            o[i] = (b[i] + 0.22 * b[(i - delay) % N]
                    + 0.0484 * b[(i - 2 * delay) % N])

    peak = max(max(abs(s) for s in out[0]), max(abs(s) for s in out[1]))
    gain = 0.89 / peak if peak > 0 else 1.0
    inter = [0] * (2 * N)
    for i in range(N):
        inter[2 * i] = int(out[0][i] * gain * 32767)
        inter[2 * i + 1] = int(out[1][i] * gain * 32767)
    return struct.pack(f"<{2 * N}h", *inter)


def main():
    here = Path(__file__).parent
    if "--check" in sys.argv:
        p = here / "audio.pcm"
        want = 4 * N
        got = p.stat().st_size if p.exists() else -1
        print(f"audio.pcm: {got} bytes, want {want} bytes "
              f"({N} pairs, {FRAMES} frames at {FPS} fps)")
        print("OK" if got == want else "MISMATCH")
        return
    data = render()
    (here / "audio.pcm").write_bytes(data)
    print(f"audio.pcm: {len(data)} bytes ({N} pairs, {FRAMES} frames at {FPS} fps)")


if __name__ == "__main__":
    main()
