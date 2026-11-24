"""The Midnight Watch — Chapters IV & V: 3D Celestial Orrery and the Midnight Bell Tower."""
import math
import numpy as np

from clock import CX, CY, DOT_H, DOT_W, XX, YY, Canvas
from score import BELL_STRIKES, bell_impulse

_RNG = np.random.default_rng(4500)
_STAR_X = _RNG.uniform(0.0, DOT_W, 240)
_STAR_Y = _RNG.uniform(0.0, DOT_H, 240)
_STAR_PH = _RNG.uniform(0.0, 2.0 * math.pi, 240)
_STAR_BR = _RNG.uniform(0.35, 1.0, 240)
_NOISE = _RNG.random((DOT_H, DOT_W))
_SPARK_ANG = _RNG.uniform(-math.pi * 0.85, math.pi * 0.85, 64)
_SPARK_SPD = _RNG.uniform(22.0, 76.0, 64)


def _rot3(pts, rx, ry, rz):
    """Apply Euler rotations (X, Y, Z) to an (N, 3) point array."""
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    cx, sx = math.cos(rx), math.sin(rx)
    y, z = y * cx - z * sx, y * sx + z * cx
    cy, sy = math.cos(ry), math.sin(ry)
    x, z = x * cy + z * sy, -x * sy + z * cy
    cz, sz = math.cos(rz), math.sin(rz)
    x, y = x * cz - y * sz, x * sz + y * cz
    return np.column_stack((x, y, z))


def _project(pts, cam_z=275.0, scale=260.0):
    """Perspective project 3D points onto the 248 x 180 Braille plane."""
    z = pts[:, 2]
    f = scale / np.maximum(cam_z - z, 40.0)
    return CX + pts[:, 0] * f, CY + pts[:, 1] * f, z, f


def render_orrery(frame, local):
    """Chapter IV: true 3D-projected brass armillary sphere, orbiting worlds, and comet."""
    cv = Canvas()
    t = frame / 15.0

    # Deep starfield and faint diagonal indigo Milky Way ribbon.
    mw_d = np.abs((XX - CX) * 0.42 + (YY - CY) * 0.90)
    mw = (mw_d < 36.0) & (_NOISE < 0.032 * (1.0 - mw_d / 36.0))
    cv.paint(mw, (36, 48, 86))

    twinkle = 0.55 + 0.45 * np.sin(t * 2.2 + _STAR_PH)
    sb = (_STAR_BR * twinkle)[:, None]
    star_rgb = np.column_stack((140 + 100 * sb[:, 0], 162 + 86 * sb[:, 0], 210 + 45 * sb[:, 0]))
    cv.points(_STAR_X, _STAR_Y, star_rgb)

    # Sweeping silver-cyan comet arcing across the upper cosmos.
    comet_t = local
    comet_x = 18.0 + 212.0 * comet_t
    comet_y = 32.0 + 24.0 * math.sin(comet_t * math.pi * 1.15) - 10.0 * comet_t
    for k in range(28, 0, -1):
        u = max(0.0, comet_t - k * 0.0045)
        tx = 18.0 + 212.0 * u
        ty = 32.0 + 24.0 * math.sin(u * math.pi * 1.15) - 10.0 * u
        fade = (1.0 - k / 29.0) ** 1.9
        cv.points(np.array([tx]), np.array([ty]), (140 * fade, 212 * fade, 255 * fade),
                  radius=0.5 + 0.8 * fade)
    cv.disc(comet_x, comet_y, 2.0, (224, 248, 255))

    # Build four counter-rotating 3D brass armillary rings (back and front halves depth-sorted).
    th = np.linspace(0.0, 2.0 * math.pi, 440, endpoint=False)
    unit_ring = np.column_stack((np.cos(th), np.sin(th), np.zeros_like(th)))

    rings_spec = [
        (74.0, 0.36,  t * 0.16,  0.18, (206, 164, 92),  True),   # outer meridian
        (64.0, 1.12, -t * 0.24,  0.22, (242, 198, 114), True),   # ecliptic with ticks
        (52.0, 0.72,  t * 0.34, -0.45, (168, 196, 232), False),  # silver celestial equator
        (38.0, 1.38, -t * 0.42,  0.60, (224, 168, 96),  False),  # inner colure
    ]
    ring_layers = []
    for rad, rx, ry, rz, base_col, ticked in rings_spec:
        pts3 = _rot3(unit_ring * rad, rx, ry, rz)
        sx, sy, sz, _ = _project(pts3)
        ring_layers.append((sx, sy, sz, base_col))
        if ticked:
            # Fine degree notches jutting radially from the brass ring.
            idx_t = np.arange(0, 440, 12)
            outer3 = _rot3(unit_ring[idx_t] * (rad + 3.8), rx, ry, rz)
            ox, oy, oz, _ = _project(outer3)
            ring_layers.append((ox, oy, oz, (252, 218, 138)))

    # Orbiting worlds in true 3D orbital planes, plus Saturn's tilted ring!
    worlds_spec = [
        # (orbit_r, speed, phase, tilt_x, tilt_z, radius, rgb_lo, rgb_hi, saturn_ring)
        (24.0, 1.35, 0.4,  0.42,  0.15, 2.8, (168, 92, 58),  (242, 168, 114), False),  # Mercury
        (38.0, 0.88, 2.1,  0.34, -0.18, 4.4, (58, 124, 198), (156, 218, 255), False),  # Earth
        (51.0, 0.62, 4.3,  0.48,  0.22, 3.6, (176, 72, 54),  (248, 134, 96),  False),  # Mars
        (65.0, 0.40, 1.1,  0.38, -0.26, 5.6, (78, 168, 174), (178, 238, 232), True),   # Saturn
    ]
    world_items = []
    for orb_r, spd, ph, tx, tz, rad, c_lo, c_hi, has_ring in worlds_spec:
        a = ph + t * spd
        p3 = _rot3(np.array([[orb_r * math.cos(a), 0.0, orb_r * math.sin(a)]]), tx, 0.0, tz)
        px, py, pz, pf = _project(p3)
        world_items.append((float(pz[0]), float(px[0]), float(py[0]), rad * float(pf[0]), c_lo, c_hi, has_ring, tx, tz, p3[0]))
        # Orbiting tiny silver Moon circling Earth.
        if rad == 4.4:
            ma = t * 3.2
            m3 = p3 + _rot3(np.array([[8.5 * math.cos(ma), 0.0, 8.5 * math.sin(ma)]]), tx, 0.0, tz)
            mx, my, mz, mf = _project(m3)
            world_items.append((float(mz[0]), float(mx[0]), float(my[0]), 1.7 * float(mf[0]),
                                (156, 168, 192), (242, 246, 255), False, 0.0, 0.0, m3[0]))

    def draw_rings(front):
        for sx, sy, sz, base_col in ring_layers:
            sel = (sz >= 0.0) if front else (sz < 0.0)
            if not np.any(sel):
                continue
            depth = np.clip((sz[sel] + 78.0) / 156.0, 0.30, 1.0)
            cols = np.asarray(base_col, dtype=np.float64)[None, :] * depth[:, None]
            cv.points(sx[sel], sy[sel], cols, radius=0.85 if front else 0.55)

    def draw_world(item):
        z, px, py, pr, c_lo, c_hi, has_ring, tx, tz, p3 = item
        # Slender brass armature connecting planet back to the central sun spindle.
        cv.segment(CX, CY, px, py, 0.55, (92, 74, 44))
        if has_ring:
            rth = np.linspace(0.0, 2.0 * math.pi, 96)
            ring3 = p3[None, :] + _rot3(
                np.column_stack((np.cos(rth) * 11.5, np.zeros_like(rth), np.sin(rth) * 11.5)),
                0.55, 0.2, -0.35,
            )
            rx_p, ry_p, rz_p, _ = _project(ring3)
            back_r = rz_p < z
            cv.points(rx_p[back_r], ry_p[back_r], (216, 186, 126), radius=0.55)
        cv.disc(px, py, pr, c_lo)
        cv.ring(px, py, pr * 0.55, pr, c_lo, -2.2, c_hi)
        cv.disc(px - pr * 0.25, py - pr * 0.25, pr * 0.35, c_hi)
        if has_ring:
            front_r = rz_p >= z
            cv.points(rx_p[front_r], ry_p[front_r], (244, 214, 148), radius=0.6)

    # Back half of rings and planets behind the Sun.
    draw_rings(front=False)
    for item in sorted([w for w in world_items if w[0] < 0.0], key=lambda x: x[0]):
        draw_world(item)

    # Blazing golden clockwork Sun at the center of the orrery with pulsing corona.
    pulse = 1.0 + 0.09 * math.sin(t * 3.14)
    sun_r = 12.2 * pulse
    d_sun = np.hypot(XX - CX, YY - CY)
    corona = (d_sun > sun_r) & (d_sun < sun_r + 14.0) & (_NOISE < 0.16 * (1.0 - (d_sun - sun_r) / 14.0))
    cv.add_glow(corona, (246, 178, 76), 0.9)
    for k in range(12):
        ra = t * 0.35 + k * (math.pi / 6.0)
        rlen = sun_r + (7.5 if k % 2 == 0 else 4.5) * pulse
        cv.segment(CX + sun_r * 0.9 * math.cos(ra), CY + sun_r * 0.9 * math.sin(ra),
                   CX + rlen * math.cos(ra), CY + rlen * math.sin(ra), 0.7, (252, 206, 114), glow=True)
    cv.disc(CX, CY, sun_r, (238, 162, 58))
    cv.disc(CX, CY, sun_r * 0.72, (255, 224, 138))
    cv.disc(CX - 2.2, CY - 2.2, sun_r * 0.36, (255, 248, 218))

    # Front half of rings and planets passing cleanly in front of the Sun.
    for item in sorted([w for w in world_items if w[0] >= 0.0], key=lambda x: x[0]):
        draw_world(item)
    draw_rings(front=True)
    return cv, []


def render_bell_tower(frame, local):
    """Chapter V: colossal bronze cathedral bell, articulated brass hammer, and acoustic shockwaves."""
    cv = Canvas()
    t = frame / 15.0

    # Find the most recent and upcoming bronze bell strikes to animate hammer & swing.
    since_strike = 9.0
    until_strike = 9.0
    for sf, _, _ in BELL_STRIKES:
        dt = (frame - sf) / 15.0
        if 0.0 <= dt < since_strike:
            since_strike = dt
        if -2.0 < dt < 0.0 and (-dt) < until_strike:
            until_strike = -dt

    impact = bell_impulse(frame)

    # Tall arched Gothic belfry window silhouette revealing midnight stars outside.
    win_half = 86.0
    win_arch = (np.abs(XX - CX) < win_half) & (
        (YY >= 68.0) | (np.hypot((XX - CX) * 0.92, YY - 68.0) < 78.0)
    )
    stars = win_arch & (_NOISE > 0.992)
    cv.paint(stars, (132, 158, 212))
    # Stone-and-brass belfry masonry frame and louvered side beams.
    frame_rim = (~win_arch) & (
        (np.abs(XX - CX) < win_half + 7.0)
        & ((YY >= 68.0) | (np.hypot((XX - CX) * 0.92, YY - 68.0) < 85.0))
    )
    cv.paint(frame_rim, (72, 58, 42))
    for ly in range(42, DOT_H - 12, 16):
        cv.segment(6.0, ly, 30.0, ly - 5.0, 1.0, (56, 46, 36))
        cv.segment(DOT_W - 30.0, ly - 5.0, DOT_W - 6.0, ly, 1.0, (56, 46, 36))

    # Heavy horizontal oak-and-iron belfry yoke beam at the top.
    yoke_y = 26.0
    yoke = (YY >= yoke_y - 4.5) & (YY <= yoke_y + 4.5) & (np.abs(XX - CX) <= 78.0)
    cv.paint(yoke, (108, 78, 44))
    cv.segment(CX - 78.0, yoke_y - 4.5, CX + 78.0, yoke_y - 4.5, 0.8, (186, 146, 86))

    # Damped physical bell swing triggered by each strike.
    swing = 0.085 * math.exp(-1.35 * since_strike) * math.sin(6.5 * since_strike)
    cos_s, sin_s = math.cos(swing), math.sin(swing)
    piv_x, piv_y = CX, yoke_y + 4.0

    # Transform screen coordinates into bell-local space (u across, v downward from pivot).
    rx = XX - piv_x
    ry = YY - piv_y
    u = rx * cos_s + ry * sin_s
    v = -rx * sin_s + ry * cos_s

    # Authentic flared cathedral bell profile: crown (v=12) -> waist (v=54) -> flared lip (v=106).
    s = np.clip((v - 12.0) / 94.0, 0.0, 1.0)
    half_bell = 16.0 + 13.0 * (s ** 0.7) + 27.0 * (s ** 3.2)
    bell_mask = (v >= 12.0) & (v <= 106.0) & (np.abs(u) <= half_bell)
    # Sculpted bronze crown canons and iron straps bolting the bell to the oak headstock.
    crown_canons = (v >= 0.0) & (v < 13.0) & (
        (np.abs(u) <= 4.5) | ((np.abs(np.abs(u) - 10.5) <= 2.4) & (v >= 3.0))
    )
    cv.paint(crown_canons, (152, 118, 66))
    for strap_x in (-11.0, 0.0, 11.0):
        cv.segment(piv_x + strap_x, yoke_y - 5.0, piv_x + strap_x, yoke_y + 6.0, 1.3, (176, 152, 112))

    # 3D cylindrical bronze shading with glowing molten rim on strike!
    nx = np.clip(u / np.maximum(half_bell, 1.0), -1.0, 1.0)
    nz = np.sqrt(np.maximum(0.0, 1.0 - nx * nx))
    lit = np.clip(0.32 + 0.68 * (-0.58 * nx + 0.81 * nz), 0.12, 1.0)
    # Horizontal relief bands engraved around the crown, inscription band, and sound bow.
    bands = ((np.abs(v - 28.0) < 1.8) | (np.abs(v - 88.0) < 2.2) | (np.abs(v - 103.5) < 2.0)) & bell_mask
    hot_rim = np.exp(-((v - 94.0) / 14.0) ** 2) * impact

    if np.any(bell_mask):
        cv.field |= bell_mask
        br = np.clip(72.0 + 148.0 * lit[bell_mask] + 95.0 * hot_rim[bell_mask], 0.0, 255.0)
        bg = np.clip(50.0 + 106.0 * lit[bell_mask] + 74.0 * hot_rim[bell_mask], 0.0, 255.0)
        bb = np.clip(24.0 + 48.0 * lit[bell_mask] + 32.0 * hot_rim[bell_mask], 0.0, 255.0)
        cv.color[bell_mask] = np.column_stack((br, bg, bb))
    cv.paint(bands, (244, 206, 128), alpha=0.85)

    # Iron clapper hanging just below the flared mouth of the bell.
    clap_a = -swing * 1.9
    cx_tip = piv_x + 114.0 * math.sin(clap_a)
    cy_tip = piv_y + 114.0 * math.cos(clap_a)
    cv.segment(piv_x, piv_y + 92.0, cx_tip, cy_tip, 1.5, (142, 134, 124))
    cv.disc(cx_tip, cy_tip, 5.2, (166, 152, 134))

    # Articulated gilded brass striker hammer on the right, snapping onto the sound bow on cue!
    # Sound bow contact point on the right edge of the bell (~ v = 92, u = +46).
    hit_x, hit_y = piv_x + 48.0, piv_y + 92.0
    h_piv_x, h_piv_y = piv_x + 88.0, piv_y + 112.0
    if until_strike < 0.45:
        cock = math.sin(math.pi * (1.0 - until_strike / 0.45)) * 0.55
    elif since_strike < 0.35:
        cock = 0.28 * math.sin(math.pi * (since_strike / 0.35))
    else:
        cock = 0.22
    # Rotate hammer arm away from the bell by `cock` radians.
    arm_dx, arm_dy = hit_x - h_piv_x, hit_y - h_piv_y
    ca, sa = math.cos(cock), math.sin(cock)
    hx = h_piv_x + arm_dx * ca - arm_dy * sa
    hy = h_piv_y + arm_dx * sa + arm_dy * ca
    cv.segment(h_piv_x, h_piv_y, hx, hy, 1.6, (198, 154, 78))
    cv.disc(hx, hy, 4.4, (244, 204, 122))
    cv.disc(h_piv_x, h_piv_y, 3.0, (218, 62, 82))

    # Concentric golden acoustic shockwave rings & burst sparks radiating from every strike!
    if since_strike < 1.85:
        d_hit = np.hypot(XX - hit_x, YY - hit_y)
        for wave_i in range(3):
            wt = since_strike - wave_i * 0.14
            if wt <= 0.0:
                continue
            rad = wt * 145.0
            fade = max(0.0, 1.0 - wt / 1.45) ** 1.4
            ring_m = (np.abs(d_hit - rad) < 2.2) & (_NOISE < 0.72 * fade + 0.15)
            cv.add_glow(ring_m, (255, 208, 118), fade * 0.92)

        # Molten brass sparks showering outward from the impact point.
        if since_strike < 0.95:
            sfade = (1.0 - since_strike / 0.95) ** 1.3
            sx = hit_x + _SPARK_SPD * since_strike * np.cos(_SPARK_ANG)
            sy = hit_y + _SPARK_SPD * since_strike * np.sin(_SPARK_ANG) + 38.0 * (since_strike ** 2)
            cv.points(sx, sy, (255 * sfade, 214 * sfade, 124 * sfade), radius=0.7)

    return cv, []
