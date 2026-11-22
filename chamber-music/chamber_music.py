# MIT License
# Copyright (c) 2026 Rari-One
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Chamber Music — a silent instrument for shell and pressure wave."""
import argparse
import math
import shutil
import sys
import time

W, H = 112, 38
FPS, FRAMES = 16, 160
TAU = math.tau
PAPER = (12, 23, 30)
INK = (121, 159, 153)
GOLD = (242, 190, 117)
LIGHT = (255, 231, 182)
BITS = ((1, 8), (2, 16), (4, 32), (64, 128))


def mix(a, b, amount):
    amount = max(0, min(1, amount))
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def pulse(phase, distance):
    # A long breath, followed by silence before the next attack.
    age = (phase - 0.76 * distance) % 1
    return (1 - math.exp(-age * 100)) * math.exp(-age * 15) * 1.68


def shell_point(x, y):
    """Unroll the shell to (angle along the spiral, depth across a chamber)."""
    radius = math.hypot(x, y)
    if radius < 0.022:
        return None
    growth, lip = 0.185, 0.58
    turn = (math.atan2(y, x) - lip) % TAU - TAU
    outside = 1.43 * math.exp(growth * turn)
    log_depth = math.log(radius / outside) / (-growth * TAU)
    # Bend the final mouth into a convex lip across the cut face.
    depth = log_depth % 1
    bend = 0.25 * math.sin(math.pi * depth)
    if log_depth < 0:
        if log_depth < -1 or turn + TAU > bend:
            return None
    angle = turn - TAU * math.floor(log_depth)
    if angle > bend or angle < -7.1 * math.pi:
        return None
    position = (angle + 7.1 * math.pi) / (7.1 * math.pi)
    # Curved septa between chambers; narrow twin lines at each whorl wall.
    bowed = angle - bend + 0.20 * math.sin(TAU * depth)
    rib = abs(math.sin(8 * bowed)) * radius / 8
    wall = min(depth, 1 - depth) * radius * growth * TAU
    mouth = abs(angle - bend) * radius
    return min(wall, abs(wall - 0.028), rib, mouth), depth, position


def engrave():
    """Combine eight samples into each terminal cell's Braille engraving."""
    cells = []
    for row in range(3, H - 4):
        for col in range(3, 81):
            bits = 0
            samples = []
            for dy in range(4):
                for dx in range(2):
                    x = (col + (dx + 0.5) / 2 - 35) / 29
                    y = (row + (dy + 0.5) / 4 - 20) / 14.5
                    sample = shell_point(x, y)
                    if sample:
                        samples.append(sample)
                        if sample[0] < 0.011:
                            bits |= BITS[dy][dx]
            if samples:
                _, depth, position = samples[len(samples) // 2]
                # Nacre is scored with fine interference bands.
                grain = 0.5 + 0.5 * math.cos(34 * depth + 8 * position)
                mark = chr(0x2800 + bits) if bits else " ·:∙"[int(grain * 3.99)]
                shade = mix((29, 55, 65), (69, 132, 132), grain)
                if bits:
                    shade = mix((95, 142, 142), (231, 207, 158), depth)
                cells.append((row, col, mark, shade, position, bool(bits)))
    return cells


def picture(cells, frame):
    phase = (frame % FRAMES) / FRAMES
    page = [[(" ", PAPER)] * W for _ in range(H)]

    def put(x, y, word, color=INK):
        for i, ch in enumerate(word):
            page[y][x + i] = ch, color

    put(3, 1, "C H A M B E R   M U S I C", LIGHT)
    put(82, 1, "SECTION  /  LONGITUDINAL")
    put(3, 3, "─" * 106, (51, 74, 77))
    for y in range(5, 33):
        put(79, y, "│", (47, 68, 72))
    for y, col, ch, base, pos, edge in cells:
        energy = pulse(phase, pos)
        if ch == " " and energy > 0.20:
            ch = "·"
        if energy > 0.55 and not edge:
            ch = {" ": "·", "·": "∙", ":": ":", "∙": "•"}[ch]
        page[y][col] = ch, mix(base, LIGHT if edge else (255, 139, 68), energy)
    put(3, 33, "└──┬──┬──┬──┘", INK)
    put(3, 34, "relative scale")
    put(82, 8, "PRESSURE AT THE LIP", GOLD)
    # The trace has memory: one terminal column samples one earlier frame.
    for i in range(26):
        past = phase - (25 - i) / FRAMES
        t = (past - 0.76) % 1
        amplitude = pulse(past, 1) * math.sin(TAU * 14 * t)
        y = round(15 - 4 * amplitude)
        put(82 + i, 15, "·", (50, 72, 77))
        put(82 + i, y, "●" if i == 25 else "•", GOLD if i == 25 else INK)
    put(82, 22, "CHAMBER RESPONSE")
    for k in range(5):
        p = k / 4
        energy = pulse(phase, p)
        put(82, 24 + k, ("core", "", "", "", "lip ")[k].ljust(5) + "┊")
        put(88, 24 + k, "─" * 17, (48, 72, 77))
        put(88, 24 + k, "━" * round(17 * energy), GOLD)
    put(3, 36, "Fig. 1    An instrument in cross section.", INK)
    put(82, 36, "ONE BREATH  /  10 s")
    return page


def terminal(page, color):
    lines = []
    for row in page:
        line = []
        last = None
        for ch, rgb in row:
            if color and ch != " " and rgb != last:
                line.append("\033[38;2;%d;%d;%dm" % rgb)
                last = rgb
            line.append(ch)
        lines.append("".join(line))
    if color:
        bg = "\033[48;2;%d;%d;%dm" % PAPER
        return bg + ("\033[0m\n" + bg).join(lines) + "\033[0m"
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--still", action="store_true", help="print a single frame")
    parser.add_argument("--frame", type=int, default=124, help="still frame index (wraps at 160)")
    parser.add_argument("--no-color", action="store_true", help="use plain characters")
    args = parser.parse_args()
    cells = engrave()
    live = sys.stdout.isatty()
    color = live and not args.no_color
    if args.still or not live:
        print(terminal(picture(cells, args.frame), color))
        return
    start = time.monotonic()
    try:
        print("\033[?1049h\033[?25l", end="")
        while True:
            size = shutil.get_terminal_size()
            frame = int((time.monotonic() - start) * FPS)
            if size.columns < W or size.lines < H:
                view = f"Chamber Music needs {W} columns by {H} rows."
            else:
                view = terminal(picture(cells, frame), color)
            print("\033[H" + view + "\033[J", end="", flush=True)
            time.sleep(max(0, start + (frame + 1) / FPS - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[0m\033[?25h\033[?1049l", end="", flush=True)


if __name__ == "__main__":
    main()
