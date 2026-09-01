#!/usr/bin/env python3
"""Delete all existing emojis and upload new ones."""

import discord
import asyncio
import os
import sys

TOKEN = os.environ.get("DISCORD_TOKEN", "")
EMOJI_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(EMOJI_DIR, "upload")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    for guild in client.guilds:
        print(f"\nGuild: {guild.name} ({guild.id})")

        # Delete all existing emojis
        print(f"Deleting {len(guild.emojis)} existing emojis...")
        for emoji in guild.emojis:
            try:
                await emoji.delete(reason="Emoji refresh")
                print(f"  Deleted: {emoji.name}")
            except Exception as e:
                print(f"  Failed to delete {emoji.name}: {e}")

        # Upload new emojis from upload/ directory
        print(f"\nUploading new emojis from {UPLOAD_DIR}...")
        for filename in sorted(os.listdir(UPLOAD_DIR)):
            if not filename.endswith(".png"):
                continue
            name = filename.replace(".png", "")
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "rb") as f:
                data = f.read()
            try:
                emoji = await guild.create_custom_emoji(name=name, image=data, reason="Emoji refresh")
                print(f"  Uploaded: {emoji.name} (ID: {emoji.id})")
            except Exception as e:
                print(f"  Failed to upload {name}: {e}")

    print("\nDone!")
    await client.close()


if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set")
    sys.exit(1)

client.run(TOKEN)
