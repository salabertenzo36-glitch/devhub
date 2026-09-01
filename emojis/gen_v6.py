#!/usr/bin/env python3
"""Generate pro emojis v6 — transparent bg, detailed, bold icons."""

from PIL import Image, ImageDraw
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload")
SIZE = 128
T = (0, 0, 0, 0)
W = (255, 255, 255, 255)
B = (0, 0, 0, 0)


def new():
    return Image.new("RGBA", (SIZE, SIZE), T)


# ─── MODERATION (shield + checkmark) ───
def draw_moderation():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 10, 108, 118), radius=18, fill=W)
    d.rounded_rectangle((28, 18, 100, 110), radius=14, fill=B)
    d.polygon((64, 14, 108, 38, 108, 76, 64, 114, 20, 76, 20, 38), fill=W)
    d.polygon((64, 24, 100, 42, 100, 72, 64, 106, 28, 72, 28, 42), fill=B)
    d.line((46, 64, 58, 80), fill=W, width=8)
    d.line((58, 80, 86, 48), fill=W, width=8)
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


# ─── MOD AVANCÉE (shield + gear) ───
def draw_mod_avancee():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 10, 108, 118), radius=18, fill=W)
    d.rounded_rectangle((28, 18, 100, 110), radius=14, fill=B)
    d.polygon((64, 14, 108, 38, 108, 76, 64, 114, 20, 76, 20, 38), fill=W)
    d.polygon((64, 24, 100, 42, 100, 72, 64, 106, 28, 72, 28, 42), fill=B)
    cx, cy = 64, 66
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + 14 * math.cos(rad)
        y1 = cy + 14 * math.sin(rad)
        x2 = cx + 22 * math.cos(rad)
        y2 = cy + 22 * math.sin(rad)
        d.line((x1, y1, x2, y2), fill=W, width=5)
    d.ellipse((56, 58, 72, 74), fill=B)
    d.ellipse((59, 61, 69, 71), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


# ─── VOCAL (micro + stand) ───
def draw_vocal():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 10, 88, 58), radius=24, fill=W)
    d.rounded_rectangle((48, 18, 80, 50), radius=16, fill=B)
    d.arc((28, 48, 100, 104), 0, 180, fill=W, width=8)
    d.line((64, 100, 64, 114), fill=W, width=8)
    d.line((48, 114, 80, 114), fill=W, width=8)
    d.line((48, 114, 48, 120), fill=W, width=4)
    d.line((80, 114, 80, 120), fill=W, width=4)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


# ─── UTILITAIRES (4 rounded squares grid) ───
def draw_utilitaires():
    img = new()
    d = ImageDraw.Draw(img)
    gap = 36
    sz = 28
    ox, oy = 18, 18
    for r in range(2):
        for c in range(2):
            x = ox + c * gap
            y = oy + r * gap
            d.rounded_rectangle((x, y, x + sz, y + sz), radius=8, fill=W)
    img.save(os.path.join(OUTPUT_DIR, "utilitaires.png"))


# ─── FUN (sparkle star) ───
def draw_fun():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = 64, 64
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 46 if i % 2 == 0 else 18
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(points, fill=W)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


# ─── STATS (bar chart rising) ───
def draw_stats():
    img = new()
    d = ImageDraw.Draw(img)
    bars = [(16, 72, 18), (38, 52, 38), (60, 34, 56), (82, 56, 34)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 18, 114), radius=6, fill=W)
    d.line((12, 114, 116, 114), fill=W, width=5)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


# ─── HIÉRARCHIE (people tree) ───
def draw_hierarchie():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((46, 6, 82, 42), fill=W)
    d.line((64, 42, 64, 60), fill=W, width=7)
    d.line((64, 60, 30, 82), fill=W, width=7)
    d.line((64, 60, 98, 82), fill=W, width=7)
    d.ellipse((18, 76, 50, 108), fill=W)
    d.ellipse((78, 76, 110, 108), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


# ─── TICKETS (ticket stub with tear) ───
def draw_tickets():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 20, 114, 100), radius=14, fill=W)
    d.rectangle((14, 48, 114, 66), fill=B)
    d.ellipse((46, 26, 82, 62), fill=B)
    d.line((14, 66, 114, 66), fill=B, width=3)
    for y in range(72, 98, 8):
        d.line((20, y, 108, y), fill=B, width=2)
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


# ─── GHOSTPING (cute ghost) ───
def draw_ghostping():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((24, 12, 104, 78), radius=24, fill=W)
    d.polygon([(24, 74), (24, 112), (40, 96), (54, 112), (64, 96), (74, 112), (88, 96), (104, 112), (104, 74)], fill=W)
    d.ellipse((40, 32, 56, 48), fill=B)
    d.ellipse((72, 32, 88, 48), fill=B)
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


# ─── WELCOME (waving hand) ───
def draw_welcome():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((28, 46, 68, 98), radius=12, fill=W)
    d.rounded_rectangle((52, 36, 78, 88), radius=12, fill=W)
    d.rounded_rectangle((70, 50, 96, 96), radius=12, fill=W)
    d.rounded_rectangle((38, 90, 84, 112), radius=10, fill=W)
    d.line((32, 26, 24, 14), fill=W, width=5)
    d.line((46, 22, 46, 8), fill=W, width=5)
    d.line((60, 24, 66, 10), fill=W, width=5)
    d.line((74, 28, 84, 16), fill=W, width=5)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


# ─── AUTOMOD (shield + X) ───
def draw_automod():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((20, 10, 108, 118), radius=18, fill=W)
    d.rounded_rectangle((28, 18, 100, 110), radius=14, fill=B)
    d.polygon((64, 14, 108, 38, 108, 76, 64, 114, 20, 76, 20, 38), fill=W)
    d.polygon((64, 24, 100, 42, 100, 72, 64, 106, 28, 72, 28, 42), fill=B)
    d.line((46, 46, 82, 84), fill=W, width=8)
    d.line((82, 46, 46, 84), fill=W, width=8)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


# ─── SALON (hash channel icon) ───
def draw_salon():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 14, 114, 114), radius=16, fill=W)
    d.rounded_rectangle((22, 22, 106, 106), radius=12, fill=B)
    d.line((42, 30, 34, 98), fill=W, width=8)
    d.line((60, 30, 52, 98), fill=W, width=8)
    d.line((88, 30, 80, 98), fill=W, width=8)
    d.line((106, 30, 98, 98), fill=W, width=8)
    d.line((30, 44, 98, 44), fill=W, width=8)
    d.line((26, 88, 94, 88), fill=W, width=8)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


# ─── BUG (beetle/bug) ───
def draw_bug():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((28, 32, 100, 108), fill=W)
    d.ellipse((36, 40, 92, 100), fill=B)
    d.line((64, 32, 64, 14), fill=W, width=6)
    d.ellipse((58, 8, 70, 20), fill=W)
    d.line((28, 50, 10, 34), fill=W, width=5)
    d.line((10, 34, 4, 24), fill=W, width=5)
    d.line((28, 84, 10, 100), fill=W, width=5)
    d.line((100, 50, 118, 34), fill=W, width=5)
    d.line((118, 34, 124, 24), fill=W, width=5)
    d.line((100, 84, 118, 100), fill=W, width=5)
    d.line((64, 58, 64, 90), fill=W, width=4)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


# ─── SUGGESTION (lightbulb glowing) ───
def draw_suggestion():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((32, 4, 96, 70), fill=W)
    d.rounded_rectangle((42, 66, 86, 80), radius=4, fill=W)
    d.rounded_rectangle((46, 80, 82, 88), radius=4, fill=W)
    d.rounded_rectangle((50, 88, 78, 96), radius=4, fill=W)
    d.line((64, 106, 64, 120), fill=W, width=5)
    d.line((50, 116, 78, 116), fill=W, width=5)
    d.line((50, 120, 78, 120), fill=W, width=5)
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


# ─── SUPPORT (headset with mic) ───
def draw_support():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc((16, 10, 112, 90), 180, 360, fill=W, width=10)
    d.rounded_rectangle((12, 50, 34, 92), radius=10, fill=W)
    d.rounded_rectangle((94, 50, 116, 92), radius=10, fill=W)
    d.rounded_rectangle((40, 76, 88, 108), radius=16, fill=W)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


# ─── REPORT (flag on pole) ───
def draw_report():
    img = new()
    d = ImageDraw.Draw(img)
    d.line((28, 8, 28, 120), fill=W, width=7)
    d.rounded_rectangle((28, 8, 108, 76), radius=12, fill=W)
    d.rounded_rectangle((38, 18, 98, 66), radius=8, fill=B)
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


# ─── AUTRE (3 dots menu) ───
def draw_autre():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 12, 112, 116), radius=16, fill=W)
    d.rounded_rectangle((24, 20, 104, 108), radius=12, fill=B)
    for y in range(38, 92, 20):
        d.ellipse((54, y, 74, y + 18), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


# ─── MUSIC (double note) ───
def draw_music():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((14, 72, 52, 110), fill=W)
    d.ellipse((76, 56, 114, 94), fill=W)
    d.rectangle((46, 18, 54, 104), fill=W)
    d.rectangle((108, 10, 116, 88), fill=W)
    d.polygon((54, 16, 116, 4, 116, 24, 54, 36), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


# ─── CLEANUP (broom / sparkles) ───
def draw_cleanup():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((34, 56, 94, 118), radius=12, fill=W)
    d.line((64, 4, 64, 60), fill=W, width=8)
    d.rounded_rectangle((34, 4, 94, 26), radius=10, fill=W)
    for x in range(40, 92, 12):
        d.line((x, 118, x, 126), fill=W, width=4)
    img.save(os.path.join(OUTPUT_DIR, "cleanup.png"))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating emojis v6 (transparent bg)...")
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
    print(f"Done! {count} emojis")
