import requests
from config import TOKEN

CHANNEL_ID = "1543047493556637746"

headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

r = requests.get(f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=10", headers=headers)
for msg in r.json():
    if msg.get("author", {}).get("bot"):
        requests.delete(f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{msg['id']}", headers=headers)
        print(f"Deleted: {msg['id']}")

payload = {
    "flags": 32768,
    "components": [
        {
            "type": 17,
            "accent_color": 7931839,
            "components": [
                {
                    "type": 10,
                    "content": "## <:tickets:1545840989816492075> **Système de Tickets**"
                },
                {"type": 14},
                {
                    "type": 10,
                    "content": (
                        "Besoin d'aide ou d'une création sur mesure ?\n"
                        "Ouvrez un ticket en sélectionnant le type de votre demande.\n\n"
                        "<:bug:1545840958539833556> **Bug Report** — Signaler un bug ou une erreur\n"
                        "<:suggestion:1545840985672650812> **Suggestion** — Proposer une amélioration\n"
                        "<:support:1545840987312619590> **Support** — Besoin d'aide\n"
                        "<:report:1545840979817402459> **Report** — Signaler un membre\n"
                        "<:salon:1545840982220603443> **Création** — Demander une création\n"
                        "<:autre:1545840955855212554> **Autre** — Autre demande"
                    )
                },
                {"type": 14},
                {
                    "type": 10,
                    "content": "*Sélectionnez un type ci-dessous pour ouvrir un ticket.*"
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 3,
                            "custom_id": "ticket_select_persistent",
                            "placeholder": "Ouvrir un ticket...",
                            "options": [
                                {"label": "Bug Report", "value": "bug", "description": "Signaler un bug ou une erreur", "emoji": {"name": "bug", "id": "1545840958539833556"}},
                                {"label": "Suggestion", "value": "suggestion", "description": "Proposer une amélioration", "emoji": {"name": "suggestion", "id": "1545840985672650812"}},
                                {"label": "Support", "value": "support", "description": "Besoin d'aide", "emoji": {"name": "support", "id": "1545840987312619590"}},
                                {"label": "Report", "value": "report", "description": "Signaler un membre", "emoji": {"name": "report", "id": "1545840979817402459"}},
                                {"label": "Création", "value": "creation", "description": "Demander une création sur mesure", "emoji": {"name": "salon", "id": "1545840982220603443"}},
                                {"label": "Autre", "value": "autre", "description": "Autre demande", "emoji": {"name": "autre", "id": "1545840955855212554"}}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

r = requests.post(
    f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages",
    headers=headers,
    json=payload
)

if r.status_code == 200:
    print(f"Panel envoyé ! ID: {r.json()['id']}")
else:
    print(f"Erreur {r.status_code}: {r.text[:500]}")
