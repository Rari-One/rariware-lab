"""Night Carol — the picture. The carol is written across the sky as it is sung.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

The sky works like a sheet of music turned into stars. Left to right is time,
from the first word to the last. Up and down is pitch: every semitone is a
little under three dots higher. Each note becomes a star the moment it is sung,
and a fine trail shows how long it is held. Each voice joins its own stars
into a constellation, so the four lines of the harmony can be followed by eye:

    soprano gold, alto white, tenor green, bass red

On the last "Noel" every star of the carol flies into one star above the
church. While the bells open the next round, that star melts into snow, and
the sky is empty again for the first word.

Preview a still in a 24-bit color terminal:  python sky.py [frame]
"""
import math
import sys

import numpy as np

from carol import BAR, BEAT, FRAMES, LINES, PARTS, SUNG, frame_of
from choir import presence

W, H = 132, 44
DW, DH = W * 2, H * 4                     # 264 x 176 Braille dots
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint16)
BG = np.array([6, 9, 22], float)
TAU = 2 * math.pi
COLORS = {"soprano": np.array([255, 206, 110.]), "alto": np.array([226, 234, 248.]),
          "tenor": np.array([118, 214, 150.]), "bass": np.array([238, 96, 96.])}
HORIZON = 132                             # dot row where the hills begin
CHURCH_X = 132
STAR = (CHURCH_X, 44)                     # where the carol gathers on the last "Noel"
GATHER = (frame_of(17, 0.75), frame_of(17, 3.6))
MELT = (0, 2 * BAR - 4)                   # the star melts into snow over the bells' bars
GLOW = presence()
rng = np.random.default_rng(24)


def pitch_y(note):
    """The staff: MIDI 40 (low E) sits just above the hills, MIDI 79 near the top."""
    return HORIZON - 10 - (note - 40) * 2.75


def beat_x(bar, beat):
    """Time runs left to right from the first sung word (bar 3) to the end of bar 18."""
    return 14 + ((4 * bar + beat) - 8) / 64 * (DW - 28)


# Every note of every part, as a star with a home in the sky.
STARS = []
for part in PARTS:
    for note in SUNG:
        STARS.append(dict(part=part, x=beat_x(note["bar"], note["beat"]),
                          x_end=beat_x(note["bar"], note["beat"] + note["beats"]) - 1,
                          y=pitch_y(note["notes"][part]), start=frame_of(note["bar"], note["beat"]),
                          end=frame_of(note["bar"], note["beat"] + note["beats"])))


def outline(t):
    """A point on an eight-pointed star, t from 0 to 1 around its edge."""
    corners = []
    for k in range(16):
        r = 30 if k % 2 == 0 else 11
        a = -math.pi / 2 + k * math.pi / 8
        corners.append((STAR[0] + r * math.cos(a) * 1.0, STAR[1] + r * math.sin(a)))
    pos = t * 16
    i = int(pos) % 16
    f = pos - int(pos)
    (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 16]
    return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f


# Each star's place in the final shape, spread evenly around the edge.
for i, star in enumerate(sorted(STARS, key=lambda s: (s["x"], s["y"]))):
    star["home"] = outline(i / len(STARS))
    star["drift"] = rng.uniform(-1, 1)
    star["fall"] = rng.uniform(0.7, 1.3)

FLAKES = [(rng.uniform(0, DW), rng.uniform(0, 1), int(rng.integers(3, 7)), rng.uniform(0.4, 1)) for _ in range(80)]
BACKGROUND = [(rng.uniform(0, DW), rng.uniform(0, HORIZON - 8), rng.uniform(), int(rng.integers(4, 12)))
              for _ in range(70)]
HOUSES = [(28, 14, 10), (52, 12, 8), (74, 16, 11), (190, 14, 9), (214, 18, 12), (240, 12, 8)]
PINES = [(10, 18), (44, 12), (96, 16), (104, 11), (168, 15), (178, 10), (232, 13), (256, 17)]


def hill(x):
    return HORIZON + 6 + 5 * math.sin(x * 0.031) + 3 * math.sin(x * 0.083 + 1)


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Canvas:
    def __init__(self):
        self.lit = np.zeros((DH, DW), bool)
        self.ink = np.zeros((DH, DW, 3))

    def dot(self, x, y, color):
        r, c = int(round(y)), int(round(x))
        if 0 <= r < DH and 0 <= c < DW:
            self.lit[r, c] = True
            self.ink[r, c] = np.clip(color, 0, 255)

    def line(self, x0, y0, x1, y1, color, every=1):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(0, steps, every):
            f = k / max(1, steps - 1)
            self.dot(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, color)


def frame(n):
    canvas = Canvas()
    yy, xx = np.mgrid[:DH, :DW]

    # Background stars, each twinkling a whole number of times per loop.
    for x, y, phase, cycles in BACKGROUND:
        level = 0.35 + 0.3 * math.sin(TAU * (phase + cycles * n / FRAMES))
        canvas.dot(x, y, np.array([150, 160, 200]) * level)

    # The written carol: trails for held notes, constellation lines, then stars.
    gather = ease((n - GATHER[0]) / (GATHER[1] - GATHER[0])) if n >= GATHER[0] else 0.0
    melt = ease((n - MELT[0]) / (MELT[1] - MELT[0])) if n < MELT[1] else None
    by_part = {part: [s for s in STARS if s["part"] == part] for part in PARTS}
    for part, stars in by_part.items():
        color = COLORS[part]
        sung = [s for s in stars if s["start"] <= n]
        if melt is None and gather < 1:
            fade = 1 - gather
            for a, b in zip(sung, sung[1:]):
                canvas.line(a["x"], a["y"], b["x"], b["y"], color * 0.16 * fade, every=3)
            for s in sung:
                end = s["x"] + (s["x_end"] - s["x"]) * min(1, (n - s["start"]) / max(1, s["end"] - s["start"]))
                canvas.line(s["x"] + 3, s["y"], end, s["y"], color * 0.3 * fade, every=2)
        for s in sung if melt is None else stars:
            if melt is None:
                age = n - s["start"]
                hx, hy = s["home"]
                x = s["x"] + (hx - s["x"]) * gather
                y = s["y"] + (hy - s["y"]) * gather
                bright = 1.0 + 0.9 * math.exp(-age / 4)
            else:
                # The star melts: each point drifts down as a snowflake and fades.
                hx, hy = s["home"]
                x = hx + s["drift"] * 14 * melt + 2 * math.sin(n * 0.2 + s["drift"] * 9) * melt
                y = hy + (HORIZON - hy) * melt * s["fall"]
                bright = (1.15 - melt) * (0.9 + 0.3 * math.sin(n * 0.4 + s["drift"] * 7))
                if bright <= 0.02:
                    continue
            # A star is a little plus sign of dots; a new note flares to twice the size.
            c = np.clip(color * min(bright, 1.25) + 40 * max(0.0, bright - 1), 0, 255)
            arm = 2 if bright > 1.3 or (s["part"] == "soprano" and melt is None) else 1
            canvas.dot(x, y, np.minimum(c * 1.15 + 20, 255))
            if bright > 0.4 and (melt is None or melt < 0.5):
                for r in range(1, arm + 1):
                    for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r)):
                        canvas.dot(x + dx, y + dy, c * (0.8 if r == 1 else 0.45))

    # Once gathered, the star shines from its centre.
    shine = gather if melt is None else max(0.0, 1 - melt * 1.4)
    if shine > 0:
        r = np.hypot(xx - STAR[0], yy - STAR[1])
        core = (r < 6 * shine + 1) & (np.random.default_rng(n % 9).random((DH, DW)) < 0.8)
        canvas.lit[core] = True
        canvas.ink[core] = np.array([255, 238, 190]) * min(1, shine * 1.3)
        for k in range(8):
            a = -math.pi / 2 + k * math.pi / 4
            reach = (40 if k % 2 == 0 else 22) * shine
            canvas.line(STAR[0], STAR[1], STAR[0] + reach * math.cos(a), STAR[1] + reach * math.sin(a),
                        np.array([255, 226, 150]) * 0.45 * shine, every=2)

    # The "now" line: where the choir is in the carol, while it sings.
    now = (n / BEAT) / 4
    if 2 <= now < 18 and gather == 0:
        nx = beat_x(int(now), (now - int(now)) * 4)
        for y in range(6, HORIZON - 4, 3):
            canvas.dot(nx, y, np.array([90, 100, 140]) * (0.5 + 0.5 * math.sin(y * 0.3 + n * 0.5)))

    # Snowy hills.
    ground = np.array([hill(x) for x in range(DW)])
    snow = yy >= ground[None, :]
    texture = np.sin(xx * 12.9898 + yy * 78.233) * 43758.5453
    texture -= np.floor(texture)
    depth = yy - ground[None, :]
    canvas.lit[snow] = False
    fill = snow & (texture < 0.55 * np.exp(-depth / 18) + 0.12)
    canvas.lit |= fill
    canvas.ink[fill] = np.array([196, 210, 236]) * np.clip(1 - depth / 60, 0.35, 1)[..., None][fill]

    # Pines on the hills, dark with snow on their shoulders.
    for px, h in PINES:
        base = hill(px)
        for t in range(h):
            half = t * 0.35
            for u in np.arange(-half, half + 0.5):
                white = (t % 4 == 0) and abs(u) > half - 1.5
                canvas.dot(px + u, base - h + t, (200, 214, 236) if white else (28, 60, 46))

    # The village: houses with lit windows and snow on the roofs.
    for hx, w, h in HOUSES:
        base = hill(hx + w / 2) + 1
        for u in range(w + 1):
            roof = h + (w / 2 - abs(u - w / 2)) * 0.7
            canvas.dot(hx + u, base - roof, (214, 226, 244))
            canvas.dot(hx + u, base - roof + 1, (150, 162, 186))
        for t in range(int(h)):
            canvas.dot(hx, base - t, (70, 66, 84))
            canvas.dot(hx + w, base - t, (70, 66, 84))
        for wx in (hx + 3, hx + w - 4):
            flicker = 0.85 + 0.15 * math.sin(TAU * 7 * n / FRAMES + wx)
            for u in range(2):
                for v in range(3):
                    canvas.dot(wx + u, base - h + 4 + v, np.array([255, 196, 104]) * flicker)

    # The church, its door open and its windows warm, under the steeple.
    base = hill(CHURCH_X) + 1
    left, right, wall = CHURCH_X - 16, CHURCH_X + 16, 20
    for t in range(wall):
        canvas.dot(left, base - t, (90, 86, 104))
        canvas.dot(right, base - t, (90, 86, 104))
    for u in range(left - 2, right + 3):
        roof = wall + (18 - abs(u - CHURCH_X)) * 0.55
        canvas.dot(u, base - roof, (218, 230, 248))
    for t in range(44):
        canvas.dot(CHURCH_X - 4, base - wall - 6 - t, (90, 86, 104))
        canvas.dot(CHURCH_X + 4, base - wall - 6 - t, (90, 86, 104))
    for t in range(16):
        canvas.dot(CHURCH_X - 4 + t / 4, base - wall - 50 - t, (218, 230, 248))
        canvas.dot(CHURCH_X + 4 - t / 4, base - wall - 50 - t, (218, 230, 248))
    singing = max(GLOW[p][n] for p in PARTS)
    for u in range(-2, 3):
        for v in range(4):
            canvas.dot(CHURCH_X + u, base - wall - 40 + v, np.array([255, 200, 120]) * (0.45 + 0.55 * singing))
    for wx in (left + 5, right - 6):
        for u in range(3):
            for v in range(6):
                canvas.dot(wx + u, base - 14 + v, (255, 186, 96))
    for u in range(-3, 4):
        for v in range(8):
            canvas.dot(CHURCH_X + u, base - 8 + v, np.array([255, 170, 80]) * (0.7 if abs(u) < 3 else 0.4))

    # Four carolers by the door, each lantern glowing with its own voice.
    for k, part in enumerate(PARTS):
        cx = CHURCH_X - 38 + k * 10 + (0 if k < 2 else 56)
        foot = hill(cx) + 4
        canvas.lit[int(foot - 16):int(foot + 1), int(cx - 5):int(cx + 6)] = False   # trodden snow
        cloak = COLORS[part] * 0.55
        for t in range(9):                                   # a cloak, wider at the hem
            for u in np.arange(-1 - t * 0.4, 1 + t * 0.4 + 0.5):
                canvas.dot(cx + u, foot - 9 + t, cloak * (0.75 if abs(u) > t * 0.3 else 1))
        for u, v in ((0, -12), (1, -12), (0, -11), (1, -11), (-1, -11), (0, -10), (1, -10)):
            canvas.dot(cx + u, foot + v, (236, 208, 180) if v > -12 else cloak * 1.2)   # face, hood
        glow = GLOW[part][n]
        lx = cx + (4 if k < 2 else -4)
        canvas.line(cx + (1 if k < 2 else -1), foot - 7, lx, foot - 10, (120, 100, 80))   # arm and pole
        lantern = np.minimum(COLORS[part] * (0.45 + 0.75 * glow) + 30 * glow, 255)
        for u in (0, 1):
            for v in (0, 1, 2):
                canvas.dot(lx + u, foot - 10 + v, lantern)
        if glow > 0:
            for a in range(14):
                ang = TAU * a / 14 + n * 0.08
                canvas.dot(lx + 0.5 + 5 * math.cos(ang), foot - 9 + 4.5 * math.sin(ang), COLORS[part] * 0.5 * glow)

    # Snow falls in front of everything, each flake a whole number of times per loop.
    for x0, phase, cycles, depth in FLAKES:
        y = ((phase + cycles * n / FRAMES) % 1) * DH
        x = (x0 + 6 * math.sin(y * 0.05 + x0)) % DW
        canvas.dot(x, y, np.array([200, 212, 236]) * depth * 0.8)

    return cells(canvas, n)


def write(solid, paint, row, col, text, color):
    for k, ch in enumerate(text):
        if 0 <= col + k < W:
            solid[row, col + k] = ord(ch)
            paint[row, col + k] = np.clip(color, 0, 255)


def tokens(first_bar, last_bar):
    """The words of one line, with hyphens between the syllables of a word."""
    notes = [s for s in SUNG if first_bar - 1 <= s["bar"] <= last_bar - 1]
    joins = {"win", "o", "be", "can", "no"}
    out = []
    for i, s in enumerate(notes):
        bare = s["syllable"].strip(",.;").lower()
        nxt = notes[i + 1]["syllable"].lower() if i + 1 < len(notes) else ""
        hyphen = bare in joins and nxt[:1].isalpha() and not s["syllable"][-1] in ",.;"
        out.append((s, s["syllable"] + ("-" if hyphen else " ")))
    return out


def cells(canvas, n):
    """Fold the dots into Braille cells, then write the words and the voices."""
    l = canvas.lit.reshape(H, 4, W, 2)
    bits = (l * BITS[None, :, None, :]).sum(axis=(1, 3))
    count = np.maximum(1, l.sum(axis=(1, 3)))
    rgb = (canvas.ink * canvas.lit[..., None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3)) / count[..., None]
    ch = np.where(bits > 0, 0x2800 + bits, 32).astype(np.uint16)
    solid = np.zeros((H, W), np.uint16)
    paint = np.zeros((H, W, 3))
    solid[0] = 32
    solid[H - 2:] = 32

    # Header: the title, and where we are in the carol.
    bar = n // BAR + 1
    write(solid, paint, 0, 2, "N I G H T   C A R O L", (206, 182, 120))
    where = f"bar {bar:2d} of 18  ·  G major  ·  75 BPM"
    write(solid, paint, 0, W - 2 - len(where), where, (110, 120, 150))

    # The words, like a hymn book: sung syllables pale, the one being sung gold.
    line = next(((a, b) for a, b in LINES if a <= bar <= b), None)
    if line is None:
        text = "an original carol for four synthesized voices"
        write(solid, paint, H - 2, (W - len(text)) // 2, text, (150, 140, 120))
    else:
        parts = tokens(*line)
        text = "".join(t for _, t in parts).rstrip()
        col = (W - len(text)) // 2
        for s, t in parts:
            start = frame_of(s["bar"], s["beat"])
            end = frame_of(s["bar"], s["beat"] + s["beats"])
            color = (255, 214, 120) if start <= n < end else ((200, 208, 226) if n >= end else (84, 92, 116))
            write(solid, paint, H - 2, col, t, color)
            col += len(t)

    # Which voices are singing, in their colors.
    legend = [("● SOPRANO", "soprano"), ("● ALTO", "alto"), ("● TENOR", "tenor"), ("● BASS", "bass")]
    width = sum(len(t) for t, _ in legend) + 4 * (len(legend) - 1)
    col = (W - width) // 2
    for t, part in legend:
        write(solid, paint, H - 1, col, t, COLORS[part] * (0.35 + 0.65 * GLOW[part][n]))
        col += len(t) + 4

    ch = np.where(solid > 0, solid, ch)
    rgb = np.where((solid > 0)[..., None], paint, rgb)
    return ch, np.clip(rgb, 0, 255).round().astype(np.uint8)


def image(n):
    """One frame in the player's five-byte cells: UTF-16 code unit, then RGB."""
    ch, rgb = frame(n)
    out = np.zeros((H, W), dtype=[("c", "<u2"), ("r", "u1"), ("g", "u1"), ("b", "u1")])
    out["c"], out["r"], out["g"], out["b"] = ch, rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return out.tobytes()


if __name__ == "__main__":
    ch, rgb = frame(int(sys.argv[1]) % FRAMES if len(sys.argv) > 1 else 0)
    back = "\x1b[48;2;%d;%d;%dm" % tuple(BG.astype(int))
    for r in range(H):
        print(back + "".join("\x1b[38;2;%d;%d;%dm%s" % (*rgb[r, c], chr(ch[r, c])) for c in range(W))
              + "\x1b[0m")
