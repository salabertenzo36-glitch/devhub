#!/usr/bin/env python3
"""Upload custom emojis to Discord server."""

import discord
import asyncio
import os
import glob

TOKEN = "MTU0NDA3NzY2NjQ3MzM1MzI1Ng.GhcAP3.2n9F5Xxd1_Vc9efEUR_pTnFRePX7wKkNV4Mj9E"
GUILD_ID = 1522408621256736878

EMOJI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emojis")


async def main():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Connecté en tant que {client.user}")

        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Serveur {GUILD_ID} introuvable")
            await client.close()
            return

        existing = {e.name: e for e in guild.emojis}
        print(f"Émojis existants : {len(existing)}")

        png_files = sorted(glob.glob(os.path.join(EMOJI_DIR, "*.png")))
        uploaded = 0
        skipped = 0
        errors = 0

        for filepath in png_files:
            name = os.path.splitext(os.path.basename(filepath))[0]
            with open(filepath, "rb") as f:
                image_bytes = f.read()

            if len(image_bytes) > 256 * 1024:
                print(f"  ⚠️  {name} trop lourd ({len(image_bytes)} octets) — skip")
                skipped += 1
                continue

            if name in existing:
                print(f"  ✅ {name} existe déjà — skip")
                skipped += 1
                continue

            try:
                await guild.create_custom_emoji(name=name, image=image_bytes)
                print(f"  ✅ {name} uploadé")
                uploaded += 1
                await asyncio.sleep(1)
            except discord.HTTPException as e:
                print(f"  ❌ {name} erreur : {e}")
                errors += 1

        print(f"\nRésumé : {uploaded} uploadés, {skipped} skips, {errors} erreurs")
        print(f"Total émojis serveur : {len(guild.emojis)}/{guild.emoji_limit}")
        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
