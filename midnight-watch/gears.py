"""The Midnight Watch — Chapters II & III: The Escapement gearworks and 3D Pendulum Hall."""
import math
import numpy as np

from clock import CX, CY, DOT_H, DOT_W, XX, YY, Canvas, smoothstep

_RNG = np.random.default_rng(2030)
_DUST_X = _RNG.uniform(0.0, DOT_W, 95)
_DUST_Y = _RNG.uniform(0.0, DOT_H, 95)
_DUST_S = _RNG.uniform(0.35, 1.15, 95)
_SHIMMER = _RNG.random((DOT_H, DOT_W))


def render_escapement(frame, local):
    """Chapter II: layered meshing brass cogwheels, rocking anchor escapement, and hairspring."""
    cv = Canvas()
    t = frame / 15.0
    # Slow camera drift through the gearworks toward the arched passage ahead.
    drift_x = math.sin(local * math.pi) * 14.0
    drift_y = math.cos(local * math.pi) * 6.0

    # Warm bronze shaft of lantern light crossing diagonally through the mechanism.
    beam_d = np.abs((XX - CX + 18.0) * 0.52 + (YY - CY) * 0.85)
    beam = (beam_d < 34.0) & (_SHIMMER < 0.045 * (1.0 - beam_d / 34.0))
    cv.paint(beam, (94, 70, 38))

    # Deep background great wheel turning slowly behind the main train.
    cv.gear(CX - 54.0 - drift_x * 0.4, CY + 24.0 - drift_y * 0.4, 52.0, 28,
            t * 0.28, (54, 40, 24), (112, 82, 46), spokes=6, hub=0.20, clear_core=False)
    cv.gear(CX + 62.0 - drift_x * 0.4, CY - 34.0 - drift_y * 0.4, 44.0, 24,
            -t * 0.327 + 0.14, (58, 42, 26), (118, 86, 48), spokes=5, hub=0.22, clear_core=False)

    # Exact meshing gear train: radii proportional to tooth counts so teeth interlock cleanly.
    # Base pitch radius scale = 1.95 dots per tooth.
    w_main = t * 0.62
    g1_x, g1_y, g1_r, g1_t = CX - 34.0 - drift_x, CY + 8.0 - drift_y, 35.1, 18
    # Gear 2 meshes at distance (r1 + r2 + 2.4) at angle -22 deg.
    a12 = math.radians(-22.0)
    g2_r, g2_t = 23.4, 12
    g2_x = g1_x + (g1_r + g2_r + 2.5) * math.cos(a12)
    g2_y = g1_y + (g1_r + g2_r + 2.5) * math.sin(a12)
    w2 = -w_main * (g1_t / g2_t) + math.pi / g2_t

    # Gear 3 meshes below Gear 2 at angle +56 deg.
    a23 = math.radians(56.0)
    g3_r, g3_t = 29.25, 15
    g3_x = g2_x + (g2_r + g3_r + 2.5) * math.cos(a23)
    g3_y = g2_y + (g2_r + g3_r + 2.5) * math.sin(a23)
    w3 = -w2 * (g2_t / g3_t) + math.pi / g3_t

    # Escape wheel at top-center, stepping discretely on every half-second tick!
    tick_idx = math.floor(t * 2.0)
    tick_frac = (t * 2.0) % 1.0
    esc_step = tick_idx + smoothstep(0.0, 0.24, tick_frac)
    esc_x, esc_y, esc_r = CX - 2.0 - drift_x * 0.8, CY - 42.0 - drift_y * 0.8, 22.0
    esc_ang = esc_step * (2.0 * math.pi / 15.0)

    # Render the brass, copper, and steel gear train with directional sheen.
    cv.gear(g1_x, g1_y, g1_r, g1_t, w_main, (112, 82, 38), (236, 190, 108), spokes=5)
    cv.gear(g2_x, g2_y, g2_r, g2_t, w2, (124, 72, 46), (232, 150, 96), spokes=4)
    cv.gear(g3_x, g3_y, g3_r, g3_t, w3, (104, 78, 38), (224, 178, 98), spokes=5)
    cv.gear(esc_x, esc_y, esc_r, 15, esc_ang, (118, 134, 162), (218, 232, 250), spokes=3, hub=0.25)

    # Rocking anchor escapement pallet fork clicking in exact sync with the stereo tick-tock.
    piv_x, piv_y = esc_x, esc_y - 30.0
    rock = 0.24 * math.sin(math.pi * esc_step)
    for side in (-1.0, 1.0):
        arm_a = math.pi * 0.5 + rock + side * 0.56
        ex = piv_x + 21.0 * math.cos(arm_a)
        ey = piv_y + 21.0 * math.sin(arm_a)
        cv.segment(piv_x, piv_y, ex, ey, 1.4, (196, 212, 238))
        # Pallet claw reaching toward the escape teeth.
        claw_a = arm_a - side * 0.72
        cv.segment(ex, ey, ex + 6.5 * math.cos(claw_a), ey + 6.5 * math.sin(claw_a), 1.1, (242, 198, 118))
    cv.disc(piv_x, piv_y, 2.8, (230, 62, 86))

    # Breathing gold balance hairspring in the upper-right foreground.
    hs_x, hs_y = CX + 64.0 - drift_x * 1.15, CY + 24.0 - drift_y * 1.15
    breath = 1.0 + 0.14 * math.sin(2.0 * math.pi * t)
    s_u = np.linspace(0.5, 5.5 * 2.0 * math.pi, 420)
    sr = (2.8 + 0.84 * s_u) * breath
    sx = hs_x + sr * np.cos(s_u + 0.35 * math.sin(2.0 * math.pi * t))
    sy = hs_y + sr * np.sin(s_u + 0.35 * math.sin(2.0 * math.pi * t))
    cv.points(sx, sy, (246, 206, 124), radius=0.55)
    cv.ring(hs_x, hs_y, 30.5, 33.0, (118, 86, 42), -2.2, (236, 192, 112))

    # Crimson-rose ruby jewel bearings at every gear arbor, pulsing warmly on each tick.
    pulse = math.exp(-5.0 * tick_frac)
    ruby = (204 + 50 * pulse, 44 + 42 * pulse, 72 + 46 * pulse)
    for jx, jy, jr in ((g1_x, g1_y, 4.4), (g2_x, g2_y, 3.4), (g3_x, g3_y, 3.8), (esc_x, esc_y, 3.2), (hs_x, hs_y, 3.4)):
        cv.ring(jx, jy, jr, jr + 1.6, (218, 178, 102))
        cv.disc(jx, jy, jr - 0.3, ruby)

    # Floating golden dust motes drifting across the warm gearworks light.
    mx = (_DUST_X + t * 5.0 * _DUST_S) % DOT_W
    my = (_DUST_Y + np.sin(t * 0.9 + _DUST_X * 0.05) * 4.0) % DOT_H
    cv.points(mx, my, (198, 162, 102))
    return cv, []


def render_pendulum_hall(frame, local):
    """Chapter III: 3D-perspective Gothic brass cathedral with polyrhythmic swinging pendulums."""
    cv = Canvas()
    t = frame / 15.0
    van_x = CX + math.sin(local * math.pi * 2.0) * 8.0
    van_y = CY - 8.0

    # Diagonal shafts of cool silver-blue moonlight cutting across the dark vault.
    for shaft_x in (CX - 58.0, CX + 14.0, CX + 72.0):
        d_beam = np.abs((XX - shaft_x) * 0.88 + (YY - CY) * 0.44)
        mask = (d_beam < 18.0) & (_SHIMMER < 0.055 * (1.0 - d_beam / 18.0))
        cv.paint(mask, (76, 104, 152))

    # Receding 3D-perspective Gothic brass arches gliding continuously past the camera.
    # Z flows from 6.5 (far) down to 0.55 (near) seamlessly at constant speed.
    arch_speed = 0.68
    for i in range(7):
        z = ((i - t * arch_speed) % 7.0) + 0.55
        scale = 1.45 / z
        depth_fade = smoothstep(7.2, 1.2, z)
        half_w = 78.0 * scale
        floor_y = van_y + 56.0 * scale
        spring_y = van_y - 16.0 * scale
        apex_y = van_y - 68.0 * scale
        col_rgb = (
            62 + 154 * depth_fade,
            48 + 118 * depth_fade,
            30 + 62 * depth_fade,
        )
        # Left and right Gothic brass pillars.
        cv.segment(van_x - half_w, floor_y, van_x - half_w, spring_y, max(0.8, 1.45 * scale), col_rgb)
        cv.segment(van_x + half_w, floor_y, van_x + half_w, spring_y, max(0.8, 1.45 * scale), col_rgb)
        # Pointed cathedral arch curve meeting at the vault apex.
        u = np.linspace(0.0, 1.0, 56)
        lx = van_x - half_w * (1.0 - u)
        rx = van_x + half_w * (1.0 - u)
        ay = spring_y + (apex_y - spring_y) * (u ** 0.62)
        cv.points(lx, ay, col_rgb, radius=max(0.55, 0.85 * scale))
        cv.points(rx, ay, col_rgb, radius=max(0.55, 0.85 * scale))
        # Floor cross-rib in perspective.
        if floor_y < DOT_H:
            cv.segment(van_x - half_w, floor_y, van_x + half_w, floor_y, 0.7,
                       (46 + 68 * depth_fade, 46 + 60 * depth_fade, 58 + 52 * depth_fade))

    # Distant starlit celestial portal glowing softly at the vanishing point ahead.
    d_van = np.hypot(XX - van_x, YY - (van_y + 4.0))
    portal = (d_van < 18.0) & (_SHIMMER < 0.24 * (1.0 - d_van / 18.0))
    cv.add_glow(portal, (132, 178, 248), 0.75)

    # Perspective floor rails leading the eye toward the celestial doorway ahead.
    for sgn in (-1.0, 1.0):
        cv.segment(van_x + sgn * 16.0, van_y + 12.0, van_x + sgn * 112.0, DOT_H - 2.0, 0.9, (112, 92, 62))

    # Three golden pendulums anchored to suspended brass crossbeams swinging in polyrhythm.
    # The foreground pendulum swings at 0.25 Hz (one full pass per 2-second bar = stereo whoosh!).
    pendulums = [
        (0.55, 0.375, 0.50, 26.0, 72.0,  7.5, (148, 114, 64), (206, 168, 102)),  # far
        (0.78, 0.3125, 0.58, 16.0, 92.0, 10.5, (182, 138, 70), (242, 198, 118)),  # mid
        (1.00, 0.250, 0.65,  8.0, 112.0, 14.5, (206, 152, 68), (255, 228, 152)),  # near hero
    ]
    for depth, freq, max_ang, piv_y, length, bob_r, c_lo, c_hi in pendulums:
        piv_x = van_x
        # Horizontal brass suspension beam and ruby pivot bearing.
        beam_w = 24.0 + 46.0 * depth
        cv.segment(piv_x - beam_w, piv_y, piv_x + beam_w, piv_y, 0.8 + 0.4 * depth, c_lo)
        # Luminous motion trail of previous bob positions.
        for k in range(10, 0, -1):
            tk = t - k * 0.045
            ak = max_ang * math.sin(2.0 * math.pi * freq * tk)
            bx = piv_x + length * math.sin(ak)
            by = piv_y + length * math.cos(ak)
            fade = (1.0 - k / 11.0) ** 1.8 * 0.48
            cv.ring(bx, by, bob_r * 0.85, bob_r * 1.02,
                    (c_hi[0] * fade, c_hi[1] * fade, c_hi[2] * fade))

        ang_now = max_ang * math.sin(2.0 * math.pi * freq * t)
        bx = piv_x + length * math.sin(ang_now)
        by = piv_y + length * math.cos(ang_now)
        # Slender pendulum rod + sculpted golden sun-disc bob with inner specular highlight.
        cv.segment(piv_x, piv_y, bx, by, 0.9 + 0.5 * depth, c_lo)
        cv.disc(piv_x, piv_y, 2.2 + 1.0 * depth, (226, 62, 86))
        cv.disc(bx, by, bob_r, c_lo)
        cv.ring(bx, by, bob_r * 0.65, bob_r, c_lo, -2.2, c_hi)
        cv.disc(bx - bob_r * 0.24, by - bob_r * 0.24, bob_r * 0.32, c_hi)

    # Drifting dust motes sparkling in the cathedral moonlight.
    mx = (_DUST_X + np.sin(t * 0.5 + _DUST_Y * 0.04) * 8.0) % DOT_W
    my = (_DUST_Y - t * 3.2 * _DUST_S) % DOT_H
    cv.points(mx, my, (176, 192, 224))
    return cv, []
