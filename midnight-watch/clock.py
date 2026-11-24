"""The Midnight Watch — master clock, chapters, and vectorized Braille canvas."""
import math
import numpy as np

W, H = 124, 45
FPS, FRAMES = 15, 900               # 60.0 s exact — 100% of the v1 frame cap
DOT_W, DOT_H = W * 2, H * 4         # 248 x 180 square-aspect Braille dot plane
CX, CY = DOT_W * 0.5, DOT_H * 0.5
BG_HEX = "#06080f"
BG = np.array([6, 8, 15], dtype=np.uint8)
BITS = np.array([[1, 8], [2, 16], [4, 32], [64, 128]], dtype=np.uint16)
BLOCKS = " ▁▂▃▄▅▆▇█"

# Precomputed coordinate grids shared across every chapter renderer.
YY, XX = np.mgrid[:DOT_H, :DOT_W].astype(np.float64)

# Six ten-second chapters (150 frames each) trace one full minute inside the watch.
CHAPTERS = [
    (0,   150, "I · THE DIAL",          "SURFACE"),
    (150, 300, "II · THE ESCAPEMENT",   "GEARWORKS"),
    (300, 450, "III · THE PENDULUM",    "PENDULUM VAULT"),
    (450, 600, "IV · THE ORRERY",       "CELESTIAL CORE"),
    (600, 750, "V · THE BELL TOWER",    "BELFRY"),
    (750, 900, "VI · STROKE OF TWELVE", "MIDNIGHT"),
]


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else (hi if v > hi else v)


def smoothstep(edge0, edge1, x):
    t = clamp((x - edge0) / max(edge1 - edge0, 1e-9))
    return t * t * (3.0 - 2.0 * t)


def chapter_info(frame):
    idx = min(len(CHAPTERS) - 1, frame // 150)
    start, end, title, depth = CHAPTERS[idx]
    local = (frame - start) / (end - start)
    return idx, local, title, depth


class Canvas:
    """248 x 180 Braille dot plane with RGB ink and soft additive glow support."""

    def __init__(self):
        self.field = np.zeros((DOT_H, DOT_W), dtype=bool)
        self.color = np.zeros((DOT_H, DOT_W, 3), dtype=np.float64)

    def paint(self, mask, rgb, alpha=1.0):
        if not np.any(mask):
            return
        rgb_arr = np.asarray(rgb, dtype=np.float64)
        if alpha >= 0.999:
            self.field |= mask
            self.color[mask] = rgb_arr
        else:
            existing = self.field & mask
            fresh = (~self.field) & mask
            if np.any(existing):
                self.color[existing] = (1.0 - alpha) * self.color[existing] + alpha * rgb_arr
            if np.any(fresh):
                self.field |= fresh
                self.color[fresh] = rgb_arr

    def add_glow(self, mask, rgb, strength=1.0):
        if not np.any(mask):
            return
        rgb_arr = np.asarray(rgb, dtype=np.float64) * strength
        existing = self.field & mask
        fresh = (~self.field) & mask
        if np.any(existing):
            self.color[existing] = np.clip(self.color[existing] + rgb_arr, 0.0, 255.0)
        if np.any(fresh):
            self.field |= fresh
            self.color[fresh] = np.clip(rgb_arr, 0.0, 255.0)

    def clear_mask(self, mask):
        self.field &= ~mask

    def disc(self, cx, cy, radius, rgb, dither=None, density=1.0):
        dx = XX - cx
        dy = YY - cy
        m = (dx * dx + dy * dy) <= (radius * radius)
        if dither is not None and density < 1.0:
            m &= dither < density
        self.paint(m, rgb)

    def ring(self, cx, cy, r_in, r_out, rgb, lit_angle=None, hi_rgb=None):
        dx = XX - cx
        dy = YY - cy
        r2 = dx * dx + dy * dy
        m = (r2 >= r_in * r_in) & (r2 <= r_out * r_out)
        if not np.any(m):
            return
        if lit_angle is not None and hi_rgb is not None:
            ang = np.arctan2(dy[m], dx[m])
            shade = 0.5 + 0.5 * np.cos(ang - lit_angle)
            lo = np.asarray(rgb, dtype=np.float64)
            hi = np.asarray(hi_rgb, dtype=np.float64)
            self.field |= m
            self.color[m] = lo[None, :] + (hi - lo)[None, :] * shade[:, None]
        else:
            self.paint(m, rgb)

    def segment(self, x0, y0, x1, y1, thickness, rgb, glow=False):
        """Draw an anti-aliased-width line segment directly onto the dot plane."""
        vx, vy = x1 - x0, y1 - y0
        l2 = vx * vx + vy * vy
        if l2 < 1e-6:
            return
        # Restrict bounding box for fast rendering across 900 frames.
        pad = thickness + 2.0
        bx0 = max(0, int(math.floor(min(x0, x1) - pad)))
        bx1 = min(DOT_W, int(math.ceil(max(x0, x1) + pad)))
        by0 = max(0, int(math.floor(min(y0, y1) - pad)))
        by1 = min(DOT_H, int(math.ceil(max(y0, y1) + pad)))
        if bx0 >= bx1 or by0 >= by1:
            return
        gx = XX[by0:by1, bx0:bx1]
        gy = YY[by0:by1, bx0:bx1]
        t = np.clip(((gx - x0) * vx + (gy - y0) * vy) / l2, 0.0, 1.0)
        dx = gx - (x0 + t * vx)
        dy = gy - (y0 + t * vy)
        m = (dx * dx + dy * dy) <= (thickness * thickness)
        if not np.any(m):
            return
        sub_f = self.field[by0:by1, bx0:bx1]
        sub_c = self.color[by0:by1, bx0:bx1]
        rgb_arr = np.asarray(rgb, dtype=np.float64)
        if glow:
            ex = sub_f & m
            fr = (~sub_f) & m
            if np.any(ex):
                sub_c[ex] = np.clip(sub_c[ex] + rgb_arr, 0.0, 255.0)
            if np.any(fr):
                sub_f |= fr
                sub_c[fr] = np.clip(rgb_arr, 0.0, 255.0)
        else:
            sub_f |= m
            sub_c[m] = rgb_arr

    def points(self, xs, ys, rgbs, radius=0.0):
        """Plot a batch of floating-point coordinates onto the Braille grid."""
        ix = np.rint(xs).astype(np.int32)
        iy = np.rint(ys).astype(np.int32)
        ok = (ix >= 0) & (ix < DOT_W) & (iy >= 0) & (iy < DOT_H)
        if not np.any(ok):
            return
        ix, iy = ix[ok], iy[ok]
        col = np.asarray(rgbs, dtype=np.float64)
        if col.ndim == 2:
            col = col[ok]
        if radius <= 0.6:
            self.field[iy, ix] = True
            self.color[iy, ix] = col
        else:
            offsets = [
                (dx, dy)
                for dy in range(-int(math.ceil(radius)), int(math.ceil(radius)) + 1)
                for dx in range(-int(math.ceil(radius)), int(math.ceil(radius)) + 1)
                if dx * dx + dy * dy <= radius * radius
            ]
            for dx, dy in offsets:
                jx = ix + dx
                jy = iy + dy
                v = (jx >= 0) & (jx < DOT_W) & (jy >= 0) & (jy < DOT_H)
                if np.any(v):
                    self.field[jy[v], jx[v]] = True
                    self.color[jy[v], jx[v]] = col[v] if col.ndim == 2 else col

    def gear(self, cx, cy, radius, teeth, angle, rgb_lo, rgb_hi, spokes=5, hub=0.22, clear_core=True):
        """Draw a toothed brass gear wheel with cut-out spokes and a turned hub."""
        outer = radius + max(2.2, radius * 0.11)
        bx0 = max(0, int(math.floor(cx - outer - 2)))
        bx1 = min(DOT_W, int(math.ceil(cx + outer + 2)))
        by0 = max(0, int(math.floor(cy - outer - 2)))
        by1 = min(DOT_H, int(math.ceil(cy + outer + 2)))
        if bx0 >= bx1 or by0 >= by1:
            return
        dx = XX[by0:by1, bx0:bx1] - cx
        dy = YY[by0:by1, bx0:bx1] - cy
        r = np.hypot(dx, dy)
        th = np.arctan2(dy, dx) - angle
        # Trapezoidal gear teeth profile around the outer pitch circle.
        tooth_wave = np.clip(np.cos(teeth * th) * 2.2, -1.0, 1.0)
        tooth_r = radius + (outer - radius) * (0.5 + 0.5 * tooth_wave)
        rim_in = radius * 0.78
        hub_r = radius * hub
        rim = (r >= rim_in) & (r <= tooth_r)
        hub_ring = (r >= hub_r * 0.48) & (r <= hub_r)
        # Radial spokes spanning between hub and inner rim.
        spoke_ang = np.abs(np.sin(0.5 * spokes * th))
        spoke_half = np.maximum(0.06, 1.5 / np.maximum(r, 1.0))
        spoke_mask = (r > hub_r * 0.85) & (r < rim_in + 0.8) & (spoke_ang < spoke_half)
        metal = rim | hub_ring | spoke_mask
        sub_f = self.field[by0:by1, bx0:bx1]
        sub_c = self.color[by0:by1, bx0:bx1]
        if clear_core:
            interior = r < rim_in
            sub_f &= ~(interior & ~metal)
        if np.any(metal):
            shade = 0.5 + 0.5 * np.cos(np.arctan2(dy[metal], dx[metal]) + 2.3)
            lo = np.asarray(rgb_lo, dtype=np.float64)
            hi = np.asarray(rgb_hi, dtype=np.float64)
            sub_f |= metal
            sub_c[metal] = lo[None, :] + (hi - lo)[None, :] * shade[:, None]

    def fade(self, factor):
        """Scale ink luminance toward background for smooth chapter dissolves."""
        if factor < 0.999:
            self.color[self.field] = BG[None, :] + (self.color[self.field] - BG[None, :]) * factor

    def composite_over(self, other, alpha):
        """Blend another canvas over this one during chapter transitions."""
        if alpha <= 0.001:
            return
        if alpha >= 0.999:
            self.field = other.field.copy()
            self.color = other.color.copy()
            return
        self.fade(1.0 - alpha)
        m = other.field
        if np.any(m):
            other_c = BG[None, :] + (other.color[m] - BG[None, :]) * alpha
            both = self.field & m
            only = (~self.field) & m
            if np.any(both):
                self.color[both] = np.clip(self.color[both] + other_c[both[m]] - BG[None, :] * 0.5, 0.0, 255.0)
            if np.any(only):
                self.field |= only
                self.color[only] = other_c[only[m]]

    def to_cells(self):
        """Pack the 248 x 180 Braille plane into a (45, 124) structured cell grid."""
        dots = self.field.reshape(H, 4, W, 2)
        masks = (dots * BITS[None, :, None, :]).sum(axis=(1, 3))
        sums = (self.color * self.field[:, :, None]).reshape(H, 4, W, 2, 3).sum(axis=(1, 3))
        counts = np.maximum(1, dots.sum(axis=(1, 3)))[:, :, None]
        rgb = np.clip(np.rint(sums / counts), 0, 255).astype(np.uint8)
        cells = np.zeros((H, W), dtype=[("glyph", "<u2"), ("ink", "u1", 3)])
        cells["glyph"] = np.where(masks > 0, 0x2800 + masks, 32)
        cells["ink"] = np.where(masks[:, :, None] > 0, rgb, BG)
        return cells


def put_text(cells, row, col, text, rgb):
    for i, ch in enumerate(text):
        c = col + i
        if 0 <= row < H and 0 <= c < W:
            cells[row, c]["glyph"] = ord(ch)
            cells[row, c]["ink"] = rgb
