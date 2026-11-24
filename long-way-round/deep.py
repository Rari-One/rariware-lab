"""The Long Way Round — the living sea: a whale, jellyfish, a shoal and an anglerfish.

MIT License. Copyright (c) 2026 Rari-One. See LICENSE.txt.

Each creature moves a whole number of times per loop, so nothing jumps when
the minute starts again. They draw into the same dot canvas as the world.
"""
import math

import numpy as np

from journey import FRAMES

TAU = 2 * math.pi


def _patch(canvas, x0, y0, x1, y1):
    """World coordinates for the screen dots inside a world box, or None."""
    sx0, sy0 = canvas.screen(x0, y0)
    c0, c1 = int(max(0, math.floor(sx0))), int(min(canvas.lit.shape[1], math.ceil(sx0 + x1 - x0) + 1))
    r0, r1 = int(max(0, math.floor(sy0))), int(min(canvas.lit.shape[0], math.ceil(sy0 + y1 - y0) + 1))
    if c0 >= c1 or r0 >= r1:
        return None
    rows, cols = np.mgrid[r0:r1, c0:c1]
    return (slice(r0, r1), slice(c0, c1)), x0 + cols - sx0, y0 + rows - sy0


def whale(canvas, n):
    # The whale: a long silhouette that hides the water behind it.
    # It swims east just under the swell between frames 540 and 720.
    if not 530 <= n <= 730:
        return
    head = 1650 + 3.4 * (n - 540)
    top = 732 + 4 * math.sin(TAU * (n - 540) / 120)
    patch = _patch(canvas, head - 104, top - 16, head + 2, top + 16)
    if patch is None:
        return
    where, wx, wy = patch
    u = wx - (head - 96)                          # 0 at the tail stock, 96 at the snout
    flap = 4 * math.sin(TAU * n / 14)
    half = 10 * np.sqrt(np.clip(1 - ((u - 50) / 48) ** 2, 0, 1)) * np.clip(u / 26, 0.22, 1)
    v = wy - top - 1.5 * (u < 30) * flap * (30 - u) / 30
    body = (u >= 0) & (np.abs(v - 0.15 * half) <= half)
    fluke = (u < 2) & (u > -8) & (np.abs(v) <= (u + 8) * 1.2)
    fin = (np.abs(u - 62 + (v - 4) * 0.9) < 1.2) & (v > 4) & (v < 14)
    shape = body | fluke | fin
    inner = shape.copy()
    for shift, axis in ((1, 0), (-1, 0), (1, 1), (-1, 1)):
        inner &= np.roll(shape, shift, axis)
    outline = shape & ~inner
    grooves = body & (v > 0.45 * half) & (v.astype(int) % 2 == 0) & (u > 50) & (u < 88)
    eye = (np.abs(u - 84) < 1) & (np.abs(v - 1.5) < 1)
    lit, ink = canvas.lit[where], canvas.ink[where]
    lit[inner] = False
    for mask, color in ((outline, (92, 116, 146)), (grooves, (56, 72, 96)), (eye, (170, 190, 210))):
        lit[mask] = True
        ink[mask] = color


JELLIES = [(1915, 860, 7, (240, 120, 200), .1), (1990, 950, 9, (100, 220, 230), .45),
           (2060, 830, 6, (170, 130, 250), .7), (2105, 1000, 8, (240, 120, 200), .25),
           (2215, 900, 10, (250, 180, 90), .85), (2260, 1030, 6, (100, 220, 230), .6)]


def jellies(canvas, n):
    # Jellyfish: each bell pulses and drifts, trailing waving threads.
    for x, y, size, color, phase in JELLIES:
        bob = y + 10 * math.sin(TAU * (2 * n / FRAMES + phase))
        beat = 0.5 + 0.5 * math.sin(TAU * (28 * n / FRAMES + phase))
        rx, ry = size * (1 + 0.15 * beat), size * 0.7 * (1 - 0.1 * beat)
        patch = _patch(canvas, x - rx - 1, bob - ry - 1, x + rx + 1, bob + 1)
        if patch is not None:
            where, wx, wy = patch
            r = ((wx - x) / rx) ** 2 + ((wy - bob) / ry) ** 2
            bell = (r <= 1) & (wy <= bob)
            rim = bell & (r > 0.62)
            core = bell & ~rim & ((wx + wy).astype(int) % 3 == 0)
            glow = np.array(color) * (0.55 + 0.45 * beat)
            canvas.lit[where] |= rim | core
            canvas.ink[where][rim] = glow
            canvas.ink[where][core] = glow * 0.5
        for k in range(5):
            base = x + (k - 2) * rx * 0.35
            for t in range(int(size * 2.3)):
                sway = 2.5 * math.sin(0.25 * t - TAU * 10 * n / FRAMES + k)
                canvas.dot(base + sway * t / (size * 2.3), bob + 1 + t,
                           np.array(color) * (0.6 - 0.45 * t / (size * 2.3)))


def shoal(canvas, n):
    # Fish: a shoal circles the open water, turning together.
    cx = 2000 + 200 * math.cos(TAU * 2 * n / FRAMES)
    cy = 800 + 35 * math.sin(TAU * 3 * n / FRAMES)
    heading = -1 if math.sin(TAU * 2 * n / FRAMES) > 0 else 1
    for i in range(36):
        fx = cx + 22 * math.cos(TAU * (4 * n / FRAMES + i * 0.618)) + 9 * math.sin(i * 2.3)
        fy = cy + 9 * math.sin(TAU * (6 * n / FRAMES) + i) + 6 * math.cos(i * 1.7)
        silver = np.array([150, 176, 204]) * (1.4 if (i * 7 + n) % 23 == 0 else 1.0)
        for k in range(3):
            canvas.dot(fx - heading * k, fy, silver * (1 - 0.25 * k))
        canvas.dot(fx - heading * 3, fy - 1, silver * 0.5)
        canvas.dot(fx - heading * 3, fy + 1, silver * 0.5)


def angler(canvas, n):
    # Anglerfish: a faint shape in the dark, and a lure that pulses.
    bx, by = 2120, 1064 + 2 * math.sin(TAU * 4 * n / FRAMES)
    patch = _patch(canvas, bx - 14, by - 9, bx + 14, by + 9)
    if patch is not None:
        where, wx, wy = patch
        r = ((wx - bx) / 13) ** 2 + ((wy - by) / 8) ** 2
        shell = (r <= 1) & (r > 0.7)
        canvas.lit[where] &= ~(r <= 1)
        canvas.lit[where] |= shell
        canvas.ink[where][shell] = (40, 56, 72)
    for k in range(5):                                       # teeth
        canvas.dot(bx - 12 + k, by + (1 if k % 2 else 2), (190, 200, 205))
    canvas.dot(bx - 7, by - 3, (120, 150, 160))              # eye
    lx = bx - 16 + 2 * math.sin(TAU * 6 * n / FRAMES)
    ly = by - 15 + 2 * math.cos(TAU * 6 * n / FRAMES)
    for t in np.linspace(0, 1, 14):                         # the stalk
        canvas.dot(bx - 4 + (lx - bx + 4) * t, by - 7 + (ly - by + 7) * t - 5 * math.sin(math.pi * t),
                   (60, 72, 80))
    pulse = 0.6 + 0.4 * math.sin(TAU * 20 * n / FRAMES)
    for dx in (0, 1):
        for dy in (0, 1):
            canvas.dot(lx + dx, ly + dy, np.array([230, 255, 150]) * pulse)
    for k in range(10):
        a = TAU * k / 10 + n * 0.2
        canvas.dot(lx + 4 * math.cos(a), ly + 4 * math.sin(a), np.array([110, 140, 60]) * pulse)


def draw(canvas, n):
    """Everything alive in the sea, back to front."""
    whale(canvas, n)
    shoal(canvas, n)
    jellies(canvas, n)
    angler(canvas, n)
