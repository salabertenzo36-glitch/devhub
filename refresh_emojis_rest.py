#!/usr/bin/env python3
"""Delete and upload emojis via REST API (no gateway needed)."""

import requests
import os
import sys
import base64
import time

TOKEN = os.environ.get("DISCORD_TOKEN", "")
EMOJI_DIR = os.path.dirname(os.path.abspath(__file__))
HEADERS = {"Authorization": f"Bot {TOKEN}"}
API = "https://discord.com/api/v10"


def get_guilds():
    r = requests.get(f"{API}/users/@me/guilds", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def get_emojis(guild_id):
    r = requests.get(f"{API}/guilds/{guild_id}/emojis", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def delete_emoji(guild_id, emoji_id):
    r = requests.delete(f"{API}/guilds/{guild_id}/emojis/{emoji_id}", headers=HEADERS)
    return r.status_code == 204


def create_emoji(guild_id, name, image_path):
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    r = requests.post(
        f"{API}/guilds/{guild_id}/emojis",
        headers=HEADERS,
        json={"name": name, "image": f"data:image/png;base64,{image_data}"}
    )
    if r.status_code in (200, 201):
        return r.json()
    print(f"  Error {r.status_code}: {r.text}")
    return None


if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    sys.exit(1)

guilds = get_guilds()
print(f"Found {len(guilds)} guild(s)")

for guild in guilds:
    gid = guild["id"]
    print(f"\n=== {guild['name']} ({gid}) ===")

    # Delete all emojis
    emojis = get_emojis(gid)
    print(f"Deleting {len(emojis)} emojis...")
    for emoji in emojis:
        if delete_emoji(gid, emoji["id"]):
            print(f"  Deleted: {emoji['name']}")
        else:
            print(f"  Failed: {emoji['name']}")
        time.sleep(0.5)

    # Upload new emojis
    upload_dir = os.path.join(EMOJI_DIR, "emojis", "upload")
    files = sorted([f for f in os.listdir(upload_dir) if f.endswith(".png")])
    print(f"\nUploading {len(files)} new emojis...")
    for filename in files:
        name = filename.replace(".png", "")
        path = os.path.join(upload_dir, filename)
        result = create_emoji(gid, name, path)
        if result:
            print(f"  Uploaded: {result['name']} (ID: {result['id']})")
        time.sleep(0.5)

print("\nDone!")
