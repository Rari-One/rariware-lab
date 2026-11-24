"""The Midnight Watch — Chapters I & VI: The antique pocket watch dial and midnight return."""
import math
import numpy as np

from clock import CX, CY, DOT_H, DOT_W, H, W, XX, YY, Canvas, put_text, smoothstep
from score import bell_impulse

_RNG = np.random.default_rng(1159)
_VELVET_GRAIN = _RNG.random((DOT_H, DOT_W))
_MOON_STARS = _RNG.random((DOT_H, DOT_W))

# Roman numeral positions around the dial (clock angle where 0 is 12 o'clock).
ROMANS = [
    (0, "XII"), (1, "I"), (2, "II"), (3, "III"), (4, "IV"), (5, "V"),
    (6, "VI"), (7, "VII"), (8, "VIII"), (9, "IX"), (10, "X"), (11, "XI"),
]


def render_dial(frame, local, returning=False):
    """Render Chapter I (zooming into the dial) or Chapter VI (pulling back to midnight)."""
    cv = Canvas()
    t = frame / 15.0

    # Smooth zoom curve: hold at 1.0 to admire the watch, then dive into the skeleton heart.
    if not returning:
        z_t = smoothstep(0.32, 0.98, local)
        zoom = 1.0 + 4.8 * (z_t ** 2.1)
    else:
        z_t = smoothstep(0.02, 0.68, local)
        zoom = 1.0 + 4.8 * ((1.0 - z_t) ** 2.1)

    r_case = 71.0 * zoom
    r_inner = 63.0 * zoom
    r_track = 57.5 * zoom
    r_aperture = 20.5 * zoom

    dx = XX - CX
    dy = YY - CY
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)

    # Subtle midnight-blue velvet background stipple outside the gold case.
    velvet = (r > r_case + 4.0) & (_VELVET_GRAIN > 0.986)
    cv.paint(velvet, (24, 32, 56))

    # Pocket watch bow & winding crown at 12 o'clock (visible while case is in frame).
    if zoom < 1.65:
        crown_y = CY - r_case - 5.5 * zoom
        cv.ring(CX, crown_y - 6.0 * zoom, 6.0 * zoom, 8.2 * zoom, (118, 88, 44), -2.2, (236, 194, 114))
        stem = (np.abs(dx) <= 4.2 * zoom) & (YY >= crown_y - 2.0 * zoom) & (YY <= CY - r_case + 2.0)
        cv.paint(stem, (194, 152, 82))

    # Visible clockwork glimpses inside the central skeleton aperture before we enter.
    cv.gear(CX - 7.5 * zoom, CY + 4.5 * zoom, 11.5 * zoom, 14, t * 0.85,
            (92, 66, 32), (186, 138, 72), spokes=4, clear_core=False)
    cv.gear(CX + 8.5 * zoom, CY - 5.0 * zoom, 9.5 * zoom, 12, -t * 1.05 + 0.2,
            (110, 74, 38), (210, 158, 88), spokes=5, clear_core=False)
    cv.disc(CX, CY, 3.0 * zoom, (218, 56, 78))  # central ruby jewel bearing

    # Porcelain dial face outside the central skeleton cutout.
    dial_face = (r >= r_aperture) & (r <= r_inner)
    # Fine concentric guilloche pattern etched delicately into the ivory face.
    guilloche = dial_face & ((np.sin(r * 1.45 / max(zoom, 1.0)) > 0.72) & (_VELVET_GRAIN < 0.12))
    cv.paint(guilloche, (34, 38, 48))

    # Gold outer bezel, double step rim, and inner skeleton brass collar.
    cv.ring(CX, CY, r_inner, r_case, (108, 80, 40), -2.35, (242, 202, 124))
    cv.ring(CX, CY, r_inner - 1.4 * zoom, r_inner + 0.4 * zoom, (62, 46, 26))
    cv.ring(CX, CY, r_aperture - 1.3 * zoom, r_aperture + 1.4 * zoom, (112, 84, 42), -2.3, (234, 192, 116))

    # 60 minute ticks and 12 bold hour batons around the chapter ring.
    deg = (np.degrees(ang) + 450.0) % 360.0
    m_dist = np.minimum(deg % 6.0, 6.0 - deg % 6.0)
    h_dist = np.minimum(deg % 30.0, 30.0 - deg % 30.0)
    min_ticks = (m_dist < 0.55 / math.sqrt(zoom)) & (r >= r_track) & (r <= r_inner - 2.0 * zoom)
    hr_ticks = (h_dist < 1.15 / math.sqrt(zoom)) & (r >= r_track - 3.0 * zoom) & (r <= r_inner - 1.8 * zoom)
    cv.paint(min_ticks, (148, 136, 112))
    cv.paint(hr_ticks, (238, 212, 152))

    # Moon-phase sub-window at 6 o'clock (lower dial, glowing cobalt sky & silver crescent).
    moon_cx, moon_cy = CX, CY + 36.5 * zoom
    moon_r = 11.2 * zoom
    if moon_cy - moon_r < DOT_H + 10:
        md = np.hypot(XX - moon_cx, YY - moon_cy)
        window = (md <= moon_r) & (YY <= moon_cy + 3.2 * zoom)
        cv.clear_mask(window)
        sky_dots = window & (_MOON_STARS > 0.965)
        cv.paint(sky_dots, (124, 156, 224))
        # Crescent moon rising gently across the minute.
        cres_x = moon_cx - 2.0 * zoom + 4.0 * zoom * (t / 60.0)
        cres_y = moon_cy - 3.2 * zoom
        m1 = np.hypot(XX - cres_x, YY - cres_y) <= 4.3 * zoom
        m2 = np.hypot(XX - (cres_x + 2.1 * zoom), YY - (cres_y - 0.8 * zoom)) <= 3.9 * zoom
        cv.paint(window & m1 & ~m2, (244, 228, 178))
        cv.ring(moon_cx, moon_cy, moon_r - 0.8 * zoom, moon_r + 1.0 * zoom, (158, 124, 68))

    # Blued-steel hour and minute hands approaching 12:00:00, plus sweeping gold second hand.
    # At frame 0 (11:59:00), minute hand is 6 degrees shy of XII; at frame 900 it reaches XII.
    sec_ang = -math.pi * 0.5 + 2.0 * math.pi * (t / 60.0)
    min_ang = -math.pi * 0.5 - math.radians(6.0 * (1.0 - t / 60.0))
    hr_ang = -math.pi * 0.5 - math.radians(0.5 * (1.0 - t / 60.0))

    # Hour hand (short, broad blued steel) and minute hand (slender, reaches the chapter ring).
    cv.segment(CX, CY, CX + 32.0 * zoom * math.cos(hr_ang), CY + 32.0 * zoom * math.sin(hr_ang),
               1.9 * min(zoom, 1.8), (112, 164, 232))
    cv.segment(CX, CY, CX + 49.0 * zoom * math.cos(min_ang), CY + 49.0 * zoom * math.sin(min_ang),
               1.35 * min(zoom, 1.8), (144, 194, 248))

    # Second hand with counterpoise tail, ticking crisply with a slight mechanical bounce.
    tick_frac = (t * 2.0) % 1.0
    sec_step = (math.floor(t * 2.0) + smoothstep(0.0, 0.28, tick_frac)) / 120.0
    s_ang = -math.pi * 0.5 + 2.0 * math.pi * sec_step
    cv.segment(CX - 11.0 * zoom * math.cos(s_ang), CY - 11.0 * zoom * math.sin(s_ang),
               CX + 54.0 * zoom * math.cos(s_ang), CY + 54.0 * zoom * math.sin(s_ang),
               0.85, (242, 152, 82))
    cv.disc(CX, CY, 2.4 * min(zoom, 2.0), (245, 206, 126))

    # Expanding golden chime aura across the watch face on the stroke of twelve.
    chime = bell_impulse(frame)
    if returning and chime > 0.05:
        ring_r = (1.0 - chime) * 110.0 + 18.0
        halo = (np.abs(r - ring_r) < 2.4) & (_VELVET_GRAIN < 0.65)
        cv.add_glow(halo, (248, 198, 108), chime * 0.95)

    # Roman numerals overlaid in crisp JetBrains Mono when near surface scale.
    overlays = []
    if zoom < 1.32:
        alpha = 1.0 - smoothstep(1.06, 1.30, zoom)
        num_rgb = tuple(int(6 + (c - 6) * alpha) for c in (232, 214, 172))
        r_num = 46.5 * zoom
        for idx, text in ROMANS:
            if idx == 6:
                continue  # moon-phase window sits at 6 o'clock
            a = -math.pi * 0.5 + idx * (math.pi / 6.0)
            col = int(round((CX + r_num * math.cos(a)) / 2.0 - len(text) * 0.5))
            row = int(round((CY + r_num * math.sin(a)) / 4.0))
            overlays.append((row, col, text, num_rgb))

    return cv, overlays
