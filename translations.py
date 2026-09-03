TRANSLATIONS = {
    "fr": {
        # General
        "lang_set": "Langue definie sur **Francais**.",
        "lang_prompt": "Choisissez la langue du bot :",
        "lang_select": "Choisir une langue",
        "lang_current": "Langue actuelle : **Francais**",
        "error": "Une erreur est survenue.",
        "no_perm": "Permission insuffisante.",
        "success": "Action reussie.",
        "cancelled": "Action annulee.",

        # Mod
        "mod_muted": "**{user}** mute {duration} — {reason}",
        "mod_unmuted": "**{user}** unmute — {reason}",
        "mod_kicked": "**{user}** kick — {reason}",
        "mod_banned": "**{user}** ban — {reason}",
        "mod_unbanned": "**{user}** unban — {reason}",
        "mod_softbanned": "**{user}** softban — {reason}",
        "mod_warned": "**{user}** warn ({count}) — {reason}",
        "mod_unwarned": "**{user}** warns supprimes.",
        "mod_jailed": "**{user}** jail — {reason}",
        "mod_unjailed": "**{user}** unjail — {reason}",
        "mod_timeout": "**{user}** timeout {duration} — {reason}",
        "mod_purge": "**{count}** messages supprimes.",
        "mod_role_added": "Role {role} ajoute a {user}.",
        "mod_role_removed": "Role {role} retire a {user}.",
        "mod_member_not_found": "Membre introuvable.",
        "mod_no_warns": "Aucun warn a supprimer.",
        "mod_not_jailed": "Membre pas en prison.",
        "mod_not_banned": "Utilisateur non banni.",
        "mod_history_title": "Historique de moderation",
        "mod_no_history": "Aucun historique.",

        # Config
        "config_saved": "Configuration sauvegardee.",
        "config_staff_roles": "Roles staff : {roles}",
        "config_ticket_channel": "Salon de tickets : {channel}",
        "config_automod": "Automod mis a jour.",
        "config_autorole": "Autorole : {role}",
        "config_welcome": "Salon d'accueil : {channel}",
        "config_goodbye": "Salon de depart : {channel}",
        "config_boost": "Salon de boost : {channel}",
        "config_mod_panel": "Panel de mod envoye dans {channel}.",
        "config_reglement": "Reglement configure.",
        "config_reglement_post": "Reglement post envoye dans {channel}.",

        # Welcome
        "welcome_setup": "Accueil configure dans {channel}.",
        "welcome_disabled": "Accueil desactive.",
        "welcome_goodbye_setup": "Goodbye configure dans {channel}.",
        "welcome_boost_setup": "Boost configure dans {channel}.",
        "welcome_preview": "Apercu de l'accueil :",

        # Ticket
        "ticket_setup": "Tickets configures dans {channel}.",
        "ticket_panel_sent": "Panel de tickets envoye.",
        "ticket_config": "Configuration des tickets.",
        "ticket_created": "Ticket {id} cree.",
        "ticket_closed": "Ticket ferme.",
        "ticket_claimed": "Ticket reclame par {user}.",
        "ticket_added": "{user} ajoute au ticket.",
        "ticket_removed": "{user} retire du ticket.",
        "ticket_no_open": "Aucun ticket ouvert.",
        "ticket_transcript": "Transcript genere.",
        "ticket_force_closed": "Ticket force ferme.",

        # Music
        "music_added": "**{title}** ajoute a la file.",
        "music_playing": "Lecture de **{title}**.",
        "music_paused": "Musique en pause.",
        "music_resumed": "Musique reprise.",
        "music_skipped": "Musique passee.",
        "music_stopped": "Musique arretee.",
        "music_queue_empty": "File d'attente vide.",
        "music_now_playing": "En cours : **{title}**",
        "music_volume": "Volume : **{volume}%**",
        "music_disconnected": "Deconnecte.",
        "music_no_voice": "Rejoins un salon vocal d'abord.",
        "music_error": "Erreur lors de la lecture.",

        # Util
        "util_pong": "Pong ! Latence : `{ms}ms`",
        "util_uptime": "Uptime : **{time}**",
        "util_bot_info": "Informations du bot",
        "util_avatar": "Avatar de {user}",
        "util_banner": "Banniere de {user}",
        "util_server_info": "Informations du serveur",
        "util_user_info": "Informations de {user}",
        "util_say_sent": "Message envoye dans {channel}.",
        "util_embed_sent": "Embed envoye dans {channel}.",
        "util_poll_created": "Sondage cree.",
        "util_help_title": "Aide — Commandes",
        "util_afk_set": "AFK active : {reason}",
        "util_afk_removed": "AFK desactive.",
        "util_remind_set": "Rappel dans {time}.",
        "util_effectif": "Effectif : **{count}** membres",
        "util_hierarchie": "Hierarchie des roles",
        "util_staff": "Hierarchie du staff",

        # Fun
        "fun_heads": "Pile !",
        "fun_tails": "Face !",
        "fun_dice": "Tu as lance **{result}**.",
        "fun_8ball": "Reponse : **{answer}**",
        "fun_ship": "Compatibilite : **{percent}%**",
        "fun_rate": "Note : **{score}/10**",

        # Backup
        "backup_created": "Backup creee : `{id}`",
        "backup_list": "Liste des backups",
        "backup_restored": "Backup restauree.",
        "backup_deleted": "Backup supprimee.",
        "backup_none": "Aucune backup.",
        "backup_restoring": "Restauration en cours...",

        # Stats
        "stats_user": "Statistiques de {user}",
        "stats_server": "Statistiques du serveur",

        # Raid
        "raid_config_saved": "Configuration anti-raid sauvegardee.",
        "raid_log_set": "Logs configures dans {channel}.",
        "raid_whitelist_added": "{role} ajoute a la whitelist.",
        "raid_whitelist_removed": "{role} retire de la whitelist.",
        "raid_whitelist_already": "{role} deja dans la whitelist.",
        "raid_whitelist_not": "{role} n'est pas dans la whitelist.",
        "raid_blacklist_added": "`{id}` ajoute a la blacklist.",
        "raid_blacklist_removed": "`{id}` retire de la blacklist.",
        "raid_blacklist_already": "`{id}` deja dans la blacklist.",
        "raid_blacklist_not": "`{id}` n'est pas dans la blacklist.",
        "raid_lockdown_on": "**{count}** salons verrouilles.",
        "raid_lockdown_off": "**{count}** salons deverrouilles.",
        "raid_scan_done": "Scan termine.",
        "raid_scan_clean": "Aucun membre suspect detecte.",
        "raid_massban_done": "**{count}** membres bannis.",
        "raid_massban_none": "Aucun membre suspect a bannir.",
        "raid_status_title": "Anti-Raid — Status",

        # Ghostping
        "ghostping_sent": "Ghostping envoye dans {channel}.",

        # AI
        "ai_panel": "Panel de configuration IA",
        "ai_enabled": "IA activee.",
        "ai_disabled": "IA desactivee.",
        "ai_auto_mute": "Je peux pas m'auto-modérer.",

        # Owner DM
        "owner_dm_title": "Dev Hub — Language Selection",
        "owner_dm_welcome": "Hello! Thanks for adding **Dev Hub** to your server **{server}**!\n\nPlease choose the language for the bot:",
        "owner_dm_options": "React with:\n🇫🇷 **FR** — Francais\n🇬🇧 **EN** — English\n🇩🇪 **DE** — Deutsch",
        "owner_dm_selected": "Language set to **{lang}** for **{server}**!",
        "owner_dm_footer": "You can change this anytime with /language",

        # Panels
        "panel_welcome_title": "Panel Welcome",
        "panel_goodbye_title": "Panel Goodbye",
        "panel_boost_title": "Panel Boost",
        "panel_ticket_title": "Panel Tickets",
        "panel_raid_title": "Panel Anti-Raid",

        # Natural language
        "nl_muted": "**{user}** mute {duration} — {reason}",
        "nl_unmuted": "**{user}** unmute — {reason}",
        "nl_kicked": "**{user}** kick — {reason}",
        "nl_banned": "**{user}** ban — {reason}",
        "nl_unbanned": "**{user}** unban — {reason}",
        "nl_softbanned": "**{user}** softban — {reason}",
        "nl_warned": "**{user}** warn ({count}) — {reason}",
        "nl_jailed": "**{user}** jail — {reason}",
        "nl_unjailed": "**{user}** unjail — {reason}",
        "nl_unwarned": "**{user}** warns supprimes.",
        "nl_say_sent": "Message envoye dans {channel}.",

        # Anti-raid alerts
        "raid_alert_flood": "FLOOD DETECTE",
        "raid_alert_spam": "SPAM DETECTE",
        "raid_alert_mention": "MASS MENTION",
        "raid_alert_invite": "INVITE DETECTE",
        "raid_alert_caps": "CAPS DETECTE",
        "raid_alert_bot": "BOT JOIN",
        "raid_alert_alt": "ALT ACCOUNT",
        "raid_alert_blacklist": "BLACKLIST",
        "raid_alert_nuke": "NUKE DETECTE",

        # Economy
        "eco_balance_title": "Solde de {user}",
        "eco_wallet": "Porte-monnaie",
        "eco_bank": "Banque",
        "eco_total": "Total",
        "eco_level": "Niveau",
        "eco_items": "Objets",
        "eco_daily": "Recompense journaliere",
        "eco_hourly": "Recompense horaire",
        "eco_weekly": "Recompense hebdomadaire",
        "eco_work": "Travail",
        "eco_crime": "Crime",
        "eco_crime_success": "Crime reussi",
        "eco_crime_caught": "Arrete",
        "eco_slots_win": "Gagne",
        "eco_slots_lose": "Perdu",
        "eco_jackpot": "JACKPOT",
        "eco_pay_sent": "Pieces envoyees",
        "eco_pay_received": "Pieces recues",
        "eco_buy": "Achat",
        "eco_sell": "Vente",
        "eco_rob_success": "Vol reussi",
        "eco_rob_failed": "Rate",
        "eco_rob_shield": "Bouclier",
        "eco_leaderboard": "Classement economique",
        "eco_shop": "Magasin",
        "eco_inventory": "Inventaire",
        "eco_fishing": "Peche",
        "eco_mining": "Mine",
        "eco_not_enough": "Pas assez de pieces",
        "eco_cooldown": "Tu dois attendre {time}.",

        # Giveaway
        "gw_created": "Giveaway cree dans {channel} !",
        "gw_ended": "Giveaway termine.",
        "gw_rerolled": "Gagnants relances : {winners}",
        "gw_no_active": "Aucun giveaway actif.",
        "gw_not_found": "Giveaway introuvable.",
        "gw_no_participants": "Aucun participant.",

        # Poll
        "poll_created": "Sondage cree !",
        "poll_ended": "Resultats affiches !",
        "poll_not_found": "Sondage introuvable.",
        "poll_no_active": "Aucun sondage actif.",
        "poll_min_options": "Minimum 2 options.",
        "poll_max_options": "Maximum 10 options.",

        # Level
        "level_title": "Niveaux — {user}",
        "level_xp": "XP",
        "level_next": "Prochain niveau",
        "level_up": "Felicitations {user} ! Tu es maintenant niveau **{level}** !",
        "level_role_reward": "Role {role} obtenu au niveau **{level}** !",
        "level_no_data": "Aucune donnee de niveau.",
        "level_leaderboard": "Classement niveaux",
        "level_config_updated": "Config niveaux mise a jour.",

        # Log
        "log_configured": "Logs configures dans {channel}.",
        "log_toggled": "Log `{type}` {status}.",
        "log_no_channel": "Aucun salon de logs configure.",
    },
    "en": {
        # General
        "lang_set": "Language set to **English**.",
        "lang_prompt": "Choose the bot language:",
        "lang_select": "Select a language",
        "lang_current": "Current language: **English**",
        "error": "An error occurred.",
        "no_perm": "Insufficient permissions.",
        "success": "Action completed.",
        "cancelled": "Action cancelled.",

        # Mod
        "mod_muted": "**{user}** muted for {duration} — {reason}",
        "mod_unmuted": "**{user}** unmuted — {reason}",
        "mod_kicked": "**{user}** kicked — {reason}",
        "mod_banned": "**{user}** banned — {reason}",
        "mod_unbanned": "**{user}** unbanned — {reason}",
        "mod_softbanned": "**{user}** softbanned — {reason}",
        "mod_warned": "**{user}** warned ({count}) — {reason}",
        "mod_unwarned": "**{user}** warns cleared.",
        "mod_jailed": "**{user}** jailed — {reason}",
        "mod_unjailed": "**{user}** unjailed — {reason}",
        "mod_timeout": "**{user}** timed out for {duration} — {reason}",
        "mod_purge": "**{count}** messages deleted.",
        "mod_role_added": "Role {role} added to {user}.",
        "mod_role_removed": "Role {role} removed from {user}.",
        "mod_member_not_found": "Member not found.",
        "mod_no_warns": "No warns to clear.",
        "mod_not_jailed": "Member is not in jail.",
        "mod_not_banned": "User is not banned.",
        "mod_history_title": "Moderation History",
        "mod_no_history": "No history.",

        # Config
        "config_saved": "Configuration saved.",
        "config_staff_roles": "Staff roles: {roles}",
        "config_ticket_channel": "Ticket channel: {channel}",
        "config_automod": "Automod updated.",
        "config_autorole": "Autorole: {role}",
        "config_welcome": "Welcome channel: {channel}",
        "config_goodbye": "Goodbye channel: {channel}",
        "config_boost": "Boost channel: {channel}",
        "config_mod_panel": "Mod panel sent to {channel}.",
        "config_reglement": "Rules configured.",
        "config_reglement_post": "Rules posted in {channel}.",

        # Welcome
        "welcome_setup": "Welcome configured in {channel}.",
        "welcome_disabled": "Welcome disabled.",
        "welcome_goodbye_setup": "Goodbye configured in {channel}.",
        "welcome_boost_setup": "Boost configured in {channel}.",
        "welcome_preview": "Welcome preview:",

        # Ticket
        "ticket_setup": "Tickets configured in {channel}.",
        "ticket_panel_sent": "Ticket panel sent.",
        "ticket_config": "Ticket configuration.",
        "ticket_created": "Ticket {id} created.",
        "ticket_closed": "Ticket closed.",
        "ticket_claimed": "Ticket claimed by {user}.",
        "ticket_added": "{user} added to ticket.",
        "ticket_removed": "{user} removed from ticket.",
        "ticket_no_open": "No open tickets.",
        "ticket_transcript": "Transcript generated.",
        "ticket_force_closed": "Ticket force closed.",

        # Music
        "music_added": "**{title}** added to queue.",
        "music_playing": "Playing **{title}**.",
        "music_paused": "Music paused.",
        "music_resumed": "Music resumed.",
        "music_skipped": "Music skipped.",
        "music_stopped": "Music stopped.",
        "music_queue_empty": "Queue is empty.",
        "music_now_playing": "Now playing: **{title}**",
        "music_volume": "Volume: **{volume}%**",
        "music_disconnected": "Disconnected.",
        "music_no_voice": "Join a voice channel first.",
        "music_error": "Error playing music.",

        # Util
        "util_pong": "Pong! Latency: `{ms}ms`",
        "util_uptime": "Uptime: **{time}**",
        "util_bot_info": "Bot Information",
        "util_avatar": "Avatar of {user}",
        "util_banner": "Banner of {user}",
        "util_server_info": "Server Information",
        "util_user_info": "Information about {user}",
        "util_say_sent": "Message sent to {channel}.",
        "util_embed_sent": "Embed sent to {channel}.",
        "util_poll_created": "Poll created.",
        "util_help_title": "Help — Commands",
        "util_afk_set": "AFK activated: {reason}",
        "util_afk_removed": "AFK deactivated.",
        "util_remind_set": "Reminder in {time}.",
        "util_effectif": "Members: **{count}**",
        "util_hierarchie": "Role Hierarchy",
        "util_staff": "Staff Hierarchy",

        # Fun
        "fun_heads": "Heads!",
        "fun_tails": "Tails!",
        "fun_dice": "You rolled **{result}**.",
        "fun_8ball": "Answer: **{answer}**",
        "fun_ship": "Compatibility: **{percent}%**",
        "fun_rate": "Rating: **{score}/10**",

        # Backup
        "backup_created": "Backup created: `{id}`",
        "backup_list": "Backup List",
        "backup_restored": "Backup restored.",
        "backup_deleted": "Backup deleted.",
        "backup_none": "No backups.",
        "backup_restoring": "Restoring...",

        # Stats
        "stats_user": "Stats for {user}",
        "stats_server": "Server Stats",

        # Raid
        "raid_config_saved": "Anti-raid configuration saved.",
        "raid_log_set": "Logs configured in {channel}.",
        "raid_whitelist_added": "{role} added to whitelist.",
        "raid_whitelist_removed": "{role} removed from whitelist.",
        "raid_whitelist_already": "{role} already in whitelist.",
        "raid_whitelist_not": "{role} is not in whitelist.",
        "raid_blacklist_added": "`{id}` added to blacklist.",
        "raid_blacklist_removed": "`{id}` removed from blacklist.",
        "raid_blacklist_already": "`{id}` already in blacklist.",
        "raid_blacklist_not": "`{id}` is not in blacklist.",
        "raid_lockdown_on": "**{count}** channels locked.",
        "raid_lockdown_off": "**{count}** channels unlocked.",
        "raid_scan_done": "Scan complete.",
        "raid_scan_clean": "No suspicious members detected.",
        "raid_massban_done": "**{count}** members banned.",
        "raid_massban_none": "No suspicious members to ban.",
        "raid_status_title": "Anti-Raid — Status",

        # Ghostping
        "ghostping_sent": "Ghostping sent to {channel}.",

        # AI
        "ai_panel": "AI Configuration Panel",
        "ai_enabled": "AI enabled.",
        "ai_disabled": "AI disabled.",
        "ai_auto_mute": "I can't self-moderate.",

        # Owner DM
        "owner_dm_title": "Dev Hub — Language Selection",
        "owner_dm_welcome": "Hello! Thanks for adding **Dev Hub** to your server **{server}**!\n\nPlease choose the language for the bot:",
        "owner_dm_options": "React with:\n🇫🇷 **FR** — Francais\n🇬🇧 **EN** — English\n🇩🇪 **DE** — Deutsch",
        "owner_dm_selected": "Language set to **{lang}** for **{server}**!",
        "owner_dm_footer": "You can change this anytime with /language",

        # Panels
        "panel_welcome_title": "Welcome Panel",
        "panel_goodbye_title": "Goodbye Panel",
        "panel_boost_title": "Boost Panel",
        "panel_ticket_title": "Tickets Panel",
        "panel_raid_title": "Anti-Raid Panel",

        # Natural language
        "nl_muted": "**{user}** muted for {duration} — {reason}",
        "nl_unmuted": "**{user}** unmuted — {reason}",
        "nl_kicked": "**{user}** kicked — {reason}",
        "nl_banned": "**{user}** banned — {reason}",
        "nl_unbanned": "**{user}** unbanned — {reason}",
        "nl_softbanned": "**{user}** softbanned — {reason}",
        "nl_warned": "**{user}** warned ({count}) — {reason}",
        "nl_jailed": "**{user}** jailed — {reason}",
        "nl_unjailed": "**{user}** unjailed — {reason}",
        "nl_unwarned": "**{user}** warns cleared.",
        "nl_say_sent": "Message sent to {channel}.",

        # Anti-raid alerts
        "raid_alert_flood": "FLOOD DETECTED",
        "raid_alert_spam": "SPAM DETECTED",
        "raid_alert_mention": "MASS MENTION",
        "raid_alert_invite": "INVITE DETECTED",
        "raid_alert_caps": "CAPS DETECTED",
        "raid_alert_bot": "BOT JOIN",
        "raid_alert_alt": "ALT ACCOUNT",
        "raid_alert_blacklist": "BLACKLIST",
        "raid_alert_nuke": "NUKE DETECTED",

        # Economy
        "eco_balance_title": "Balance of {user}",
        "eco_wallet": "Wallet",
        "eco_bank": "Bank",
        "eco_total": "Total",
        "eco_level": "Level",
        "eco_items": "Items",
        "eco_daily": "Daily reward",
        "eco_hourly": "Hourly reward",
        "eco_weekly": "Weekly reward",
        "eco_work": "Work",
        "eco_crime": "Crime",
        "eco_crime_success": "Crime successful",
        "eco_crime_caught": "Caught",
        "eco_slots_win": "Won",
        "eco_slots_lose": "Lost",
        "eco_jackpot": "JACKPOT",
        "eco_pay_sent": "Coins sent",
        "eco_pay_received": "Coins received",
        "eco_buy": "Purchase",
        "eco_sell": "Sale",
        "eco_rob_success": "Robbery successful",
        "eco_rob_failed": "Failed",
        "eco_rob_shield": "Shield",
        "eco_leaderboard": "Economy Leaderboard",
        "eco_shop": "Shop",
        "eco_inventory": "Inventory",
        "eco_fishing": "Fishing",
        "eco_mining": "Mining",
        "eco_not_enough": "Not enough coins",
        "eco_cooldown": "You must wait {time}.",

        # Giveaway
        "gw_created": "Giveaway created in {channel}!",
        "gw_ended": "Giveaway ended.",
        "gw_rerolled": "Winners rerolled: {winners}",
        "gw_no_active": "No active giveaways.",
        "gw_not_found": "Giveaway not found.",
        "gw_no_participants": "No participants.",

        # Poll
        "poll_created": "Poll created!",
        "poll_ended": "Results displayed!",
        "poll_not_found": "Poll not found.",
        "poll_no_active": "No active polls.",
        "poll_min_options": "Minimum 2 options.",
        "poll_max_options": "Maximum 10 options.",

        # Level
        "level_title": "Levels — {user}",
        "level_xp": "XP",
        "level_next": "Next level",
        "level_up": "Congratulations {user}! You are now level **{level}**!",
        "level_role_reward": "Role {role} obtained at level **{level}**!",
        "level_no_data": "No level data.",
        "level_leaderboard": "Level Leaderboard",
        "level_config_updated": "Level config updated.",

        # Log
        "log_configured": "Logs configured in {channel}.",
        "log_toggled": "Log `{type}` {status}.",
        "log_no_channel": "No log channel configured.",
    },
    "de": {
        # General
        "lang_set": "Sprache auf **Deutsch** gesetzt.",
        "lang_prompt": "Waehle die Bot-Sprache:",
        "lang_select": "Sprache waehlen",
        "lang_current": "Aktuelle Sprache: **Deutsch**",
        "error": "Ein Fehler ist aufgetreten.",
        "no_perm": "Unzureichende Berechtigungen.",
        "success": "Aktion erfolgreich.",
        "cancelled": "Aktion abgebrochen.",

        # Mod
        "mod_muted": "**{user}** stummgeschaltet fuer {duration} — {reason}",
        "mod_unmuted": "**{user}** nicht mehr stumm — {reason}",
        "mod_kicked": "**{user}** gekickt — {reason}",
        "mod_banned": "**{user}** gebannt — {reason}",
        "mod_unbanned": "**{user}** entbannt — {reason}",
        "mod_softbanned": "**{user}** softban — {reason}",
        "mod_warned": "**{user}** gewarnt ({count}) — {reason}",
        "mod_unwarned": "**{user}** Warnungen geloescht.",
        "mod_jailed": "**{user}** im Gefaengnis — {reason}",
        "mod_unjailed": "**{user}** aus dem Gefaengnis — {reason}",
        "mod_timeout": "**{user}** fuer {duration} blockiert — {reason}",
        "mod_purge": "**{count}** Nachrichten geloescht.",
        "mod_role_added": "Rolle {role} zu {user} hinzugefuegt.",
        "mod_role_removed": "Rolle {role} von {user} entfernt.",
        "mod_member_not_found": "Mitglied nicht gefunden.",
        "mod_no_warns": "Keine Warnungen zum Loeschen.",
        "mod_not_jailed": "Mitglied ist nicht im Gefaengnis.",
        "mod_not_banned": "Benutzer ist nicht gebannt.",
        "mod_history_title": "Moderationsverlauf",
        "mod_no_history": "Kein Verlauf.",

        # Config
        "config_saved": "Konfiguration gespeichert.",
        "config_staff_roles": "Staff-Rollen: {roles}",
        "config_ticket_channel": "Ticket-Kanal: {channel}",
        "config_automod": "Automod aktualisiert.",
        "config_autorole": "Autorolle: {role}",
        "config_welcome": "Willkommenskanal: {channel}",
        "config_goodbye": "Abschiedskanal: {channel}",
        "config_boost": "Boost-Kanal: {channel}",
        "config_mod_panel": "Mod-Panel in {channel} gesendet.",
        "config_reglement": "Regeln konfiguriert.",
        "config_reglement_post": "Regeln in {channel} gepostet.",

        # Welcome
        "welcome_setup": "Willkommen in {channel} konfiguriert.",
        "welcome_disabled": "Willkommen deaktiviert.",
        "welcome_goodbye_setup": "Abschied in {channel} konfiguriert.",
        "welcome_boost_setup": "Boost in {channel} konfiguriert.",
        "welcome_preview": "Willkommens-Vorschau:",

        # Ticket
        "ticket_setup": "Tickets in {channel} konfiguriert.",
        "ticket_panel_sent": "Ticket-Panel gesendet.",
        "ticket_config": "Ticket-Konfiguration.",
        "ticket_created": "Ticket {id} erstellt.",
        "ticket_closed": "Ticket geschlossen.",
        "ticket_claimed": "Ticket von {user} uebernommen.",
        "ticket_added": "{user} zum Ticket hinzugefuegt.",
        "ticket_removed": "{user} aus Ticket entfernt.",
        "ticket_no_open": "Keine offenen Tickets.",
        "ticket_transcript": "Transkript erstellt.",
        "ticket_force_closed": "Ticket zwangsweise geschlossen.",

        # Music
        "music_added": "**{title}** zur Warteschlange hinzugefuegt.",
        "music_playing": "Spiele **{title}**.",
        "music_paused": "Musik pausiert.",
        "music_resumed": "Musik fortgesetzt.",
        "music_skipped": "Musik uebersprungen.",
        "music_stopped": "Musik gestoppt.",
        "music_queue_empty": "Warteschlange ist leer.",
        "music_now_playing": "Jetzt spielend: **{title}**",
        "music_volume": "Lautstaerke: **{volume}%**",
        "music_disconnected": "Getrennt.",
        "music_no_voice": "Tritt zuerst einem Sprachkanal bei.",
        "music_error": "Fehler beim Abspielen.",

        # Util
        "util_pong": "Pong! Latenz: `{ms}ms`",
        "util_uptime": "Uptime: **{time}**",
        "util_bot_info": "Bot-Informationen",
        "util_avatar": "Avatar von {user}",
        "util_banner": "Banner von {user}",
        "util_server_info": "Server-Informationen",
        "util_user_info": "Informationen ueber {user}",
        "util_say_sent": "Nachricht an {channel} gesendet.",
        "util_embed_sent": "Embed an {channel} gesendet.",
        "util_poll_created": "Umfrage erstellt.",
        "util_help_title": "Hilfe — Befehle",
        "util_afk_set": "AFK aktiviert: {reason}",
        "util_afk_removed": "AFK deaktiviert.",
        "util_remind_set": "Erinnerung in {time}.",
        "util_effectif": "Mitglieder: **{count}**",
        "util_hierarchie": "Rollen-Hierarchie",
        "util_staff": "Staff-Hierarchie",

        # Fun
        "fun_heads": "Kopf!",
        "fun_tails": "Zahl!",
        "fun_dice": "Du hast **{result}** gewuerfelt.",
        "fun_8ball": "Antwort: **{answer}**",
        "fun_ship": "Kompatibilitaet: **{percent}%**",
        "fun_rate": "Bewertung: **{score}/10**",

        # Backup
        "backup_created": "Backup erstellt: `{id}`",
        "backup_list": "Backup-Liste",
        "backup_restored": "Backup wiederhergestellt.",
        "backup_deleted": "Backup geloescht.",
        "backup_none": "Keine Backups.",
        "backup_restoring": "Wird wiederhergestellt...",

        # Stats
        "stats_user": "Statistiken fuer {user}",
        "stats_server": "Server-Statistiken",

        # Raid
        "raid_config_saved": "Anti-Raid-Konfiguration gespeichert.",
        "raid_log_set": "Logs in {channel} konfiguriert.",
        "raid_whitelist_added": "{role} zur Whitelist hinzugefuegt.",
        "raid_whitelist_removed": "{role} von Whitelist entfernt.",
        "raid_whitelist_already": "{role} bereits in Whitelist.",
        "raid_whitelist_not": "{role} ist nicht in Whitelist.",
        "raid_blacklist_added": "`{id}` zur Blacklist hinzugefuegt.",
        "raid_blacklist_removed": "`{id}` von Blacklist entfernt.",
        "raid_blacklist_already": "`{id}` bereits in Blacklist.",
        "raid_blacklist_not": "`{id}` ist nicht in Blacklist.",
        "raid_lockdown_on": "**{count}** Kanale gesperrt.",
        "raid_lockdown_off": "**{count}** Kanale entsperrt.",
        "raid_scan_done": "Scan abgeschlossen.",
        "raid_scan_clean": "Keine verdaechtigen Mitglieder erkannt.",
        "raid_massban_done": "**{count}** Mitglieder gebannt.",
        "raid_massban_none": "Keine verdaechtigen Mitglieder zum Bannen.",
        "raid_status_title": "Anti-Raid — Status",

        # Ghostping
        "ghostping_sent": "Ghostping an {channel} gesendet.",

        # AI
        "ai_panel": "KI-Konfigurations-Panel",
        "ai_enabled": "KI aktiviert.",
        "ai_disabled": "KI deaktiviert.",
        "ai_auto_mute": "Ich kann mich nicht selbst moderieren.",

        # Owner DM
        "owner_dm_title": "Dev Hub — Sprachauswahl",
        "owner_dm_welcome": "Hallo! Danke dass du **Dev Hub** zu deinem Server **{server}** hinzugefuegt hast!\n\nBitte waehle die Sprache fuer den Bot:",
        "owner_dm_options": "Reagiere mit:\n🇫🇷 **FR** — Francais\n🇬🇧 **EN** — English\n🇩🇪 **DE** — Deutsch",
        "owner_dm_selected": "Sprache auf **{lang}** fuer **{server}** gesetzt!",
        "owner_dm_footer": "Du kannst das jederzeit mit /language aendern",

        # Panels
        "panel_welcome_title": "Willkommen-Panel",
        "panel_goodbye_title": "Abschieds-Panel",
        "panel_boost_title": "Boost-Panel",
        "panel_ticket_title": "Tickets-Panel",
        "panel_raid_title": "Anti-Raid-Panel",

        # Natural language
        "nl_muted": "**{user}** stummgeschaltet fuer {duration} — {reason}",
        "nl_unmuted": "**{user}** nicht mehr stumm — {reason}",
        "nl_kicked": "**{user}** gekickt — {reason}",
        "nl_banned": "**{user}** gebannt — {reason}",
        "nl_unbanned": "**{user}** entbannt — {reason}",
        "nl_softbanned": "**{user}** softban — {reason}",
        "nl_warned": "**{user}** gewarnt ({count}) — {reason}",
        "nl_jailed": "**{user}** im Gefaengnis — {reason}",
        "nl_unjailed": "**{user}** aus dem Gefaengnis — {reason}",
        "nl_unwarned": "**{user}** Warnungen geloescht.",
        "nl_say_sent": "Nachricht an {channel} gesendet.",

        # Anti-raid alerts
        "raid_alert_flood": "FLUT ERKANNT",
        "raid_alert_spam": "SPAM ERKANNT",
        "raid_alert_mention": "MASS-ERWAHNUNG",
        "raid_alert_invite": "EINLADUNG ERKANNT",
        "raid_alert_caps": "GROSSBUCHSTABEN ERKANNT",
        "raid_alert_bot": "BOT BEIGETRETEN",
        "raid_alert_alt": "ALT-KONTO",
        "raid_alert_blacklist": "BLACKLIST",
        "raid_alert_nuke": "NUKE ERKANNT",

        # Economy
        "eco_balance_title": "Guthaben von {user}",
        "eco_wallet": "Brieftasche",
        "eco_bank": "Bank",
        "eco_total": "Gesamt",
        "eco_level": "Level",
        "eco_items": "Gegenstaende",
        "eco_daily": "Taegliche Belohnung",
        "eco_hourly": "Stuendliche Belohnung",
        "eco_weekly": "Woechentliche Belohnung",
        "eco_work": "Arbeit",
        "eco_crime": "Verbrechen",
        "eco_crime_success": "Verbrechen erfolgreich",
        "eco_crime_caught": "Erwischt",
        "eco_slots_win": "Gewonnen",
        "eco_slots_lose": "Verloren",
        "eco_jackpot": "JACKPOT",
        "eco_pay_sent": "Muenzen gesendet",
        "eco_pay_received": "Muenzen erhalten",
        "eco_buy": "Kauf",
        "eco_sell": "Verkauf",
        "eco_rob_success": "Raub erfolgreich",
        "eco_rob_failed": "Fehlgeschlagen",
        "eco_rob_shield": "Schild",
        "eco_leaderboard": "Wirtschafts-Rangliste",
        "eco_shop": "Geschaeft",
        "eco_inventory": "Inventar",
        "eco_fishing": "Angeln",
        "eco_mining": "Bergbau",
        "eco_not_enough": "Nicht genug Muenzen",
        "eco_cooldown": "Du musst {time} warten.",

        # Giveaway
        "gw_created": "Giveaway erstellt in {channel}!",
        "gw_ended": "Giveaway beendet.",
        "gw_rerolled": "Gewinner neu gezogen: {winners}",
        "gw_no_active": "Keine aktiven Giveaways.",
        "gw_not_found": "Giveaway nicht gefunden.",
        "gw_no_participants": "Keine Teilnehmer.",

        # Poll
        "poll_created": "Umfrage erstellt!",
        "poll_ended": "Ergebnisse angezeigt!",
        "poll_not_found": "Umfrage nicht gefunden.",
        "poll_no_active": "Keine aktiven Umfragen.",
        "poll_min_options": "Mindestens 2 Optionen.",
        "poll_max_options": "Maximal 10 Optionen.",

        # Level
        "level_title": "Level — {user}",
        "level_xp": "XP",
        "level_next": "Naechstes Level",
        "level_up": "Herzlichen Glueckwunsch {user}! Du bist jetzt Level **{level}**!",
        "level_role_reward": "Rolle {role} erhalten ab Level **{level}**!",
        "level_no_data": "Keine Level-Daten.",
        "level_leaderboard": "Level-Rangliste",
        "level_config_updated": "Level-Konfiguration aktualisiert.",

        # Log
        "log_configured": "Logs konfiguriert in {channel}.",
        "log_toggled": "Log `{type}` {status}.",
        "log_no_channel": "Kein Log-Kanal konfiguriert.",
    },
}

# Language names for display
LANG_NAMES = {
    "fr": "Francais",
    "en": "English",
    "de": "Deutsch",
}

LANG_FLAGS = {
    "fr": "FR",
    "en": "EN",
    "de": "DE",
}


def get_lang(guild_id, settings=None):
    """Get the language for a guild, defaulting to 'fr'."""
    if settings:
        s = settings.get(str(guild_id), {})
        return s.get("language", "fr")
    return "fr"


def t(key, guild_id=None, lang=None, **kwargs):
    """Get a translated string. Pass either guild_id (looks up settings) or lang directly."""
    if lang is None:
        lang = get_lang(guild_id) if guild_id else "fr"
    strings = TRANSLATIONS.get(lang, TRANSLATIONS["fr"])
    text = strings.get(key, TRANSLATIONS["fr"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
