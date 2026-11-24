"""The Long Way Round — the route. One drop of water goes all the way round in a minute.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

Everything the picture and the music share lives here: the clock, the shape of
the land, the path the drop takes, and the camera that follows it. The world
wraps around every 2,560 dots, so when the drop climbs back into its cloud at
the end, it is the same cloud it fell from, and the loop has no seam.
"""
import numpy as np

FPS, FRAMES, RATE = 14, 896, 48000
N = RATE * FRAMES // FPS           # 3,072,000 stereo sample pairs: exactly 64 seconds
BPM, BEAT, BAR = 105, 8, 32        # one beat is 8 frames; 28 bars of 4/4
W, H = 130, 43                     # 5,590 cells, close to the player's decoded limit
DW, DH = 2 * W, 4 * H              # 260 x 172 Braille dots on screen
PERIOD = 2560                      # the width of the world in dots
SEA = 700                          # sea level; y grows downward

CHAPTERS = [(0, "I", "CLOUD"), (128, "II", "FALL"), (224, "III", "SNOWMELT"),
            (384, "IV", "RIVER"), (544, "V", "SEA"), (640, "VI", "DEEP"),
            (768, "VII", "RETURN")]
LANDING = 224                      # the drop meets the snow on the downbeat of bar 8
BELLS = (448, 464)                 # the church bell tolls twice in bar 15
WHALE, WHALE_AGAIN = 608, 708      # a whale calls as it passes, and again far off
VENT = 768                         # a hydrothermal vent lifts the drop

# The land, as (x, ground height) around the world: a peak, a long slope of
# pines, a river plain, the coast, a deep trench, and a cliff back to the peak.
RIDGE = [(0, 460), (120, 360), (300, 290), (480, 380), (700, 470), (900, 560),
         (1150, 645), (1300, 655), (1600, 662), (1700, 690), (1740, 760),
         (1850, 820), (2000, 980), (2120, 1110), (2250, 1120), (2350, 900),
         (2450, 760), (2500, 690), (2540, 560)]
_xs = np.array([p[0] for p in RIDGE], float)
_ys = np.array([p[1] for p in RIDGE], float)


def ground(x):
    """Height of the ground at world x: a periodic Catmull-Rom spline plus rock."""
    x = np.mod(np.asarray(x, float), PERIOD)
    k = len(_xs)
    i = np.searchsorted(_xs, x, side="right") - 1
    x0 = _xs[i]
    x1 = np.where(i + 1 < k, _xs[(i + 1) % k], PERIOD)
    t = (x - x0) / (x1 - x0)
    p0, p1, p2, p3 = _ys[(i - 1) % k], _ys[i], _ys[(i + 1) % k], _ys[(i + 2) % k]
    y = 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
               + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)
    rock = (6 * np.sin(2 * np.pi * 9 * x / PERIOD) + 3 * np.sin(2 * np.pi * 29 * x / PERIOD + 1)
            + 1.5 * np.sin(2 * np.pi * 71 * x / PERIOD + 2))
    calm = 1 - 0.85 * np.clip(np.minimum((x - 1100) / 80, (1720 - x) / 80), 0, 1)
    return y + rock * calm


def surface(x, f):
    """The sea's surface: two swells, each a whole number of times per loop."""
    return (SEA + 2.5 * np.sin(2 * np.pi * (np.asarray(x) / 64 - 12 * f / FRAMES))
            + 1.2 * np.sin(2 * np.pi * (np.asarray(x) / 23 + 20 * f / FRAMES)))


def drop(f):
    """Where the drop is on frame f, as (x, y, vapour): 1 is vapour, 0 is a drop."""
    f = f % FRAMES
    if f < 128:
        # The cloud: vapour gathers into one drop.
        u = f / 128
        return 150 + 25 * u, -150 + 10 * u, max(0.0, 1 - f / 44)
    if f < 224:
        # The fall: gravity and a west wind carry it down onto the peak.
        u = (f - 128) / 96
        y1 = float(ground(300)) - 2
        return 175 + 125 * u, -140 + (y1 + 140) * u ** 1.5, 0.0
    if f < 384:
        # Snowmelt: it runs down the mountain with the stream.
        x = 300 + 850 * (f - 224) / 160
        return x, float(ground(x)) - 2, 0.0
    if f < 544:
        # The river carries it slowly through the village to the coast.
        x = 1150 + 570 * (f - 384) / 160
        return x, min(float(ground(x)), float(surface(x, f))) - 2, 0.0
    if f < 640:
        # The sea: it rides the swell, then slips beneath it.
        u = (f - 544) / 96
        x = 1720 + 240 * u
        return x, float(surface(x, f)) - 1 + max(0.0, (u - 0.7) / 0.3) * 28, 0.0
    if f < 768:
        # The deep: it sinks, slowing, toward the vent on the trench floor.
        u = (f - 640) / 128
        return 1960 + 215 * u, 727 + 358 * (1 - (1 - u) ** 2), 0.0
    # The return: warm water lifts it, it breaks the surface as vapour,
    # and the wind carries it up and east, round the world, into its cloud.
    u = (f - 768) / 128
    y = 1085 - 1235 * u * u * (3 - 2 * u)
    return 2175 + 535 * u, y, float(np.clip((SEA - 20 - y) / 400, 0, 1))


BREACH = next(f for f in range(768, FRAMES) if drop(f)[1] < SEA)

# The camera leads the drop: below it while falling, above it on the water.
_LEAD = [(0, 0, 0), (110, 0, 0), (150, 0, 45), (210, 0, 45), (236, 30, -28), (530, 30, -28),
         (600, 10, -28), (650, 0, 0), (770, 0, 0), (805, 0, -40), (880, 0, -20), (896, 0, 0)]


def _camera():
    frames = np.arange(FRAMES)
    path = np.array([drop(f)[:2] for f in frames])
    lead = np.array([[np.interp(f, [k[0] for k in _LEAD], [k[i] for k in _LEAD]) for i in (1, 2)]
                     for f in frames])
    raw = path + lead
    raw[:, 0] -= PERIOD * frames / FRAMES          # remove the lap, so x is periodic
    kernel = np.exp(-0.5 * (np.fft.fftfreq(FRAMES) * FRAMES * 2 * np.pi * 5 / FRAMES) ** 2)
    smooth = np.real(np.fft.ifft(np.fft.fft(raw, axis=0) * kernel[:, None], axis=0))
    smooth[:, 0] += PERIOD * frames / FRAMES
    return np.round(smooth).astype(int)


CAMERA = _camera()


def chapter(f):
    """The chapter playing on frame f, as an index into CHAPTERS."""
    return max(i for i, (start, _, _) in enumerate(CHAPTERS) if start <= f % FRAMES)
