import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "")
_client = None
_db = None


def connect():
    global _client, _db
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI environment variable is not set")
    _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    _db = _client["devhub"]
    _client.admin.command("ping")
    print("▸ MongoDB connecté")


def _load(collection):
    doc = _db[collection].find_one({"_id": "data"})
    if doc:
        doc.pop("_id", None)
        return doc
    return {}


def _save(collection, data):
    data["_id"] = "data"
    _db[collection].replace_one({"_id": "data"}, data, upsert=True)


def load_settings():
    return _load("settings")


def save_settings(data):
    _save("settings", data)


def load_tickets():
    return _load("tickets")


def save_tickets(data):
    _save("tickets", data)


def load_warns():
    return _load("warns")


def save_warns(data):
    _save("warns", data)


def load_jail():
    return _load("jail")


def save_jail(data):
    _save("jail", data)


def load_backups():
    return _load("backups")


def save_backups(data):
    _save("backups", data)


def load_mod_log():
    return _load("mod_log")


def save_mod_log(data):
    _save("mod_log", data)


def load_raid_state():
    return _load("raid_state")


def save_raid_state(state):
    _save("raid_state", state)


def save_ticket_config(guild_id, config):
    settings = load_settings()
    gid = str(guild_id)
    if gid not in settings:
        settings[gid] = {}
    settings[gid]["ticket_config"] = config
    save_settings(settings)


def save_raid_config(gid, config):
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    settings[gid].update(config)
    save_settings(settings)
