"""The Midnight Watch — 60-second stereo synthesizer for clockwork, strings, cosmos, and bells."""
import math
import numpy as np

from score import BAR_SAMPLES, BAR_SPEC, BARS, BEAT_SAMPLES, BELL_STRIKES, RATE, TOTAL, midi_hz


def _wrap_add(bus, start, stereo):
    """Add a stereo buffer onto bus modulo TOTAL so tails wrap seamlessly across the seam."""
    s = int(round(start)) % TOTAL
    n = len(stereo)
    first = min(TOTAL - s, n)
    bus[s:s + first] += stereo[:first]
    if first < n:
        rem = n - first
        if rem <= TOTAL:
            bus[:rem] += stereo[first:]
        else:
            pos = first
            while pos < n:
                chunk = min(TOTAL, n - pos)
                bus[:chunk] += stereo[pos:pos + chunk]
                pos += chunk


def _place(bus, start, wave, pan):
    pan = max(-0.9, min(0.9, float(pan)))
    gains = np.sqrt([(1.0 - pan) * 0.5, (1.0 + pan) * 0.5])
    _wrap_add(bus, start, wave[:, None] * gains[None, :])


def _tick_wave(rng, is_tick):
    # Escapement click: crisp brass pallet-fork impulse plus subtle resonant body ring.
    t = np.arange(int(RATE * 0.065)) / RATE
    f1 = 3150.0 if is_tick else 2580.0
    f2 = 5920.0 if is_tick else 4860.0
    body = (
        np.sin(2.0 * np.pi * f1 * t) * np.exp(-95.0 * t)
        + 0.45 * np.sin(2.0 * np.pi * f2 * t) * np.exp(-160.0 * t)
        + 0.25 * np.sin(2.0 * np.pi * (f1 * 0.28) * t) * np.exp(-55.0 * t)
    )
    click = rng.standard_normal(len(t)) * np.exp(-380.0 * t)
    env = 1.0 - np.exp(-1800.0 * t)
    return (0.75 * body + 0.30 * click) * env


def _music_box(midi, dur_s=2.4):
    # Music box / celesta: clear tine fundamental with delicate bell-like upper partials.
    f = midi_hz(midi)
    t = np.arange(int(RATE * dur_s)) / RATE
    w = 2.0 * np.pi * f * t
    tone = (
        1.00 * np.sin(w) * np.exp(-1.9 * t)
        + 0.28 * np.sin(2.0 * w) * np.exp(-3.8 * t)
        + 0.14 * np.sin(3.98 * w) * np.exp(-7.5 * t)
        + 0.06 * np.sin(6.10 * w) * np.exp(-14.0 * t)
    )
    env = (1.0 - np.exp(-320.0 * t)) * np.minimum(1.0, (dur_s - t) * 10.0)
    return tone * env


def _harpsichord(midi, dur_s=1.25):
    # Harpsichord pluck: bright metallic string articulation locked to the gear teeth.
    f = midi_hz(midi)
    t = np.arange(int(RATE * dur_s)) / RATE
    w = 2.0 * np.pi * f * t
    tone = (
        1.00 * np.sin(w) * np.exp(-2.8 * t)
        + 0.62 * np.sin(2.0 * w) * np.exp(-4.4 * t)
        + 0.38 * np.sin(3.0 * w) * np.exp(-6.5 * t)
        + 0.22 * np.sin(4.0 * w) * np.exp(-9.5 * t)
        + 0.12 * np.sin(5.0 * w) * np.exp(-13.5 * t)
    )
    env = (1.0 - np.exp(-480.0 * t)) * np.minimum(1.0, (dur_s - t) * 14.0)
    return tone * env


def _reed_lead(midi, dur_s):
    # Celestial woodwind / reed lead: warm breathing vibrato soaring over the orrery.
    f = midi_hz(midi)
    n = max(1, int(RATE * (dur_s + 0.35)))
    t = np.arange(n) / RATE
    vib_depth = 0.0042 * np.minimum(1.0, t / 0.35)
    phase = 2.0 * np.pi * f * t + (f * vib_depth / 5.2) * np.sin(2.0 * np.pi * 5.2 * t)
    tone = (
        1.00 * np.sin(phase)
        + 0.34 * np.sin(2.0 * phase)
        + 0.19 * np.sin(3.0 * phase)
        + 0.07 * np.sin(4.0 * phase)
    )
    attack = 1.0 - np.exp(-16.0 * t)
    release = np.clip((dur_s + 0.35 - t) / 0.32, 0.0, 1.0) ** 1.4
    return tone * attack * release


def _pad_chord(bass_midi, chord_midis, dur_s, warmth=1.0):
    # Bowed cello bass and warm cathedral organ pad with gentle stereo chorus.
    n = int(RATE * dur_s)
    t = np.arange(n) / RATE
    swell = np.sin(np.pi * np.arange(n) / n) ** 0.78
    fb = midi_hz(bass_midi)
    pb = 2.0 * np.pi * fb * t
    left = (np.sin(pb) + 0.38 * np.sin(2.0 * pb + 0.10 * np.sin(15.0 * t)) + 0.14 * np.sin(3.0 * pb)) * 0.55
    right = (np.sin(pb * 1.0007) + 0.36 * np.sin(2.0 * pb * 1.0007) + 0.12 * np.sin(3.0 * pb)) * 0.55
    for idx, m in enumerate(chord_midis):
        fm = midi_hz(m)
        det = 1.0012 if (idx % 2 == 0) else 0.9988
        pl = 2.0 * np.pi * fm * t
        pr = 2.0 * np.pi * (fm * det) * t
        w_voice = 0.24 * warmth / len(chord_midis) * 4.0
        left += w_voice * (np.sin(pl) + 0.22 * np.sin(2.0 * pl))
        right += w_voice * (np.sin(pr) + 0.22 * np.sin(2.0 * pr))
    return np.column_stack((left * swell, right * swell))


def _bronze_bell(midi, dur_s=6.5):
    # Grand bronze midnight chime: minor-third cathedral bell partials and sub-octave hum.
    f = midi_hz(midi)
    t = np.arange(int(RATE * dur_s)) / RATE
    partials = (
        (0.500, 0.55, 0.42),   # hum (octave below)
        (1.000, 1.00, 0.68),   # prime
        (1.189, 0.52, 1.05),   # minor-third tierce
        (1.500, 0.32, 1.60),   # quint
        (2.000, 0.44, 1.95),   # nominal octave
        (2.756, 0.22, 3.40),   # superquint shimmer
        (3.980, 0.10, 6.20),   # strike brilliance
    )
    wave = np.zeros_like(t)
    for ratio, amp, decay in partials:
        wave += amp * np.sin(2.0 * np.pi * (f * ratio) * t) * np.exp(-decay * t)
    attack = 1.0 - np.exp(-420.0 * t)
    tail = np.minimum(1.0, (dur_s - t) * 2.5)
    return wave * attack * tail


def _pendulum_whoosh(rng, dur_s=1.45):
    # Soft filtered air swoosh as the heavy brass pendulum sweeps through bottom center.
    n = int(RATE * dur_s)
    t = np.arange(n) / RATE
    noise = rng.standard_normal(n)
    # Smooth noise with a low-pass boxcar and modulate at warm rushing air frequencies.
    kernel = np.ones(48) / 48.0
    low = np.convolve(noise, kernel, mode="same")
    carrier = np.sin(2.0 * np.pi * (140.0 + 95.0 * np.sin(np.pi * t / dur_s)) * t)
    env = np.sin(np.pi * t / dur_s) ** 2.2
    return (0.65 * low + 0.35 * low * carrier) * env


def render():
    """Synthesize the complete 60-second 48 kHz 16-bit stereo PCM soundtrack."""
    dry = np.zeros((TOTAL, 2), dtype=np.float64)
    wet_src = np.zeros((TOTAL, 2), dtype=np.float64)
    rng = np.random.default_rng(1200)

    tick_hi = _tick_wave(rng, True)
    tick_lo = _tick_wave(rng, False)
    whoosh_base = _pendulum_whoosh(rng)

    # 1. Mechanical escapement ticks across the entire 60-second minute (2 ticks per second).
    for beat in range(BARS * 4):
        bar = beat // 4
        chapter = bar // 5
        amp = (0.24, 0.34, 0.16, 0.08, 0.20, 0.24)[chapter]
        is_tick = (beat % 2 == 0)
        pan = -0.16 if is_tick else 0.16
        _place(dry, beat * BEAT_SAMPLES, amp * (tick_hi if is_tick else tick_lo), pan)
        # Double-speed brass ratchet escapement echo inside the Gearworks (Chapter II).
        if chapter == 1:
            _place(dry, beat * BEAT_SAMPLES + BEAT_SAMPLES // 2, 0.11 * tick_lo, -pan * 1.8)

    # 2. Thirty bars of harmony, pads, harpsichord gearwork, music box, and celestial reed.
    for bar, (bass, chord, melody) in enumerate(BAR_SPEC):
        bar_start = bar * BAR_SAMPLES
        chapter = bar // 5

        # Warm cello and cathedral organ swell underlying each chapter.
        pad_gain = (0.14, 0.20, 0.34, 0.32, 0.36, 0.22)[chapter]
        pad_dur = 2.45 if chapter in (2, 3, 4) else 2.20
        pad = _pad_chord(bass, chord, pad_dur, warmth=1.0 if chapter != 1 else 0.65)
        _wrap_add(wet_src, bar_start, pad_gain * pad)

        # Harpsichord / gearwork eighth-note arpeggio in Chapter II and reprise in V.
        if chapter in (1, 4):
            arp_gain = 0.16 if chapter == 1 else 0.11
            for step in range(8):
                note = chord[step % len(chord)] + (12 if step in (3, 7) else 0)
                pan = -0.45 + 0.90 * (step / 7.0)
                _place(wet_src, bar_start + step * (BEAT_SAMPLES // 2), arp_gain * _harpsichord(note, 0.95), pan)

        # Shimmering celesta arpeggio inside the Orrery (Chapter IV).
        if chapter == 3:
            for step in range(4):
                note = chord[step % len(chord)] + 12
                pan = 0.55 * math.cos(bar * 1.1 + step * 0.9)
                _place(wet_src, bar_start + step * BEAT_SAMPLES + BEAT_SAMPLES // 2, 0.13 * _music_box(note, 2.2), pan)

        # Pendulum air whoosh sweeping stereo left-to-right across Chapter III.
        if chapter == 2:
            pan = -0.62 if (bar % 2 == 0) else 0.62
            _place(dry, bar_start + int(RATE * 0.28), 0.24 * whoosh_base, pan)

        # Main watchmaker theme across every chapter, transforming its timber as we travel.
        for beat_off, midi, dur_beats in melody:
            onset = bar_start + int(round(beat_off * BEAT_SAMPLES))
            dur_s = dur_beats * 0.5
            if chapter in (0, 5):
                _place(wet_src, onset, 0.25 * _music_box(midi, 2.5), 0.18 * math.sin(bar + beat_off))
            elif chapter == 1:
                _place(wet_src, onset, 0.22 * _harpsichord(midi, 1.3), -0.25 if beat_off < 2 else 0.25)
            elif chapter == 2:
                _place(wet_src, onset, 0.22 * _reed_lead(midi - 12, dur_s), -0.18)
                _place(wet_src, onset, 0.12 * _music_box(midi, 2.0), 0.28)
            elif chapter == 3:
                _place(wet_src, onset, 0.24 * _reed_lead(midi, dur_s), 0.22 * math.sin(bar * 0.7))
                _place(wet_src, onset, 0.14 * _music_box(midi, 2.4), -0.30 * math.sin(bar * 0.7))
            elif chapter == 4:
                _place(wet_src, onset, 0.20 * _reed_lead(midi, dur_s), -0.20)
                _place(wet_src, onset, 0.18 * _music_box(midi, 2.6), 0.25)

    # 3. Colossal bronze cathedral chimes in Chapters V and VI, wrapping into bar 0.
    for strike_frame, midi, amp in BELL_STRIKES:
        sample_pos = int(round(strike_frame * (RATE / 15.0)))
        bell = _bronze_bell(midi, dur_s=6.8)
        _place(wet_src, sample_pos, 0.34 * amp * bell, -0.10)
        _place(wet_src, sample_pos + 320, 0.14 * amp * bell, 0.42)

    # 4. Subtle stereo hall reflections wrapped seamlessly modulo TOTAL.
    mix = dry + wet_src
    tap1 = int(RATE * 0.23)
    tap2 = int(RATE * 0.41)
    mix += 0.20 * np.roll(wet_src[:, ::-1], tap1, axis=0)
    mix += 0.11 * np.roll(wet_src, tap2, axis=0)

    # Gentle soft-knee warmth and normalization with generous headroom.
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak
    mix = np.tanh(mix * 1.18) / np.tanh(1.18)
    return np.round(25600.0 * mix).astype("<i2")
