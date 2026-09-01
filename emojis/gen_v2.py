#!/usr/bin/env python3
"""Generate custom emojis in Discord style (white icons on transparent background)."""

from PIL import Image, ImageDraw
import math
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE = 128
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def new():
    return Image.new("RGBA", (SIZE, SIZE), TRANSPARENT)


def draw_moderation():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    d.rounded_rectangle((20, 25, 108, 108), radius=16, fill=WHITE)
    d.rounded_rectangle((40, 50, 88, 80), radius=8, fill=(0, 0, 0, 255))
    d.rectangle((60, 48, 68, 75), fill=(0, 0, 0, 255))
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


def draw_mod_avancee():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 25, 108, 108), radius=16, fill=WHITE)
    d.rounded_rectangle((42, 55, 86, 78), radius=6, fill=(0, 0, 0, 255))
    d.rectangle((62, 48, 66, 55), fill=(0, 0, 0, 255))
    d.ellipse((58, 82, 70, 94), fill=(0, 0, 0, 255))
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


def draw_vocal():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 35, 70, 75), radius=10, fill=WHITE)
    d.rectangle((68, 50, 90, 60), fill=WHITE)
    d.rounded_rectangle((88, 42, 98, 68), radius=5, fill=WHITE)
    d.arc((40, 72, 88, 108), 0, 180, fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


def draw_utilitaires():
    img = new()
    d = ImageDraw.Draw(img)
    s = 28
    for r in range(2):
        for c in range(2):
            x = 24 + c * 38
            y = 24 + r * 38
            d.rounded_rectangle((x, y, x + s, y + s), radius=6, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "utilitaires.png"))


def draw_fun():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    for angle in range(0, 360, 72):
        rad = math.radians(angle - 90)
        x = cx + 35 * math.cos(rad)
        y = cy + 35 * math.sin(rad)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=WHITE)
    d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


def draw_stats():
    img = new()
    d = ImageDraw.Draw(img)
    bars = [(25, 65, 12), (45, 50, 27), (65, 35, 42), (85, 55, 22)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 14, 105), radius=4, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


def draw_hierarchie():
    img = new()
    d = ImageDraw.Draw(img)
    d.polygon((64, 20, 95, 50, 80, 50, 85, 95, 43, 95, 48, 50, 33, 50), fill=WHITE)
    d.rectangle((48, 92, 80, 100), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


def draw_tickets():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 30, 106, 98), radius=10, fill=WHITE)
    d.rectangle((22, 30, 106, 50), fill=WHITE)
    d.ellipse((50, 38, 78, 66), fill=(0, 0, 0, 255))
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


def draw_ghostping():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((35, 25, 93, 85), radius=14, fill=WHITE)
    d.rectangle((58, 85, 70, 100), fill=WHITE)
    d.rectangle((45, 98, 83, 108), fill=WHITE)
    d.ellipse((53, 42, 75, 64), fill=(0, 0, 0, 255))
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


def draw_welcome():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc((25, 35, 103, 113), 180, 360, fill=WHITE, width=6)
    d.line((25, 74, 25, 95), fill=WHITE, width=6)
    d.line((103, 74, 103, 95), fill=WHITE, width=6)
    d.line((64, 20, 64, 50), fill=WHITE, width=5)
    d.line((50, 35, 64, 20), fill=WHITE, width=5)
    d.line((78, 35, 64, 20), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


def draw_automod():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 25, 108, 108), radius=16, fill=WHITE)
    d.rounded_rectangle((42, 55, 86, 78), radius=6, fill=(0, 0, 0, 255))
    d.rectangle((62, 48, 66, 55), fill=(0, 0, 0, 255))
    d.line((48, 86, 60, 98), fill=(0, 0, 0, 255), width=5)
    d.line((60, 98, 80, 74), fill=(0, 0, 0, 255), width=5)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


def draw_salon():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((25, 25, 103, 103), radius=10, fill=WHITE)
    d.rounded_rectangle((30, 30, 98, 98), radius=8, fill=(0, 0, 0, 255))
    d.rounded_rectangle((38, 42, 60, 54), radius=4, fill=WHITE)
    d.rounded_rectangle((38, 60, 72, 72), radius=4, fill=WHITE)
    d.rounded_rectangle((38, 78, 56, 90), radius=4, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


def draw_bug():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((30, 35, 98, 98), fill=WHITE)
    d.ellipse((38, 43, 90, 90), fill=(0, 0, 0, 255))
    d.ellipse((50, 55, 78, 78), fill=WHITE)
    d.line((30, 55, 15, 45), fill=WHITE, width=4)
    d.line((30, 75, 15, 85), fill=WHITE, width=4)
    d.line((98, 55, 113, 45), fill=WHITE, width=4)
    d.line((98, 75, 113, 85), fill=WHITE, width=4)
    d.line((64, 35, 64, 18), fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


def draw_suggestion():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((38, 20, 90, 75), radius=18, fill=WHITE)
    d.rectangle((55, 72, 73, 88), fill=WHITE)
    d.rectangle((48, 88, 80, 95), fill=WHITE)
    d.rounded_rectangle((55, 35, 73, 55), radius=4, fill=(0, 0, 0, 255))
    d.rectangle((61, 58, 67, 65), fill=(0, 0, 0, 255))
    d.ellipse((61, 68, 67, 74), fill=(0, 0, 0, 255))
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


def draw_support():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((25, 40, 80, 95), radius=20, fill=WHITE)
    d.arc((60, 25, 108, 80), 90, 270, fill=WHITE, width=8)
    d.rectangle((95, 45, 108, 70), fill=WHITE)
    d.rounded_rectangle((95, 45, 108, 70), radius=4, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


def draw_report():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 20, 98, 108), radius=10, fill=WHITE)
    d.rounded_rectangle((38, 28, 90, 95), radius=6, fill=(0, 0, 0, 255))
    d.rectangle((60, 40, 68, 65), fill=WHITE)
    d.ellipse((60, 72, 68, 80), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


def draw_creation():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 30, 108, 108), radius=10, fill=WHITE)
    d.rounded_rectangle((28, 38, 100, 100), radius=6, fill=(0, 0, 0, 255))
    d.rounded_rectangle((38, 48, 90, 58), radius=3, fill=WHITE)
    d.rounded_rectangle((38, 64, 72, 74), radius=3, fill=WHITE)
    d.rounded_rectangle((38, 80, 60, 90), radius=3, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


def draw_autre():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((25, 20, 103, 108), radius=10, fill=WHITE)
    d.rounded_rectangle((32, 27, 96, 101), radius=6, fill=(0, 0, 0, 255))
    d.rounded_rectangle((40, 38, 88, 48), radius=3, fill=WHITE)
    d.rounded_rectangle((40, 56, 88, 66), radius=3, fill=WHITE)
    d.rounded_rectangle((40, 74, 88, 84), radius=3, fill=WHITE)
    d.rounded_rectangle((40, 92, 68, 100), radius=3, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


def draw_music():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((25, 70, 45, 90), fill=WHITE)
    d.ellipse((83, 60, 103, 80), fill=WHITE)
    d.rectangle((42, 30, 48, 85), fill=WHITE)
    d.rectangle((100, 22, 106, 75), fill=WHITE)
    d.polygon((48, 28, 106, 18, 106, 32, 48, 42), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


if __name__ == "__main__":
    print("Generating emojis...")
    draw_moderation()
    draw_mod_avancee()
    draw_vocal()
    draw_utilitaires()
    draw_fun()
    draw_stats()
    draw_hierarchie()
    draw_tickets()
    draw_ghostping()
    draw_welcome()
    draw_automod()
    draw_salon()
    draw_bug()
    draw_suggestion()
    draw_support()
    draw_report()
    draw_creation()
    draw_autre()
    draw_music()
    print(f"Done! {len(os.listdir(OUTPUT_DIR))} files in {OUTPUT_DIR}")
