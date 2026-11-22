"""Umbra Choir. Eight measures for struck glass, bowed bass and distant harmonics."""
import numpy as np

RATE = 48000
BEAT = 32000
TOTAL = 32 * BEAT
# Each bar carries a bass pitch and four upper partials. The last chord
# leaves the third open, so the opening D can sound like an answer.
VOICINGS = [
    (38, (57, 64, 65, 72)), (34, (57, 60, 65, 69)),
    (41, (55, 60, 64, 69)), (36, (55, 62, 64, 67)),
    (31, (53, 58, 62, 69)), (39, (55, 58, 65, 70)),
    (33, (55, 59, 64, 67)), (33, (52, 57, 62, 64)),
]
# Off-beat attacks leave a breath between the glass notes.
RHYTHM = ((0, 0), (.75, 2), (1.5, 1), (2.75, 3))
def strikes():
    for bar, (_, notes) in enumerate(VOICINGS):
        for delay, voice in RHYTHM:
            yield bar * 4 + delay, notes[voice], voice

def render():
    mix = np.zeros((TOTAL, 2))
    def place(beat, wave, pan):
        # Wrap ringing tails into the opening instead of cutting them at the seam.
        start = round(beat * BEAT) % TOTAL
        stereo = wave[:, None] * np.sqrt([(1-pan)/2, (1+pan)/2])
        first = min(TOTAL-start, len(wave))
        mix[start:start+first] += stereo[:first]
        mix[:len(wave)-first] += stereo[first:]

    for beat, pitch, voice in strikes():
        # Glass has a bright, slightly inharmonic attack and a long clear fundamental.
        t = np.arange(RATE*3) / RATE
        phase = 2*np.pi * 440 * 2**((pitch-69)/12) * t
        ring = np.sin(phase)*np.exp(-2*t) + .32*np.sin(2.71*phase)*np.exp(-5*t)
        ring += .11*np.sin(4.08*phase)*np.exp(-8*t)
        envelope = (1-np.exp(-180*t))*np.minimum(1,(3-t)*12)
        place(beat, .34*ring*envelope, (-.62,-.22,.28,.65)[voice])
        place(beat+.46, .065*ring*envelope, (.65,.28,-.22,-.62)[voice])

    for bar, (bass, notes) in enumerate(VOICINGS):
        # The bow opens slowly under the glass, then hands its pitch to the next bow.
        t = np.arange(4*BEAT) / RATE
        swell = np.sin(np.pi*np.arange(4*BEAT)/(4*BEAT))**.85
        phase = 2*np.pi*440*2**((bass-69)/12)*t
        bow = np.sin(phase)+.30*np.sin(2*phase+.09*np.sin(21*t))
        place(4*bar, .29*swell*bow, -.14)
        # At conjunction, a high harmonic answers from the opposite side.
        if bar in (3,4,6):
            overtone = np.sin(2*np.pi*440*2**((notes[2]+12-69)/12)*t)
            place(4*bar+.25,.11*swell*overtone,.57)
    return np.round(26500 * mix / np.max(np.abs(mix))).astype('<i2')

