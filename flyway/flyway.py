#!/usr/bin/env python3
"""Flyway — a heron flies home over a whole day.

A grey heron lifts out of a reedbed at dawn, crosses open fields and the
sea, and comes down again at dusk to the same reeds. Four acts, one loop:
dawn wetlands, open country, the sea, dusk home. The light travels with
her — gold, blue, pale haze, violet — and the ground scrolls beneath her
wings. The picture is drawn on a dot canvas (two dots across, four down
per cell) and folded into Braille, so the bird keeps her curves.

120x44, 24 fps, 512 frames (21 1/3 s). The score in score.py is the same
journey in sound: wingbeats, a dawn chorus, a modal melody that changes
with the country, the sea, and the dawn theme coming home.
"""
import math
import sys

import numpy as np

W, H = 120, 44
DW, DH = 2 * W, 4 * H
FPS, FRAMES = 24, 512
ACT = FRAMES // 4          # 128 frames per act
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint8)

# The sky in four acts: (top, mid, horizon). The loop returns to dawn.
SKY = [
    ((26, 30, 58), (74, 62, 88), (214, 138, 74)),     # dawn wetlands
    ((58, 110, 168), (116, 158, 198), (196, 214, 226)),  # open country
    ((96, 130, 152), (150, 172, 186), (214, 200, 170)),  # the sea
    ((24, 20, 52), (72, 46, 92), (196, 96, 64)),      # dusk home
]
# The sun's colour follows the same acts.
SUN = [(240, 190, 90), (250, 240, 210), (244, 196, 120), (240, 140, 60)]

_rng = np.random.default_rng(417)
# Stars, waiting for dusk.
STARS = [(float(x), float(y), float(_rng.random()))
         for x, y in zip(_rng.integers(0, DW, 70), _rng.integers(2, 60, 70))]
# Fireflies over the dawn reeds.
FLIES = [(float(x), float(y), float(_rng.random() * 2 * math.pi))
         for x, y in zip(_rng.integers(20, DW - 20, 14), _rng.integers(120, 160, 14))]
# Reeds, placed in world coordinates so the ground scrolls past.
REEDS = [(float(x), float(_rng.uniform(20, 44))) for x in
         sorted(_rng.uniform(0, 900, 60))]
# Gull paths over the sea.
GULLS = [(float(_rng.uniform(0, DW)), float(_rng.uniform(20, 60)),
          float(_rng.uniform(0.15, 0.3))) for _ in range(3)]
# Glints on the water: seeded world positions, twinkling as they drift past.
GLINTS = [(float(x), int(r), float(_rng.random()))
          for x, r in zip(_rng.uniform(0, 900, 42), _rng.integers(33, 44, 42))]

# The heron's colours.
BODY = (138, 151, 168)
BODY_DARK = (96, 108, 126)
NECK = (228, 226, 220)
BEAK = (216, 169, 58)
CAP = (24, 24, 28)
LEG = (52, 48, 44)
WING = (112, 126, 145)
WING_DARK = (84, 96, 114)

# Flap schedule: the phase accumulates at a rate that eases — hard beats
# for the takeoff, a steady cruise, then a long glide into the landing.
# Offset by half a beat so the loop opens with her wings raised.
_FLAP_RATE = np.ones(FRAMES) / 32.0
_FLAP_RATE[:64] = 1 / 24.0
_FLAP_RATE[448:] = np.linspace(1 / 32.0, 0.0, FRAMES - 448)
_FLAP_PHASE = (np.cumsum(_FLAP_RATE) + 0.5) % 1.0
_FLAP_AMP = np.full(FRAMES, 40.0)
_FLAP_AMP[:64] = 48.0
_FLAP_AMP[448:] = np.linspace(40.0, 0.0, FRAMES - 448)


def _act_blend(n):
    """(act, next act, blend 0..1) — a 24-frame crossfade at each boundary."""
    pos = (n % FRAMES) / ACT
    act = int(pos) % 4
    frac = pos - int(pos)
    if frac > 1 - 24 / ACT:
        return act, (act + 1) % 4, (frac - (1 - 24 / ACT)) / (24 / ACT)
    return act, act, 0.0


def _lerp(a, b, t):
    return tuple(float(x) + (float(y) - float(x)) * t for x, y in zip(a, b))


def fill_triangle(lit, ink, p0, p1, p2, color):
    pts = sorted([p0, p1, p2], key=lambda p: p[1])
    (x0, y0), (x1, y1), (x2, y2) = pts
    if y2 == y0:
        return
    for y in range(max(0, int(math.ceil(y0))), min(DH, int(y2) + 1)):
        if y < y1:
            xa = x0 + (x1 - x0) * (y - y0) / (y1 - y0) if y1 != y0 else x0
            xb = x0 + (x2 - x0) * (y - y0) / (y2 - y0)
        else:
            xa = x1 + (x2 - x1) * (y - y1) / (y2 - y1) if y2 != y1 else x1
            xb = x0 + (x2 - x0) * (y - y0) / (y2 - y0)
        for x in range(max(0, int(math.ceil(min(xa, xb)))), min(DW, int(max(xa, xb)) + 1)):
            lit[y, x] = True
            ink[y, x] = color


def ellipse(lit, ink, cx, cy, rx, ry, color, tilt=0.0):
    ct, st = math.cos(tilt), math.sin(tilt)
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            dx, dy = x - cx, y - cy
            ex = dx * ct + dy * st
            ey = -dx * st + dy * ct
            if (ex / rx) ** 2 + (ey / ry) ** 2 <= 1 and 0 <= x < DW and 0 <= y < DH:
                lit[y, x] = True
                ink[y, x] = color


def thick_line(lit, ink, x0, y0, x1, y1, w, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        for dy in range(-w, w + 1):
            for dx in range(-w, w + 1):
                xx, yy = int(round(x + dx)), int(round(y + dy))
                if 0 <= xx < DW and 0 <= yy < DH:
                    lit[yy, xx] = True
                    ink[yy, xx] = color


def wing(lit, ink, sx, sy, angle_deg, length, color, dark):
    """One broad wing: a quad from a wide root at the shoulder to the tip."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    tx = sx + length * ca
    ty = sy + length * sa
    ax, ay = sx + 10, sy - 2
    dx, dy = sx - 6, sy + 5
    px = sx + 0.5 * length * ca - 16 * sa
    py = sy + 0.5 * length * sa + 16 * ca
    fill_triangle(lit, ink, (ax, ay), (tx, ty), (px, py), color)
    fill_triangle(lit, ink, (ax, ay), (px, py), (dx, dy), color)
    for f in (0.4, 0.7):
        ex = sx + f * (tx - sx)
        ey = sy + f * (ty - sy)
        bx = sx + f * (px - sx) * 0.85
        by = sy + f * (py - sy) * 0.85
        thick_line(lit, ink, ex, ey, bx, by, 0, dark)


def heron(lit, ink, n):
    """The bird, drawn over the sky. @marker heron"""
    phase = _FLAP_PHASE[n]
    amp = _FLAP_AMP[n]
    # Low over the reeds at both ends of the loop, high in the middle.
    cy = 74 + 24 * math.cos(2 * math.pi * n / FRAMES)
    cx = 110
    bob = 3 * math.sin(2 * math.pi * n / 256)
    cy += bob
    ang = 180 - amp * math.sin(2 * math.pi * phase + math.pi / 2)
    # Far wing first (darker, shorter, behind the body).
    wing(lit, ink, cx - 2, cy - 6, ang, 34, WING_DARK, BODY_DARK)
    # Legs trailing behind; they drop for the landing glide.
    drop = max(0.0, (n - 448) / 64.0) * 6
    thick_line(lit, ink, cx - 24, cy + 5, cx - 44, cy + 15 + drop, 0, LEG)
    thick_line(lit, ink, cx - 22, cy + 6, cx - 42, cy + 18 + drop, 0, LEG)
    # Body, tilted nose-up a touch.
    ellipse(lit, ink, cx, cy, 26, 9, BODY, tilt=-0.10)
    # Neck folded back over the shoulders.
    thick_line(lit, ink, cx + 22, cy - 4, cx + 30, cy - 14, 3, NECK)
    ellipse(lit, ink, cx + 34, cy - 15, 6, 4, NECK)
    # Black cap and eye.
    thick_line(lit, ink, cx + 29, cy - 19, cx + 39, cy - 18, 1, CAP)
    lit[int(cy - 16), int(cx + 36)] = True
    ink[int(cy - 16), int(cx + 36)] = CAP
    # Long pointed beak.
    fill_triangle(lit, ink, (cx + 39, cy - 17), (cx + 39, cy - 13), (cx + 55, cy - 15), BEAK)
    # Near wing over the body.
    wing(lit, ink, cx, cy - 5, ang, 46, WING, WING_DARK)


def frame(n):
    lit = np.zeros((DH, DW), bool)
    ink = np.zeros((DH, DW, 3))
    solid = np.zeros((H, W), np.uint16)
    paint = np.zeros((H, W, 3))
    act, nxt, blend = _act_blend(n)
    t = n / FRAMES

    # The sky: a dot gradient, dithered — dense near the horizon, sparse
    # overhead — so the sky glows and the bird still reads against it. A
    # fully lit sky would fold every cell to a solid block and swallow her.
    # @marker sky
    top = _lerp(SKY[act][0], SKY[nxt][0], blend)
    mid = _lerp(SKY[act][1], SKY[nxt][1], blend)
    hor = _lerp(SKY[act][2], SKY[nxt][2], blend)
    rows = np.arange(DH)
    grad = np.zeros((DH, 3))
    for ch in range(3):
        grad[:, ch] = np.interp(rows, [0, DH * 0.55, DH * 0.78],
                                [top[ch], mid[ch], hor[ch]])
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6],
                      [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    density = np.linspace(0.32, 0.8, DH)[:, None]
    dither = bayer[np.arange(DH)[:, None] % 4, np.arange(DW)[None, :] % 4] < density
    lit[:, :] = dither
    ink[:, :, :] = grad[:, None, :]

    # The sun arcs across the loop: low gold at dawn, high and pale at
    # midday, low orange at dusk. Drawn as dots, an ellipse in dot space —
    # cells are taller than wide, so a round sun on screen is a tall
    # ellipse here — and the bird's dots can cross in front of it.
    # @marker sun
    sun_x = 30 + 180 * t
    sun_y = 108 - 72 * math.sin(math.pi * t)
    sun_c = _lerp(SUN[act], SUN[nxt], blend)
    # Clear the sky dither in and just around the disc, so its edge folds
    # to a true curve instead of a block of solid cells.
    for y in range(int(sun_y) - 11, int(sun_y) + 12):
        for x in range(int(sun_x) - 10, int(sun_x) + 11):
            if not (0 <= x < DW and 0 <= y < DH):
                continue
            d = ((x - sun_x) / 7.0) ** 2 + ((y - sun_y) / 8.0) ** 2
            if d <= 1.44:
                lit[y, x] = False
            if d <= 1.0:
                lit[y, x] = True
                ink[y, x] = sun_c

    # Stars fade in over dusk. @marker stars
    if act == 3 or (act == 2 and blend > 0):
        strength = blend if act == 2 else min(1.0, (n - 384) / 64.0)
        for x, y, tw in STARS:
            glow = strength * (0.6 + 0.4 * math.sin(2 * math.pi * (t * 2 + tw)))
            if glow > 0.3:
                lit[int(y), int(x)] = True
                ink[int(y), int(x)] = (200 + 55 * glow, 200 + 55 * glow, 220)

    # Gulls over the sea. @marker gulls
    if act == 2:
        for gx, gy, speed in GULLS:
            x = (gx + n * speed) % DW
            y = gy + 3 * math.sin(2 * math.pi * (n / 128 + gx))
            for dx, dy in ((-3, -1), (-2, 0), (-1, 1), (0, 1), (1, 0), (2, -1), (3, -2)):
                xx, yy = int(x + dx), int(y + dy)
                if 0 <= xx < DW and 0 <= yy < DH:
                    lit[yy, xx] = True
                    ink[yy, xx] = (232, 232, 228)

    # Fireflies over the dawn reeds. @marker fireflies
    if act == 0:
        for x, y, ph in FLIES:
            fx = x + 4 * math.sin(2 * math.pi * (t * 3 + ph))
            fy = y + 3 * math.sin(2 * math.pi * (t * 2 + ph * 2))
            glow = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 4 + ph))
            if glow > 0.4:
                lit[int(fy), int(fx)] = True
                ink[int(fy), int(fx)] = (220, 220, 120 + 80 * glow)

    # The ground scrolls beneath her. Solid cells are the ground and
    # water; shimmer lives in their paint, because dots hide behind solids.
    # @marker ground
    scroll = n * 0.9
    ground_top = 128  # dots; row 32 in cells
    if act in (0, 3):
        # Reedbed water, with mist lying low over it.
        water = np.array((16, 44, 52)) if act == 0 else np.array((28, 26, 52))
        glint = np.array((120, 150, 170)) if act == 0 else np.array((150, 110, 90))
        for r in range(32, H):
            for c in range(W):
                solid[r, c] = ord("█")
                depth = (r - 32) / 12
                col = water * (1 - 0.25 * depth)
                # At dusk the setting sun lays a road of light on the water.
                if act == 3:
                    spread = 4 + (r - 32)
                    d = abs(c - sun_x / 2) / spread
                    if d < 1:
                        col = col * d + np.array((214, 130, 60)) * (1 - d) * 0.8
                paint[r, c] = col
        # Glints drifting past on the water.
        for wx, r, ph in GLINTS:
            c = int(((wx - scroll) % DW) / 2)
            if 0.5 + 0.5 * math.sin(2 * math.pi * (t * 2 + ph)) > 0.6:
                paint[r, c] = glint
        # Reeds, dark against the light, two dots wide with seed heads.
        reed_c = (38, 74, 52) if act == 0 else (24, 34, 40)
        head_c = (180, 150, 80) if act == 0 else (120, 90, 60)
        for wx, hgt in REEDS:
            x = (wx - scroll) % 900
            if x > DW - 1:
                continue
            for y in range(int(ground_top - hgt), ground_top + 8):
                for dx in (0, 1):
                    if 0 <= int(x) + dx < DW:
                        lit[y, int(x) + dx] = True
                        ink[y, int(x) + dx] = reed_c
            lit[int(ground_top - hgt), int(x)] = True
            ink[int(ground_top - hgt), int(x)] = head_c
        # Mist: soft horizontal bands drifting over the water.
        for y in range(124, 136, 2):
            for x in range(DW):
                if (x + n // 2) % 23 < 9 and (x * y) % 7 < 3:
                    lit[y, x] = True
                    ink[y, x] = (150, 160, 170) if act == 0 else (120, 90, 110)
    elif act == 1:
        # Open country: rolling fields in patchwork, hedgerows, a river.
        for c in range(W):
            wx = c * 2 + scroll
            hill = 4 * math.sin(wx / 55) + 2 * math.sin(wx / 23 + 1.7)
            top = int(ground_top + hill * 2)
            patch = int(wx // 42) % 3
            field = [(74, 110, 62), (96, 128, 70), (168, 148, 84)][patch]
            for r in range(top // 4, H):
                solid[r, c] = ord("█")
                paint[r, c] = np.array(field) * (0.75 + 0.25 * (r / H))
            # Hedgerow along the profile.
            r = top // 4
            if 0 <= r < H:
                solid[r, c] = ord("▀")
                paint[r, c] = (30, 52, 34)
        # The river winds through the fields.
        for c in range(W):
            wx = c * 2 + scroll
            ry = 152 + 5 * math.sin(wx / 40)
            for y in range(int(ry) - 1, int(ry) + 2):
                r = y // 4
                if 0 <= r < H:
                    solid[r, c] = ord("█")
                    paint[r, c] = (52, 96, 138)
    else:
        # The sea: glittering water to the horizon, cliffs at the end.
        for r in range(32, H):
            for c in range(W):
                solid[r, c] = ord("█")
                col = np.array((24, 64, 92), dtype=float)
                if r == 32:
                    col = np.array((120, 150, 170), dtype=float)  # horizon light
                paint[r, c] = col
        for wx, r, ph in GLINTS:
            c = int(((wx - scroll) % DW) / 2)
            if 0.5 + 0.5 * math.sin(2 * math.pi * (t * 2 + ph)) > 0.6:
                paint[r, c] = (180, 210, 230)
        # Cliffs rise on the right as the act ends.
        rise = max(0.0, (n - 320) / 64.0)
        if rise > 0:
            for c in range(W):
                wx = c * 2 + scroll
                cliff = 150 - 26 * rise * max(0.0, math.sin(wx / 90 + 2.0))
                for r in range(int(cliff) // 4, H):
                    solid[r, c] = ord("█")
                    paint[r, c] = (52, 52, 58)

    heron(lit, ink, n)
    return cells(lit, ink, solid, paint)


def cells(lit, ink, solid, paint):
    """Fold the dot canvas into Braille cells, then lay solid cells over it."""
    l = lit.reshape(H, 4, W, 2)
    bits = (l * BITS[None, :, None, :]).sum(axis=(1, 3))
    count = np.maximum(1, l.sum(axis=(1, 3)))
    rgb = (ink * lit[..., None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3)) / count[..., None]
    ch = np.where(bits > 0, 0x2800 + bits, 32).astype(np.uint16)
    ch[bits == 255] = ord("█")
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
    n = int(sys.argv[1]) % FRAMES if len(sys.argv) > 1 else 0
    ch, rgb = frame(n)
    print(f"frame {n}: {len(np.unique(ch))} distinct chars, "
          f"{len(np.unique(rgb.reshape(-1, 3), axis=0))} distinct colors")
