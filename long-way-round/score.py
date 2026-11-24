"""The Long Way Round — the score. Twenty-eight bars, one for each stretch of the road.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

The theme belongs to the drop. A celesta finds it inside the cloud, a flute
carries it down the stream and through the village, glass bells keep it in the
deep, and on the way home the flute and the celesta sing it together. The drop
itself flares on every note of it. At 105 BPM one beat is exactly eight frames.
"""
import numpy as np

from journey import CHAPTERS, BAR, FPS, FRAMES

SPB = 60 / 105                                   # seconds per beat
PITCH = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

VOICINGS = {
    "Dmaj7": "D3 A3 C#4 F#4", "Bm7": "B2 F#3 A3 D4", "Gmaj7": "G2 D3 F#3 B3",
    "Asus4": "A2 E3 A3 D4", "Em7": "E3 B3 D4 G4", "F#m7": "F#3 C#4 E4 A4",
    "G6": "G2 D3 E3 B3", "D": "D3 A3 D4 F#4", "A/C#": "E3 A3 C#4 E4", "Bm": "B2 F#3 B3 D4",
    "G": "G2 D3 G3 B3", "A": "A2 E3 A3 C#4", "D/F#": "F#3 A3 D4 F#4", "Em": "E3 G3 B3 E4",
    "Em9": "E3 G3 B3 D4 F#4", "F#": "F#3 A#3 C#4 F#4",
}

# The journey, one bar per line: chord, bass note, and the theme as name:beats.
SCORE = [
    # I. Cloud: the drop condenses
    ("Dmaj7", "D2", "F#5:1 E5:.5 D5:.5 A4:1.5 B4:.5"),          # bar 1
    ("Bm7", "B1", "D5:1 B4:1 F#5:1.5 E5:.5"),                    # bar 2
    ("Gmaj7", "G1", "D5:1 B4:.5 A4:.5 F#4:1 B4:1"),              # bar 3
    ("Asus4", "A1", "E5:1.5 D5:.5 E5:1 A4:1"),                   # bar 4
    # II. Fall: down through the night, onto the peak
    ("Em7", "E2", "G5:1.5 F#5:.5 E5:1 B4:1"),                    # bar 5
    ("F#m7", "F#2", "C#6:1.5 A5:.5 F#5:1 E5:1"),                 # bar 6
    ("G6", "G1", "D5:2 E5:1 -:1"),                               # bar 7
    # III. Snowmelt: the stream runs down through the pines
    ("D", "D2", "F#5:1 E5:.5 D5:.5 A4:1.5 B4:.5"),               # bar 8
    ("A/C#", "C#2", "C#5:1 E5:1 A5:1.5 E5:.5"),                  # bar 9
    ("Bm", "B1", "F#5:1 D5:.5 B4:.5 F#4:1 B4:1"),                # bar 10
    ("G", "G1", "D5:1.5 E5:.5 G5:1 F#5:.5 E5:.5"),               # bar 11
    ("A", "A1", "E5:2 C#5:1 A4:1"),                              # bar 12
    # IV. River: through the village at night
    ("G", "G1", "B4:1 D5:1 G5:1.5 F#5:.5"),                      # bar 13
    ("D/F#", "F#1", "F#5:1 E5:.5 D5:.5 A4:2"),                   # bar 14
    ("Em", "E2", "G4:1 B4:1 E5:1 D5:.5 B4:.5"),                  # bar 15
    ("A", "A1", "C#5:1.5 D5:.5 E5:1 A5:1"),                      # bar 16
    ("D", "D2", "F#5:3 -:1"),                                    # bar 17
    # V. Sea: open water under the moon
    ("Bm", "B1", "F#5:2 E5:1 D5:1"),                             # bar 18
    ("G", "G1", "D5:2 B4:2"),                                    # bar 19
    ("A", "A1", "C#5:2 E5:2"),                                   # bar 20
    # VI. Deep: slow glass in the dark
    ("Bm", "B1", "B4:1.5 F#4:.5 D5:2"),                          # bar 21
    ("Gmaj7", "G1", "-:1 B4:1 A4:1 F#4:1"),                      # bar 22
    ("Em9", "E2", "E5:2 D5:1 B4:1"),                             # bar 23
    ("F#", "F#1", "C#5:2 A#4:2"),                                # bar 24
    # VII. Return: lifted, out of the sea and up to the cloud
    ("G", "G1", "B4:1 D5:1 G5:1 F#5:1"),                         # bar 25
    ("A", "A1", "E5:1 C#5:1 A5:1.5 E5:.5"),                      # bar 26
    ("Bm", "B1", "F#5:1 B5:1 A5:1 F#5:1"),                       # bar 27
    ("A", "A1", "E5:2 A5:1.5 -:.5"),                             # bar 28
]
SCENES = ["cloud", "fall", "snowmelt", "river", "sea", "deep", "return"]
FIRST_BAR = [start // BAR for start, _, _ in CHAPTERS]


def midi(name):
    return 12 * (int(name[-1]) + 1) + PITCH[name[:-1]]


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def scene(bar):
    return SCENES[max(i for i, first in enumerate(FIRST_BAR) if first <= bar)]


def bar_time(bar, beat=0.0):
    return (4 * bar + beat) * SPB


def chord(bar):
    return [midi(name) for name in VOICINGS[SCORE[bar][0]].split()]


def melody():
    """Every note of the theme as (start in seconds, MIDI note, beats, bar)."""
    notes = []
    for bar, (_, _, line) in enumerate(SCORE):
        beat = 0.0
        for token in line.split():
            name, length = token.split(":")
            if name != "-":
                notes.append((bar_time(bar, beat), midi(name), float(length), bar))
            beat += float(length)
        assert abs(beat - 4) < 1e-9, f"bar {bar + 1} has {beat} beats"
    return notes


def third_below(note):
    """A diatonic third under a note of D major, for the village harmony."""
    scale = [2, 4, 6, 7, 9, 11, 1]
    if note % 12 not in scale:
        return None
    target = scale[(scale.index(note % 12) - 2) % 7]
    return note - (note % 12 - target) % 12


def pulse():
    """How brightly the drop shines on each frame: it flares on every theme note."""
    frames = np.arange(FRAMES)
    glow = np.zeros(FRAMES)
    for start, _, _, _ in melody():
        glow += np.exp(-((frames - start * FPS) % FRAMES) / 3)
    return np.minimum(glow, 1.0)
