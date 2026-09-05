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
    # === CORE (19 used by bot) ===
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
    # === MODERATION EXTRAS ===
    "ban": "ban",
    "kick": "user-minus",
    "mute": "volume-x",
    "unmute": "volume-2",
    "warn": "triangle-alert",
    "timeout": "clock",
    "jail": "lock-keyhole",
    "jail_open": "lock-open",
    "purge": "trash-2",
    "history": "scroll-text",
    "case": "folder-open",
    "eye": "eye",
    "eye_off": "eye-off",
    "search": "search",
    "mod_log": "book-open",
    # === CONFIG ===
    "settings": "settings",
    "cog": "cog",
    "sliders": "sliders-horizontal",
    "palette": "palette",
    "toggle_on": "toggle-right",
    "toggle_off": "toggle-left",
    "link": "link",
    "unlink": "unlink",
    "copy": "copy",
    "clipboard": "clipboard",
    # === WELCOME / GOODBYE ===
    "party": "party-popper",
    "heart": "heart",
    "coffee": "coffee",
    "wave": "hand-wave",
    "door": "door-open",
    "rocket": "rocket",
    "crown": "crown",
    "medal": "medal",
    # === TICKETS ===
    "message": "message-circle",
    "inbox": "inbox",
    "send": "send",
    "reply": "reply",
    "forward": "forward",
    "archive": "archive",
    "tag": "tag",
    # === MUSIC ===
    "headphones": "headphones",
    "volume": "volume-2",
    "play": "play",
    "pause": "pause",
    "skip": "skip-forward",
    "rewind": "skip-back",
    "shuffle": "shuffle",
    "repeat": "repeat",
    "list": "list-music",
    "disc": "disc",
    "radio": "radio",
    "mic_live": "mic",
    "audio_lines": "audio-lines",
    # === FUN ===
    "gamepad": "gamepad-2",
    "trophy": "trophy",
    "dice": "dice-5",
    "dice_1": "dice-1",
    "dice_6": "dice-6",
    "coin": "coins",
    "star": "star",
    "heart_hands": "heart-handshake",
    "smile": "smile",
    "laugh": "laugh",
    "cool": "sunglasses",
    "fire": "flame",
    "lightning": "zap",
    "thunder": "cloud-lightning",
    "rainbow": "rainbow",
    "sun": "sun",
    "moon": "moon",
    # === STATS / GRAPH ===
    "trending_up": "trending-up",
    "trending_down": "trending-down",
    "activity": "activity",
    "pie_chart": "pie-chart",
    "line_chart": "line-chart",
    "target": "target",
    "gauge": "gauge",
    "database": "database",
    "server": "server",
    "cpu": "cpu",
    "hard_drive": "hard-drive",
    "memory": "memory-stick",
    # === BACKUP ===
    "save": "save",
    "download": "download",
    "upload": "upload",
    "cloud": "cloud",
    "cloud_upload": "cloud-upload",
    "cloud_download": "cloud-download",
    "refresh": "refresh-cw",
    "rotate_ccw": "rotate-ccw",
    # === UTILITY ===
    "check": "check",
    "x_mark": "x",
    "plus": "plus",
    "minus": "minus",
    "info": "info",
    "help": "help-circle",
    "alert": "alert-triangle",
    "bell": "bell",
    "bell_off": "bell-off",
    "pin": "pin",
    "unpin": "pin-off",
    "lock": "lock",
    "unlock": "lock-open",
    "key": "key",
    "shield": "shield",
    "shield_check": "shield-check",
    "shield_alert": "shield-alert",
    # === NAVIGATION ===
    "arrow_up": "arrow-up",
    "arrow_down": "arrow-down",
    "arrow_left": "arrow-left",
    "arrow_right": "arrow-right",
    "chevron_up": "chevron-up",
    "chevron_down": "chevron-down",
    "chevron_left": "chevron-left",
    "chevron_right": "chevron-right",
    "external_link": "external-link",
    "home": "home",
    "menu": "menu",
    # === SOCIAL ===
    "user": "user",
    "user_plus": "user-plus",
    "user_minus": "user-minus",
    "user_check": "user-check",
    "users": "users",
    "user_x": "user-x",
    "crown2": "crown",
    "badge": "badge-check",
    "award": "award",
    "handshake": "handshake",
    # === MISC ===
    "hammer": "hammer",
    "wrench": "wrench",
    "screwdriver": "screwdriver",
    "ruler": "ruler",
    "compass": "compass",
    "map": "map",
    "flag2": "flag",
    "bookmark": "bookmark",
    "bookmark_check": "bookmark-check",
    "calendar": "calendar",
    "clock2": "clock",
    "timer": "timer",
    "hourglass": "hourglass",
    "trash": "trash",
    "edit": "pencil",
    "pen": "pen-line",
    "scissors": "scissors",
    "paperclip": "paperclip",
    "image": "image",
    "camera": "camera",
    "film": "film",
    "video": "video",
    "monitor": "monitor",
    "smartphone": "smartphone",
    "tablet": "tablet",
    "mouse": "mouse",
    "keyboard": "keyboard",
    "printer": "printer",
    "scan": "scan-line",
    "qr_code": "qr-code",
    "code": "code",
    "terminal": "terminal",
    "git_branch": "git-branch",
    "git_commit": "git-commit",
    "git_merge": "git-merge",
    "git_pull_request": "git-pull-request",
    "box": "box",
    "package": "package",
    "layers": "layers",
    "layout": "layout",
    "sidebar": "panel-left",
    "grid": "grid-3x3",
    "maximize": "maximize",
    "minimize": "minimize",
    "move": "move",
    "grip": "grip-vertical",
    "cursor": "mouse-pointer",
    "click": "pointer",
    "finger": "hand-index",
    "thumb_up": "thumbs-up",
    "thumb_down": "thumbs-down",
    "clap": "hand-metal",
    "peace": "hand-metal",
    "ok": "circle-check",
    "cancel": "circle-x",
    "question": "circle-help",
    "empty": "circle-dot",
    "full": "circle",
    "dots_horizontal": "ellipsis",
    "dots_vertical": "more-vertical",
    "hash2": "hash",
    "at": "at-sign",
    "percent": "percent",
    "dollar": "dollar-sign",
    "euro": "euro",
    "bitcoin": "bitcoin",
    "wallet": "wallet",
    "credit_card": "credit-card",
    "receipt": "receipt",
    "shopping_cart": "shopping-cart",
    "store": "store",
    "gift": "gift",
    "balloon": "balloon",
    "confetti": "confetti",
    "cake": "cake",
    "cookie": "cookie",
    "apple": "apple",
    "beer": "beer",
    "wine": "wine",
    "coffee2": "coffee",
    "pizza": "pizza",
    "hot_dog": "hotdog",
    "ice_cream": "ice-cream-cone",
    "candy": "candy",
    "lollipop": "lollipop",
    "popcorn": "popcorn",
    "pretzel": "pretzel",
    "donut": "donut",
    "cupcake": "cupcake",
    "cake_slice": "cake-slice",
    "party2": "party-popper",
    "balloon2": "balloon",
    "sparkle": "sparkle",
    "wand": "wand-sparkles",
    "magic": "wand-sparkles",
    "potion": "flask-round",
    "crystal": "gem",
    "diamond": "diamond",
    "ring": "circle-dot",
    "crown3": "crown",
    "throne": "armchair",
    "castle": "castle",
    "tower": "tower-control",
    "bridge": "bridge",
    "tent": "tent",
    "campfire": "flame-kindling",
    "tree_pine": "tree-pine",
    "tree deciduous": "tree-deciduous",
    "flower": "flower-2",
    "leaf": "leaf",
    "sprout": "sprout",
    "seedling": "sprout",
    "mushroom": "mushroom",
    "cactus": "cactus",
    "palm_tree": "tree-palm",
    "snowflake": "snowflake",
    "cloud_rain": "cloud-rain",
    "cloud_snow": "cloud-snow",
    "cloud_sun": "cloud-sun",
    "star_half": "star-half",
    "star_off": "star-off",
    "heart_crack": "heart-crack",
    "skull": "skull",
    "bone": "bone",
    "spider": "spider",
    "bug_beetle": "bug",
    "butterfly": "butterfly",
    "bird": "bird",
    "cat": "cat",
    "dog": "dog",
    "fish": "fish",
    "turtle": "turtle",
    "rabbit": "rabbit",
    "bear": "bear",
    "fox": "fox",
    "wolf": "wolf",
    "lion": "lion",
    "tiger": "tiger",
    "elephant": "elephant",
    "whale": "whale",
    "dolphin": "dolphin",
    "shark": "shark",
    "octopus": "octopus",
    "crab": "crab",
    "snail": "snail",
    "ant": "ant",
    "bee": "bee",
    "ladybug": "ladybug",
    "worm": "worm",
    "feather": "feather",
    "shell": "shell",
    "rock": "mountain",
    "volcano": "mountain-snow",
    "island": "island",
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
