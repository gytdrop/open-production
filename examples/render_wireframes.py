"""Render SVG wireframes to PNG using an SVG parser + Pillow fallback.

Attempts svglib first; if import or rendering fails, falls back to generating
a labelled placeholder PNG so the 6 output files always exist.

Usage: python examples/render_wireframes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIREFRAME_DIR = ROOT / "docs" / "wireframes"

SVG_FILES = [
    "01-directors-canvas.svg",
    "02-guided-flow.svg",
    "03-timeline-editor.svg",
    "04-agent-console.svg",
    "05-node-graph.svg",
    "all-views-composite.svg",
]

WIDTH, HEIGHT = 1200, 800


def render_with_svglib(svg_path: Path, png_path: Path) -> bool:
    """Try to render with svglib + reportlab. Returns True on success."""
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM

        drawing = svg2rlg(str(svg_path))
        if drawing is None:
            return False
        renderPM.drawToFile(drawing, str(png_path), fmt="PNG")
        return png_path.exists()
    except Exception:
        return False


def render_placeholder(svg_path: Path, png_path: Path) -> None:
    """Generate a labelled placeholder PNG using Pillow."""
    from PIL import Image, ImageDraw

    # Parse the SVG viewBox to get intended dimensions, fall back to defaults
    w, h = WIDTH, HEIGHT
    try:
        import re
        text = svg_path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'viewBox=["\']0\s+0\s+(\d+)\s+(\d+)["\']', text)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
    except Exception:
        pass

    # Create a white canvas with a light grey border
    img = Image.new("RGB", (w, h), color="#f7f8fa")
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle([(0, 0), (w - 1, h - 1)], outline="#e5e7eb", width=3)

    # Title box
    title_h = min(60, h // 10)
    draw.rectangle([(0, 0), (w, title_h)], fill="#3b82d4")

    # Label: SVG file name (without extension, replace dashes with spaces)
    label = svg_path.stem.replace("-", " ").title()
    label = f"Open Production — {label}"

    # Draw label text using the default font (no truetype required)
    draw.text((20, title_h // 4), label, fill="#ffffff")

    # Watermark
    note = "(PNG placeholder rendered from SVG source)"
    draw.text((20, h - 25), note, fill="#57606a")

    img.save(str(png_path), format="PNG")


def main() -> int:
    ok_count = 0
    for name in SVG_FILES:
        svg_path = WIREFRAME_DIR / name
        png_path = WIREFRAME_DIR / name.replace(".svg", ".png")

        if not svg_path.exists():
            print(f"  SKIP  {name} (SVG not found)", file=sys.stderr)
            continue

        # Try high-quality render first, fall back to placeholder
        if render_with_svglib(svg_path, png_path):
            method = "svglib"
        else:
            render_placeholder(svg_path, png_path)
            method = "placeholder"

        size_kb = png_path.stat().st_size // 1024
        print(f"  OK [{method}]  {png_path.name}  ({size_kb} KB)")
        ok_count += 1

    print(f"\n{ok_count}/{len(SVG_FILES)} PNGs written to {WIREFRAME_DIR}")
    return 0 if ok_count == len(SVG_FILES) else 1


if __name__ == "__main__":
    sys.exit(main())
