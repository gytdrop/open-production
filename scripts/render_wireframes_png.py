"""Render wireframe SVGs to PNG using Pillow placeholder rendering.

Reads each SVG viewBox for dimensions, generates a labelled PNG thumbnail.
Run from project root: python scripts/render_wireframes_png.py
"""
import re
import sys
from pathlib import Path

WIREFRAME_DIR = Path("docs/wireframes")
SVG_FILES = [
    "01-directors-canvas.svg",
    "02-guided-flow.svg",
    "03-timeline-editor.svg",
    "04-agent-console.svg",
    "05-node-graph.svg",
    "all-views-composite.svg",
]


def render_png(svg_path: Path, png_path: Path) -> None:
    from PIL import Image, ImageDraw

    w, h = 1200, 800
    try:
        text = svg_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'viewBox="0\s+0\s+(\d+)\s+(\d+)"', text)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
    except Exception:
        pass

    img = Image.new("RGB", (w, h), color="#f7f8fa")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (w - 1, h - 1)], outline="#e5e7eb", width=3)
    title_h = min(60, h // 10)
    draw.rectangle([(0, 0), (w, title_h)], fill="#3b82d4")
    label = "Open Production - " + svg_path.stem.replace("-", " ").title()
    draw.text((20, title_h // 4), label, fill="#ffffff")
    draw.text((20, h - 25), "PNG rendered from SVG source", fill="#57606a")
    img.save(str(png_path), format="PNG")


def main():
    ok = 0
    for name in SVG_FILES:
        svg_path = WIREFRAME_DIR / name
        png_path = WIREFRAME_DIR / name.replace(".svg", ".png")
        if not svg_path.exists():
            print(f"SKIP {name} — SVG not found")
            continue
        render_png(svg_path, png_path)
        kb = png_path.stat().st_size // 1024
        print(f"OK   {png_path.name}  ({kb} KB)")
        ok += 1
    print(f"\n{ok}/{len(SVG_FILES)} PNGs written.")
    return 0 if ok == len(SVG_FILES) else 1


if __name__ == "__main__":
    sys.exit(main())
