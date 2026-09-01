#!/usr/bin/env python3
"""Generate colorful pro emojis v5 — gradients, shadows, bold."""

from PIL import Image, ImageDraw, ImageFont
import math
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upload")
SIZE = 128
T = (0, 0, 0, 0)

# Color palette — metallic silver theme
C1 = (176, 184, 196)  # light silver
C2 = (120, 130, 145)  # medium silver
C3 = (80, 90, 105)    # dark silver
C4 = (60, 68, 80)     # darker
WHITE = (255, 255, 255)
BG_DARK = (30, 34, 42)
ACCENT = (140, 180, 255)  # blue accent
GREEN = (100, 220, 140)
RED = (240, 80, 90)
YELLOW = (255, 210, 60)
PURPLE = (160, 120, 255)
PINK = (255, 130, 170)


def new():
    return Image.new("RGBA", (SIZE, SIZE), T)


def gradient_bg(img, c1, c2):
    d = ImageDraw.Draw(img)
    for y in range(SIZE):
        r = int(c1[0] + (c2[0] - c1[0]) * y / SIZE)
        g = int(c1[1] + (c2[1] - c1[1]) * y / SIZE)
        b = int(c1[2] + (c2[2] - c1[2]) * y / SIZE)
        d.line((0, y, SIZE, y), fill=(r, g, b, 255))
    return d


def circle_bg(img, c1, c2):
    d = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2
    for r in range(SIZE // 2, 0, -1):
        t = r / (SIZE // 2)
        cr = int(c1[0] * t + c2[0] * (1 - t))
        cg = int(c1[1] * t + c2[1] * (1 - t))
        cb = int(c1[2] * t + c2[2] * (1 - t))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(cr, cg, cb, 255))
    return d


# ─── MODERATION (shield + check, blue) ───
def draw_moderation():
    img = new()
    circle_bg(img, (60, 130, 220), (30, 70, 140))
    d = ImageDraw.Draw(img)
    d.polygon((64, 14, 110, 38, 110, 74, 64, 114, 18, 74, 18, 38), fill=WHITE)
    d.polygon((64, 22, 102, 42, 102, 70, 64, 106, 26, 70, 26, 42), fill=(50, 120, 210))
    d.line((44, 64, 58, 80), fill=WHITE, width=8)
    d.line((58, 80, 86, 48), fill=WHITE, width=8)
    img.save(os.path.join(OUTPUT_DIR, "moderation.png"))


# ─── MOD AVANCÉE (shield + gear, purple) ───
def draw_mod_avancee():
    img = new()
    circle_bg(img, (120, 80, 200), (70, 40, 140))
    d = ImageDraw.Draw(img)
    d.polygon((64, 14, 110, 38, 110, 74, 64, 114, 18, 74, 18, 38), fill=WHITE)
    d.polygon((64, 22, 102, 42, 102, 70, 64, 106, 26, 70, 26, 42), fill=(110, 70, 190))
    cx, cy = 64, 68
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = cx + 16 * math.cos(rad)
        y1 = cy + 16 * math.sin(rad)
        x2 = cx + 24 * math.cos(rad)
        y2 = cy + 24 * math.sin(rad)
        d.line((x1, y1, x2, y2), fill=WHITE, width=5)
    d.ellipse((56, 60, 72, 76), fill=(110, 70, 190))
    d.ellipse((59, 63, 69, 73), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "mod_avancee.png"))


# ─── VOCAL (micro, green) ───
def draw_vocal():
    img = new()
    circle_bg(img, (60, 180, 120), (30, 100, 70))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 12, 88, 60), radius=24, fill=WHITE)
    d.rounded_rectangle((46, 18, 82, 54), radius=18, fill=(50, 170, 110))
    d.arc((28, 52, 100, 108), 0, 180, fill=WHITE, width=8)
    d.line((64, 104, 64, 118), fill=WHITE, width=8)
    d.line((48, 118, 80, 118), fill=WHITE, width=8)
    img.save(os.path.join(OUTPUT_DIR, "vocal.png"))


# ─── UTILITAIRES (4 squares, yellow) ───
def draw_utilitaires():
    img = new()
    circle_bg(img, (230, 190, 40), (180, 140, 20))
    d = ImageDraw.Draw(img)
    gap = 36
    sz = 26
    ox, oy = 20, 20
    for r in range(2):
        for c in range(2):
            x = ox + c * gap
            y = oy + r * gap
            d.rounded_rectangle((x, y, x + sz, y + sz), radius=8, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "utilitaires.png"))


# ─── FUN (star, pink) ───
def draw_fun():
    img = new()
    circle_bg(img, (255, 120, 160), (200, 60, 100))
    d = ImageDraw.Draw(img)
    cx, cy = 64, 64
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = 44 if i % 2 == 0 else 20
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d.polygon(points, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "fun.png"))


# ─── STATS (bars, teal) ───
def draw_stats():
    img = new()
    circle_bg(img, (50, 180, 180), (25, 100, 110))
    d = ImageDraw.Draw(img)
    bars = [(18, 72, 16), (40, 50, 38), (62, 34, 54), (84, 56, 32)]
    for x, y, h in bars:
        d.rounded_rectangle((x, y, x + 18, 112), radius=6, fill=WHITE)
    d.line((14, 112, 114, 112), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "stats.png"))


# ─── HIÉRARCHIE (tree, orange) ───
def draw_hierarchie():
    img = new()
    circle_bg(img, (240, 150, 40), (180, 90, 20))
    d = ImageDraw.Draw(img)
    d.ellipse((46, 8, 82, 44), fill=WHITE)
    d.line((64, 44, 64, 60), fill=WHITE, width=7)
    d.line((64, 60, 32, 82), fill=WHITE, width=7)
    d.line((64, 60, 96, 82), fill=WHITE, width=7)
    d.ellipse((20, 76, 48, 104), fill=WHITE)
    d.ellipse((80, 76, 108, 104), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "hierarchie.png"))


# ─── TICKETS (ticket, blue) ───
def draw_tickets():
    img = new()
    circle_bg(img, (70, 140, 230), (35, 80, 160))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((16, 20, 112, 98), radius=14, fill=WHITE)
    d.rectangle((16, 48, 112, 64), fill=(60, 130, 220))
    d.ellipse((48, 28, 80, 60), fill=(60, 130, 220))
    for y in range(68, 96, 8):
        d.line((22, y, 106, y), fill=(200, 200, 210), width=2)
    img.save(os.path.join(OUTPUT_DIR, "tickets.png"))


# ─── GHOSTPING (ghost, purple) ───
def draw_ghostping():
    img = new()
    circle_bg(img, (140, 100, 220), (80, 50, 160))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((26, 14, 102, 80), radius=22, fill=WHITE)
    d.polygon([(26, 76), (26, 110), (42, 94), (56, 110), (68, 94), (82, 110), (102, 76)], fill=WHITE)
    d.ellipse((42, 34, 58, 50), fill=(130, 90, 210))
    d.ellipse((70, 34, 86, 50), fill=(130, 90, 210))
    img.save(os.path.join(OUTPUT_DIR, "ghostping.png"))


# ─── WELCOME (hand wave, teal) ───
def draw_welcome():
    img = new()
    circle_bg(img, (60, 200, 180), (30, 120, 110))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((30, 48, 70, 100), radius=12, fill=WHITE)
    d.rounded_rectangle((54, 38, 80, 90), radius=12, fill=WHITE)
    d.rounded_rectangle((72, 52, 96, 98), radius=12, fill=WHITE)
    d.rounded_rectangle((40, 92, 86, 114), radius=10, fill=WHITE)
    d.line((34, 28, 26, 16), fill=WHITE, width=5)
    d.line((48, 24, 48, 10), fill=WHITE, width=5)
    d.line((62, 26, 68, 12), fill=WHITE, width=5)
    d.line((76, 30, 86, 18), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "welcome.png"))


# ─── AUTOMOD (shield + X, red) ───
def draw_automod():
    img = new()
    circle_bg(img, (220, 60, 70), (150, 30, 40))
    d = ImageDraw.Draw(img)
    d.polygon((64, 14, 110, 38, 110, 74, 64, 114, 18, 74, 18, 38), fill=WHITE)
    d.polygon((64, 22, 102, 42, 102, 70, 64, 106, 26, 70, 26, 42), fill=(210, 50, 60))
    d.line((46, 48, 82, 84), fill=WHITE, width=8)
    d.line((82, 48, 46, 84), fill=WHITE, width=8)
    img.save(os.path.join(OUTPUT_DIR, "automod.png"))


# ─── SALON (hash, blue) ───
def draw_salon():
    img = new()
    circle_bg(img, (60, 120, 210), (30, 60, 130))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 18, 110, 110), radius=14, fill=WHITE)
    d.rounded_rectangle((24, 24, 104, 104), radius=10, fill=(50, 110, 200))
    d.line((40, 32, 34, 96), fill=WHITE, width=8)
    d.line((56, 32, 50, 96), fill=WHITE, width=8)
    d.line((88, 32, 82, 96), fill=WHITE, width=8)
    d.line((104, 32, 98, 96), fill=WHITE, width=8)
    d.line((32, 42, 100, 42), fill=WHITE, width=8)
    d.line((28, 86, 96, 86), fill=WHITE, width=8)
    img.save(os.path.join(OUTPUT_DIR, "salon.png"))


# ─── BUG (beetle, green) ───
def draw_bug():
    img = new()
    circle_bg(img, (80, 190, 80), (40, 120, 40))
    d = ImageDraw.Draw(img)
    d.ellipse((28, 34, 100, 106), fill=WHITE)
    d.ellipse((36, 42, 92, 98), fill=(70, 180, 70))
    d.line((64, 34, 64, 16), fill=WHITE, width=6)
    d.ellipse((58, 10, 70, 22), fill=WHITE)
    d.line((28, 50, 12, 36), fill=WHITE, width=5)
    d.line((12, 36, 6, 26), fill=WHITE, width=5)
    d.line((28, 82, 12, 96), fill=WHITE, width=5)
    d.line((100, 50, 116, 36), fill=WHITE, width=5)
    d.line((116, 36, 122, 26), fill=WHITE, width=5)
    d.line((100, 82, 116, 96), fill=WHITE, width=5)
    d.line((64, 58, 64, 88), fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "bug.png"))


# ─── SUGGESTION (lightbulb, yellow) ───
def draw_suggestion():
    img = new()
    circle_bg(img, (255, 200, 40), (200, 150, 20))
    d = ImageDraw.Draw(img)
    d.ellipse((34, 8, 94, 72), fill=WHITE)
    d.rounded_rectangle((42, 68, 86, 82), radius=4, fill=(240, 190, 30))
    d.rounded_rectangle((46, 82, 82, 90), radius=4, fill=(240, 190, 30))
    d.rounded_rectangle((50, 90, 78, 98), radius=4, fill=(240, 190, 30))
    d.line((64, 108, 64, 120), fill=WHITE, width=5)
    d.line((52, 116, 76, 116), fill=WHITE, width=5)
    img.save(os.path.join(OUTPUT_DIR, "suggestion.png"))


# ─── SUPPORT (headset, blue) ───
def draw_support():
    img = new()
    circle_bg(img, (60, 140, 220), (30, 80, 150))
    d = ImageDraw.Draw(img)
    d.arc((18, 14, 110, 94), 180, 360, fill=WHITE, width=10)
    d.rounded_rectangle((14, 54, 34, 92), radius=8, fill=WHITE)
    d.rounded_rectangle((94, 54, 114, 92), radius=8, fill=WHITE)
    d.rounded_rectangle((42, 78, 86, 108), radius=16, fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "support.png"))


# ─── REPORT (flag, red) ───
def draw_report():
    img = new()
    circle_bg(img, (230, 60, 70), (160, 30, 40))
    d = ImageDraw.Draw(img)
    d.line((30, 12, 30, 118), fill=WHITE, width=7)
    d.rounded_rectangle((30, 12, 106, 78), radius=10, fill=WHITE)
    d.rounded_rectangle((40, 22, 96, 68), radius=6, fill=(220, 50, 60))
    img.save(os.path.join(OUTPUT_DIR, "report.png"))


# ─── AUTRE (dots menu, gray) ───
def draw_autre():
    img = new()
    circle_bg(img, (140, 150, 170), (80, 90, 110))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((18, 14, 110, 114), radius=14, fill=WHITE)
    d.rounded_rectangle((26, 22, 102, 106), radius=10, fill=(130, 140, 160))
    for y in range(38, 92, 18):
        d.ellipse((56, y, 72, y + 16), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "autre.png"))


# ─── MUSIC (note, purple) ───
def draw_music():
    img = new()
    circle_bg(img, (150, 80, 220), (90, 40, 160))
    d = ImageDraw.Draw(img)
    d.ellipse((16, 72, 50, 106), fill=WHITE)
    d.ellipse((76, 58, 110, 92), fill=WHITE)
    d.rectangle((44, 20, 52, 100), fill=WHITE)
    d.rectangle((104, 12, 112, 84), fill=WHITE)
    d.polygon((52, 18, 112, 6, 112, 26, 52, 38), fill=WHITE)
    img.save(os.path.join(OUTPUT_DIR, "music.png"))


# ─── CLEANUP (broom, teal) ───
def draw_cleanup():
    img = new()
    circle_bg(img, (50, 190, 170), (25, 110, 100))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((36, 58, 92, 116), radius=10, fill=WHITE)
    d.line((64, 8, 64, 62), fill=WHITE, width=8)
    d.rounded_rectangle((36, 8, 92, 28), radius=8, fill=WHITE)
    for x in range(42, 90, 10):
        d.line((x, 116, x, 126), fill=WHITE, width=4)
    img.save(os.path.join(OUTPUT_DIR, "cleanup.png"))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generating colorful emojis v5...")
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
    print(f"Done! {count} emojis in {OUTPUT_DIR}")
