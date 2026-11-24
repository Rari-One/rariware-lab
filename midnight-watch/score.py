"""The Midnight Watch — 30-bar musical score, themes, and synchronized clockwork cues."""
import math

RATE = 48000
BAR_SEC = 2.0
BARS = 30                           # 30 bars x 2.0 s = 60.0 s exact (120 BPM, 4/4)
BAR_SAMPLES = int(RATE * BAR_SEC)   # 96,000 stereo sample pairs per bar
TOTAL = BARS * BAR_SAMPLES          # 2,880,000 stereo sample pairs = 11,520,000 bytes (91.6% of 12 MiB)
BEAT_SAMPLES = BAR_SAMPLES // 4     # 24,000 samples per quarter-note beat

# Harmony in E minor / G major across six five-bar chapters.
# Each entry: (bass_midi, chord_midis, melody_pattern_of_(beat_offset, midi, dur_beats))
# The recurring watchmaker motif (E5-G5-B5-A5-G5-F#5) transforms across every chamber.
BAR_SPEC = [
    # Chapter I — The Dial (bars 0-4): intimate music box over steady escapement ticks.
    (40, (52, 59, 64, 67), ((0.0, 76, 1.0), (1.0, 79, 1.0), (2.0, 83, 1.5), (3.5, 81, 0.5))),
    (38, (50, 57, 62, 66), ((0.0, 79, 1.5), (1.5, 78, 0.5), (2.0, 74, 2.0))),
    (36, (48, 55, 60, 64), ((0.0, 72, 1.0), (1.0, 76, 1.0), (2.0, 79, 1.5), (3.5, 76, 0.5))),
    (35, (47, 54, 59, 63), ((0.0, 78, 1.5), (2.0, 75, 1.0), (3.0, 71, 1.0))),
    (40, (52, 59, 64, 71), ((0.0, 76, 1.0), (1.5, 79, 1.0), (2.5, 83, 1.5))),

    # Chapter II — The Escapement (bars 5-9): bright harpsichord gearwork and ruby clicks.
    (40, (52, 59, 64, 67), ((0.0, 76, 0.5), (0.5, 79, 0.5), (1.0, 83, 0.5), (1.5, 79, 0.5), (2.0, 81, 1.0), (3.0, 78, 1.0))),
    (43, (55, 59, 62, 67), ((0.0, 79, 0.5), (0.5, 83, 0.5), (1.0, 86, 0.5), (1.5, 83, 0.5), (2.0, 81, 1.0), (3.0, 79, 1.0))),
    (36, (48, 55, 60, 67), ((0.0, 76, 0.5), (0.5, 79, 0.5), (1.0, 84, 0.5), (1.5, 79, 0.5), (2.0, 83, 1.0), (3.0, 79, 1.0))),
    (33, (45, 52, 57, 64), ((0.0, 76, 0.5), (0.5, 81, 0.5), (1.0, 84, 0.5), (1.5, 81, 0.5), (2.0, 79, 1.0), (3.0, 76, 1.0))),
    (35, (47, 54, 59, 66), ((0.0, 78, 1.0), (1.0, 81, 0.5), (1.5, 83, 0.5), (2.0, 87, 1.5), (3.5, 83, 0.5))),

    # Chapter III — The Pendulum Hall (bars 10-14): deep bowed cello and cathedral organ swell.
    (40, (52, 59, 64, 67), ((0.0, 76, 2.0), (2.0, 79, 1.0), (3.0, 78, 1.0))),
    (36, (48, 55, 60, 64), ((0.0, 72, 2.0), (2.0, 76, 1.0), (3.0, 79, 1.0))),
    (33, (45, 52, 57, 60), ((0.0, 81, 1.5), (1.5, 79, 0.5), (2.0, 76, 2.0))),
    (38, (50, 57, 62, 66), ((0.0, 74, 1.5), (1.5, 78, 0.5), (2.0, 81, 2.0))),
    (35, (47, 54, 59, 63), ((0.0, 83, 2.0), (2.0, 78, 2.0))),

    # Chapter IV — The Orrery (bars 15-19): soaring G-major / E-minor celestial reed & celesta.
    (43, (55, 62, 67, 71), ((0.0, 83, 1.0), (1.0, 86, 1.0), (2.0, 91, 1.5), (3.5, 88, 0.5))),
    (38, (50, 57, 62, 66), ((0.0, 86, 1.5), (1.5, 83, 0.5), (2.0, 81, 2.0))),
    (40, (52, 59, 64, 67), ((0.0, 79, 1.0), (1.0, 83, 1.0), (2.0, 88, 1.5), (3.5, 86, 0.5))),
    (36, (48, 55, 60, 67), ((0.0, 84, 1.5), (1.5, 83, 0.5), (2.0, 79, 2.0))),
    (38, (50, 57, 62, 69), ((0.0, 81, 1.0), (1.0, 83, 1.0), (2.0, 86, 2.0))),

    # Chapter V — The Bell Tower (bars 20-24): bronze midnight chimes tolling over full strings.
    (40, (52, 59, 64, 67), ((0.0, 76, 1.5), (2.0, 83, 1.5), (3.5, 81, 0.5))),
    (36, (48, 55, 60, 64), ((0.0, 79, 1.5), (2.0, 84, 1.5), (3.5, 83, 0.5))),
    (38, (50, 57, 62, 66), ((0.0, 81, 1.5), (2.0, 86, 1.5), (3.5, 83, 0.5))),
    (35, (47, 54, 59, 63), ((0.0, 78, 1.5), (2.0, 83, 1.5), (3.5, 87, 0.5))),
    (40, (52, 59, 64, 71), ((0.0, 88, 2.0), (2.0, 83, 2.0))),

    # Chapter VI — The Stroke of Twelve (bars 25-29): settling home toward the midnight chime.
    (36, (48, 55, 60, 64), ((0.0, 79, 1.5), (2.0, 76, 2.0))),
    (33, (45, 52, 57, 64), ((0.0, 76, 1.5), (2.0, 72, 2.0))),
    (35, (47, 54, 59, 63), ((0.0, 75, 1.5), (2.0, 71, 2.0))),
    (35, (47, 54, 59, 66), ((0.0, 78, 2.0), (2.0, 75, 2.0))),
    (40, (52, 59, 64, 67), ((0.0, 76, 3.5),)),
]

# Exact bronze bell strike frames in Chapters V and VI (synchronized to the hammer animation).
# Every strike lands cleanly on a 15-fps frame boundary.
BELL_STRIKES = [
    (600, 52, 0.90),  # bar 20 beat 0 (E3)
    (630, 48, 0.85),  # bar 21 beat 0 (C3)
    (660, 50, 0.90),  # bar 22 beat 0 (D3)
    (690, 47, 0.92),  # bar 23 beat 0 (B2)
    (720, 52, 1.00),  # bar 24 beat 0 (E3 — grand peak)
    (765, 52, 0.72),  # bar 25 beat 2
    (810, 55, 0.65),  # bar 27 beat 0
    (870, 52, 1.00),  # bar 29 beat 0 — the final midnight chime wrapping into bar 0
]


def midi_hz(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def bell_impulse(frame):
    """Return decaying intensity [0, 1] of the most recent bronze bell strike."""
    best = 0.0
    for strike_frame, _, amp in BELL_STRIKES:
        dt = ((frame - strike_frame) % 900) / 15.0
        if dt < 4.5:
            val = amp * math.exp(-1.15 * dt)
            if val > best:
                best = val
    return best


def meter_levels(frame):
    """Four live fractional-block meter levels (TICK, BELL, MELODY, BASS) in [0, 1]."""
    t = frame / 15.0
    bar = int(t // BAR_SEC) % BARS
    bar_t = t % BAR_SEC
    beat_phase = (t * 2.0) % 1.0
    chapter = bar // 5

    # Escapement tick pulse: strong in dial & gearworks, softer in cosmos.
    tick_weight = (0.85, 1.00, 0.55, 0.30, 0.70, 0.80)[chapter]
    tick = tick_weight * math.exp(-6.5 * beat_phase)

    # Bronze bell & chime resonance.
    bell = bell_impulse(frame)
    if chapter in (0, 3, 5):
        bell = max(bell, 0.45 * math.exp(-2.8 * ((bar_t * 2.0) % 1.0)))

    # Singing melody / wind energy across each chamber.
    mel = 0.18
    for off, _, dur in BAR_SPEC[bar][2]:
        dt = bar_t - off * 0.5
        if 0.0 <= dt <= dur * 0.65:
            env = math.sin(math.pi * min(1.0, dt / max(dur * 0.65, 0.1))) ** 0.6
            mel = max(mel, 0.25 + 0.72 * env)

    # Deep organ / cello bass swell.
    bass_weight = (0.35, 0.62, 0.96, 0.88, 1.00, 0.58)[chapter]
    bass = bass_weight * (0.35 + 0.65 * (math.sin(math.pi * (bar_t / BAR_SEC)) ** 0.75))

    return (
        max(0.05, min(1.0, tick)),
        max(0.05, min(1.0, bell)),
        max(0.05, min(1.0, mel)),
        max(0.05, min(1.0, bass)),
    )
