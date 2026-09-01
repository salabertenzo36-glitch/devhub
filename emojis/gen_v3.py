#!/usr/bin/env python3
"""Generate professional custom emojis — thick, bold, clean."""

from PIL import Image, ImageDraw
import math
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE = 128
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 0)
TRANSPARENT = (0, 0, 0, 0)
STROKE = 6


def new():
    return Image.new("RGBA", (SIZE, SIZE), TRANSPARENT)


def draw_moderation():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 18, 110, 110), radius=18, fill=WHITE)
    d.rounded_rectangle((38, 42, 90, 82), radius=10, fill=BLACK)
    d.rounded_rectangle((56, 36, 72, 42), radius=3, fill=BLACK)
    d.rounded_rectangle((56, 82, 72, 92), radius=3, fill=BLACK)
    d.rectangle((60, 52, 68, 72), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


def draw_mod_avancee():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 18, 110, 110), radius=18, fill=WHITE)
    d.rounded_rectangle((40, 48, 88, 80), radius=10, fill=BLACK)
    d.rounded_rectangle((60, 38, 68, 48), radius=3, fill=BLACK)
    d.ellipse((56, 84, 72, 100), fill=BLACK)
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


def draw_vocal():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((28, 30, 68, 72), radius=12, fill=WHITE)
    d.rectangle((66, 42, 92, 56), fill=WHITE)
    d.rounded_rectangle((90, 36, 102, 62), radius=6, fill=WHITE)
    d.arc((38, 68, 90, 106), 0, 180, fill=WHITE, width=6)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


def draw_utilitaires():
    img = new()
    d = ImageDraw.Draw(img)
    gap = 36
    sz = 26
    ox, oy = 22, 22
    for r in range(2):
        for c in range(2):
            x = ox + c * gap
            y = oy + r * gap
            d.rounded_rectangle((x, y, x + sz, y + sz), radius=7, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "utilitaires.png"))


def draw_fun():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    for angle in range(0, 360, 72):
        rad = math.radians(angle - 90)
        x = cx + 34 * math.cos(rad)
        y = cy + 34 * math.sin(rad)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=WHITE)
    d.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


def draw_stats():
    img = new()
    d = ImageDraw.Draw(img)
    bars = [(22, 68, 14), (44, 48, 34), (66, 32, 50), (88, 52, 30)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 16, 108), radius=5, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


def draw_hierarchie():
    img = new()
    d = ImageDraw.Draw(img)
    d.polygon((64, 16, 100, 48, 82, 48, 88, 100, 40, 100, 46, 48, 28, 48), fill=WHITE)
    d.rounded_rectangle((46, 96, 82, 106), radius=4, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


def draw_tickets():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 24, 108, 100), radius=14, fill=WHITE)
    d.rounded_rectangle((20, 24, 108, 52), radius=14, fill=WHITE)
    d.rectangle((20, 40, 108, 52), fill=WHITE)
    d.ellipse((50, 34, 78, 62), fill=BLACK)
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


def draw_ghostping():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((32, 20, 96, 82), radius=16, fill=WHITE)
    d.rounded_rectangle((56, 82, 72, 96), radius=3, fill=WHITE)
    d.rounded_rectangle((44, 94, 84, 106), radius=5, fill=WHITE)
    d.ellipse((52, 38, 76, 62), fill=BLACK)
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


def draw_welcome():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc((22, 30, 106, 110), 180, 360, fill=WHITE, width=8)
    d.line((22, 70, 22, 96), fill=WHITE, width=8)
    d.line((106, 70, 106, 96), fill=WHITE, width=8)
    d.line((64, 14, 64, 48), fill=WHITE, width=6)
    d.line((48, 30, 64, 14), fill=WHITE, width=6)
    d.line((80, 30, 64, 14), fill=WHITE, width=6)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


def draw_automod():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 18, 110, 110), radius=18, fill=WHITE)
    d.rounded_rectangle((40, 48, 88, 80), radius=10, fill=BLACK)
    d.rounded_rectangle((60, 38, 68, 48), radius=3, fill=BLACK)
    d.line((46, 88, 62, 102), fill=BLACK, width=6)
    d.line((62, 102, 82, 72), fill=BLACK, width=6)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


def draw_salon():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 22, 106, 106), radius=12, fill=WHITE)
    d.rounded_rectangle((28, 28, 100, 100), radius=8, fill=BLACK)
    d.rounded_rectangle((36, 40, 62, 52), radius=5, fill=WHITE)
    d.rounded_rectangle((36, 58, 74, 70), radius=5, fill=WHITE)
    d.rounded_rectangle((36, 76, 58, 88), radius=5, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


def draw_bug():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((26, 30, 102, 100), fill=WHITE)
    d.ellipse((34, 38, 94, 92), fill=BLACK)
    d.ellipse((48, 52, 80, 78), fill=WHITE)
    d.line((26, 52, 12, 40), fill=WHITE, width=5)
    d.line((26, 78, 12, 90), fill=WHITE, width=5)
    d.line((102, 52, 116, 40), fill=WHITE, width=5)
    d.line((102, 78, 116, 90), fill=WHITE, width=5)
    d.line((64, 30, 64, 14), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


def draw_suggestion():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((34, 16, 94, 72), radius=20, fill=WHITE)
    d.rounded_rectangle((54, 68, 74, 86), radius=4, fill=WHITE)
    d.rounded_rectangle((46, 84, 82, 94), radius=5, fill=WHITE)
    d.rounded_rectangle((54, 32, 74, 52), radius=5, fill=BLACK)
    d.rectangle((62, 56, 66, 62), fill=BLACK)
    d.ellipse((62, 66, 66, 70), fill=BLACK)
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


def draw_support():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 36, 78, 96), radius=22, fill=WHITE)
    d.arc((58, 20, 110, 78), 90, 270, fill=WHITE, width=10)
    d.rounded_rectangle((94, 40, 108, 68), radius=5, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


def draw_report():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((28, 16, 100, 110), radius=12, fill=WHITE)
    d.rounded_rectangle((36, 24, 92, 102), radius=8, fill=BLACK)
    d.rounded_rectangle((58, 36, 70, 64), radius=4, fill=WHITE)
    d.ellipse((58, 72, 70, 84), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


def draw_autre():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 16, 106, 110), radius=12, fill=WHITE)
    d.rounded_rectangle((30, 24, 98, 102), radius=8, fill=BLACK)
    d.rounded_rectangle((38, 34, 90, 46), radius=5, fill=WHITE)
    d.rounded_rectangle((38, 54, 90, 66), radius=5, fill=WHITE)
    d.rounded_rectangle((38, 74, 90, 86), radius=5, fill=WHITE)
    d.rounded_rectangle((38, 94, 68, 102), radius=5, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


def draw_music():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((22, 68, 46, 92), fill=WHITE)
    d.ellipse((82, 56, 106, 80), fill=WHITE)
    d.rectangle((40, 26, 48, 86), fill=WHITE)
    d.rectangle((100, 18, 108, 72), fill=WHITE)
    d.polygon((48, 24, 108, 14, 108, 30, 48, 40), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


def draw_cleanup():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((34, 44, 94, 108), radius=10, fill=WHITE)
    d.rounded_rectangle((28, 30, 100, 52), radius=10, fill=WHITE)
    d.rectangle((28, 42, 100, 52), fill=WHITE)
    d.rectangle((56, 20, 72, 34), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "cleanup.png"))


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
    draw_autre()
    draw_music()
    draw_cleanup()
    count = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')])
    print(f"Done! {count} emojis generated.")
