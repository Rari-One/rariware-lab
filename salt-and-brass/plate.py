"""Salt & Brass — circular Chladni standing waves and salt-grain migration in Braille."""
import math
import numpy as np
from score import MODES, midi_hz, midi_name, partial_levels

W, H, FRAMES, FPS = 120, 44, 384, 24
BAR_FRAMES = FRAMES // len(MODES)  # 48 frames = 2.0 s per mode
DOT_W, DOT_H = W * 2, H * 4        # 240 x 176 physical square Braille dots
CX, CY, R_PLATE = DOT_W * 0.5, DOT_H * 0.5, 73.5
BG = np.array([10, 12, 18], dtype=np.uint8)
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint16)
BLOCKS = " ▁▂▃▄▅▆▇█"


def bessel_j(m, x):
    """First-kind Bessel function J_m(x) via alternating series (exact for x <= 14)."""
    out = np.zeros_like(x, dtype=np.float64)
    half = 0.5 * x
    term = (half ** m) / math.factorial(m)
    for k in range(36):
        out += term
        term = -term * (half * half) / ((k + 1) * (k + m + 1))
    return out


def build_fields():
    """Precompute circular Chladni standing-wave amplitudes and nodal gradients."""
    yy, xx = np.mgrid[:DOT_H, :DOT_W]
    dx = xx - CX
    dy = yy - CY
    r = np.hypot(dx, dy)
    rn = r / R_PLATE
    ang = np.arctan2(dy, dx)
    inside = rn <= 0.96

    fields = []
    for mode in MODES:
        _, _, m1, k1, m2, k2, mix2, bow_deg, _, _ = mode
        phi = math.radians(bow_deg)
        # Circular plate eigenmode: radial Bessel standing wave times angular cosine.
        z = bessel_j(m1, k1 * rn) * np.cos(m1 * (ang - phi))
        if mix2 != 0.0:
            z = z + mix2 * bessel_j(m2, k2 * rn) * np.cos(m2 * (ang - phi))
        scale = np.percentile(np.abs(z[inside]), 98)
        z = np.clip(z / max(scale, 1e-6), -1.4, 1.4)
        # Potential energy U = Z^2 vanishes along the quiet nodal curves where salt settles.
        gy, gx = np.gradient(z * z)
        fields.append((z, gx, gy))
    return xx, yy, r, ang, fields


def sample_grid(grid, x, y):
    ix = np.clip(np.rint(x).astype(np.int32), 0, DOT_W - 1)
    iy = np.clip(np.rint(y).astype(np.int32), 0, DOT_H - 1)
    return grid[iy, ix]


def simulate_salt(fields, count=5400):
    """Simulate salt grains migrating across two full cycles; record the steady second loop."""
    rng = np.random.default_rng(1787)
    # Uniform disk initialization inside the plate bezel.
    rad = (R_PLATE - 2.5) * np.sqrt(rng.random(count))
    theta = rng.uniform(0.0, 2.0 * np.pi, count)
    px = CX + rad * np.cos(theta)
    py = CY + rad * np.sin(theta)
    vx = np.zeros(count, dtype=np.float64)
    vy = np.zeros(count, dtype=np.float64)

    def step_frame(frame_idx):
        nonlocal px, py, vx, vy
        bar = frame_idx // BAR_FRAMES
        phase = (frame_idx % BAR_FRAMES) / BAR_FRAMES
        z_grid, gx_grid, gy_grid = fields[bar]
        # Bow excitation spikes at each measure onset and relaxes so patterns lock crisp.
        excite = 1.70 * math.exp(-4.8 * phase) + 0.34 * math.exp(-14.0 * abs(phase - 0.39))
        for _ in range(4):
            z = sample_grid(z_grid, px, py)
            gx = sample_grid(gx_grid, px, py)
            gy = sample_grid(gy_grid, px, py)
            az = np.abs(z)
            # Antinodes toss salt randomly; nodal gradients draw grains onto Z = 0 curves.
            kick = (0.10 + 1.48 * excite) * (az ** 0.85) + 0.08 * excite
            vx = 0.60 * vx - 2.05 * gx + rng.normal(0.0, 1.0, count) * kick
            vy = 0.60 * vy - 2.05 * gy + rng.normal(0.0, 1.0, count) * kick
            px += vx
            py += vy
            dx = px - CX
            dy = py - CY
            dist = np.hypot(dx, dy)
            outside = dist > (R_PLATE - 2.0)
            if np.any(outside):
                pull = (R_PLATE - 2.2) / dist[outside]
                px[outside] = CX + dx[outside] * pull
                py[outside] = CY + dy[outside] * pull
                vx[outside] *= -0.25
                vy[outside] *= -0.25

    # Warm-up pass brings grains into the natural Mode VIII steady state before frame 0.
    for n in range(FRAMES):
        step_frame(n)

    loop_start_x = px.copy()
    loop_start_y = py.copy()
    history = []

    for n in range(FRAMES):
        step_frame(n)
        # In the final quiet frames of Mode VIII, guide settled grains seamlessly to frame 0.
        if n >= FRAMES - 12:
            if n == FRAMES - 12:
                # Pair particles by polar angle + quantized radius for minimal drift.
                key_cur = np.arctan2(py - CY, px - CX) + 0.015 * np.rint(np.hypot(px - CX, py - CY) / 4.0)
                key_dst = np.arctan2(loop_start_y - CY, loop_start_x - CX) + 0.015 * np.rint(np.hypot(loop_start_x - CX, loop_start_y - CY) / 4.0)
                order_cur = np.argsort(key_cur)
                order_dst = np.argsort(key_dst)
                target_x = np.empty_like(px)
                target_y = np.empty_like(py)
                target_x[order_cur] = loop_start_x[order_dst]
                target_y[order_cur] = loop_start_y[order_dst]
            blend = ((n - (FRAMES - 12) + 1) / 12.0) ** 2
            px = px + (target_x - px) * blend * 0.42
            py = py + (target_y - py) * blend * 0.42
            if n == FRAMES - 1:
                px, py = target_x.copy(), target_y.copy()
        speed = np.hypot(vx, vy)
        history.append((px.copy(), py.copy(), speed))
    return history


def put_text(cells, row, col, text, rgb):
    for i, ch in enumerate(text):
        c = col + i
        if 0 <= row < H and 0 <= c < W:
            cells[row, c]["glyph"] = ord(ch)
            cells[row, c]["ink"] = rgb


def generate_frames():
    """Yield all 384 frames as 5-byte-per-cell Lab Player binary slices."""
    xx, yy, r, ang, fields = build_fields()
    history = simulate_salt(fields)
    rng = np.random.default_rng(404)

    # Static patinated brass bezel, engraved rim ticks, center pin, and brushed iron grain.
    bezel = (r >= R_PLATE + 0.6) & (r <= R_PLATE + 4.8)
    inner_lip = (r >= R_PLATE - 0.6) & (r <= R_PLATE + 0.6)
    center_pin = r <= 2.4
    ang_deg = (np.degrees(ang) + 360.0) % 360.0
    tick_major = (np.minimum(ang_deg % 90.0, 90.0 - ang_deg % 90.0) < 0.75) & (r >= R_PLATE + 5.2) & (r <= R_PLATE + 9.2)
    tick_minor = (np.minimum(ang_deg % 15.0, 15.0 - ang_deg % 15.0) < 0.55) & (r >= R_PLATE + 5.2) & (r <= R_PLATE + 7.4)
    ticks = tick_major | tick_minor
    # Subtle 3D directional lighting across the circular brass rim.
    rim_light = 0.5 + 0.5 * np.cos(ang + 2.35)
    plate_patina = (r < R_PLATE - 1.2) & (rng.random((DOT_H, DOT_W)) > 0.986)
    shimmer_noise = rng.random((DOT_H, DOT_W))

    for n in range(FRAMES):
        bar = n // BAR_FRAMES
        local = n % BAR_FRAMES
        phase = local / BAR_FRAMES
        roman, mode_label, _, _, _, _, _, bow_deg, bass, chord = MODES[bar]
        z_grid, _, _ = fields[bar]

        field = np.zeros((DOT_H, DOT_W), dtype=bool)
        color = np.zeros((DOT_H, DOT_W, 3), dtype=np.float64)

        # Brushed dark iron plate interior.
        field |= plate_patina
        color[plate_patina] = (28.0, 32.0, 42.0)

        # Ephemeral antinode shimmer reveals the standing wave energy right after the bow strikes.
        wave_glow = math.exp(-5.0 * phase)
        if wave_glow > 0.04:
            az = np.abs(z_grid)
            shimmer = (r < R_PLATE - 1.2) & (az > 0.42) & (shimmer_noise < 0.22 * wave_glow * az)
            field |= shimmer
            color[shimmer] = (150.0 + 70.0 * wave_glow, 94.0 + 48.0 * wave_glow, 46.0 + 20.0 * wave_glow)

        # Inward circular bow-impact ripple radiating from the contact point on the rim.
        if phase < 0.45:
            phi = math.radians(bow_deg)
            bx = CX + (R_PLATE + 2.0) * math.cos(phi)
            by = CY + (R_PLATE + 2.0) * math.sin(phi)
            d_bow = np.hypot(xx - bx, yy - by)
            front = phase * 340.0
            ripple = (r < R_PLATE - 0.8) & (np.abs(d_bow - front) < 2.2) & (shimmer_noise < 0.55)
            fade = max(0.0, 1.0 - phase / 0.45)
            field |= ripple
            color[ripple] = (180.0 + 68.0 * fade, 126.0 + 54.0 * fade, 64.0 + 24.0 * fade)

        # Engraved brass bezel and radial degree ticks.
        field |= bezel
        color[bezel, 0] = 92.0 + 112.0 * rim_light[bezel]
        color[bezel, 1] = 69.0 + 86.0 * rim_light[bezel]
        color[bezel, 2] = 38.0 + 48.0 * rim_light[bezel]

        field |= inner_lip
        color[inner_lip] = (54.0, 42.0, 26.0)

        field |= ticks
        color[ticks] = (118.0, 96.0, 62.0)

        field |= center_pin
        color[center_pin] = (138.0, 106.0, 62.0)

        # Luminous bow contact arc glowing outside the rim at the active azimuth.
        bow_pulse = math.sin(math.pi * min(1.0, phase / 0.65)) ** 0.7 if phase < 0.65 else 0.0
        if bow_pulse > 0.02:
            d_ang = ((ang_deg - bow_deg + 180.0) % 360.0) - 180.0
            arc = (np.abs(d_ang) <= 10.5) & (r >= R_PLATE + 5.6) & (r <= R_PLATE + 8.8)
            field |= arc
            color[arc] = (
                178.0 + 77.0 * bow_pulse,
                114.0 + 82.0 * bow_pulse,
                52.0 + 58.0 * bow_pulse,
            )
            # Slender tangent bow stroke gliding past the rim contact point.
            phi = math.radians(bow_deg)
            nx, ny = math.cos(phi), math.sin(phi)
            tx, ty = -ny, nx
            px0 = CX + (R_PLATE + 7.2) * nx
            py0 = CY + (R_PLATE + 7.2) * ny
            rx, ry = xx - px0, yy - py0
            along = rx * tx + ry * ty
            perp = np.abs(rx * nx + ry * ny)
            slide = (phase / 0.65 - 0.5) * 26.0
            bow_hair = (perp <= 0.9) & (np.abs(along - slide) <= 18.0) & (r >= R_PLATE + 5.0)
            field |= bow_hair
            color[bow_hair] = (
                160.0 + 85.0 * bow_pulse,
                122.0 + 72.0 * bow_pulse,
                72.0 + 48.0 * bow_pulse,
            )

        # Splat salt grains onto the 240 x 176 Braille dot plane.
        px, py, speed = history[n]
        ix = np.clip(np.rint(px).astype(np.int32), 0, DOT_W - 1)
        iy = np.clip(np.rint(py).astype(np.int32), 0, DOT_H - 1)
        density = np.zeros((DOT_H, DOT_W), dtype=np.float64)
        kinetic = np.zeros((DOT_H, DOT_W), dtype=np.float64)
        np.add.at(density, (iy, ix), 1.0)
        np.add.at(kinetic, (iy, ix), speed)

        salt = density > 0.0
        avg_spd = np.zeros_like(density)
        avg_spd[salt] = kinetic[salt] / density[salt]
        pile = np.clip((density[salt] - 1.0) / 3.0, 0.0, 1.0)
        leap = np.clip(avg_spd[salt] / 1.4, 0.0, 1.0)

        # Settled salt gleams warm porcelain ivory; leaping grains flash pale molten gold.
        sr = 222.0 + 33.0 * pile + 28.0 * leap
        sg = 212.0 + 36.0 * pile - 12.0 * leap
        sb = 194.0 + 46.0 * pile - 78.0 * leap
        field |= salt
        color[salt, 0] = np.clip(sr, 0.0, 255.0)
        color[salt, 1] = np.clip(sg, 0.0, 255.0)
        color[salt, 2] = np.clip(sb, 0.0, 255.0)

        # Pack 2x4 Braille dots into 5-byte Lab Player cells.
        dots = field.reshape(H, 4, W, 2)
        masks = (dots * BITS[None, :, None, :]).sum(axis=(1, 3))
        sums = (color * field[:, :, None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3))
        counts = np.maximum(1, dots.sum(axis=(1, 3)))[:, :, None]
        avg_rgb = np.clip(np.rint(sums / counts), 0, 255).astype(np.uint8)

        cells = np.zeros((H, W), dtype=[("glyph", "<u2"), ("ink", "u1", 3)])
        cells["glyph"] = np.where(masks > 0, 0x2800 + masks, 32)
        cells["ink"] = np.where(masks[:, :, None] > 0, avg_rgb, BG)

        # Corner workshop engravings and live fractional-block harmonic partial meters.
        brass_hi = (214, 176, 108)
        brass_mid = (146, 122, 86)
        brass_dim = (102, 89, 70)

        put_text(cells, 1, 3, "SALT & BRASS", brass_hi)
        put_text(cells, 2, 3, "CHLADNI PLATE · NO. IV", brass_dim)

        freq_hz = midi_hz(chord[0])
        top_r1 = f"MODE ({mode_label}) · {freq_hz:5.1f} Hz"
        top_r2 = "  ".join(midi_name(m) for m in (bass, *chord))
        put_text(cells, 1, W - 3 - len(top_r1), top_r1, brass_hi)
        put_text(cells, 2, W - 3 - len(top_r2), top_r2, brass_mid)

        # Live fractional-block (▁-█) harmonic meters tracking the four audio envelopes.
        levels = partial_levels(bar, phase)
        meter_colors = ((196, 146, 84), (228, 186, 114), (242, 224, 186), (234, 152, 88))
        put_text(cells, H - 5, 3, "PARTIALS", brass_dim)
        for j, lvl in enumerate(levels):
            steps = max(1, min(16, int(round(lvl * 16.0))))
            bot_blk = BLOCKS[min(8, steps)] * 2
            top_blk = BLOCKS[max(0, steps - 8)] * 2
            put_text(cells, H - 4, 3 + j * 4, top_blk, meter_colors[j])
            put_text(cells, H - 3, 3 + j * 4, bot_blk, meter_colors[j])
        put_text(cells, H - 2, 3, "f1  f2  f3  f4", brass_dim)

        bot_r1 = f"BAR {roman} / VIII"
        bot_r2 = f"BOW {bow_deg:03d}°"
        put_text(cells, H - 3, W - 3 - len(bot_r1), bot_r1, brass_hi)
        put_text(cells, H - 2, W - 3 - len(bot_r2), bot_r2, brass_mid)

        yield cells.tobytes()
