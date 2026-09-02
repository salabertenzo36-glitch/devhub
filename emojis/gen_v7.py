#!/usr/bin/env python3
"""Generate pro emojis v7 — clean white icons, transparent bg, smooth."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload")
SIZE = 128
T = (0, 0, 0, 0)
W = (255, 255, 255, 255)
S = (200, 200, 200, 255)


def new():
    return Image.new("RGBA", (SIZE, SIZE), T)


# ─── MODERATION (shield + checkmark) ───
def draw_moderation():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = 64, 64
    d.rounded_rectangle((18, 8, 110, 120), radius=20, fill=W)
    d.rounded_rectangle((24, 14, 104, 114), radius=16, fill=T)
    d.polygon((64, 12, 110, 36, 110, 80, 64, 116, 18, 80, 18, 36), fill=W)
    d.polygon((64, 22, 102, 40, 102, 74, 64, 108, 26, 74, 26, 40), fill=T)
    d.line((44, 64, 58, 82), fill=W, width=10)
    d.line((58, 82, 86, 46), fill=W, width=10)
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


# ─── MOD AVANCÉE (shield + gear) ───
def draw_mod_avancee():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 8, 110, 120), radius=20, fill=W)
    d.rounded_rectangle((24, 14, 104, 114), radius=16, fill=T)
    d.polygon((64, 12, 110, 36, 110, 80, 64, 116, 18, 80, 18, 36), fill=W)
    d.polygon((64, 22, 102, 40, 102, 74, 64, 108, 26, 74, 26, 40), fill=T)
    cx, cy = 64, 66
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + 16 * math.cos(rad)
        y1 = cy + 16 * math.sin(rad)
        x2 = cx + 26 * math.cos(rad)
        y2 = cy + 26 * math.sin(rad)
        d.line((x1, y1, x2, y2), fill=W, width=6)
    d.ellipse((54, 56, 74, 76), fill=T)
    d.ellipse((57, 59, 71, 73), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


# ─── VOCAL (micro) ───
def draw_vocal():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((38, 8, 90, 56), radius=26, fill=W)
    d.rounded_rectangle((46, 16, 82, 48), radius=18, fill=T)
    d.arc((26, 44, 102, 108), 0, 180, fill=W, width=10)
    d.line((64, 98, 64, 114), fill=W, width=10)
    d.line((46, 114, 82, 114), fill=W, width=10)
    d.line((46, 114, 46, 122), fill=W, width=6)
    d.line((82, 114, 82, 122), fill=W, width=6)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


# ─── UTILITAIRES (4 rounded squares grid) ───
def draw_utilitaires():
    img = new()
    d = ImageDraw.Draw(img)
    gap = 38
    sz = 30
    ox, oy = 14, 14
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
        r = 48 if i % 2 == 0 else 18
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(points, fill=W)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


# ─── STATS (bar chart) ───
def draw_stats():
    img = new()
    d = ImageDraw.Draw(img)
    bars = [(14, 72, 20), (38, 50, 42), (62, 30, 62), (86, 52, 40)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 20, 118), radius=6, fill=W)
    d.line((10, 118, 118, 118), fill=W, width=6)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


# ─── HIÉRARCHIE (people) ───
def draw_hierarchie():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((42, 4, 86, 48), fill=W)
    d.line((64, 48, 64, 64), fill=W, width=8)
    d.line((64, 64, 26, 86), fill=W, width=8)
    d.line((64, 64, 102, 86), fill=W, width=8)
    d.ellipse((14, 78, 54, 118), fill=W)
    d.ellipse((74, 78, 114, 118), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


# ─── TICKETS (ticket) ───
def draw_tickets():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((12, 18, 116, 102), radius=16, fill=W)
    d.rectangle((12, 48, 116, 68), fill=T)
    d.ellipse((42, 22, 86, 66), fill=T)
    d.line((12, 68, 116, 68), fill=T, width=4)
    for y in range(76, 100, 8):
        d.line((18, y, 110, y), fill=T, width=3)
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


# ─── GHOSTPING (ghost) ───
def draw_ghostping():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 10, 106, 78), radius=26, fill=W)
    d.polygon([(22, 72), (22, 116), (38, 96), (52, 116), (64, 96), (76, 116), (90, 96), (106, 116), (106, 72)], fill=W)
    d.ellipse((38, 30, 56, 50), fill=T)
    d.ellipse((72, 30, 90, 50), fill=T)
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


# ─── WELCOME (wave hand) ───
def draw_welcome():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((24, 42, 68, 100), radius=14, fill=W)
    d.rounded_rectangle((50, 30, 80, 90), radius=14, fill=W)
    d.rounded_rectangle((68, 46, 100, 98), radius=14, fill=W)
    d.rounded_rectangle((34, 88, 86, 114), radius=12, fill=W)
    d.line((30, 22, 20, 8), fill=W, width=6)
    d.line((44, 18, 42, 2), fill=W, width=6)
    d.line((60, 20, 68, 4), fill=W, width=6)
    d.line((76, 24, 88, 10), fill=W, width=6)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


# ─── AUTOMOD (shield + X) ───
def draw_automod():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 8, 110, 120), radius=20, fill=W)
    d.rounded_rectangle((24, 14, 104, 114), radius=16, fill=T)
    d.polygon((64, 12, 110, 36, 110, 80, 64, 116, 18, 80, 18, 36), fill=W)
    d.polygon((64, 22, 102, 40, 102, 74, 64, 108, 26, 74, 26, 40), fill=T)
    d.line((44, 44, 84, 86), fill=W, width=10)
    d.line((84, 44, 44, 86), fill=W, width=10)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


# ─── SALON (hash) ───
def draw_salon():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((12, 12, 116, 116), radius=18, fill=W)
    d.rounded_rectangle((20, 20, 108, 108), radius=14, fill=T)
    d.line((40, 28, 30, 100), fill=W, width=10)
    d.line((62, 28, 52, 100), fill=W, width=10)
    d.line((90, 28, 80, 100), fill=W, width=10)
    d.line((112, 28, 102, 100), fill=W, width=10)
    d.line((28, 42, 100, 42), fill=W, width=10)
    d.line((24, 90, 96, 90), fill=W, width=10)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


# ─── BUG ───
def draw_bug():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((24, 28, 104, 112), fill=W)
    d.ellipse((32, 36, 96, 104), fill=T)
    d.line((64, 28, 64, 10), fill=W, width=7)
    d.ellipse((56, 4, 72, 20), fill=W)
    d.line((24, 48, 6, 30), fill=W, width=6)
    d.line((6, 30, 0, 18), fill=W, width=6)
    d.line((24, 88, 6, 106), fill=W, width=6)
    d.line((104, 48, 122, 30), fill=W, width=6)
    d.line((122, 30, 128, 18), fill=W, width=6)
    d.line((104, 88, 122, 106), fill=W, width=6)
    d.line((64, 56, 64, 92), fill=W, width=5)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


# ─── SUGGESTION (lightbulb) ───
def draw_suggestion():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((28, 2, 100, 72), fill=W)
    d.rounded_rectangle((38, 68, 90, 82), radius=4, fill=W)
    d.rounded_rectangle((42, 82, 86, 90), radius=4, fill=W)
    d.rounded_rectangle((46, 90, 82, 98), radius=4, fill=W)
    d.line((64, 108, 64, 122), fill=W, width=6)
    d.line((48, 118, 80, 118), fill=W, width=6)
    d.line((48, 122, 80, 122), fill=W, width=6)
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


# ─── SUPPORT (headset) ───
def draw_support():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc((14, 6, 114, 88), 180, 360, fill=W, width=12)
    d.rounded_rectangle((8, 48, 34, 94), radius=12, fill=W)
    d.rounded_rectangle((94, 48, 120, 94), radius=12, fill=W)
    d.rounded_rectangle((36, 74, 92, 110), radius=18, fill=W)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


# ─── REPORT (flag) ───
def draw_report():
    img = new()
    d = ImageDraw.Draw(img)
    d.line((26, 6, 26, 122), fill=W, width=8)
    d.rounded_rectangle((26, 6, 110, 78), radius=14, fill=W)
    d.rounded_rectangle((36, 16, 100, 68), radius=10, fill=T)
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


# ─── AUTRE (dots) ───
def draw_autre():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((14, 10, 114, 118), radius=18, fill=W)
    d.rounded_rectangle((22, 18, 106, 110), radius=14, fill=T)
    for y in range(36, 94, 24):
        d.ellipse((52, y, 76, y + 20), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


# ─── MUSIC (note) ───
def draw_music():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse((10, 70, 54, 114), fill=W)
    d.ellipse((74, 52, 118, 96), fill=W)
    d.rectangle((44, 14, 54, 108), fill=W)
    d.rectangle((108, 6, 118, 90), fill=W)
    d.polygon((54, 12, 118, 0, 118, 22, 54, 34), fill=W)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


# ─── CLEANUP (broom) ───
def draw_cleanup():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 52, 98, 120), radius=14, fill=W)
    d.line((64, 2, 64, 56), fill=W, width=10)
    d.rounded_rectangle((30, 2, 98, 24), radius=12, fill=W)
    for x in range(36, 96, 14):
        d.line((x, 120, x, 128), fill=W, width=5)
    img.save(os.path.join(OUTPUT_DIR, "cleanup.png"))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating emojis v7 (clean white, transparent bg)...")
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
