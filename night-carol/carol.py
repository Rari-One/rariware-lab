"""Night Carol — the score. An original carol for four voices, words and music.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

The tune and the words are written out below, one bar per line. Only the
melody (the soprano) is written by hand. The other three voices are found by a
small rule, the kind a harmony student learns first: for every syllable, give
each lower voice a note of the chord that is as close as possible to the note
it sang last. That rule is called voice leading, and it is why the alto, tenor
and bass lines move smoothly instead of jumping about.

Everything else in the piece reads from here: choir.py sings these notes, and
sky.py draws them as stars.
"""
BPM = 75
FPS = 15
BEAT = 12                 # frames per beat: 60 / 75 * 15
BAR = 4 * BEAT            # 4/4 time, 48 frames per bar
BARS = 18
FRAMES = BAR * BARS       # 864 frames: 57.6 seconds
RATE = 48000
SECONDS_PER_BEAT = 60 / BPM

NAMES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

# Chords, as (pitch classes, bass pitch class). "D/F#" means a D chord with
# F sharp in the bass; "D7" adds the seventh, C, which pulls toward G.
CHORDS = {
    "G": ("G B D", "G"), "G/B": ("G B D", "B"), "G/D": ("G B D", "D"),
    "C": ("C E G", "C"), "D": ("D F# A", "D"), "D/F#": ("D F# A", "F#"),
    "D7": ("D F# A C", "D"), "Em": ("E G B", "E"), "Am": ("A C E", "A"),
    "A": ("A C# E", "A"),
}

# The carol. Each bar is a list of (syllable, melody note, beats, chord).
# Bars 1 and 2 are the bells' introduction, so they have no words.
SCORE = [
    [],                                                                      # bar 1
    [],                                                                      # bar 2
    [("Hush,", "B4", 1.5, "G"), ("the", "A4", .5, "D/F#"),
     ("snow", "G4", 1, "Em"), ("on", "B4", 1, "G/B")],                       # bar 3
    [("the", "C5", 1, "C"), ("town;", "D5", 3, "G")],                        # bar 4
    [("lamps", "E5", 1.5, "C"), ("in", "D5", .5, "G/B"),
     ("the", "C5", 1, "Am"), ("win", "B4", 1, "G")],                         # bar 5
    [("dows", "C5", 1, "C"), ("glow.", "A4", 3, "D")],                       # bar 6
    [("Far", "D5", 1, "G"), ("on", "B4", .5, "Em"),
     ("the", "D5", .5, "G"), ("hill,", "G5", 2, "C")],                       # bar 7
    [("the", "E5", 1, "C"), ("night", "E5", 1, "Am"),
     ("is", "D5", 1, "D"), ("still,", "C5", 1, "D7")],                       # bar 8
    [("stars", "B4", 1.5, "G"), ("o", "A4", .5, "D/F#"),
     ("ver", "B4", 1, "Em"), ("all", "D5", 1, "G")],                         # bar 9
    [("be", "A4", 1, "D7"), ("low.", "G4", 3, "G")],                         # bar 10
    [("Ring,", "E5", 1.5, "C"), ("bells,", "D5", .5, "G/B"),
     ("ring", "E5", 1, "Am"), ("through", "G5", 1, "C")],                    # bar 11
    [("the", "F#5", .5, "D"), ("win", "E5", .5, "A"),
     ("ter", "E5", 1, "A"), ("night;", "D5", 2, "D")],                       # bar 12
    [("sing", "B4", 1.5, "G"), ("as", "C5", .5, "Am"),
     ("the", "D5", 1, "G"), ("can", "E5", 1, "C")],                          # bar 13
    [("dles", "C5", 1, "Am"), ("burn.", "D5", 3, "D")],                      # bar 14
    [("No", "D5", 1, "G"), ("el,", "G5", 1, "Em"),
     ("no", "E5", 1, "C"), ("el,", "C5", 1, "Am")],                          # bar 15
    [("the", "B4", 1.5, "G/D"), ("year", "C5", .5, "Am"),
     ("will", "A4", 2, "D7")],                                               # bar 16
    [("turn.", "G4", 4, "G")],                                               # bar 17
    [("No", "E5", 2, "C"), ("el.", "D5", 2, "G")],                           # bar 18
]

# The four lines of words as they appear on screen, by first and last bar.
LINES = [(3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 17), (18, 18)]

# Where each voice may sing, as MIDI note numbers (60 is middle C).
RANGES = {"soprano": (62, 81), "alto": (55, 74), "tenor": (48, 67), "bass": (40, 60)}
PARTS = ["soprano", "alto", "tenor", "bass"]


def midi(name):
    return 12 * (int(name[-1]) + 1) + NAMES[name[:-1]]


def hz(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def chord_tones(symbol):
    tones, bass = CHORDS[symbol]
    return {NAMES[t] for t in tones.split()}, NAMES[bass]


def nearest(candidates, previous):
    return min(candidates, key=lambda n: (abs(n - previous), n))


def harmonize():
    """Give every syllable four notes, one per voice, by simple voice leading."""
    previous = {"alto": 62, "tenor": 55, "bass": 43}
    voiced = []
    for bar, notes in enumerate(SCORE):
        beat = 0.0
        for syllable, name, beats, symbol in notes:
            soprano = midi(name)
            tones, root = chord_tones(symbol)
            low, high = RANGES["bass"]
            bass = nearest([n for n in range(low, high + 1) if n % 12 == root], previous["bass"])
            low, high = RANGES["alto"]
            alto = nearest([n for n in range(low, min(high, soprano - 1) + 1)
                            if n % 12 in tones and n >= soprano - 12], previous["alto"])
            # The tenor fills in whichever chord note is still missing, if it can.
            missing = tones - {soprano % 12, alto % 12, bass % 12}
            low, high = RANGES["tenor"]
            room = [n for n in range(max(low, bass + 3), min(high, alto - 1) + 1) if n % 12 in tones]
            preferred = [n for n in room if n % 12 in missing] or room or [alto - 5]
            tenor = nearest(preferred, previous["tenor"])
            previous.update(alto=alto, tenor=tenor, bass=bass)
            voiced.append(dict(bar=bar, beat=beat, beats=beats, syllable=syllable, chord=symbol,
                               notes={"soprano": soprano, "alto": alto, "tenor": tenor, "bass": bass}))
            beat += beats
        assert not notes or abs(beat - 4) < 1e-9, f"bar {bar + 1} has {beat} beats"
    return voiced


def seconds(bar, beat=0.0):
    return (4 * bar + beat) * SECONDS_PER_BEAT


def frame_of(bar, beat=0.0):
    return int(round((4 * bar + beat) * BEAT))


SUNG = harmonize()

# The bells' peal for the introduction: the scale of G falling, twice, then
# the first chord. Each entry is (bar, beat, note).
PEAL = [(0, i / 2, midi(n)) for i, n in enumerate("G5 F#5 E5 D5 C5 B4 A4 G4".split())]
PEAL += [(1, i / 2, midi(n)) for i, n in enumerate("B5 A5 G5 F#5 E5 D5".split())]
PEAL += [(1, 3, midi("G5")), (1, 3, midi("D5")), (1, 3, midi("B4"))]
