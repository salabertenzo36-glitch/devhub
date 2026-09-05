#!/usr/bin/env python3
"""Generate emojis from Lucide — download SVG, convert with rsvg-convert, make white."""

import urllib.request
import subprocess
import io
import os
from PIL import Image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload")
SIZE = 128
RSVG = "/opt/homebrew/bin/rsvg-convert"

ICON_MAP = {
    "moderation": "shield-check",
    "mod_avancee": "shield",
    "vocal": "mic",
    "utilitaires": "layout-grid",
    "fun": "sparkles",
    "stats": "bar-chart-3",
    "hierarchie": "users",
    "tickets": "ticket",
    "ghostping": "ghost",
    "welcome": "hand",
    "automod": "shield-ban",
    "salon": "hash",
    "bug": "bug",
    "suggestion": "lightbulb",
    "support": "headphones",
    "report": "flag",
    "autre": "ellipsis",
    "music": "music",
    "cleanup": "eraser",
}


def download_svg(icon_name):
    url = f"https://unpkg.com/lucide-static@latest/icons/{icon_name}.svg"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def svg_to_png(svg_data):
    proc = subprocess.run(
        [RSVG, "-w", str(SIZE), "-h", str(SIZE)],
        input=svg_data,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())
    return Image.open(io.BytesIO(proc.stdout)).convert("RGBA")


def make_white(img):
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        if a > 0:
            new_data.append((255, 255, 255, a))
        else:
            new_data.append((0, 0, 0, 0))
    img.putdata(new_data)
    return img


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating {len(ICON_MAP)} emojis from Lucide SVGs via rsvg-convert...")

    for name, icon in ICON_MAP.items():
        try:
            svg_data = download_svg(icon)
            img = svg_to_png(svg_data)
            img = make_white(img)
            path = os.path.join(OUTPUT_DIR, f"{name}.png")
            img.save(path, "PNG")
            print(f"  {name}.png <- {icon}")
        except Exception as e:
            print(f"  ERROR {name}: {e}")

    count = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")])
    print(f"Done! {count} emojis in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
