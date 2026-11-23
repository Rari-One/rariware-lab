"""Salt & Brass — eight harmonic modes for bowed brass plate, bronze partials, and leaping salt."""
import numpy as np

RATE = 48000
BAR = 96000          # 2.0 seconds per measure (48 visual frames at 24 fps)
BARS = 8
TOTAL = BARS * BAR   # 16.0 seconds = 768,000 stereo sample pairs

# Each measure pairs a Chladni circular eigenmode with a musical chord and bow rim angle.
# Format: (roman, label, m1, k1, m2, k2, mix2, bow_deg, bass_midi, chord_midis)
# k values are radial zeros of Bessel J_m so the plate rim stays a clean nodal boundary.
MODES = [
    ("I",    "2,2", 2,  8.417, 0,  0.000,  0.00,   0, 38, (69, 74, 77)),  # D2 · A4 D5 F5
    ("II",   "3,2", 3,  9.761, 0,  0.000,  0.00,  45, 34, (65, 69, 74)),  # Bb1 · F4 A4 D5
    ("III",  "0,4", 0, 11.792, 4,  7.588,  0.38,  90, 36, (67, 72, 76)),  # C2 · G4 C5 E5
    ("IV",   "4,2", 4, 11.065, 0,  0.000,  0.00, 135, 33, (64, 69, 73)),  # A1 · E4 A4 C#5
    ("V",    "2,3", 2, 11.620, 0,  8.654,  0.55, 180, 31, (62, 67, 71)),  # G1 · D4 G4 B4
    ("VI",   "5,2", 5, 12.339, 0,  0.000,  0.00, 225, 29, (60, 65, 69)),  # F1 · C4 F4 A4
    ("VII",  "3,3", 3, 13.015, 1, 10.173, -0.48, 270, 31, (62, 69, 76)),  # G1 · D4 A4 E5
    ("VIII", "1,4", 1, 13.324, 3,  9.761,  0.46, 315, 33, (64, 67, 72)),  # A1 · E4 G4 C5
]

NOTE_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")


def midi_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def midi_name(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def partial_levels(bar_index, phase):
    """Four normalized modal energy envelopes in [0, 1] for the live plate readout."""
    t = phase * 2.0
    bow = np.sin(np.pi * phase) ** 0.75 * 0.72 + 0.18 * np.exp(-3.5 * t)
    bell = np.exp(-1.55 * t) * (1.0 - np.exp(-45.0 * t))
    answer = np.exp(-2.1 * ((t - 0.78) % 2.0)) * (0.85 if t >= 0.78 else 0.18)
    spark = np.exp(-4.8 * t) * (1.0 - np.exp(-90.0 * t))
    return (
        float(np.clip(bow, 0.0, 1.0)),
        float(np.clip(bell, 0.0, 1.0)),
        float(np.clip(answer, 0.0, 1.0)),
        float(np.clip(spark, 0.0, 1.0)),
    )


def render():
    """Synthesize a seamless 16-second 48 kHz 16-bit stereo PCM loop."""
    mix = np.zeros((TOTAL, 2), dtype=np.float64)
    rng = np.random.default_rng(1787)  # Year of Chladni's Entdeckungen

    def place(sample_start, wave, pan):
        # Wrap ringing tails cleanly across the loop boundary so there is no seam cut.
        start = int(round(sample_start)) % TOTAL
        pan = float(np.clip(pan, -0.88, 0.88))
        gains = np.sqrt([(1.0 - pan) * 0.5, (1.0 + pan) * 0.5])
        stereo = wave[:, None] * gains[None, :]
        first = min(TOTAL - start, len(wave))
        mix[start:start + first] += stereo[:first]
        if first < len(wave):
            mix[:len(wave) - first] += stereo[first:]

    t_bell = np.arange(int(RATE * 3.4)) / RATE
    t_bow = np.arange(int(BAR * 1.18)) / RATE
    t_salt = np.arange(int(RATE * 0.72)) / RATE

    for idx, mode in enumerate(MODES):
        _, _, _, _, _, _, _, bow_deg, bass, chord = mode
        bar_start = idx * BAR
        bow_pan = 0.58 * np.cos(np.deg2rad(bow_deg))

        # Bowed brass fundamental: slow rosin-warmed swell across the plate rim.
        f_bass = midi_hz(bass)
        swell = np.sin(np.pi * np.arange(len(t_bow)) / len(t_bow)) ** 0.82
        vib = 0.0022 * np.sin(2.0 * np.pi * 4.2 * t_bow)
        ph = 2.0 * np.pi * f_bass * (t_bow + vib / (2.0 * np.pi * 4.2))
        bow_wave = (
            1.00 * np.sin(ph)
            + 0.36 * np.sin(2.0 * ph + 0.12 * np.sin(17.0 * t_bow))
            + 0.14 * np.sin(3.0 * ph)
            + 0.05 * np.sin(5.0 * ph) * np.exp(-0.55 * t_bow)
        )
        place(bar_start, 0.30 * swell * bow_wave, -0.22 * bow_pan)

        # Struck bronze plate partials: three chord tones with authentic modal ratios.
        for v, midi in enumerate(chord):
            f = midi_hz(midi)
            w = 2.0 * np.pi * f * t_bell
            attack = 1.0 - np.exp(-220.0 * t_bell)
            tail = np.minimum(1.0, (t_bell[-1] - t_bell) * 6.0)
            plate_tone = (
                1.00 * np.sin(w) * np.exp(-1.35 * t_bell)
                + 0.34 * np.sin(2.00 * w + 0.08) * np.exp(-2.60 * t_bell)
                + 0.19 * np.sin(2.756 * w) * np.exp(-4.40 * t_bell)
                + 0.08 * np.sin(3.98 * w) * np.exp(-7.20 * t_bell)
            ) * attack * tail
            offset = v * int(RATE * 0.032)
            voice_pan = np.clip(bow_pan * 0.6 + (-0.42, 0.04, 0.46)[v], -0.82, 0.82)
            place(bar_start + offset, (0.21, 0.18, 0.16)[v] * plate_tone, voice_pan)

        # Off-beat harmonic answer: a quiet higher partial ringing from the opposite side.
        f_ans = midi_hz(chord[2] + (12 if idx in (2, 4, 6) else 0))
        w_ans = 2.0 * np.pi * f_ans * t_bell
        ans_env = (1.0 - np.exp(-140.0 * t_bell)) * np.exp(-2.05 * t_bell)
        ans_tail = np.minimum(1.0, (t_bell[-1] - t_bell) * 6.0)
        ans_wave = (np.sin(w_ans) + 0.22 * np.sin(2.756 * w_ans) * np.exp(-2.5 * t_bell)) * ans_env * ans_tail
        place(bar_start + int(RATE * 0.78), 0.095 * ans_wave, -bow_pan * 0.75)

        # Salt whisper: crystalline high-band shimmer as grains leap off the antinodes.
        noise = rng.standard_normal(len(t_salt))
        carriers = (
            np.sin(2.0 * np.pi * (2900.0 + 180.0 * idx) * t_salt)
            + 0.65 * np.sin(2.0 * np.pi * (4650.0 - 140.0 * idx) * t_salt)
        )
        # Smooth the modulated noise with a short moving average to focus the grain band.
        grain = np.convolve(noise * carriers, np.ones(14) / 14.0, mode="same")
        grain_env = (1.0 - np.exp(-85.0 * t_salt)) * np.exp(-6.2 * t_salt)
        place(bar_start + int(RATE * 0.015), 0.085 * grain * grain_env, bow_pan * 0.85)

    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak
    return np.round(25800.0 * mix).astype("<i2")
