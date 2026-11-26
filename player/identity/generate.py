"""Render the two rectangle-based SVG masters. Requires Pillow 13.0.0."""
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SVG = "{http://www.w3.org/2000/svg}"
# A 20x grid represents every half-unit radius exactly before downsampling.
SCALE = 20


def render(master, fills):
    root = ElementTree.parse(HERE / master).getroot()
    if root.get("viewBox") != "0 0 100 100":
        raise ValueError("Expected the 100-unit square identity master")
    image = Image.new("RGBA", (100 * SCALE, 100 * SCALE))
    draw = ImageDraw.Draw(image)

    def paint(node, fill):
        fill = fills.get(node.get("id"), node.get("fill", fill))
        if node.tag in (SVG + "svg", SVG + "g"):
            for child in node:
                paint(child, fill)
        elif node.tag == SVG + "rect":
            x, y, w, h, r = (round(float(node.get(k, 0)) * SCALE)
                              for k in ("x", "y", "width", "height", "rx"))
            draw.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=r, fill=fill)
        elif node.tag != SVG + "title":
            raise ValueError(f"Unsupported identity element {node.tag}")

    paint(root, None)
    return image


if __name__ == "__main__":
    icon = render("lab-player-icon.svg", {})
    for size in (16, 32, 48, 256):
        icon.resize((size, size), Image.Resampling.LANCZOS).save(HERE / f"icon-{size}.png")
    icon.save(HERE / "lab-player.ico", sizes=[(n, n) for n in (16, 20, 24, 32, 40, 48, 64, 128, 256)])
    for theme, body, tip in (("lab", "#BEAEDC", "#89E2BF"), ("ide", "#C49DF6", "#80C2FF")):
        mark = render("lab-player-master.svg", {"cells": body, "leading-cell": tip})
        mark.resize((24, 24), Image.Resampling.LANCZOS).save(HERE / f"mark-{theme}.png")
