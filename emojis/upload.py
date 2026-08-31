import requests
import os
import base64

TOKEN = "MTU0MzAxMDEwOTYzMzA3NzI5OA.GhEOdk.1XDD3Pb4Pb9cMFA_5nGFuNAoYGPFqb-kan-G9s"
GUILD_ID = "1522408621256736878"
EMOJI_DIR = "/Users/epsylon2/:eof/bot/emojis"

headers = {
    "Authorization": f"Bot {TOKEN}"
}

# Names of our custom emojis
OUR_EMOJIS = {
    "moderation", "mod_avancee", "vocal", "utilitaires", "fun", "stats",
    "hierarchie", "tickets", "ghostping", "welcome", "automod", "salon",
    "bug", "suggestion", "support", "report", "autre"
}

# Get existing emojis
r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis", headers=headers)
existing = r.json()
print(f"Existing emojis: {len(existing)}")

# Delete old versions of our emojis
for e in existing:
    if e["name"] in OUR_EMOJIS:
        r = requests.delete(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis/{e['id']}",
            headers=headers
        )
        print(f"  Deleted: :{e['name']}: ({e['id']})")

# Upload new versions
for fname in sorted(os.listdir(EMOJI_DIR)):
    if not fname.endswith(".png"):
        continue
    name = fname.replace(".png", "")
    path = os.path.join(EMOJI_DIR, fname)

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    payload = {
        "name": name,
        "image": f"data:image/png;base64,{data}",
        "roles": []
    }
    r = requests.post(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis",
        headers=headers,
        json=payload
    )
    if r.status_code == 201:
        emoji = r.json()
        print(f"  Uploaded: :{emoji['name']}: -> {emoji['id']}")
    else:
        print(f"  FAILED: {name} -> {r.status_code} {r.text[:200]}")

# Final list
r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis", headers=headers)
emojis = r.json()
print(f"\nTotal emojis: {len(emojis)}")
for e in emojis:
    print(f"  :{e['name']}: -> {e['id']}")
