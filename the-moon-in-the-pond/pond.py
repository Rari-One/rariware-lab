"""The Moon in the Pond: rain breaks up the reflection of a full moon, then the pond goes still.

Run pack.py to build the package; this file does the drawing. It uses only the standard library.

The picture is a top-down view of a dark pond at night. A full moon and a few stars are reflected in
it, three lily pads float on it, and a seeded shower of rain falls across one 24-second loop.

Three techniques do the work, each in its own section below:

1. The wave equation, solved with finite differences. The water is a grid of heights. Each step,
   every point is pulled toward the average of its four neighbours (the discrete Laplacian), and a
   little damping makes old ripples fade.
2. Displacement-mapped reflection. To find what a point of water reflects, we look up the sky at a
   position nudged by the slope of the water there. Flat water mirrors the moon; rippled water
   scatters it into rings and slivers.
3. Brightness ramps. Each character cell gets a glyph and a colour picked from its brightness, so
   a grid of text reads as light on water.
"""
import math
import random

# ── Canvas and timing ──────────────────────────────────────────────────────────────────────────
COLS, ROWS = 112, 36          # character cells; each cell is 9 x 18 pixels in the player
FPS = 15
BPM = 80                      # the rain falls on a musical grid that score.py shares
BARS = 8
BEAT = 60 / BPM
LOOP_SECONDS = BARS * 4 * BEAT        # 24 seconds
FRAMES = round(LOOP_SECONDS * FPS)    # 360 frames
BACKGROUND = "#05080f"

# The water is simulated on square "pixels". A cell is twice as tall as it is wide, so each cell
# covers one simulation column and two simulation rows.
W, H = COLS, ROWS * 2
SUBSTEPS = 4                  # wave steps per frame; more steps make the ripples travel further
C2 = 0.24                     # (wave speed)^2 per step; must stay below 0.5 for the grid to be stable
DAMPING = 0.978               # each step keeps 97.8% of the motion, so a ripple fades in about 3 s

SEED = 1907


# ── The rain schedule ──────────────────────────────────────────────────────────────────────────
def rain_schedule(seed=SEED):
    """Return drops as (time in seconds, x, y, size) on a sixteenth-note grid.

    The density per bar makes the shower swell and fade. The last bar and a half stay dry, so the
    pond is calm again when the loop wraps around to the first drop.
    """
    rng = random.Random(seed)
    density = [0.12, 0.28, 0.5, 0.8, 0.95, 0.6, 0.3, 0.0]
    sixteenth = BEAT / 4
    drops = [(0.0, 70.0, 30.0, 1.0)]  # one large drop into the moon to begin
    for bar, chance in enumerate(density):
        for slot in range(16):
            if bar == 0 and slot == 0:
                continue
            if bar == 6 and slot >= 8:
                break  # dry from the middle of bar 7
            # In heavy bars a slot can hold two drops: the second gets whatever chance is above 0.5.
            for odds in (chance, chance - 0.5):
                if rng.random() < odds:
                    t = (bar * 16 + slot) * sixteenth
                    x = rng.uniform(6, W - 6)
                    y = rng.uniform(6, H - 6)
                    size = rng.choice([0.45, 0.6, 0.75, 1.0])
                    drops.append((t, x, y, size))
    return drops


DROPS = rain_schedule()


# ── The pond's furniture ───────────────────────────────────────────────────────────────────────
MOON = (70.0, 30.0, 9.5)                       # centre x, centre y, radius, in simulation pixels
PADS = [(18, 14, 8.5, 0.6), (30, 58, 7.0, 3.6), (97, 60, 9.0, 2.2)]  # x, y, radius, notch angle


def make_stars(seed=SEED):
    rng = random.Random(seed + 1)
    return [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.25, 0.6)) for _ in range(26)]


STARS = make_stars()


def on_pad(x, y):
    """Return the pad a point lies on, or None. Each pad is a disc with a wedge cut out."""
    for i, (px, py, r, notch) in enumerate(PADS):
        dx, dy = x - px, y - py
        if dx * dx + dy * dy <= r * r:
            angle = math.atan2(dy, dx)
            gap = (angle - notch + math.pi) % (2 * math.pi) - math.pi
            if abs(gap) > 0.32 or dx * dx + dy * dy < 1.5:
                return i
    return None


# ── 1. The wave equation ───────────────────────────────────────────────────────────────────────
def strike(u, x, y, size):
    """A drop pushes a small Gaussian dimple into the surface."""
    radius = 1.4 + size
    for j in range(max(1, int(y - 4)), min(H - 1, int(y + 5))):
        for i in range(max(1, int(x - 4)), min(W - 1, int(x + 5))):
            d2 = (i - x) ** 2 + (j - y) ** 2
            u[j][i] -= 2.6 * size * math.exp(-d2 / (radius * radius))


def wave_step(u, prev):
    """One leapfrog step of u_tt = c^2 (u_xx + u_yy), with damping. Edges are held still."""
    nxt = [[0.0] * W for _ in range(H)]
    for j in range(1, H - 1):
        up, row, down, old, out = u[j - 1], u[j], u[j + 1], prev[j], nxt[j]
        for i in range(1, W - 1):
            laplacian = up[i] + down[i] + row[i - 1] + row[i + 1] - 4 * row[i]
            out[i] = (2 * row[i] - old[i] + C2 * laplacian) * DAMPING
    return nxt


def swell(x, y, t):
    """A faint breeze swell. Its period divides the loop, so it wraps seamlessly."""
    phase = 2 * math.pi * t / (LOOP_SECONDS / 4)
    return 0.03 * math.sin(0.19 * x + 0.11 * y - phase) + 0.02 * math.sin(0.07 * x - 0.23 * y + phase)


def simulate():
    """Yield the height field for every frame of the loop."""
    u = [[0.0] * W for _ in range(H)]
    prev = [[0.0] * W for _ in range(H)]
    pending = sorted(DROPS)
    for frame in range(FRAMES):
        t = frame / FPS
        while pending and pending[0][0] <= t + 0.5 / FPS:
            _, x, y, size = pending.pop(0)
            if on_pad(x, y) is None:
                strike(u, x, y, size)
                strike(prev, x, y, size)  # same dimple in both, so it starts at rest
        for _ in range(SUBSTEPS):
            u, prev = wave_step(u, prev), u
        yield u


# ── 2. Displacement-mapped reflection ─────────────────────────────────────────────────────────
def sky(x, y):
    """Brightness and source of the sky seen at a point: the moon, a halo and a few stars."""
    mx, my, mr = MOON
    d = math.hypot(x - mx, y - my)
    if d < mr:
        # A bright disc that dims slightly toward its rim (limb darkening).
        return min(1.0, 0.97 - 0.25 * (d / mr) ** 4), "moon"
    halo = 0.22 * math.exp(-((d - mr) / 6.0) ** 2)
    star = 0.0
    for sx, sy, s in STARS:
        if abs(x - sx) < 0.6 and abs(y - sy) < 0.5:
            star = max(star, s)
    return (halo, "moon") if halo >= star else (star, "star")


def light(u, x, y, t):
    """Reflected brightness, its source (moon, star or glint) and slope at simulation pixel (x, y)."""
    xl, xr = max(x - 1, 0), min(x + 1, W - 1)
    yu, yd = max(y - 1, 0), min(y + 1, H - 1)
    gx = (u[y][xr] - u[y][xl]) / 2 + (swell(x + 1, y, t) - swell(x - 1, y, t)) / 2
    gy = (u[yd][x] - u[yu][x]) / 2 + (swell(x, y + 1, t) - swell(x, y - 1, t)) / 2
    # Look up the sky a few pixels away along the slope: that is the displacement map.
    b, kind = sky(x + 9 * gx, y + 9 * gy)
    # Ripple faces tilted toward the moonlight (which falls from the upper left) catch a glint,
    # and any steep slope shows a faint sheen, so each ring reads all the way round.
    glint = max(0.0, -(gx * 0.6 + gy * 0.8))
    sheen = min(0.68, 5.0 * glint + 2.0 * math.hypot(gx, gy))  # capped below the solid blocks
    if sheen > b:
        b, kind = sheen, "glint"
    return min(b, 1.0), kind, math.hypot(gx, gy)


# ── 3. Brightness ramps: from light to glyphs ────────────────────────────────────────────────
WATER_RAMP = " .·-~≈=≡▒▓█"
DARK_WATER = (22, 38, 62)
MOONLIGHT = (246, 232, 186)
STARLIGHT = (150, 182, 222)
PAD_DARK, PAD_LIT = (34, 72, 46), (98, 150, 88)


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


def quantize(value, steps):
    return round(max(0.0, min(1.0, value)) * steps) / steps


def water_cell(b, kind, slope):
    """Pick a glyph and colour for a cell of open water."""
    if kind == "star":
        return ("•" if b > 0.45 else "·"), mix(DARK_WATER, STARLIGHT, 0.4 + b)
    if b < 0.07:
        return " ", DARK_WATER
    b = quantize(b, 14)
    glyph = WATER_RAMP[max(1, min(len(WATER_RAMP) - 1, int(b * len(WATER_RAMP))))]
    tint = MOONLIGHT if kind == "moon" else STARLIGHT
    return glyph, mix(DARK_WATER, tint, 0.25 + 0.75 * b)


def pad_cell(u, pad, x, y, top, bottom):
    """A lily pad tilts with the water under it, so its shade follows the local slope.

    top and bottom say which half of the cell the pad covers; half blocks keep its edge round.
    """
    tilt = (u[min(y + 2, H - 1)][x] - u[max(y - 1, 0)][x]) * 3
    shade = quantize(0.5 + tilt, 5)
    glyph = "█" if top and bottom else "▀" if top else "▄"
    return glyph, mix(PAD_DARK, PAD_LIT, shade)


def splash_cells(t):
    """Bright splash glyphs for one frame after each impact."""
    marks = {}
    for dt, x, y, size in DROPS:
        age = t - dt
        if 0 <= age < 1.5 / FPS and on_pad(x, y) is None:
            marks[(int(x), int(y) // 2)] = ("*" if size > 0.7 else "°", (236, 240, 248))
    return marks


def frames():
    """Yield each frame as a list of rows, each row a list of (glyph, (r, g, b)) cells."""
    for frame, u in enumerate(simulate()):
        t = frame / FPS
        marks = splash_cells(t)
        picture = []
        for row in range(ROWS):
            line = []
            for col in range(COLS):
                if (col, row) in marks:
                    line.append(marks[(col, row)])
                    continue
                y0, y1 = 2 * row, 2 * row + 1
                top, bottom = on_pad(col + 0.5, y0 + 0.5), on_pad(col + 0.5, y1 + 0.5)
                if top is not None or bottom is not None:
                    line.append(pad_cell(u, top if top is not None else bottom, col, y0,
                                         top is not None, bottom is not None))
                    continue
                # Average the two simulation rows that share this cell.
                b0, k0, s0 = light(u, col, y0, t)
                b1, k1, s1 = light(u, col, y1, t)
                kind = "star" if "star" in (k0, k1) else k0 if b0 >= b1 else k1
                line.append(water_cell(max(b0, b1) if kind == "star" else (b0 + b1) / 2, kind, max(s0, s1)))
            picture.append(line)
        yield picture


if __name__ == "__main__":
    # Print the first frame as plain text, a quick look without the player.
    for line in next(frames()):
        print("".join(glyph for glyph, _ in line))
