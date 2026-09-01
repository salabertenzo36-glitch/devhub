#!/usr/bin/env python3
"""Generate pro emojis v4 — thick strokes, bold, detailed, 128x128."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload")
SIZE = 128
WHITE = (255, 255, 255, 255)
BG = (0, 0, 0, 0)
T = (0, 0, 0, 0)


def new():
    return Image.new("RGBA", (SIZE, SIZE), BG)


# ─── MODERATION (shield + check) ───
def draw_moderation():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 12, 112, 116), radius=20, fill=WHITE)
    d.rounded_rectangle((24, 20, 104, 108), radius=16, fill=T)
    d.polygon((64, 18, 106, 40, 106, 72, 64, 112, 22, 72, 22, 40), fill=WHITE)
    d.polygon((64, 26, 98, 44, 98, 68, 64, 104, 30, 68, 30, 44), fill=T)
    d.line((44, 66, 58, 80), fill=WHITE, width=6)
    d.line((58, 80, 84, 52), fill=WHITE, width=6)
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


# ─── MOD AVANCÉE (shield + gear) ───
def draw_mod_avancee():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 12, 112, 116), radius=20, fill=WHITE)
    d.rounded_rectangle((24, 20, 104, 108), radius=16, fill=T)
    d.polygon((64, 18, 106, 40, 106, 72, 64, 112, 22, 72, 22, 40), fill=WHITE)
    d.polygon((64, 26, 98, 44, 98, 68, 64, 104, 30, 68, 30, 44), fill=T)
    cx, cy = 64, 68
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + 18 * math.cos(rad)
        y1 = cy + 18 * math.sin(rad)
        x2 = cx + 26 * math.cos(rad)
        y2 = cy + 26 * math.sin(rad)
        d.line((x1, y1, x2, y2), fill=WHITE, width=4)
    d.ellipse((54, 58, 74, 78), fill=T)
    d.ellipse((58, 62, 70, 74), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


# ─── VOCAL (micro) ───
def draw_vocal():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((42, 14, 86, 62), radius=22, fill=WHITE)
    d.arc((30, 56, 98, 108), 0, 180, fill=WHITE, width=8)
    d.line((64, 104, 64, 118), fill=WHITE, width=8)
    d.line((48, 118, 80, 118), fill=WHITE, width=8)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


# ─── UTILITAIRES (4 squares grid) ───
def draw_utilitaires():
    img = new()
    d = ImageDraw.Draw(img)
    gap = 38
    sz = 28
    ox, oy = 20, 20
    for r in range(2):
        for c in range(2):
            x = ox + c * gap
            y = oy + r * gap
            d.rounded_rectangle((x, y, x + sz, y + sz), radius=8, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "utilitaires.png"))


# ─── FUN (star / sparkle) ───
def draw_fun():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = 64, 64
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 44 if i % 2 == 0 else 20
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(points, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


# ─── STATS (bar chart) ───
def draw_stats():
    img = new()
    d = ImageDraw.Draw(img)
    bars = [(18, 72, 16), (40, 50, 38), (62, 34, 54), (84, 56, 32)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 18, 112), radius=6, fill=WHITE)
    d.line((14, 112, 114, 112), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


# ─── HIÉRARCHIE (tree) ───
def draw_hierarchie():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((48, 10, 80, 42), fill=WHITE)
    d.line((64, 42, 64, 62), fill=WHITE, width=6)
    d.line((64, 62, 34, 82), fill=WHITE, width=6)
    d.line((64, 62, 94, 82), fill=WHITE, width=6)
    d.ellipse((22, 78, 46, 102), fill=WHITE)
    d.ellipse((82, 78, 106, 102), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


# ─── TICKETS (ticket stub) ───
def draw_tickets():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 22, 110, 96), radius=14, fill=WHITE)
    d.rectangle((18, 50, 110, 66), fill=T)
    d.ellipse((50, 30, 78, 58), fill=T)
    d.line((18, 66, 110, 66), fill=T, width=3)
    for y in range(70, 94, 8):
        d.line((24, y, 104, y), fill=T, width=2)
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


# ─── GHOSTPING (ghost) ───
def draw_ghostping():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((28, 16, 100, 82), radius=20, fill=WHITE)
    d.polygon([(28, 78), (28, 108), (44, 92), (56, 108), (68, 92), (80, 108), (100, 78)], fill=WHITE)
    d.ellipse((44, 36, 60, 52), fill=T)
    d.ellipse((68, 36, 84, 52), fill=T)
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


# ─── WELCOME (hand wave) ───
def draw_welcome():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((32, 50, 72, 100), radius=12, fill=WHITE)
    d.rounded_rectangle((56, 40, 82, 90), radius=12, fill=WHITE)
    d.rounded_rectangle((74, 54, 96, 96), radius=12, fill=WHITE)
    d.rounded_rectangle((42, 94, 88, 114), radius=10, fill=WHITE)
    d.line((36, 30, 28, 18), fill=WHITE, width=5)
    d.line((50, 26, 50, 12), fill=WHITE, width=5)
    d.line((64, 28, 70, 14), fill=WHITE, width=5)
    d.line((78, 32, 88, 20), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


# ─── AUTOMOD (shield + X) ───
def draw_automod():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 12, 112, 116), radius=20, fill=WHITE)
    d.rounded_rectangle((24, 20, 104, 108), radius=16, fill=T)
    d.polygon((64, 18, 106, 40, 106, 72, 64, 112, 22, 72, 22, 40), fill=WHITE)
    d.polygon((64, 26, 98, 44, 98, 68, 64, 104, 30, 68, 30, 44), fill=T)
    d.line((48, 50, 80, 82), fill=WHITE, width=7)
    d.line((80, 50, 48, 82), fill=WHITE, width=7)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


# ─── SALON (hash / channel) ───
def draw_salon():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 16, 112, 112), radius=14, fill=WHITE)
    d.rounded_rectangle((24, 24, 104, 104), radius=10, fill=T)
    d.line((42, 34, 36, 94), fill=WHITE, width=7)
    d.line((58, 34, 52, 94), fill=WHITE, width=7)
    d.line((86, 34, 80, 94), fill=WHITE, width=7)
    d.line((100, 34, 94, 94), fill=WHITE, width=7)
    d.line((34, 44, 102, 44), fill=WHITE, width=7)
    d.line((28, 84, 96, 84), fill=WHITE, width=7)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


# ─── BUG (beetle) ───
def draw_bug():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((30, 36, 98, 104), fill=WHITE)
    d.ellipse((38, 44, 90, 96), fill=T)
    d.line((64, 36, 64, 18), fill=WHITE, width=6)
    d.ellipse((58, 12, 70, 24), fill=WHITE)
    d.line((30, 52, 14, 38), fill=WHITE, width=5)
    d.line((14, 38, 8, 28), fill=WHITE, width=5)
    d.line((30, 80, 14, 94), fill=WHITE, width=5)
    d.line((14, 94, 8, 104), fill=WHITE, width=5)
    d.line((98, 52, 114, 38), fill=WHITE, width=5)
    d.line((114, 38, 120, 28), fill=WHITE, width=5)
    d.line((98, 80, 114, 94), fill=WHITE, width=5)
    d.line((114, 94, 120, 104), fill=WHITE, width=5)
    d.line((64, 60, 64, 86), fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


# ─── SUGGESTION (lightbulb) ───
def draw_suggestion():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((36, 10, 92, 72), fill=WHITE)
    d.rounded_rectangle((44, 68, 84, 82), radius=4, fill=WHITE)
    d.rounded_rectangle((48, 82, 80, 90), radius=4, fill=WHITE)
    d.rounded_rectangle((52, 90, 76, 98), radius=4, fill=WHITE)
    d.line((64, 108, 64, 120), fill=WHITE, width=5)
    d.line((52, 116, 76, 116), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


# ─── SUPPORT (headset) ───
def draw_support():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc((20, 16, 108, 96), 180, 360, fill=WHITE, width=10)
    d.rounded_rectangle((16, 56, 34, 92), radius=8, fill=WHITE)
    d.rounded_rectangle((94, 56, 112, 92), radius=8, fill=WHITE)
    d.rounded_rectangle((44, 80, 84, 108), radius=16, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


# ─── REPORT (flag) ───
def draw_report():
    img = new()
    d = ImageDraw.Draw(img)
    d.line((32, 14, 32, 116), fill=WHITE, width=7)
    d.rounded_rectangle((32, 14, 104, 78), radius=10, fill=WHITE)
    d.rounded_rectangle((42, 24, 94, 68), radius=6, fill=T)
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


# ─── AUTRE (dots menu) ───
def draw_autre():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 14, 110, 114), radius=14, fill=WHITE)
    d.rounded_rectangle((26, 22, 102, 106), radius=10, fill=T)
    for y in range(38, 92, 18):
        d.ellipse((56, y, 72, y + 16), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


# ─── MUSIC (note) ───
def draw_music():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((18, 74, 50, 106), fill=WHITE)
    d.ellipse((78, 60, 110, 92), fill=WHITE)
    d.rectangle((46, 22, 54, 100), fill=WHITE)
    d.rectangle((106, 14, 114, 86), fill=WHITE)
    d.polygon((54, 20, 114, 8, 114, 28, 54, 40), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


# ─── CLEANUP (broom) ───
def draw_cleanup():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((38, 60, 90, 116), radius=10, fill=WHITE)
    d.line((64, 10, 64, 64), fill=WHITE, width=8)
    d.rounded_rectangle((38, 10, 90, 30), radius=8, fill=WHITE)
    for x in range(44, 88, 10):
        d.line((x, 116, x, 126), fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "cleanup.png"))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating emojis v4...")
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
    print(f"Done! {count} emojis generated in {OUTPUT_DIR}")
