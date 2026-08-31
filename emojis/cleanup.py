import requests

TOKEN = "MTU0MzAxMDEwOTYzMzA3NzI5OA.GhEOdk.1XDD3Pb4Pb9cMFA_5nGFuNAoYGPFqb-kan-G9s"
GUILD_ID = "1522408621256736878"

headers = {"Authorization": f"Bot {TOKEN}"}

# Names of our custom emojis - keep only the NEWEST ones
OUR_EMOJIS = {
    "moderation", "mod_avancee", "vocal", "utilitaires", "fun", "stats",
    "hierarchie", "tickets", "ghostping", "welcome", "automod", "salon",
    "bug", "suggestion", "support", "report", "autre"
}

# New emoji IDs (from latest upload)
NEW_IDS = {
    "1543707507631853683", "1543707509376680068", "1543707511281156286",
    "1543707513273196736", "1543707515995295876", "1543707518847680512",
    "1543707521401884843", "1543707525185142948", "1543707527483494541",
    "1543707529039577128", "1543707530671427685", "1543707532298559599",
    "1543707533858832567", "1543707535796600942", "1543707537696628857",
    "1543707539764416572", "1543707541702185041"
}

# Get all emojis
r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis", headers=headers)
emojis = r.json()

# Find duplicates - old ones with same name but different ID
for e in emojis:
    if e["name"] in OUR_EMOJIS and e["id"] not in NEW_IDS:
        r = requests.delete(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis/{e['id']}",
            headers=headers
        )
        print(f"  Deleted old: :{e['name']}: ({e['id']})")

# Final list
r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis", headers=headers)
emojis = r.json()
print(f"\nTotal emojis: {len(emojis)}")
for e in sorted(emojis, key=lambda x: x["name"]):
    print(f"  :{e['name']}: -> {e['id']}")
