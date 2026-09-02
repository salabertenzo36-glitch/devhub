import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json
import os
import time
import random
import asyncio
import hashlib
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont

from config import TOKEN

BOT_START = datetime.now(timezone.utc)

class DevHub(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        self.add_view(PersistentTicketView())


# ─── GROUPES DE COMMANDES ───
mod = app_commands.Group(name="mod", description="Modération")
config = app_commands.Group(name="config", description="Configuration du bot")
welcome = app_commands.Group(name="welcome", description="Welcome, Goodbye & Boost")
ticket = app_commands.Group(name="ticket", description="Système de tickets")
music = app_commands.Group(name="music", description="Commandes musique")
util = app_commands.Group(name="util", description="Utilitaires")
fun = app_commands.Group(name="fun", description="Fun & Jeux")
backup = app_commands.Group(name="backup", description="Sauvegardes")
stats = app_commands.Group(name="stats", description="Statistiques")
raid = app_commands.Group(name="raid", description="Anti-raid")
ghostping = app_commands.Group(name="ghostping", description="Ghostping & Autorole")
ai = app_commands.Group(name="ai", description="Intelligence artificielle")


class PersistentTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Select(
            placeholder="Ouvrir un ticket...",
            options=[
                discord.SelectOption(label="Bug Report", value="bug", description="Signaler un bug", emoji="🐛"),
                discord.SelectOption(label="Suggestion", value="suggestion", description="Proposer une amélioration", emoji="💡"),
                discord.SelectOption(label="Support", value="support", description="Besoin d'aide", emoji="🎧"),
                discord.SelectOption(label="Report", value="report", description="Signaler un membre", emoji="🚨"),
                discord.SelectOption(label="Création", value="creation", description="Demander une création", emoji="🎨"),
                discord.SelectOption(label="Autre", value="autre", description="Autre demande", emoji="📋"),
            ],
            custom_id="ticket_select_persistent"
        ))


class PersistentTicketClose(discord.ui.LayoutView):
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_colour=None)
        container.add_item(discord.ui.TextDisplay("## Ticket Fermé"))
        container.add_item(discord.ui.Separator())
        row = discord.ui.ActionRow()
        row.add_item(discord.ui.Button(label="Rouvrir", style=discord.ButtonStyle.secondary, custom_id=f"ticket_reopen_{channel_id}"))
        row.add_item(discord.ui.Button(label="Supprimer", style=discord.ButtonStyle.danger, custom_id=f"ticket_delete_{channel_id}"))
        container.add_item(row)
        self.add_item(container)


bot = DevHub()

ROLES_PER_PAGE = 15
TICKETS_FILE = "tickets.json"
SETTINGS_FILE = "settings.json"


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_tickets():
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_tickets(data):
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)



WARNS_FILE = "warns.json"


def load_warns():
    if os.path.exists(WARNS_FILE):
        try:
            with open(WARNS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_warns(data):
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)


JAIL_FILE = "jail.json"


def load_jail():
    if os.path.exists(JAIL_FILE):
        try:
            with open(JAIL_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_jail(data):
    with open(JAIL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def ts(d):
    return f"<t:{int(d.timestamp())}:d>"


def ts_relative(d):
    return f"<t:{int(d.timestamp())}:R>"


def embed_simple(title=None, description=None):
    e = discord.Embed(color=0x000000, timestamp=datetime.now(timezone.utc))
    if title:
        e.title = title
    if description:
        e.description = description
    return e


def view_text(*lines):
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=None)
    for line in lines:
        container.add_item(discord.ui.TextDisplay(line or "\u200b"))
    view.add_item(container)
    return view


def make_page_view(guild, lines, title, page, total):
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=None)
    if guild.icon:
        section = discord.ui.Section(
            accessory=discord.ui.Thumbnail(media=guild.icon.url, description=guild.name)
        )
        section.add_item(discord.ui.TextDisplay(f"## {title} — {guild.name}"))
        container.add_item(section)
    else:
        container.add_item(discord.ui.TextDisplay(f"## {title} — {guild.name}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("\n".join(lines) if lines else "`Aucun rôle`"))
    if total > 1:
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(f"**Page {page} / {total}**"))
    view.add_item(container)
    return view


# ──────────────────────────────────────────────
#  CANVAS IMAGE GENERATION
# ──────────────────────────────────────────────

COLORS = {
    "bg": (5, 5, 7),
    "surface": (12, 12, 16),
    "card": (17, 17, 22),
    "silver": (176, 184, 196),
    "silver_bright": (208, 212, 220),
    "dim": (82, 82, 91),
    "muted": (63, 63, 70),
    "white": (255, 255, 255),
    "accent": (176, 184, 196),
}

FONTS = {
    "bold": "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "regular": "/System/Library/Fonts/Supplemental/Arial.ttf",
    "linux_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "linux_regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}


def get_font(style, size):
    import platform
    if platform.system() == "Linux":
        style = f"linux_{style}"
    path = FONTS.get(style, FONTS.get("regular", FONTS.get("linux_regular")))
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_circle_avatar(img, avatar_img, center, radius):
    avatar = avatar_img.resize((radius * 2, radius * 2), Image.LANCZOS)
    mask = Image.new("L", (radius * 2, radius * 2), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, radius * 2 - 1, radius * 2 - 1), fill=255)
    img.paste(avatar, (center[0] - radius, center[1] - radius), mask)


def draw_accent_line(draw, x, y, width, color=COLORS["accent"]):
    for i in range(width):
        alpha = 1.0 - abs(i - width / 2) / (width / 2)
        c = tuple(int(c * alpha) for c in color)
        draw.point((x + i, y), fill=c)


async def fetch_avatar(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.read()
                return Image.open(io.BytesIO(data)).convert("RGBA")
    return Image.new("RGBA", (256, 256), COLORS["silver"])


async def generate_welcome_image(member):
    W, H = 1000, 480
    img = Image.new("RGBA", (W, H), COLORS["bg"] + (255,))
    draw = ImageDraw.Draw(img)

    draw_rounded_rect(draw, (0, 0, W - 1, H - 1), radius=24, fill=COLORS["surface"] + (255,))

    for i in range(W):
        alpha = max(0, 0.1 - abs(i - W / 2) / (W / 2) * 0.1)
        c = COLORS["accent"]
        draw.point((i, 0), fill=c + (int(alpha * 255),))
        draw.point((i, 1), fill=c + (int(alpha * 200),))
        draw.point((i, 2), fill=c + (int(alpha * 150),))

    avatar = await fetch_avatar(member.display_avatar.url)
    draw_circle_avatar(img, avatar, (170, 210), 90)

    draw.ellipse((70, 110, 72 + 200, 112 + 200), outline=COLORS["accent"] + (80,), width=2)

    font_title = get_font("bold", 48)
    font_name = get_font("bold", 34)
    font_sub = get_font("regular", 22)
    font_small = get_font("regular", 16)

    draw.text((300, 120), "Bienvenue", fill=COLORS["accent"], font=font_title)

    name = member.display_name
    if len(name) > 26:
        name = name[:24] + ".."
    draw.text((300, 180), name, fill=COLORS["white"], font=font_name)

    draw.text((300, 226), f"sur {member.guild.name}", fill=COLORS["dim"], font=font_sub)

    draw.line((300, 270, 720, 270), fill=COLORS["accent"] + (50,), width=1)

    member_count = member.guild.member_count
    draw.text((300, 290), f"Membre #{member_count}", fill=COLORS["silver"], font=font_sub)

    created = member.created_at.strftime("%d/%m/%Y")
    draw.text((300, 330), f"Compte créé le {created}", fill=COLORS["muted"], font=font_small)

    draw.line((40, H - 55, W - 40, H - 55), fill=COLORS["accent"] + (30,), width=1)
    draw.text((W // 2 - 50, H - 44), "Dev Hub", fill=COLORS["muted"], font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="welcome.png")


async def generate_goodbye_image(member):
    W, H = 1000, 480
    img = Image.new("RGBA", (W, H), COLORS["bg"] + (255,))
    draw = ImageDraw.Draw(img)

    draw_rounded_rect(draw, (0, 0, W - 1, H - 1), radius=24, fill=COLORS["surface"] + (255,))

    for i in range(W):
        alpha = max(0, 0.06 - abs(i - W / 2) / (W / 2) * 0.06)
        c = COLORS["dim"]
        draw.point((i, 0), fill=c + (int(alpha * 255),))
        draw.point((i, 1), fill=c + (int(alpha * 200),))

    avatar = await fetch_avatar(member.display_avatar.url)

    avatar_gray = avatar.copy()
    gray_data = avatar_gray.getdata()
    gray_list = []
    for r, g, b, a in gray_data:
        avg = int(0.299 * r + 0.587 * g + 0.114 * b)
        gray_list.append((avg, avg, avg, a))
    avatar_gray.putdata(gray_list)

    draw_circle_avatar(img, avatar_gray, (170, 210), 90)

    draw.ellipse((70, 110, 72 + 200, 112 + 200), outline=COLORS["dim"] + (50,), width=2)

    font_title = get_font("bold", 48)
    font_name = get_font("bold", 34)
    font_sub = get_font("regular", 22)
    font_small = get_font("regular", 16)

    draw.text((300, 120), "Au revoir", fill=COLORS["dim"], font=font_title)

    name = member.display_name
    if len(name) > 26:
        name = name[:24] + ".."
    draw.text((300, 180), name, fill=COLORS["white"], font=font_name)

    draw.text((300, 226), f"a quitté {member.guild.name}", fill=COLORS["muted"], font=font_sub)

    draw.line((300, 270, 720, 270), fill=COLORS["dim"] + (40,), width=1)

    member_count = member.guild.member_count
    draw.text((300, 290), f"Il reste {member_count} membres", fill=COLORS["dim"], font=font_sub)

    draw.line((40, H - 55, W - 40, H - 55), fill=COLORS["dim"] + (25,), width=1)
    draw.text((W // 2 - 50, H - 44), "Dev Hub", fill=COLORS["muted"], font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="goodbye.png")


async def generate_boost_image(member):
    W, H = 1000, 480
    img = Image.new("RGBA", (W, H), COLORS["bg"] + (255,))
    draw = ImageDraw.Draw(img)

    draw_rounded_rect(draw, (0, 0, W - 1, H - 1), radius=24, fill=COLORS["surface"] + (255,))

    for i in range(W):
        progress = i / W
        wave = (0.5 + 0.5 * math.sin(progress * 6.28)) * 0.14
        c = COLORS["accent"]
        draw.point((i, 0), fill=c + (int(wave * 255),))
        draw.point((i, 1), fill=c + (int(wave * 200),))
        draw.point((i, 2), fill=c + (int(wave * 150),))

    avatar = await fetch_avatar(member.display_avatar.url)
    draw_circle_avatar(img, avatar, (170, 210), 90)

    draw.ellipse((70, 110, 72 + 200, 112 + 200), outline=COLORS["accent"] + (100,), width=2)

    font_title = get_font("bold", 48)
    font_name = get_font("bold", 34)
    font_sub = get_font("regular", 22)
    font_small = get_font("regular", 16)

    draw.text((300, 120), "Boost", fill=COLORS["accent"], font=font_title)

    name = member.display_name
    if len(name) > 26:
        name = name[:24] + ".."
    draw.text((300, 180), name, fill=COLORS["white"], font=font_name)

    draw.text((300, 226), f"a boosté {member.guild.name}", fill=COLORS["silver"], font=font_sub)

    draw.line((300, 270, 720, 270), fill=COLORS["accent"] + (50,), width=1)

    boost_count = member.guild.premium_subscription_count or 0
    draw.text((300, 290), f"Boost total : {boost_count}", fill=COLORS["accent"], font=font_sub)

    draw.line((40, H - 55, W - 40, H - 55), fill=COLORS["accent"] + (30,), width=1)
    draw.text((W // 2 - 50, H - 44), "Dev Hub", fill=COLORS["muted"], font=font_small)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="boost.png")


@bot.event
async def on_ready():
    print(f"▸ {bot.user.name} connecté")
    print(f"▸ Serveurs : {len(bot.guilds)}")

    total_members = sum(g.member_count or 0 for g in bot.guilds)
    activity = discord.Streaming(
        name=f"Dev Hub — {len(bot.guilds)} serveurs | {total_members} membres",
        url="https://www.twitch.tv/devhub"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

    emoji_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emojis", "upload")
    if os.path.isdir(emoji_dir):
        OUR_EMOJIS = {
            "moderation", "mod_avancee", "vocal", "utilitaires", "fun", "stats",
            "hierarchie", "tickets", "ghostping", "welcome", "automod", "salon",
            "bug", "suggestion", "support", "report", "autre", "music", "cleanup"
        }
        for guild in bot.guilds:
            existing = {e.name: e for e in guild.emojis}
            for name in OUR_EMOJIS:
                if name in existing:
                    try:
                        await existing[name].delete(reason="Emoji refresh v7")
                    except discord.Forbidden:
                        pass
            for fname in sorted(os.listdir(emoji_dir)):
                if not fname.endswith(".png"):
                    continue
                ename = fname.replace(".png", "")
                path = os.path.join(emoji_dir, fname)
                with open(path, "rb") as f:
                    data = f.read()
                try:
                    await guild.create_custom_emoji(name=ename, image=data, reason="Emoji v7")
                    print(f"  ▸ Emoji uploadé : :{ename}:")
                except discord.Forbidden:
                    print(f"  ▸ Permission refusée pour :{ename}:")
                    break
                except discord.HTTPException:
                    pass
            print(f"▸ Emojis mis à jour pour {guild.name}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"▸ Ajouté à {guild.name} ({guild.id}) — {guild.member_count} membres")

    total_members = sum(g.member_count or 0 for g in bot.guilds)
    activity = discord.Streaming(
        name=f"Dev Hub — {len(bot.guilds)} serveurs | {total_members} membres",
        url="https://www.twitch.tv/devhub"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

    channel = bot.get_channel(1544098981670289530)
    if channel:
        owner = guild.owner
        owner_text = f"{owner.mention} (`{owner.id}`)" if owner else "`Inconnu`"
        view = view_text(
            "## 📥 Nouveau serveur",
            f"**Nom** {guild.name}",
            f"**ID** `{guild.id}`",
            f"**Membres** `{guild.member_count}`",
            f"**Propriétaire** {owner_text}",
            f"**Boost** `{guild.premium_subscription_count or 0}`",
            f"**Salons** `{len(guild.channels)}`",
            f"**Rôles** `{len(guild.roles)}`",
            f"**Créé le** <t:{int(guild.created_at.timestamp())}:R>",
            "",
            f"**Total serveurs** `{len(bot.guilds)}`"
        )
        try:
            await channel.send(view=view)
        except discord.Forbidden:
            pass


@bot.event
async def on_guild_remove(guild: discord.Guild):
    print(f"▸ Retiré de {guild.name} ({guild.id})")
    total_members = sum(g.member_count or 0 for g in bot.guilds)
    activity = discord.Streaming(
        name=f"Dev Hub — {len(bot.guilds)} serveurs | {total_members} membres",
        url="https://www.twitch.tv/devhub"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type not in (discord.InteractionType.component, discord.InteractionType.modal_submit):
        return
    custom_id = interaction.data.get("custom_id", "")
    cid = custom_id

    if custom_id == "help_category_select":
        value = interaction.data.get("values", [None])[0]
        if value and value in HELP_CATEGORIES:
            view = make_help_view(value)
            await interaction.response.edit_message(view=view)
        else:
            await interaction.response.defer()
        return

    if custom_id == "reglement_accept":
        gid = str(interaction.guild.id)
        settings = load_settings()
        s = settings.get(gid, {})
        role_id = s.get("reglement_role")
        if not role_id:
            await interaction.response.send_message("Le systeme de reglement n'est pas configure.", ephemeral=True)
            return
        role = interaction.guild.get_role(int(role_id))
        if not role:
            await interaction.response.send_message("Le role de reglement est introuvable.", ephemeral=True)
            return
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            await interaction.response.send_message("Membre introuvable.", ephemeral=True)
            return
        if role in member.roles:
            await interaction.response.send_message("Tu as deja accepte le reglement.", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason="Reglement accepte")
            await interaction.response.send_message(f"Reglement accepte ! Le role {role.mention} t'a ete attribue.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Impossible d'assigner le role (permissions manquantes).", ephemeral=True)
        return

    if custom_id in ("ticket_select_persistent", "ticket_setup_select", "ticket_select", "ticket_panel_select"):
        value = interaction.data.get("values", [None])[0]
        if value:
            await handle_ticket_open(interaction, value)

    # --- TICKET: CLAIM ---
    elif custom_id.startswith("ticket_claim_"):
        channel_id = custom_id.replace("ticket_claim_", "")
        if str(interaction.channel.id) != channel_id:
            return
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        cid = str(interaction.channel.id)
        if gid not in tickets or cid not in tickets[gid]:
            await interaction.response.send_message("Ticket introuvable.", ephemeral=True)
            return
        ticket = tickets[gid][cid]
        if ticket.get("claimed_by"):
            claimer = interaction.guild.get_member(ticket["claimed_by"])
            claimer_name = claimer.display_name if claimer else "Inconnu"
            await interaction.response.send_message(f"Ce ticket est déjà claim par **{claimer_name}**.", ephemeral=True)
            return
        ticket["claimed_by"] = interaction.user.id
        ticket["claimed_at"] = datetime.now(timezone.utc).isoformat()
        save_tickets(tickets)
        view = view_text(
            f"## Ticket Claim",
            f"**Claim par** {interaction.user.mention}",
            f"**Le** <t:{int(datetime.now(timezone.utc).timestamp())}:R>"
        )
        await interaction.response.send_message(view=view)

    # --- TICKET: ADD MEMBER ---
    elif custom_id.startswith("ticket_add_"):
        channel_id = custom_id.replace("ticket_add_", "")
        if str(interaction.channel.id) != channel_id:
            return
        modal = discord.ui.Modal(title="Ajouter un membre", custom_id=f"ticket_add_modal_{channel_id}")
        modal.add_item(discord.ui.TextInput(label="ID ou mention du membre", placeholder="123456789012345678 ou @user"))
        await interaction.response.send_modal(modal)

    # --- TICKET: REMOVE MEMBER ---
    elif custom_id.startswith("ticket_remove_"):
        channel_id = custom_id.replace("ticket_remove_", "")
        if str(interaction.channel.id) != channel_id:
            return
        modal = discord.ui.Modal(title="Retirer un membre", custom_id=f"ticket_remove_modal_{channel_id}")
        modal.add_item(discord.ui.TextInput(label="ID ou mention du membre", placeholder="123456789012345678 ou @user"))
        await interaction.response.send_modal(modal)

    # --- TICKET: TRANSCRIPT ---
    elif custom_id.startswith("ticket_transcript_"):
        channel_id = custom_id.replace("ticket_transcript_", "")
        if str(interaction.channel.id) != channel_id:
            return
        await interaction.response.defer(ephemeral=True)
        messages = []
        async for message in interaction.channel.history(limit=500, oldest_first=True):
            if not message.author.bot:
                messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author.display_name}: {message.content}")
            elif message.embeds:
                for e in message.embeds:
                    if e.description:
                        messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author.display_name}: {e.description}")
        transcript = "\n".join(messages) if messages else "Aucun message."
        file = discord.File(
            fp=io.BytesIO(transcript.encode()),
            filename=f"transcript-{interaction.channel.name}.txt"
        )
        await interaction.followup.send("Transcript généré :", file=file, ephemeral=True)

    # --- TICKET: CLOSE ---
    elif custom_id.startswith("ticket_close_"):
        channel_id = custom_id.replace("ticket_close_", "")
        if str(interaction.channel.id) != channel_id:
            return
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        cid = str(interaction.channel.id)
        if gid not in tickets or cid not in tickets[gid]:
            await interaction.response.send_message("Ticket introuvable.", ephemeral=True)
            return
        ticket = tickets[gid][cid]
        ticket["status"] = "closed"
        ticket["closed_at"] = datetime.now(timezone.utc).isoformat()
        ticket["closed_by"] = interaction.user.id
        save_tickets(tickets)

        config = get_ticket_config(interaction.guild.id)
        close_msg = config.get("close_msg", "Ticket fermé. Merci d'avoir contacté le support.")
        await interaction.response.send_message(close_msg)

        member = interaction.guild.get_member(ticket["user_id"])
        if member:
            await interaction.channel.set_permissions(member, view_channel=False, send_messages=False)

        view = PersistentTicketClose(interaction.channel.id)
        await interaction.channel.send(view=view)

        log_channel_id = config.get("ticket_log_channel")
        if log_channel_id:
            log_ch = interaction.guild.get_channel(int(log_channel_id))
            if log_ch:
                messages = []
                async for message in interaction.channel.history(limit=500, oldest_first=True):
                    if not message.author.bot:
                        messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author.display_name}: {message.content}")
                transcript = "\n".join(messages) if messages else "Aucun message."
                file = discord.File(
                    fp=io.BytesIO(transcript.encode()),
                    filename=f"transcript-{interaction.channel.name}.txt"
                )
                await log_ch.send(
                    f"**Ticket fermé** par {interaction.user.mention}\n"
                    f"**Salon** `{interaction.channel.name}`\n"
                    f"**Membre** {member.mention if member else 'Inconnu'}",
                    file=file
                )

    elif custom_id.startswith("ticket_reopen_"):
        channel_id = custom_id.replace("ticket_reopen_", "")
        if str(interaction.channel.id) != channel_id:
            return
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        cid = str(interaction.channel.id)
        if gid not in tickets or cid not in tickets[gid]:
            await interaction.response.send_message("Ticket introuvable.", ephemeral=True)
            return
        ticket = tickets[gid][cid]
        ticket["status"] = "open"
        ticket["reopened_at"] = datetime.now(timezone.utc).isoformat()
        save_tickets(tickets)
        member = interaction.guild.get_member(ticket["user_id"])
        if member:
            await interaction.channel.set_permissions(member, view_channel=True, send_messages=True)

        types = get_ticket_types(interaction.guild.id)
        type_label = types.get(ticket["type"], {}).get("label", "Inconnu")

        await interaction.response.send_message("Ticket rouvert.")
        view = discord.ui.LayoutView()
        container = discord.ui.Container(accent_colour=None)
        if member:
            section = discord.ui.Section(
                accessory=discord.ui.Thumbnail(media=member.display_avatar.url, description=member.display_name)
            )
            section.add_item(discord.ui.TextDisplay(
                f"## Ticket Réouvert\n"
                f"**Membre** {member.mention}\n"
                f"**Type** {type_label}"
            ))
            container.add_item(section)
        else:
            container.add_item(discord.ui.TextDisplay("## Ticket Réouvert"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay("**Utilisez /close pour fermer le ticket.**"))
        view.add_item(container)
        await interaction.channel.send(view=view)

    elif custom_id.startswith("ticket_delete_"):
        channel_id = custom_id.replace("ticket_delete_", "")
        if str(interaction.channel.id) != channel_id:
            return
        await interaction.response.send_message("Suppression du salon...")
        try:
            await interaction.channel.delete()
        except discord.Forbidden:
            await interaction.followup.send("Pas les permissions pour supprimer ce salon.")

    # --- PANELS (components) ---
    elif cid in ("wp_channel", "wp_message", "wp_image", "wp_disable",
                 "gp_channel", "gp_message", "gp_image", "gp_disable",
                 "bp_channel", "bp_message", "bp_image", "bp_disable",
                 "mp_automod", "mp_log", "mp_purge",
                 "ai_on", "ai_off"):
        gid = str(interaction.guild.id) if interaction.guild else None
        settings = load_settings()
        if gid and gid not in settings:
            settings[gid] = {}

        if cid == "wp_channel":
            modal = discord.ui.Modal(title="Salon Welcome", custom_id="wp_channel_modal")
            modal.add_item(discord.ui.TextInput(label="ID ou mention du salon", placeholder="#general"))
            await interaction.response.send_modal(modal)
        elif cid == "wp_message":
            modal = discord.ui.Modal(title="Message Welcome", custom_id="wp_message_modal")
            modal.add_item(discord.ui.TextInput(label="Message", placeholder="Bienvenue {user} sur {server} !", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif cid == "wp_image":
            current = settings[gid].get("welcome_image", True)
            settings[gid]["welcome_image"] = not current
            save_settings(settings)
            await interaction.response.send_message(f"Image Canvas : {'Activée' if not current else 'Désactivée'}", ephemeral=True)
        elif cid == "wp_disable":
            settings[gid].pop("welcome_channel", None)
            settings[gid].pop("welcome_message", None)
            settings[gid].pop("welcome_image", None)
            save_settings(settings)
            await interaction.response.send_message("Welcome désactivé.", ephemeral=True)
        elif cid == "gp_channel":
            modal = discord.ui.Modal(title="Salon Goodbye", custom_id="gp_channel_modal")
            modal.add_item(discord.ui.TextInput(label="ID ou mention du salon", placeholder="#goodbye"))
            await interaction.response.send_modal(modal)
        elif cid == "gp_message":
            modal = discord.ui.Modal(title="Message Goodbye", custom_id="gp_message_modal")
            modal.add_item(discord.ui.TextInput(label="Message", placeholder="{user} a quitté {server}.", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif cid == "gp_image":
            current = settings[gid].get("goodbye_image", True)
            settings[gid]["goodbye_image"] = not current
            save_settings(settings)
            await interaction.response.send_message(f"Image Canvas : {'Activée' if not current else 'Désactivée'}", ephemeral=True)
        elif cid == "gp_disable":
            settings[gid].pop("goodbye_channel", None)
            settings[gid].pop("goodbye_message", None)
            settings[gid].pop("goodbye_image", None)
            save_settings(settings)
            await interaction.response.send_message("Goodbye désactivé.", ephemeral=True)
        elif cid == "bp_channel":
            modal = discord.ui.Modal(title="Salon Boost", custom_id="bp_channel_modal")
            modal.add_item(discord.ui.TextInput(label="ID ou mention du salon", placeholder="#boost"))
            await interaction.response.send_modal(modal)
        elif cid == "bp_message":
            modal = discord.ui.Modal(title="Message Boost", custom_id="bp_message_modal")
            modal.add_item(discord.ui.TextInput(label="Message", placeholder="{user} a boosté {server} !", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif cid == "bp_image":
            current = settings[gid].get("boost_image", True)
            settings[gid]["boost_image"] = not current
            save_settings(settings)
            await interaction.response.send_message(f"Image Canvas : {'Activée' if not current else 'Désactivée'}", ephemeral=True)
        elif cid == "bp_disable":
            settings[gid].pop("boost_channel", None)
            settings[gid].pop("boost_message", None)
            settings[gid].pop("boost_image", None)
            save_settings(settings)
            await interaction.response.send_message("Boost désactivé.", ephemeral=True)
        elif cid == "mp_automod":
            current = settings[gid].get("automod_enabled", False)
            settings[gid]["automod_enabled"] = not current
            save_settings(settings)
            await interaction.response.send_message(f"Automod : {'ON' if not current else 'OFF'}", ephemeral=True)
        elif cid == "mp_log":
            modal = discord.ui.Modal(title="Salon Logs Mod", custom_id="mp_log_modal")
            modal.add_item(discord.ui.TextInput(label="ID ou mention du salon", placeholder="#mod-logs"))
            await interaction.response.send_modal(modal)
        elif cid == "mp_purge":
            deleted = await interaction.channel.purge(limit=100)
            await interaction.response.send_message(f"`{len(deleted)}` messages supprimés.", ephemeral=True)
        elif cid == "ai_on":
            settings[gid]["ai_enabled"] = True
            save_settings(settings)
            await interaction.response.send_message("🤖 IA activée.", ephemeral=True)
        elif cid == "ai_off":
            settings[gid]["ai_enabled"] = False
            save_settings(settings)
            await interaction.response.send_message("😴 IA désactivée.", ephemeral=True)

    # --- TICKET CONFIG BUTTONS ---
    elif cid in ("tc_title", "tc_desc", "tc_color", "tc_category", "tc_logs", "tc_limit", "tc_welcome", "tc_close_msg", "tc_channel", "tc_send_panel", "tc_add_type", "tc_remove_type", "tc_reset"):
        gid = str(interaction.guild.id) if interaction.guild else None
        if not gid:
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Permission requise : Administrateur.", ephemeral=True)
            return

        if cid == "tc_channel":
            modal = discord.ui.Modal(title="Salon des tickets", custom_id="tc_channel_modal")
            current_ch = load_settings().get(gid, {}).get("ticket_channel", "")
            modal.add_item(discord.ui.TextInput(label="ID du salon", placeholder="123456789012345678", default=str(current_ch) if current_ch else ""))
            await interaction.response.send_modal(modal)
        elif cid == "tc_send_panel":
            await interaction.response.defer(ephemeral=True)
            settings = load_settings()
            ticket_channel_id = settings.get(gid, {}).get("ticket_channel")
            if not ticket_channel_id:
                await interaction.followup.send("Canal de tickets non configuré.", ephemeral=True)
                return
            channel = interaction.guild.get_channel(int(ticket_channel_id))
            if not channel:
                await interaction.followup.send("Salon introuvable.", ephemeral=True)
                return
            config = get_ticket_config(interaction.guild.id)
            types = get_ticket_types(interaction.guild.id)
            panel_color = config.get("panel_color", None)
            panel_title = config.get("panel_title", f"Support — {interaction.guild.name}")
            panel_desc = config.get("panel_desc", "Ouvrez un ticket en sélectionnant le type de votre demande ci-dessous.")
            panel_view = discord.ui.LayoutView()
            pc = discord.ui.Container(accent_colour=panel_color)
            if interaction.guild.icon:
                section = discord.ui.Section(
                    accessory=discord.ui.Thumbnail(media=interaction.guild.icon.url, description=interaction.guild.name)
                )
                section.add_item(discord.ui.TextDisplay(f"## {panel_title}"))
                pc.add_item(section)
            else:
                pc.add_item(discord.ui.TextDisplay(f"## {panel_title}"))
            pc.add_item(discord.ui.Separator())
            pc.add_item(discord.ui.TextDisplay(panel_desc))
            pc.add_item(discord.ui.Separator())
            for k, v in types.items():
                pc.add_item(discord.ui.TextDisplay(f"**{v.get('emoji', '❓')} {v['label']}** — {v['desc']}"))
            pc.add_item(discord.ui.Separator())
            pc.add_item(discord.ui.TextDisplay("*Sélectionnez un type dans le menu ci-dessous pour ouvrir un ticket.*"))
            row = discord.ui.ActionRow()
            select = discord.ui.Select(
                placeholder="Ouvrir un ticket...",
                options=[
                    discord.SelectOption(label=v["label"], value=k, description=v["desc"], emoji=v.get("emoji", "❓"))
                    for k, v in types.items()
                ],
                custom_id="ticket_setup_select"
            )
            row.add_item(select)
            pc.add_item(row)
            panel_view.add_item(pc)
            await channel.send(view=panel_view)
            await interaction.followup.send(f"Panel envoyé dans {channel.mention}.", ephemeral=True)
        elif cid == "tc_add_type":
            modal = discord.ui.Modal(title="Ajouter un type de ticket", custom_id="tc_add_type_modal")
            modal.add_item(discord.ui.TextInput(label="Clé (ex: bug)", placeholder="bug"))
            modal.add_item(discord.ui.TextInput(label="Nom affiché", placeholder="Bug Report"))
            modal.add_item(discord.ui.TextInput(label="Emoji", placeholder="🐛"))
            modal.add_item(discord.ui.TextInput(label="Description", placeholder="Signaler un bug"))
            await interaction.response.send_modal(modal)
        elif cid == "tc_remove_type":
            types = get_ticket_types(interaction.guild.id)
            if not types:
                await interaction.response.send_message("Aucun type à supprimer.", ephemeral=True)
                return
            modal = discord.ui.Modal(title="Supprimer un type", custom_id="tc_remove_type_modal")
            options_text = ", ".join(f"`{k}`" for k in types.keys())
            modal.add_item(discord.ui.TextInput(label=f"Clé à supprimer ({options_text})", placeholder="bug"))
            await interaction.response.send_modal(modal)
        elif cid == "tc_reset":
            settings = load_settings()
            settings[gid].pop("ticket_config", None)
            settings[gid].pop("ticket_types", None)
            save_settings(settings)
            await interaction.response.send_message("Configuration tickets réinitialisée.", ephemeral=True)
        elif cid == "tc_title":
            modal = discord.ui.Modal(title="Titre du panel", custom_id="tc_title_modal")
            modal.add_item(discord.ui.TextInput(label="Titre", placeholder="Support", default=get_ticket_config(interaction.guild.id).get("panel_title", "Support")))
            await interaction.response.send_modal(modal)
        elif cid == "tc_desc":
            modal = discord.ui.Modal(title="Description du panel", custom_id="tc_desc_modal")
            modal.add_item(discord.ui.TextInput(label="Description", placeholder="Besoin d'aide ?", style=discord.TextStyle.paragraph, default=get_ticket_config(interaction.guild.id).get("panel_desc", "")))
            await interaction.response.send_modal(modal)
        elif cid == "tc_color":
            modal = discord.ui.Modal(title="Couleur hex", custom_id="tc_color_modal")
            current_color = get_ticket_config(interaction.guild.id).get("panel_color")
            hex_str = f"#{current_color:06x}" if current_color else "#b0b8c4"
            modal.add_item(discord.ui.TextInput(label="Couleur (hex)", placeholder="#b0b8c4", default=hex_str))
            await interaction.response.send_modal(modal)
        elif cid == "tc_category":
            modal = discord.ui.Modal(title="Catégorie des tickets", custom_id="tc_category_modal")
            current_cat = get_ticket_config(interaction.guild.id).get("ticket_category", "")
            modal.add_item(discord.ui.TextInput(label="ID de la catégorie", placeholder="123456789012345678", default=str(current_cat) if current_cat else ""))
            await interaction.response.send_modal(modal)
        elif cid == "tc_logs":
            modal = discord.ui.Modal(title="Salon des logs", custom_id="tc_logs_modal")
            current_log = get_ticket_config(interaction.guild.id).get("ticket_log_channel", "")
            modal.add_item(discord.ui.TextInput(label="ID du salon logs", placeholder="123456789012345678", default=str(current_log) if current_log else ""))
            await interaction.response.send_modal(modal)
        elif cid == "tc_limit":
            modal = discord.ui.Modal(title="Limite de tickets", custom_id="tc_limit_modal")
            modal.add_item(discord.ui.TextInput(label="Nombre max (0 = illimité)", placeholder="1", default=str(get_ticket_config(interaction.guild.id).get("ticket_limit", 1))))
            await interaction.response.send_modal(modal)
        elif cid == "tc_welcome":
            modal = discord.ui.Modal(title="Message d'accueil", custom_id="tc_welcome_modal")
            modal.add_item(discord.ui.TextInput(label="Message", placeholder="Décrivez votre demande...", style=discord.TextStyle.paragraph, default=get_ticket_config(interaction.guild.id).get("welcome_msg", "")[:100]))
            await interaction.response.send_modal(modal)
        elif cid == "tc_close_msg":
            modal = discord.ui.Modal(title="Message de fermeture", custom_id="tc_close_msg_modal")
            modal.add_item(discord.ui.TextInput(label="Message", placeholder="Ticket fermé.", style=discord.TextStyle.paragraph, default=get_ticket_config(interaction.guild.id).get("close_msg", "")[:100]))
            await interaction.response.send_modal(modal)

    # --- RAID PANEL BUTTONS ---
    elif cid in ("raid_on", "raid_off", "raid_lockdown", "raid_scan", "raid_massban"):
        gid = str(interaction.guild.id) if interaction.guild else None
        if not gid:
            await interaction.response.send_message("Erreur.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Permission requise : Administrateur.", ephemeral=True)
            return

        if cid == "raid_on":
            save_raid_config(gid, {"anti_raid": True})
            await interaction.response.send_message("Anti-raid activé.", ephemeral=True)

        elif cid == "raid_off":
            save_raid_config(gid, {"anti_raid": False})
            await interaction.response.send_message("Anti-raid desactive.", ephemeral=True)

        elif cid == "raid_lockdown":
            state_data = load_raid_state()
            is_locked = state_data.get(gid, {}).get("locked", False)
            everyone = interaction.guild.default_role
            count = 0
            if not is_locked:
                for channel in interaction.guild.text_channels:
                    try:
                        overwrite = channel.overwrites_for(everyone)
                        overwrite.send_messages = False
                        await channel.set_permissions(everyone, overwrite=overwrite, reason="Lockdown")
                        lockdown_channels[gid].add(channel.id)
                        count += 1
                    except discord.Forbidden:
                        pass
                save_raid_state(state_data | {gid: {"locked": True, "channels": list(lockdown_channels[gid])}})
                await interaction.response.send_message(f"**{count}** salons verrouilles.", ephemeral=True)
            else:
                for channel in interaction.guild.text_channels:
                    try:
                        overwrite = channel.overwrites_for(everyone)
                        overwrite.send_messages = None
                        await channel.set_permissions(everyone, overwrite=overwrite, reason="Unlockdown")
                        lockdown_channels[gid].discard(channel.id)
                        count += 1
                    except discord.Forbidden:
                        pass
                state_data.pop(gid, None)
                save_raid_state(state_data)
                await interaction.response.send_message(f"**{count}** salons deverrouilles.", ephemeral=True)

        elif cid == "raid_scan":
            await interaction.response.defer()
            config = get_raid_config(gid)
            suspects = []
            now = datetime.now(timezone.utc)
            for member in interaction.guild.members:
                if member.bot:
                    continue
                if any(r.id in config.get("whitelist", []) for r in member.roles):
                    continue
                score = 0
                reasons = []
                account_age = now - member.created_at
                if account_age < timedelta(days=config["min_account_age"]):
                    s = min(15, (config["min_account_age"] - account_age.days) * 2)
                    score += s
                    reasons.append(f"Compte age {account_age.days}j")
                if config["check_avatar"] and is_default_avatar(member):
                    score += 5
                    reasons.append("Avatar par defaut")
                if score >= config["score_kick"]:
                    suspects.append((member, score, reasons))
            if not suspects:
                await interaction.followup.send("Aucun membre suspect detecte.")
                return
            lines = [f"**{len(suspects)} membres suspects:**\n"]
            for member, score, reasons in suspects[:25]:
                lines.append(f"- {member.mention} (`{member.id}`) — Score `{score}` — {', '.join(reasons)}")
            if len(suspects) > 25:
                lines.append(f"\n... et {len(suspects) - 25} autres.")
            await interaction.followup.send("\n".join(lines))

        elif cid == "raid_massban":
            await interaction.response.defer()
            flagged = flagged_members.get(gid, [])
            if not flagged:
                await interaction.followup.send("Aucun membre suspect a bannir.")
                return
            count = 0
            for uid in flagged:
                member = interaction.guild.get_member(uid)
                if member:
                    try:
                        await member.ban(reason="Anti-raid massban", delete_message_seconds=86400)
                        count += 1
                    except discord.Forbidden:
                        pass
            flagged_members[gid] = []
            await interaction.followup.send(f"**{count}** membres bannis.")

    # --- MODALS (panels) ---
    elif interaction.type == discord.InteractionType.modal_submit:
        gid = str(interaction.guild.id) if interaction.guild else None
        if not gid:
            return
        settings = load_settings()
        if gid not in settings:
            settings[gid] = {}
        value = interaction.data["components"][0]["components"][0]["value"]

        if cid == "wp_channel_modal":
            ch_id = value.strip("<#>")
            try:
                ch = interaction.guild.get_channel(int(ch_id))
                if ch:
                    settings[gid]["welcome_channel"] = ch.id
                    save_settings(settings)
                    await interaction.response.send_message(f"Salon welcome : {ch.mention}", ephemeral=True)
                    return
            except ValueError:
                pass
            await interaction.response.send_message("Salon introuvable.", ephemeral=True)
        elif cid == "wp_message_modal":
            settings[gid]["welcome_message"] = value
            save_settings(settings)
            await interaction.response.send_message(f"Message : `{value}`", ephemeral=True)
        elif cid == "gp_channel_modal":
            ch_id = value.strip("<#>")
            try:
                ch = interaction.guild.get_channel(int(ch_id))
                if ch:
                    settings[gid]["goodbye_channel"] = ch.id
                    save_settings(settings)
                    await interaction.response.send_message(f"Salon goodbye : {ch.mention}", ephemeral=True)
                    return
            except ValueError:
                pass
            await interaction.response.send_message("Salon introuvable.", ephemeral=True)
        elif cid == "gp_message_modal":
            settings[gid]["goodbye_message"] = value
            save_settings(settings)
            await interaction.response.send_message(f"Message : `{value}`", ephemeral=True)
        elif cid == "bp_channel_modal":
            ch_id = value.strip("<#>")
            try:
                ch = interaction.guild.get_channel(int(ch_id))
                if ch:
                    settings[gid]["boost_channel"] = ch.id
                    save_settings(settings)
                    await interaction.response.send_message(f"Salon boost : {ch.mention}", ephemeral=True)
                    return
            except ValueError:
                pass
            await interaction.response.send_message("Salon introuvable.", ephemeral=True)
        elif cid == "bp_message_modal":
            settings[gid]["boost_message"] = value
            save_settings(settings)
            await interaction.response.send_message(f"Message : `{value}`", ephemeral=True)
        elif cid == "mp_log_modal":
            ch_id = value.strip("<#>")
            try:
                ch = interaction.guild.get_channel(int(ch_id))
                if ch:
                    settings[gid]["mod_log_channel"] = ch.id
                    save_settings(settings)
                    await interaction.response.send_message(f"Salon logs : {ch.mention}", ephemeral=True)
                    return
            except ValueError:
                pass
            await interaction.response.send_message("Salon introuvable.", ephemeral=True)

        # --- TICKET CONFIG MODALS ---
        elif cid == "tc_channel_modal":
            settings = load_settings()
            try:
                ch_id = int(value)
                ch = interaction.guild.get_channel(ch_id)
                if not ch:
                    await interaction.response.send_message("Salon introuvable.", ephemeral=True)
                    return
                settings[gid]["ticket_channel"] = ch_id
                save_settings(settings)
                await interaction.response.send_message(f"Salon tickets mis à jour : {ch.mention}", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("ID invalide.", ephemeral=True)
        elif cid == "tc_add_type_modal":
            components = interaction.data["components"]
            cle = components[0]["components"][0]["value"].strip().lower()
            label = components[1]["components"][0]["value"]
            emoji = components[2]["components"][0]["value"]
            desc = components[3]["components"][0]["value"]
            settings = load_settings()
            custom_types = settings.get(gid, {}).get("ticket_types", {})
            custom_types[cle] = {"label": label, "emoji": emoji, "desc": desc}
            settings[gid]["ticket_types"] = custom_types
            save_settings(settings)
            await interaction.response.send_message(f"Type ajouté : {emoji} **{label}** (`{cle}`)", ephemeral=True)
        elif cid == "tc_remove_type_modal":
            cle = value.strip().lower()
            settings = load_settings()
            custom_types = settings.get(gid, {}).get("ticket_types", {})
            if cle in custom_types:
                name = custom_types[cle]["label"]
                del custom_types[cle]
                settings[gid]["ticket_types"] = custom_types
                save_settings(settings)
                await interaction.response.send_message(f"Type supprimé : **{name}** (`{cle}`)", ephemeral=True)
            else:
                await interaction.response.send_message(f"Type `{cle}` introuvable.", ephemeral=True)
        elif cid == "tc_title_modal":
            config = get_ticket_config(interaction.guild.id)
            config["panel_title"] = value
            save_ticket_config(interaction.guild.id, config)
            await interaction.response.send_message(f"Titre mis à jour : **{value}**", ephemeral=True)
        elif cid == "tc_desc_modal":
            config = get_ticket_config(interaction.guild.id)
            config["panel_desc"] = value
            save_ticket_config(interaction.guild.id, config)
            await interaction.response.send_message(f"Description mise à jour.", ephemeral=True)
        elif cid == "tc_color_modal":
            config = get_ticket_config(interaction.guild.id)
            try:
                color_int = int(value.replace("#", ""), 16)
                config["panel_color"] = color_int
                save_ticket_config(interaction.guild.id, config)
                await interaction.response.send_message(f"Couleur mise à jour : `{value}`", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("Couleur invalide. Format : `#b0b8c4`", ephemeral=True)
        elif cid == "tc_category_modal":
            config = get_ticket_config(interaction.guild.id)
            try:
                cat_id = int(value)
                cat = interaction.guild.get_channel(cat_id)
                if not cat or not isinstance(cat, discord.CategoryChannel):
                    await interaction.response.send_message("Catégorie introuvable.", ephemeral=True)
                    return
                config["ticket_category"] = cat_id
                save_ticket_config(interaction.guild.id, config)
                await interaction.response.send_message(f"Catégorie mise à jour : {cat.mention}", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("ID invalide.", ephemeral=True)
        elif cid == "tc_logs_modal":
            config = get_ticket_config(interaction.guild.id)
            try:
                ch_id = int(value)
                ch = interaction.guild.get_channel(ch_id)
                if not ch:
                    await interaction.response.send_message("Salon introuvable.", ephemeral=True)
                    return
                config["ticket_log_channel"] = ch_id
                save_ticket_config(interaction.guild.id, config)
                await interaction.response.send_message(f"Salon logs mis à jour : {ch.mention}", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("ID invalide.", ephemeral=True)
        elif cid == "tc_limit_modal":
            config = get_ticket_config(interaction.guild.id)
            try:
                limit = int(value)
                config["ticket_limit"] = max(0, limit)
                save_ticket_config(interaction.guild.id, config)
                text = f"`{limit}`" if limit > 0 else "`Illimité`"
                await interaction.response.send_message(f"Limite mise à jour : {text}", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("Nombre invalide.", ephemeral=True)
        elif cid == "tc_welcome_modal":
            config = get_ticket_config(interaction.guild.id)
            config["welcome_msg"] = value
            save_ticket_config(interaction.guild.id, config)
            await interaction.response.send_message("Message d'accueil mis à jour.", ephemeral=True)
        elif cid == "tc_close_msg_modal":
            config = get_ticket_config(interaction.guild.id)
            config["close_msg"] = value
            save_ticket_config(interaction.guild.id, config)
            await interaction.response.send_message("Message de fermeture mis à jour.", ephemeral=True)

        # --- TICKET: ADD MEMBER MODAL ---
        elif cid.startswith("ticket_add_modal_"):
            channel_id = cid.replace("ticket_add_modal_", "")
            if str(interaction.channel.id) != channel_id:
                return
            user_input = value.strip("<@!>")
            try:
                member_id = int(user_input)
                target = interaction.guild.get_member(member_id)
            except ValueError:
                await interaction.response.send_message("ID invalide.", ephemeral=True)
                return
            if not target:
                await interaction.response.send_message("Membre introuvable.", ephemeral=True)
                return
            await interaction.channel.set_permissions(target, view_channel=True, send_messages=True, attach_files=True)
            tickets = load_tickets()
            gid = str(interaction.guild.id)
            cid_ticket = str(interaction.channel.id)
            if gid in tickets and cid_ticket in tickets[gid]:
                extra = tickets[gid][cid_ticket].get("extra_members", [])
                if member_id not in extra:
                    extra.append(member_id)
                    tickets[gid][cid_ticket]["extra_members"] = extra
                    save_tickets(tickets)
            await interaction.response.send_message(f"{target.mention} ajouté au ticket par {interaction.user.mention}.")

        # --- TICKET: REMOVE MEMBER MODAL ---
        elif cid.startswith("ticket_remove_modal_"):
            channel_id = cid.replace("ticket_remove_modal_", "")
            if str(interaction.channel.id) != channel_id:
                return
            user_input = value.strip("<@!>")
            try:
                member_id = int(user_input)
                target = interaction.guild.get_member(member_id)
            except ValueError:
                await interaction.response.send_message("ID invalide.", ephemeral=True)
                return
            if not target:
                await interaction.response.send_message("Membre introuvable.", ephemeral=True)
                return
            if target.id == interaction.user.id:
                await interaction.response.send_message("Vous ne pouvez pas vous retirer vous-même.", ephemeral=True)
                return
            await interaction.channel.set_permissions(target, overwrite=None)
            tickets = load_tickets()
            gid = str(interaction.guild.id)
            cid_ticket = str(interaction.channel.id)
            if gid in tickets and cid_ticket in tickets[gid]:
                extra = tickets[gid][cid_ticket].get("extra_members", [])
                if member_id in extra:
                    extra.remove(member_id)
                    tickets[gid][cid_ticket]["extra_members"] = extra
                    save_tickets(tickets)
            await interaction.response.send_message(f"{target.mention} retiré du ticket par {interaction.user.mention}.")


# ──────────────────────────────────────────────
#  GHOSTPING & AUTOROLE
# ──────────────────────────────────────────────


@ghostping.command(name="send", description="Ghostping tous les membres d'un salon un par un")
@app_commands.describe(channel="Le salon cible")
@app_commands.checks.has_permissions(administrator=True)
async def ghostping_send(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"Ghostping dans {channel.mention}...", ephemeral=True)

    count = 0
    for member in channel.members:
        if member.bot:
            continue
        try:
            msg = await channel.send(member.mention)
            await msg.delete()
            count += 1
        except (discord.Forbidden, discord.NotFound):
            pass

    await interaction.followup.send(f"`{count}` ghostpings envoyés dans {channel.mention}.", ephemeral=True)


@welcome.command(name="ghostping", description="Gère les salons de welcome ghostping (add/list/remove/clear)")
@app_commands.describe(
    action="Action à effectuer",
    channels="Les salons (add/remove uniquement)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="add", value="add"),
    app_commands.Choice(name="list", value="list"),
    app_commands.Choice(name="remove", value="remove"),
    app_commands.Choice(name="clear", value="clear"),
])
@app_commands.checks.has_permissions(administrator=True)
async def welcome_ghostping(interaction: discord.Interaction, action: str, channels: str = None):
    settings = load_settings()
    gid = str(interaction.guild.id)

    if gid not in settings:
        settings[gid] = {}

    if action == "add":
        if not channels:
            await interaction.response.send_message("Spécifiez au moins un salon.", ephemeral=True)
            return
        ids = []
        for c in channels.split():
            c = c.strip("<#>")
            try:
                ch = interaction.guild.get_channel(int(c))
                if ch:
                    ids.append(str(ch.id))
            except ValueError:
                pass
        existing = settings[gid].get("welcome_ghostpings", [])
        existing.extend(ids)
        settings[gid]["welcome_ghostpings"] = list(set(existing))
        save_settings(settings)
        mentions = ", ".join(f"<#{cid}>" for cid in settings[gid]["welcome_ghostpings"])
        await interaction.response.send_message(f"Welcome ghostping : {mentions}", ephemeral=True)

    elif action == "list":
        channel_ids = settings.get(gid, {}).get("welcome_ghostpings", [])
        if not channel_ids:
            await interaction.response.send_message("Aucun salon configuré.", ephemeral=True)
            return
        lines = [f"<#{cid}>" for cid in channel_ids]
        view = view_text("## Welcome Ghostping", "Salons configurés :", *lines)
        await interaction.response.send_message(view=view, ephemeral=True)

    elif action == "remove":
        if not channels:
            await interaction.response.send_message("Spécifiez le salon à retirer.", ephemeral=True)
            return
        if gid in settings and "welcome_ghostpings" in settings[gid]:
            c = channels.strip("<#>")
            try:
                cid = str(int(c))
                if cid in settings[gid]["welcome_ghostpings"]:
                    settings[gid]["welcome_ghostpings"].remove(cid)
                    save_settings(settings)
                    await interaction.response.send_message(f"<#{cid}> retiré.", ephemeral=True)
                    return
            except ValueError:
                pass
        await interaction.response.send_message("Channel non trouvé dans la liste.", ephemeral=True)

    elif action == "clear":
        settings[gid]["welcome_ghostpings"] = []
        save_settings(settings)
        await interaction.response.send_message("Welcome ghostping vidé.", ephemeral=True)


@config.command(name="autorole", description="Définit un rôle automatique à l'arrivée des membres")
@app_commands.describe(role="Le rôle à attribuer (laisser vide pour désactiver)")
@app_commands.checks.has_permissions(administrator=True)
async def autorole(interaction: discord.Interaction, role: discord.Role = None):
    settings = load_settings()
    gid = str(interaction.guild.id)

    if gid not in settings:
        settings[gid] = {}

    if role:
        settings[gid]["autorole"] = role.id
        save_settings(settings)
        await interaction.response.send_message(f"Autorole défini sur {role.mention}.", ephemeral=True)
    else:
        settings[gid].pop("autorole", None)
        save_settings(settings)
        await interaction.response.send_message("Autorole désactivé.", ephemeral=True)


# ──────────────────────────────────────────────
#  MODERATION
# ──────────────────────────────────────────────

@mod.command(name="warn", description="Avertir un membre")
@app_commands.describe(member="Le membre à warn", reason="Raison du warn")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
    if member.bot:
        await interaction.response.send_message("Impossible de warn un bot.", ephemeral=True)
        return

    warns = load_warns()
    gid = str(interaction.guild.id)
    mid = str(member.id)

    if gid not in warns:
        warns[gid] = {}
    if mid not in warns[gid]:
        warns[gid][mid] = []

    warns[gid][mid].append({
        "reason": reason,
        "by": interaction.user.id,
        "at": datetime.now(timezone.utc).isoformat()
    })
    save_warns(warns)

    count = len(warns[gid][mid])
    view = view_text(
        f"## Warn — {member.display_name}",
        f"**Membre** {member.mention}",
        f"**Raison** {reason}",
        f"**Par** {interaction.user.mention}",
        f"**Total warns** `{count}`"
    )
    await interaction.response.send_message(view=view)

    try:
        await member.send(f"Vous avez été warné sur **{interaction.guild.name}** pour : {reason}")
    except discord.Forbidden:
        pass


@mod.command(name="warnings", description="Affiche les warns d'un membre")
@app_commands.describe(member="Le membre à inspecter")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    warns = load_warns()
    gid = str(interaction.guild.id)
    mid = str(member.id)

    user_warns = warns.get(gid, {}).get(mid, [])

    if not user_warns:
        await interaction.response.send_message(f"{member.mention} n'a aucun warn.", ephemeral=True)
        return

    lines = []
    for i, w in enumerate(user_warns, 1):
        by = interaction.guild.get_member(w["by"])
        by_name = by.display_name if by else "Inconnu"
        lines.append(f"**{i}.** {w['reason']} — par `{by_name}` le {w['at'][:10]}")

    view = view_text(
        f"## Warns — {member.display_name}",
        f"**Total** `{len(user_warns)}`",
        "",
        *lines
    )
    await interaction.response.send_message(view=view)


@mod.command(name="clearwarns", description="Supprime les warns d'un membre")
@app_commands.describe(member="Le membre")
@app_commands.checks.has_permissions(administrator=True)
async def clearwarns(interaction: discord.Interaction, member: discord.Member):
    warns = load_warns()
    gid = str(interaction.guild.id)
    mid = str(member.id)

    if gid in warns and mid in warns[gid]:
        count = len(warns[gid][mid])
        del warns[gid][mid]
        save_warns(warns)
        await interaction.response.send_message(f"`{count}` warns supprimés pour {member.mention}.")
    else:
        await interaction.response.send_message("Aucun warn à supprimer.", ephemeral=True)


@mod.command(name="mute", description="Mute un membre (timeout)")
@app_commands.describe(member="Le membre", duration="Durée en minutes", reason="Raison")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: int = 10, reason: str = "Aucune raison"):
    if member.bot:
        await interaction.response.send_message("Impossible de mute un bot.", ephemeral=True)
        return

    until = datetime.now(timezone.utc) + timedelta(minutes=duration)
    await member.timeout(until, reason=reason)

    view = view_text(
        f"## Mute — {member.display_name}",
        f"**Durée** `{duration}` minutes",
        f"**Raison** {reason}",
        f"**Par** {interaction.user.mention}",
        f"**Jusqu'au** <t:{int(until.timestamp())}:R>"
    )
    await interaction.response.send_message(view=view)


@mod.command(name="unmute", description="Démute un membre")
@app_commands.describe(member="Le membre")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"{member.mention} a été démuté.")


@mod.command(name="kick", description="Expulser un membre du serveur")
@app_commands.describe(member="Le membre", reason="Raison")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
    if member.bot:
        await interaction.response.send_message("Impossible de kick un bot.", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Rôle insuffisant.", ephemeral=True)
        return

    try:
        await member.send(f"Vous avez été expulsé de **{interaction.guild.name}** pour : {reason}")
    except discord.Forbidden:
        pass

    await member.kick(reason=reason)
    view = view_text(
        f"## Kick — {member.display_name}",
        f"**Membre** `{member}`",
        f"**Raison** {reason}",
        f"**Par** {interaction.user.mention}"
    )
    await interaction.response.send_message(view=view)


@mod.command(name="ban", description="Bannir un membre du serveur")
@app_commands.describe(member="Le membre", reason="Raison", delete_days="Jours de messages à supprimer (0-7)")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison", delete_days: int = 0):
    if member.bot:
        await interaction.response.send_message("Impossible de ban un bot.", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Rôle insuffisant.", ephemeral=True)
        return

    try:
        await member.send(f"Vous avez été banni de **{interaction.guild.name}** pour : {reason}")
    except discord.Forbidden:
        pass

    await member.ban(reason=reason, delete_message_days=min(delete_days, 7))
    view = view_text(
        f"## Ban — {member.display_name}",
        f"**Membre** `{member}` (`{member.id}`)",
        f"**Raison** {reason}",
        f"**Messages supprimés** `{min(delete_days, 7)}` jours",
        f"**Par** {interaction.user.mention}"
    )
    await interaction.response.send_message(view=view)


@mod.command(name="unban", description="Débannir un utilisateur")
@app_commands.describe(user_id="ID de l'utilisateur à débannir")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        uid = int(user_id)
    except ValueError:
        await interaction.response.send_message("ID invalide.", ephemeral=True)
        return

    try:
        user = await bot.fetch_user(uid)
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"`{user}` a été débanni.")
    except discord.NotFound:
        await interaction.response.send_message("Utilisateur non banni.", ephemeral=True)


@mod.command(name="timeout", description="Timeout un membre (format : 1h30m)")
@app_commands.describe(member="Le membre", duration="Durée (ex: 1h30m, 30m, 2d)", reason="Raison")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "Aucune raison"):
    total = 0
    current = ""
    for c in duration:
        if c.isdigit():
            current += c
        elif c == "d" and current:
            total += int(current) * 86400
            current = ""
        elif c == "h" and current:
            total += int(current) * 3600
            current = ""
        elif c == "m" and current:
            total += int(current) * 60
            current = ""
        elif c == "s" and current:
            total += int(current)
            current = ""

    if total <= 0:
        await interaction.response.send_message("Durée invalide.", ephemeral=True)
        return

    until = datetime.now(timezone.utc) + timedelta(seconds=total)
    await member.timeout(until, reason=reason)

    view = view_text(
        f"## Timeout — {member.display_name}",
        f"**Durée** `{duration}`",
        f"**Raison** {reason}",
        f"**Jusqu'au** <t:{int(until.timestamp())}:R>"
    )
    await interaction.response.send_message(view=view)


@mod.command(name="purge", description="Supprimer des messages dans le salon")
@app_commands.describe(amount="Nombre de messages à supprimer (max 100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int = 10):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Entre 1 et 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.followup.send(f"`{len(deleted) - 1}` messages supprimés.", ephemeral=True)


@mod.command(name="role", description="Ajoute ou retire un rôle à un membre")
@app_commands.describe(member="Le membre", role="Le rôle à gérer")
@app_commands.checks.has_permissions(manage_roles=True)
async def role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"Rôle `{role.name}` retiré à {member.mention}.")
    else:
        await member.add_roles(role)
        await interaction.response.send_message(f"Rôle `{role.name}` ajouté à {member.mention}.")


# ──────────────────────────────────────────────
#  UTILITAIRES
# ──────────────────────────────────────────────

@util.command(name="ping", description="Affiche la latence du bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    view = view_text(f"## Ping", f"**Latence** `{latency}ms`")
    await interaction.response.send_message(view=view)


@util.command(name="avatar", description="Affiche l'avatar d'un membre")
@app_commands.describe(member="Le membre")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    view = view_text(
        f"## Avatar — {member.display_name}",
        f"[Lien direct]({member.display_avatar.url})"
    )
    await interaction.response.send_message(view=view)


@util.command(name="banner", description="Affiche la bannière d'un membre")
@app_commands.describe(member="Le membre")
async def banner(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    user = await bot.fetch_user(member.id)
    if user.banner:
        view = view_text(
            f"## Bannière — {member.display_name}",
            f"[Lien direct]({user.banner.url})"
        )
    else:
        view = view_text(f"## Bannière — {member.display_name}", "Aucune bannière définie.")
    await interaction.response.send_message(view=view)


@util.command(name="serverinfo", description="Affiche les informations du serveur")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild

    total = guild.member_count
    humans = sum(1 for m in guild.members if not m.bot)
    bots_count = sum(1 for m in guild.members if m.bot)
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    roles_count = len(guild.roles) - 1
    emojis = len(guild.emojis)

    view = view_text(
        f"## {guild.name}",
        f"**ID** `{guild.id}`",
        f"**Créé le** <t:{int(guild.created_at.timestamp())}:d>",
        f"**Propriétaire** <@{guild.owner_id}>",
        "",
        f"**Membres** `{total}` — **Humains** `{humans}` — **Bots** `{bots_count}`",
        f"**Texte** `{text_channels}` — **Vocal** `{voice_channels}`",
        f"**Rôles** `{roles_count}` — **Emojis** `{emojis}`",
        f"**Boosts** `{guild.premium_subscription_count}` (niveau {guild.premium_tier})"
    )
    await interaction.response.send_message(view=view)


@util.command(name="userinfo", description="Affiche les informations détaillées d'un membre")
@app_commands.describe(member="Le membre")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user

    roles = [r.mention for r in member.roles[1:]][::-1]
    roles_text = ", ".join(roles[:15])
    if len(roles) > 15:
        roles_text += f" +{len(roles) - 15}"

    perms = [p[0].replace("_", " ").title() for p in member.guild_permissions if p[1]]
    perms_text = ", ".join(perms[:10])
    if len(perms) > 10:
        perms_text += f" +{len(perms) - 10}"

    status_map = {
        discord.Status.online: "En ligne",
        discord.Status.idle: "Inactif",
        discord.Status.dnd: "Ne pas déranger",
        discord.Status.offline: "Hors ligne"
    }

    view = view_text(
        f"## {member.display_name}",
        f"**Compte** {member.mention}",
        f"**ID** `{member.id}`",
        f"**Statut** {status_map.get(member.status, 'Inconnu')}",
        f"**Créé le** <t:{int(member.created_at.timestamp())}:d> (<t:{int(member.created_at.timestamp())}:R>)",
        f"**A rejoint le** <t:{int(member.joined_at.timestamp())}:d> (<t:{int(member.joined_at.timestamp())}:R>)",
        "",
        f"**Rôles [{len(roles)}]** {roles_text or '`Aucun`'}",
        f"**Permissions [{len(perms)}]** {perms_text or '`Aucune`'}"
    )
    await interaction.response.send_message(view=view)


@util.command(name="members", description="Affiche la répartition des membres")
async def members(interaction: discord.Interaction):
    guild = interaction.guild

    total = guild.member_count
    humans = sum(1 for m in guild.members if not m.bot)
    bots_count = sum(1 for m in guild.members if m.bot)
    online = sum(1 for m in guild.members if m.status == discord.Status.online)
    idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
    dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
    offline = sum(1 for m in guild.members if m.status == discord.Status.offline)

    view = view_text(
        f"## Membres — {guild.name}",
        f"**Total** `{total}`",
        "",
        f"**Humains** `{humans}` — **Bots** `{bots_count}`",
        "",
        f"**En ligne** `{online}`",
        f"**Inactifs** `{idle}`",
        f"**Ne pas déranger** `{dnd}`",
        f"**Hors ligne** `{offline}`"
    )
    await interaction.response.send_message(view=view)


@util.command(name="channels", description="Liste les salons du serveur")
async def channels(interaction: discord.Interaction):
    guild = interaction.guild
    text = [c.mention for c in guild.text_channels]
    voice = [c.name for c in guild.voice_channels]
    cats = [c.name for c in guild.categories]

    text_str = ", ".join(text[:50]) or "`Aucun`"
    voice_str = ", ".join(voice[:50]) or "`Aucun`"

    if len(text_str) > 3900:
        text_str = text_str[:3900] + "..."
    if len(voice_str) > 3900:
        voice_str = voice_str[:3900] + "..."

    view = view_text(
        f"## Salons — {guild.name}",
        f"**Texte** `{len(text)}` — **Vocal** `{len(voice)}` — **Catégories** `{len(cats)}`",
        "",
        "**Texte :**",
        text_str,
        "",
        "**Vocal :**",
        voice_str
    )
    await interaction.response.send_message(view=view)


@util.command(name="roles", description="Affiche la liste des rôles du serveur")
async def roles(interaction: discord.Interaction):
    guild = interaction.guild
    sorted_roles = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)

    all_lines = []
    for i, role in enumerate(sorted_roles, 1):
        member_count = len(role.members)
        all_lines.append(f"**{i}.** {role.mention} — `{member_count}` membres")

    pages = [all_lines[i:i + ROLES_PER_PAGE] for i in range(0, len(all_lines), ROLES_PER_PAGE)]
    if not pages:
        pages = [[]]

    await interaction.response.send_message(
        view=make_page_view(guild, pages[0], "Rôles", 1, len(pages))
    )
    for idx, page in enumerate(pages[1:], 2):
        await interaction.followup.send(
            view=make_page_view(guild, page, "Rôles", idx, len(pages))
        )


@util.command(name="emojis", description="Affiche les emojis du serveur")
async def emojis(interaction: discord.Interaction):
    guild = interaction.guild
    emojis = guild.emojis

    if not emojis:
        await interaction.response.send_message("Aucun emoji sur ce serveur.", ephemeral=True)
        return

    lines = [f"{e} `{e.name}`" for e in emojis[:50]]
    emoji_str = " ".join(lines)
    if len(emoji_str) > 3900:
        emoji_str = emoji_str[:3900] + "..."

    view = view_text(
        f"## Emojis — {guild.name}",
        f"**Total** `{len(emojis)}`",
        "",
        emoji_str
    )
    await interaction.response.send_message(view=view)


@util.command(name="boosts", description="Affiche les boosters du serveur")
async def boosts(interaction: discord.Interaction):
    guild = interaction.guild
    boosters = [m for m in guild.members if m.premium_since]

    if not boosters:
        await interaction.response.send_message("Aucun booster actuel.", ephemeral=True)
        return

    lines = [f"{b.mention} — depuis <t:{int(b.premium_since.timestamp())}:R>" for b in boosters[:20]]
    view = view_text(
        f"## Boosters — {guild.name}",
        f"**Total** `{len(boosters)}` — **Boosts** `{guild.premium_subscription_count}` — **Niveau** `{guild.premium_tier}`",
        "",
        *lines
    )
    await interaction.response.send_message(view=view)


@util.command(name="say", description="Le bot envoie un message")
@app_commands.describe(message="Le message à envoyer", channel="Le salon cible")
@app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await interaction.response.send_message("Message envoyé.", ephemeral=True)
    await channel.send(message)


@util.command(name="embed", description="Crée un embed personnalisé")
@app_commands.describe(title="Titre", description="Description", channel="Salon cible")
@app_commands.checks.has_permissions(administrator=True)
async def embed(interaction: discord.Interaction, title: str, description: str, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    view = view_text(f"## {title}", description)
    await interaction.response.send_message("Embed envoyé.", ephemeral=True)
    await channel.send(view=view)


@util.command(name="poll", description="Crée un sondage")
@app_commands.describe(question="La question", option1="Option 1", option2="Option 2", option3="Option 3 (optionnel)", option4="Option 4 (optionnel)")
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    options = [option1, option2]
    if option3:
        options.append(option3)
    if option4:
        options.append(option4)

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    desc = "\n\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))

    view = view_text(f"## {question}", desc)
    msg = await interaction.response.send_message(view=view)
    message = await interaction.original_response()

    for i in range(len(options)):
        await message.add_reaction(emojis[i])


HELP_CATEGORIES = {
    "mod": {
        "label": "Modération",
        "emoji": "<:7964modbadgewhite:1544381242705846302>",
        "commands": [
            "`/mod warn` — Avertir un membre",
            "`/mod warnings` — Affiche les warns",
            "`/mod clearwarns` — Supprime les warns",
            "`/mod mute` — Mute (timeout)",
            "`/mod unmute` — Démute",
            "`/mod timeout` — Timeout (1h30m)",
            "`/mod kick` — Expulser",
            "`/mod ban` — Bannir",
            "`/mod unban` — Débannir",
            "`/mod softban` — Ban + unban (purge)",
            "`/mod jail` — Prison (toggle)",
            "`/mod history` — Historique modération",
            "`/mod case` — Voir un case",
            "`/mod purge` — Supprimer des messages",
            "`/mod role` — Ajouter/retirer un rôle",
            "`/mod mod-log` — Configurer les logs",
        ]
    },
    "config": {
        "label": "Configuration",
        "emoji": "<:56644tools:1544381257264140328>",
        "commands": [
            "`/config staff-roles` — Roles staff",
            "`/config ticket-channel` — Canal de tickets",
            "`/config automod` — Anti-link / Anti-spam",
            "`/config autorole` — Role automatique",
            "`/config mod-panel` — Panel moderation",
            "`/config reglement` — Configurer le reglement",
            "`/config reglement-post` — Poster le panel reglement",
        ]
    },
    "welcome": {
        "label": "Welcome & Goodbye",
        "emoji": "<:1882megaphone:1544381218932654143>",
        "commands": [
            "`/welcome setup` — Configurer l'accueil",
            "`/welcome disable` — Désactiver l'accueil",
            "`/welcome preview` — Aperçu accueil",
            "`/welcome ghostping` — Ghostpings d'accueil",
            "`/welcome goodbye` — Configurer le départ",
            "`/welcome boost` — Configurer les boosts",
            "`/welcome panel` — Panel interactif",
            "`/welcome goodbye-panel` — Panel goodbye",
            "`/welcome boost-panel` — Panel boost",
        ]
    },
    "ticket": {
        "label": "Tickets",
        "emoji": "<:9891chaticon:1544381248246513694>",
        "commands": [
            "`/ticket setup` — Setup complet",
            "`/ticket panel` — Envoyer le panel",
            "`/ticket config` — Configurer le panel",
            "`/ticket types` — Gérer les types",
            "`/ticket add` — Ajouter un membre",
            "`/ticket remove` — Retirer un membre",
            "`/ticket list` — Liste des tickets",
            "`/ticket transcript` — Générer un transcript",
            "`/ticket force-close` — Fermer forcé",
            "`/ticket close` — Fermer le ticket",
        ]
    },
    "music": {
        "label": "Musique",
        "emoji": "<:9183shoppingcart:1544381246854008922>",
        "commands": [
            "`/music play` — Jouer une musique",
            "`/music pause` — Pause",
            "`/music resume` — Reprendre",
            "`/music skip` — Passer",
            "`/music stop` — Arrêter",
            "`/music queue` — File d'attente",
            "`/music nowplaying` — En cours",
            "`/music volume` — Volume (0-100)",
            "`/music disconnect` — Déconnecter",
        ]
    },
    "util": {
        "label": "Utilitaires",
        "emoji": "<:10447information:1544381249550942429>",
        "commands": [
            "`/util ping` — Latence",
            "`/util uptime` — Temps de fonctionnement",
            "`/util bot-info` — Infos bot",
            "`/util avatar` — Avatar d'un membre",
            "`/util banner` — Bannière",
            "`/util serverinfo` — Infos serveur",
            "`/util userinfo` — Infos membre",
            "`/util members` — Répartition membres",
            "`/util channels` — Liste salons",
            "`/util roles` — Liste rôles",
            "`/util emojis` — Liste emojis",
            "`/util boosts` — Liste boosters",
            "`/util say` — Bot envoie un message",
            "`/util embed` — Embed personnalisé",
            "`/util poll` — Sondage",
            "`/util effectif` — Effectif complet",
            "`/util hierarchie` — Hiérarchie rôles",
            "`/util staff` — Hiérarchie staff",
            "`/util afk` — Mode AFK",
            "`/util remind` — Rappel automatique",
        ]
    },
    "fun": {
        "label": "Fun",
        "emoji": "<:75645star:1544381263517843556>",
        "commands": [
            "`/fun coinflip` — Pile ou face",
            "`/fun dice` — Lancer de dé",
            "`/fun 8ball` — Boule magique",
            "`/fun ship` — Compatibilité",
            "`/fun rate` — Noter sur 10",
        ]
    },
    "backup": {
        "label": "Backup",
        "emoji": "<:2577whitenitroboost:1544381220220182589>",
        "commands": [
            "`/backup create` — Créer une backup",
            "`/backup list` — Liste les backups",
            "`/backup restore` — Restaurer",
            "`/backup delete` — Supprimer",
        ]
    },
    "stats": {
        "label": "Statistiques",
        "emoji": "<:10845currency:1544381252105277521>",
        "commands": [
            "`/stats user` — Stats d'un membre",
            "`/stats server` — Stats du serveur",
        ]
    },
    "raid": {
        "label": "Anti-raid",
        "emoji": "<:84795adminicon:1544381268295417917>",
        "commands": [
            "`/raid config` — Configurer l'anti-raid intelligent",
            "`/raid log` — Salon de logs",
            "`/raid status` — Voir la config",
            "`/raid whitelist` — Gerer la whitelist",
            "`/raid blacklist` — Gerer la blacklist",
            "`/raid lockdown` — Verrouiller/deverrouiller",
            "`/raid massban` — Bannir les suspects",
            "`/raid scan` — Scanner les membres",
            "`/raid panel` — Panel interactif",
        ]
    },
    "ghostping": {
        "label": "Ghostping",
        "emoji": "<:1569whitepin:1544381217657323560>",
        "commands": [
            "`/ghostping send` — Ghostping un salon",
        ]
    },
    "ai": {
        "label": "IA Insolente",
        "emoji": "<:56832developer:1544381258543534150>",
        "commands": [
            "`/ai panel` — Panel de configuration",
        ]
    },
}


EMOJI_FALLBACKS = {
    "mod": "🔨",
    "config": "🔧",
    "welcome": "📢",
    "ticket": "💬",
    "util": "🔧",
    "fun": "⭐",
    "stats": "📊",
    "raid": "🤖",
    "ghostping": "👻",
    "music": "🎵",
    "backup": "💾",
    "ai": "🤖",
}

def make_help_view(category_key):
    cat = HELP_CATEGORIES[category_key]
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=None)

    container.add_item(discord.ui.TextDisplay(f"## {cat['emoji']} {cat['label']}"))
    container.add_item(discord.ui.Separator())

    lines = "\n".join(cat["commands"])
    container.add_item(discord.ui.TextDisplay(lines))

    container.add_item(discord.ui.Separator())

    options = []
    for key, val in HELP_CATEGORIES.items():
        fallback = EMOJI_FALLBACKS.get(key, "❓")
        options.append(discord.SelectOption(
            label=val["label"],
            value=key,
            description=f"{len(val['commands'])} commandes",
            emoji=fallback
        ))

    row = discord.ui.ActionRow()
    select = discord.ui.Select(
        placeholder="Choisir une catégorie...",
        options=options,
        custom_id="help_category_select",
        row=0
    )
    row.add_item(select)
    container.add_item(row)

    view.add_item(container)
    return view


HELP_PERSISTENT_CATEGORY = "mod"


@bot.tree.command(name="help", description="Affiche la liste des commandes par categorie")
@app_commands.describe(category="Categorie de commandes")
@app_commands.choices(category=[
    app_commands.Choice(name=f"{EMOJI_FALLBACKS.get(k, '❓')} {v['label']}", value=k)
    for k, v in HELP_CATEGORIES.items()
])
async def help_cmd(interaction: discord.Interaction, category: str = "mod"):
    if category not in HELP_CATEGORIES:
        category = "mod"
    view = make_help_view(category)
    await interaction.response.send_message(view=view)


# ──────────────────────────────────────────────
#  HIERARCHIE
# ──────────────────────────────────────────────

@util.command(name="effectif", description="Affiche l'effectif complet du serveur par rôle")
@app_commands.checks.has_permissions(administrator=True)
async def effectif(interaction: discord.Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    sorted_roles = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)

    lines = []
    total_members = 0

    for role in sorted_roles:
        members = sorted(role.members, key=lambda m: m.display_name.lower())
        count = len(members)
        total_members = max(total_members, guild.member_count)

        if count > 0:
            member_lines = "\n".join(f"➜ **@{m.display_name}**" for m in members[:50])
            if count > 50:
                member_lines += f"\n➜ *... et {count - 50} autres*"
        else:
            member_lines = "*Aucun membre*"

        lines.append(f"**{role.mention}** • `{count}` membre{'s' if count != 1 else ''}\n{member_lines}")

    now = datetime.now(timezone.utc).strftime("%H:%M")
    header = f"## 📋 Effectif du Serveur — {guild.name}\n*{guild.member_count} membres total • Mis à jour à {now}*\n"

    chunk_size = 8
    chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]

    first_chunk = header + "\n\n".join(chunks[0]) if chunks else header
    view = view_text(first_chunk)
    await interaction.followup.send(view=view)

    for idx, chunk in enumerate(chunks[1:], 2):
        content = "\n\n".join(chunk)
        await interaction.followup.send(view=view_text(content))


@util.command(name="hierarchie", description="Affiche la hiérarchie complète des rôles")
async def hierarchie(interaction: discord.Interaction):
    guild = interaction.guild
    sorted_roles = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)

    all_lines = []
    for i, role in enumerate(sorted_roles, 1):
        member_count = len(role.members)
        tag = " 👑" if role.permissions.administrator else ""
        all_lines.append(f"**{i}.** {role.mention} — `{member_count}` membres{tag}")

    pages = [all_lines[i:i + ROLES_PER_PAGE] for i in range(0, len(all_lines), ROLES_PER_PAGE)]
    if not pages:
        pages = [[]]

    await interaction.response.send_message(
        view=make_page_view(guild, pages[0], "Hiérarchie", 1, len(pages))
    )
    for idx, page in enumerate(pages[1:], 2):
        await interaction.followup.send(
            view=make_page_view(guild, page, "Hiérarchie", idx, len(pages))
        )


STAFF_ROLE_MIN = 1542695791821328386
STAFF_ROLE_MAX = 1542695847622352896


@util.command(name="staff", description="Affiche la hiérarchie des rôles staff")
async def staff(interaction: discord.Interaction):
    await interaction.response.defer()
    guild = interaction.guild

    sorted_roles = sorted(guild.roles[1:], key=lambda r: r.position, reverse=True)
    staff_roles = [r for r in sorted_roles if STAFF_ROLE_MIN <= r.id <= STAFF_ROLE_MAX]

    lines = []
    for role in staff_roles:
        members = sorted(role.members, key=lambda m: m.display_name.lower())
        count = len(members)

        if count > 0:
            member_lines = "\n".join(f"➜ **@{m.display_name}**" for m in members[:30])
        else:
            member_lines = "*Aucun membre*"

        lines.append(f"**{role.mention}** • `{count}` membre{'s' if count != 1 else ''}\n{member_lines}")

    now = datetime.now(timezone.utc).strftime("%H:%M")
    header = f"## 📋 Effectif Staff — {guild.name}\n*{len(staff_roles)} rôles staff • Mis à jour à {now}*\n"

    content = header + "\n\n".join(lines) if lines else header + "*Aucun rôle staff trouvé*"
    view = view_text(content)
    await interaction.followup.send(view=view)


@config.command(name="staff-roles", description="Définir les rôles staff (laisser vide = tous les admins)")
@app_commands.describe(roles="Les rôles à considérer comme staff")
@app_commands.checks.has_permissions(administrator=True)
async def set_staff_roles(interaction: discord.Interaction, roles: str = ""):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}
    if roles.strip():
        role_ids = [int(r.strip().replace("<@&", "").replace(">", "")) for r in roles.split(",") if r.strip()]
        settings[gid]["staff_roles"] = role_ids
        save_settings(settings)
        await interaction.response.send_message(f"Rôles staff configurés.", ephemeral=True)
    else:
        settings[gid].pop("staff_roles", None)
        save_settings(settings)
        await interaction.response.send_message("Rôles staff réinitialisés (tous les admins seront affichés).", ephemeral=True)


# ──────────────────────────────────────────────
#  STATS
# ──────────────────────────────────────────────

@stats.command(name="user", description="Affiche les statistiques d'un membre")
@app_commands.describe(member="Le membre à inspecter")
async def stats_user(interaction: discord.Interaction, member: discord.Member):
    roles = [r.mention for r in member.roles[1:]][::-1]
    roles_text = ", ".join(roles[:20])
    if len(roles) > 20:
        roles_text += f" +{len(roles) - 20}"

    section = discord.ui.Section(
        accessory=discord.ui.Thumbnail(media=member.display_avatar.url, description=member.display_name)
    )
    section.add_item(discord.ui.TextDisplay(
        f"**Compte** {member.mention}\n"
        f"**ID** `{member.id}`\n"
        f"**Créé le** <t:{int(member.created_at.timestamp())}:d>\n"
        f"**A rejoint le** <t:{int(member.joined_at.timestamp())}:d>"
    ))

    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=None)
    container.add_item(discord.ui.TextDisplay(f"## {member.display_name}"))
    container.add_item(discord.ui.Separator())
    container.add_item(section)
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"**Rôles [{len(roles)}]** {roles_text or '`Aucun`'}"))
    view.add_item(container)
    await interaction.response.send_message(view=view)


@stats.command(name="server", description="Affiche les statistiques du serveur")
async def statistique(interaction: discord.Interaction):
    guild = interaction.guild

    total = guild.member_count
    humans = sum(1 for m in guild.members if not m.bot)
    bots_count = sum(1 for m in guild.members if m.bot)
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    roles = len(guild.roles) - 1
    emojis = len(guild.emojis)

    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=None)

    if guild.icon:
        section = discord.ui.Section(
            accessory=discord.ui.Thumbnail(media=guild.icon.url, description=guild.name)
        )
        section.add_item(discord.ui.TextDisplay(f"## {guild.name}"))
        container.add_item(section)
    else:
        container.add_item(discord.ui.TextDisplay(f"## {guild.name}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"**Membres** `{total}` — **Humains** `{humans}` — **Bots** `{bots_count}`\n**En ligne** `{online}`"
    ))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"**Texte** `{text_channels}` — **Vocal** `{voice_channels}` — **Catégories** `{categories}`"
    ))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"**Rôles** `{roles}` — **Emojis** `{emojis}`"))
    view.add_item(container)
    await interaction.response.send_message(view=view)


RECRUITMENT_CRITERIA = """## Critères de recrutement — Equipe Staff

### Conditions préalables
- Avoir au moins 16 ans
- Membre du serveur depuis au moins 30 jours
- Aucun antécédent de sanction (ban, mute, warn)
- Activité régulière sur le serveur (minimum 50 messages/semaine)

### Compétences requises
- Maîtrise complète des règles du serveur
- Capacité à gérer les conflits sans partialiser
- Réactivité face aux signalements (temps de réponse max : 15 minutes)
- Connaissance approfondie des outils de modération (AutoMod, logs, permissions)

### Processus de candidature
1. Envoyer une demande au staff avec motif détaillé
2. Entretien oral avec un administrateur (10-15 minutes)
3. Periode d'essai de 14 jours
4. Évaluation finale par le corps administratif

### Règles internes
- Chaîne de commandement stricte : MODO > MODÉRATEUR > HELPER
- Interdiction formelle de contester une décision devant les membres
- Obligation de discrétion sur les actions de modération
- Toute violation entraîne un retrait immédiat du poste

### Causes d'exclusion automatique
- Abandon de poste sans prévenir
- Favoritisme ou partialité démontrée
- Utilisation abusive des permissions
- Comportement irrespectueux envers les membres ou l'équipe

---

Les candidatures sont ouvertes en permanence. Le staff se réserve le droit de refuser toute demande sans justification."""


# ──────────────────────────────────────────────
#  BACKUP SYSTEM
# ──────────────────────────────────────────────

BACKUPS_FILE = "backups.json"


def load_backups():
    if os.path.exists(BACKUPS_FILE):
        try:
            with open(BACKUPS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_backups(data):
    with open(BACKUPS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@backup.command(name="create", description="Créer une backup du serveur (rôles + salons)")
@app_commands.checks.has_permissions(administrator=True)
async def backup_create(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    roles_data = []
    for role in sorted(guild.roles[1:], key=lambda r: r.position):
        roles_data.append({
            "name": role.name,
            "color": role.color.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "permissions": role.permissions.value,
            "position": role.position
        })

    channels_data = []
    for ch in guild.channels:
        ch_data = {
            "name": ch.name,
            "type": str(ch.type),
            "topic": getattr(ch, "topic", None),
            "slowmode": getattr(ch, "slowmode_delay", 0),
            "nsfw": getattr(ch, "nsfw", False),
            "position": ch.position,
            "category_id": ch.category_id,
            "overwrites": {}
        }
        for target, overwrite in ch.overwrites.items():
            ch_data["overwrites"][str(target.id)] = {
                "allow": overwrite.pair()[0].value,
                "deny": overwrite.pair()[1].value,
                "target_type": "role" if isinstance(target, discord.Role) else "member"
            }
        channels_data.append(ch_data)

    emojis_data = []
    for emoji in guild.emojis:
        emojis_data.append({
            "name": emoji.name,
            "url": str(emoji.url)
        })

    backup_id = hashlib.md5(f"{guild.id}{datetime.now(timezone.utc).timestamp()}".encode()).hexdigest()[:8]
    backups = load_backups()
    gid = str(guild.id)
    if gid not in backups:
        backups[gid] = {}
    backups[gid][backup_id] = {
        "name": f"Backup {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "roles": roles_data,
        "channels": channels_data,
        "emojis": emojis_data,
        "guild_name": guild.name,
        "member_count": guild.member_count
    }
    save_backups(backups)

    view = view_text(
        f"## Backup créée — `{backup_id}`",
        f"**Nom** {guild.name}",
        f"**Rôles** `{len(roles_data)}`",
        f"**Salons** `{len(channels_data)}`",
        f"**Emojis** `{len(emojis_data)}`",
        f"**Membres** `{guild.member_count}`",
        "",
        "Utilisez `/backup-list` pour voir toutes les backups."
    )
    await interaction.followup.send(view=view)


@backup.command(name="list", description="Affiche les backups du serveur")
@app_commands.checks.has_permissions(administrator=True)
async def backup_list(interaction: discord.Interaction):
    backups = load_backups()
    gid = str(interaction.guild.id)
    if gid not in backups or not backups[gid]:
        await interaction.response.send_message("Aucune backup pour ce serveur.", ephemeral=True)
        return

    lines = []
    for bid, b in backups[gid].items():
        lines.append(f"**`{bid}`** — {b['name']} — {b.get('member_count', '?')} membres")

    view = view_text(
        f"## Backups — {interaction.guild.name}",
        f"**Total** `{len(backups[gid])}` backups",
        "",
        "\n".join(lines),
        "",
        "Utilisez `/backup-restore <id>` pour restaurer."
    )
    await interaction.response.send_message(view=view)


@backup.command(name="restore", description="Restaurer une backup du serveur")
@app_commands.describe(backup_id="L'ID de la backup à restaurer")
@app_commands.checks.has_permissions(administrator=True)
async def backup_restore(interaction: discord.Interaction, backup_id: str):
    backups = load_backups()
    gid = str(interaction.guild.id)
    if gid not in backups or backup_id not in backups[gid]:
        await interaction.response.send_message("Backup introuvable.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    b = backups[gid][backup_id]

    created_roles = {}
    for role_data in reversed(b["roles"]):
        try:
            role = await guild.create_role(
                name=role_data["name"],
                color=discord.Color(role_data["color"]),
                hoist=role_data["hoist"],
                mentionable=role_data["mentionable"],
                permissions=discord.Permissions(role_data["permissions"]),
                reason=f"Backup {backup_id}"
            )
            created_roles[role_data["name"]] = role
        except discord.Forbidden:
            pass

    category_map = {}
    for ch_data in sorted(b["channels"], key=lambda x: x["position"]):
        ch_type = ch_data["type"]
        overwrites = {}
        for target_id_str, ow_data in ch_data.get("overwrites", {}).items():
            target_id = int(target_id_str)
            if ow_data["target_type"] == "role":
                target = guild.get_role(target_id)
                if target:
                    allow = discord.Permissions(ow_data["allow"])
                    deny = discord.Permissions(ow_data["deny"])
                    overwrites[target] = discord.PermissionOverwrite.from_pair(allow, deny)

        try:
            if ch_type == "category":
                cat = await guild.create_category(name=ch_data["name"], overwrites=overwrites)
                category_map[ch_data["name"]] = cat
            elif ch_type == "text":
                parent = None
                if ch_data.get("category_id"):
                    for orig_cat_name, new_cat in category_map.items():
                        parent = new_cat
                        break
                await guild.create_text_channel(
                    name=ch_data["name"],
                    topic=ch_data.get("topic"),
                    slowmode_delay=ch_data.get("slowmode", 0),
                    nsfw=ch_data.get("nsfw", False),
                    overwrites=overwrites,
                    category=parent,
                    reason=f"Backup {backup_id}"
                )
            elif ch_type == "voice":
                await guild.create_voice_channel(
                    name=ch_data["name"],
                    overwrites=overwrites,
                    reason=f"Backup {backup_id}"
                )
        except discord.Forbidden:
            pass

    view = view_text(
        f"## Backup restaurée — `{backup_id}`",
        f"**Rôles créés** `{len(created_roles)}`",
        f"**Salons créés** `{len(b['channels'])}`",
        "",
        "La restauration est terminée."
    )
    await interaction.followup.send(view=view)


@backup.command(name="delete", description="Supprimer une backup")
@app_commands.describe(backup_id="L'ID de la backup à supprimer")
@app_commands.checks.has_permissions(administrator=True)
async def backup_delete(interaction: discord.Interaction, backup_id: str):
    backups = load_backups()
    gid = str(interaction.guild.id)
    if gid not in backups or backup_id not in backups[gid]:
        await interaction.response.send_message("Backup introuvable.", ephemeral=True)
        return
    name = backups[gid][backup_id]["name"]
    del backups[gid][backup_id]
    save_backups(backups)
    await interaction.response.send_message(f"Backup `{backup_id}` ({name}) supprimée.", ephemeral=True)


# ──────────────────────────────────────────────
#  TICKET SYSTEM V2
# ──────────────────────────────────────────────

DEFAULT_TICKET_TYPES = {
    "bug": {"label": "Bug Report", "emoji": "🐛", "desc": "Signaler un bug ou une erreur"},
    "suggestion": {"label": "Suggestion", "emoji": "💡", "desc": "Proposer une amélioration"},
    "support": {"label": "Support", "emoji": "🎧", "desc": "Besoin d'aide ou de support"},
    "report": {"label": "Report", "emoji": "🚨", "desc": "Signaler un membre ou un problème"},
    "creation": {"label": "Création", "emoji": "🎨", "desc": "Demander une création sur mesure"},
    "autre": {"label": "Autre", "emoji": "📋", "desc": "Autre demande"}
}


def get_ticket_types(guild_id):
    settings = load_settings()
    gid = str(guild_id)
    custom = settings.get(gid, {}).get("ticket_types")
    if custom:
        return custom
    return DEFAULT_TICKET_TYPES.copy()


def get_ticket_config(guild_id):
    settings = load_settings()
    gid = str(guild_id)
    return settings.get(gid, {}).get("ticket_config", {})


def save_ticket_config(guild_id, config):
    settings = load_settings()
    gid = str(guild_id)
    if gid not in settings:
        settings[gid] = {}
    settings[gid]["ticket_config"] = config
    save_settings(settings)


@ticket.command(name="config", description="Panel de configuration des tickets")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_config(interaction: discord.Interaction):
    config = get_ticket_config(interaction.guild.id)
    settings = load_settings()
    gid = str(interaction.guild.id)

    cat_text = f"<#{config['ticket_category']}>" if config.get("ticket_category") else "`Non définie`"
    log_text = f"<#{config['ticket_log_channel']}>" if config.get("ticket_log_channel") else "`Non défini`"
    ch_text = f"<#{settings.get(gid, {}).get('ticket_channel', 0)}>" if settings.get(gid, {}).get("ticket_channel") else "`Non défini`"

    types = get_ticket_types(interaction.guild.id)
    types_list = "\n".join(f"**{v.get('emoji', '❓')} {v['label']}** — `{k}`" for k, v in types.items()) or "`Aucun`"

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## Configuration Tickets"))
    container.add_item(discord.ui.Separator())

    current = (
        f"**Salon tickets** {ch_text}\n"
        f"**Catégorie** {cat_text}\n"
        f"**Salon logs** {log_text}\n"
        f"**Titre panel** `{config.get('panel_title', 'Support')}`\n"
        f"**Description** `{config.get('panel_desc', 'Non défini')[:50]}`\n"
        f"**Couleur** `{config.get('panel_color', 'Défaut')}`\n"
        f"**Limite** `{config.get('ticket_limit', 1)}`\n"
        f"**Msg accueil** `{config.get('welcome_msg', 'Non défini')[:50]}`\n"
        f"**Msg fermeture** `{config.get('close_msg', 'Non défini')[:50]}`"
    )
    container.add_item(discord.ui.TextDisplay(current))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay("## Types de tickets"))
    container.add_item(discord.ui.TextDisplay(types_list))
    container.add_item(discord.ui.Separator())

    row1 = discord.ui.ActionRow()
    row1.add_item(discord.ui.Button(label="Salon tickets", style=discord.ButtonStyle.primary, custom_id="tc_channel"))
    row1.add_item(discord.ui.Button(label="Catégorie", style=discord.ButtonStyle.primary, custom_id="tc_category"))
    row1.add_item(discord.ui.Button(label="Salon logs", style=discord.ButtonStyle.primary, custom_id="tc_logs"))
    container.add_item(row1)

    row2 = discord.ui.ActionRow()
    row2.add_item(discord.ui.Button(label="Titre", style=discord.ButtonStyle.secondary, custom_id="tc_title"))
    row2.add_item(discord.ui.Button(label="Description", style=discord.ButtonStyle.secondary, custom_id="tc_desc"))
    row2.add_item(discord.ui.Button(label="Couleur", style=discord.ButtonStyle.secondary, custom_id="tc_color"))
    container.add_item(row2)

    row3 = discord.ui.ActionRow()
    row3.add_item(discord.ui.Button(label="Msg accueil", style=discord.ButtonStyle.secondary, custom_id="tc_welcome"))
    row3.add_item(discord.ui.Button(label="Msg fermeture", style=discord.ButtonStyle.secondary, custom_id="tc_close_msg"))
    row3.add_item(discord.ui.Button(label="Limite", style=discord.ButtonStyle.secondary, custom_id="tc_limit"))
    container.add_item(row3)

    container.add_item(discord.ui.Separator())

    row4 = discord.ui.ActionRow()
    row4.add_item(discord.ui.Button(label="Envoyer le panel", style=discord.ButtonStyle.success, custom_id="tc_send_panel", emoji="📤"))
    row4.add_item(discord.ui.Button(label="Ajouter un type", style=discord.ButtonStyle.success, custom_id="tc_add_type", emoji="➕"))
    row4.add_item(discord.ui.Button(label="Supprimer un type", style=discord.ButtonStyle.danger, custom_id="tc_remove_type", emoji="➖"))
    container.add_item(row4)

    row5 = discord.ui.ActionRow()
    row5.add_item(discord.ui.Button(label="Reset config", style=discord.ButtonStyle.danger, custom_id="tc_reset"))
    container.add_item(row5)

    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


@ticket.command(name="types", description="Gérer les types de tickets")
@app_commands.describe(
    action="Ajouter, retirer ou lister",
    cle="Clé du type (ex: bug)",
    label="Nom affiché",
    emoji="Emoji du type",
    description="Description du type"
)
@app_commands.choices(action=[
    app_commands.Choice(name="list", value="list"),
    app_commands.Choice(name="add", value="add"),
    app_commands.Choice(name="remove", value="remove"),
    app_commands.Choice(name="reset", value="reset"),
])
@app_commands.checks.has_permissions(administrator=True)
async def ticket_types(
    interaction: discord.Interaction,
    action: str,
    cle: str = None,
    label: str = None,
    emoji: str = None,
    description: str = None
):
    gid = str(interaction.guild.id)
    settings = load_settings()

    if action == "list":
        types = get_ticket_types(interaction.guild.id)
        lines = []
        for k, v in types.items():
            lines.append(f"**`{k}`** — {v.get('emoji', '❓')} {v['label']} — {v['desc']}")
        view = view_text(
            "## Types de tickets",
            "\n".join(lines) or "`Aucun type personnalisé`",
            "",
            "Utilisez `/ticket-types add` pour ajouter."
        )
        await interaction.response.send_message(view=view, ephemeral=True)

    elif action == "add":
        if not cle or not label:
            await interaction.response.send_message("Clé et label requis.", ephemeral=True)
            return
        types = get_ticket_types(interaction.guild.id)
        types[cle] = {
            "label": label,
            "emoji": emoji or "❓",
            "desc": description or "Pas de description"
        }
        if gid not in settings:
            settings[gid] = {}
        settings[gid]["ticket_types"] = types
        save_settings(settings)
        await interaction.response.send_message(f"Type `{cle}` ajouté : {emoji or '❓'} {label}", ephemeral=True)

    elif action == "remove":
        if not cle:
            await interaction.response.send_message("Clé requise.", ephemeral=True)
            return
        types = get_ticket_types(interaction.guild.id)
        if cle in types:
            del types[cle]
            if gid not in settings:
                settings[gid] = {}
            settings[gid]["ticket_types"] = types
            save_settings(settings)
            await interaction.response.send_message(f"Type `{cle}` supprimé.", ephemeral=True)
        else:
            await interaction.response.send_message("Type introuvable.", ephemeral=True)

    elif action == "reset":
        if gid in settings:
            settings[gid].pop("ticket_types", None)
            save_settings(settings)
        await interaction.response.send_message("Types de tickets réinitialisés aux défauts.", ephemeral=True)


@ticket.command(name="panel", description="Envoie le panel de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    config = get_ticket_config(interaction.guild.id)
    ticket_channel_id = settings.get(gid, {}).get("ticket_channel")

    if not ticket_channel_id:
        await interaction.response.send_message("Canal de tickets non configuré. Utilisez `/set-ticket-channel`.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(int(ticket_channel_id))
    if not channel:
        await interaction.response.send_message("Canal de tickets introuvable.", ephemeral=True)
        return

    types = get_ticket_types(interaction.guild.id)
    panel_color = config.get("panel_color", None)
    panel_title = config.get("panel_title", f"Support — {interaction.guild.name}")
    panel_desc = config.get("panel_desc", "Ouvrez un ticket en sélectionnant le type de votre demande ci-dessous.")

    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=panel_color)

    if interaction.guild.icon:
        section = discord.ui.Section(
            accessory=discord.ui.Thumbnail(media=interaction.guild.icon.url, description=interaction.guild.name)
        )
        section.add_item(discord.ui.TextDisplay(f"## {panel_title}"))
        container.add_item(section)
    else:
        container.add_item(discord.ui.TextDisplay(f"## {panel_title}"))

    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(panel_desc))
    container.add_item(discord.ui.Separator())

    for k, v in types.items():
        container.add_item(discord.ui.TextDisplay(f"**{v.get('emoji', '❓')} {v['label']}** — {v['desc']}"))

    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("*Sélectionnez un type dans le menu ci-dessous pour ouvrir un ticket.*"))

    row = discord.ui.ActionRow()
    select = discord.ui.Select(
        placeholder="Ouvrir un ticket...",
        options=[
            discord.SelectOption(label=v["label"], value=k, description=v["desc"], emoji=v.get("emoji", "❓"))
            for k, v in types.items()
        ],
        custom_id="ticket_setup_select"
    )
    row.add_item(select)
    container.add_item(row)

    view.add_item(container)
    await channel.send(view=view)
    await interaction.response.send_message(f"Panel envoyé dans {channel.mention}.", ephemeral=True)


async def handle_ticket_open(interaction: discord.Interaction, ticket_type: str, creation_type: str = None):
    guild = interaction.guild
    member = interaction.user
    config = get_ticket_config(guild.id)
    types = get_ticket_types(guild.id)

    tickets = load_tickets()
    gid = str(guild.id)

    if gid not in tickets:
        tickets[gid] = {}

    ticket_limit = config.get("ticket_limit", 1)
    if ticket_limit > 0:
        open_count = sum(1 for t in tickets[gid].values() if t["user_id"] == member.id and t["status"] == "open")
        if open_count >= ticket_limit:
            await interaction.response.send_message(
                f"Vous avez déjà `{open_count}` ticket(s) ouvert(s). Limite : `{ticket_limit}`.",
                ephemeral=True
            )
            return

    type_info = types.get(ticket_type, {"label": ticket_type, "emoji": "❓"})
    label = type_info["label"]

    category_id = config.get("ticket_category")
    category = guild.get_channel(category_id) if category_id else None

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
    }

    for role in guild.roles:
        if role.permissions.administrator:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    channel = await guild.create_text_channel(
        name=f"ticket-{member.name}",
        overwrites=overwrites,
        category=category,
        topic=f"Ticket de {member} ({member.id}) — Type : {label}"
    )

    tickets[gid][str(channel.id)] = {
        "user_id": member.id,
        "type": ticket_type,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "messages": []
    }
    save_tickets(tickets)

    await interaction.response.send_message(
        f"Ticket créé : {channel.mention}",
        ephemeral=True
    )

    welcome_msg = config.get("welcome_msg", "Décrivez votre demande en détail.\nLe staff vous répondra rapidement.\n\n**Utilisez la commande /close pour fermer le ticket.**")

    view = discord.ui.LayoutView()
    panel_color = config.get("panel_color", None)
    container = discord.ui.Container(accent_colour=panel_color)

    section = discord.ui.Section(
        accessory=discord.ui.Thumbnail(media=member.display_avatar.url, description=member.display_name)
    )
    section.add_item(discord.ui.TextDisplay(
        f"## Ticket #{channel.name.split('-')[-1]}\n"
        f"**Type** {type_info.get('emoji', '❓')} {label}\n"
        f"**Membre** {member.mention}\n"
        f"**ID** `{member.id}`\n"
        f"**Créé le** <t:{int(datetime.now(timezone.utc).timestamp())}:R>"
    ))
    container.add_item(section)
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(welcome_msg))
    container.add_item(discord.ui.Separator())

    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Claim", style=discord.ButtonStyle.success, custom_id=f"ticket_claim_{channel.id}", emoji="✋"))
    row.add_item(discord.ui.Button(label="Ajouter", style=discord.ButtonStyle.primary, custom_id=f"ticket_add_{channel.id}", emoji="➕"))
    row.add_item(discord.ui.Button(label="Retirer", style=discord.ButtonStyle.primary, custom_id=f"ticket_remove_{channel.id}", emoji="➖"))
    row.add_item(discord.ui.Button(label="Transcript", style=discord.ButtonStyle.secondary, custom_id=f"ticket_transcript_{channel.id}", emoji="📄"))
    row.add_item(discord.ui.Button(label="Fermer", style=discord.ButtonStyle.danger, custom_id=f"ticket_close_{channel.id}", emoji="🔒"))
    container.add_item(row)

    view.add_item(container)
    await channel.send(view=view)


@ticket.command(name="setup", description="Setup complet du système de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    ticket_channel_id = settings.get(gid, {}).get("ticket_channel")
    if not ticket_channel_id:
        await interaction.response.send_message(
            "Canal de tickets non configuré. Utilisez `/set-ticket-channel` d'abord.",
            ephemeral=True
        )
        return
    channel = interaction.guild.get_channel(int(ticket_channel_id))
    if not channel:
        await interaction.response.send_message(
            "Canal de tickets introuvable. Vérifiez ou reconfigurez avec `/set-ticket-channel`.",
            ephemeral=True
        )
        return

    config = get_ticket_config(interaction.guild.id)
    types = get_ticket_types(interaction.guild.id)
    panel_color = config.get("panel_color", None)
    panel_title = config.get("panel_title", f"Support — {interaction.guild.name}")
    panel_desc = config.get("panel_desc", "Ouvrez un ticket en sélectionnant le type de votre demande ci-dessous.")

    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=panel_color)

    if interaction.guild.icon:
        section = discord.ui.Section(
            accessory=discord.ui.Thumbnail(media=interaction.guild.icon.url, description=interaction.guild.name)
        )
        section.add_item(discord.ui.TextDisplay(f"## {panel_title}"))
        container.add_item(section)
    else:
        container.add_item(discord.ui.TextDisplay(f"## {panel_title}"))

    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(panel_desc))
    container.add_item(discord.ui.Separator())

    for k, v in types.items():
        container.add_item(discord.ui.TextDisplay(f"**{v.get('emoji', '❓')} {v['label']}** — {v['desc']}"))

    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("*Sélectionnez un type dans le menu ci-dessous pour ouvrir un ticket.*"))

    row = discord.ui.ActionRow()
    select = discord.ui.Select(
        placeholder="Ouvrir un ticket...",
        options=[
            discord.SelectOption(label=v["label"], value=k, description=v["desc"], emoji=v.get("emoji", "❓"))
            for k, v in types.items()
        ],
        custom_id="ticket_setup_select"
    )
    row.add_item(select)
    container.add_item(row)

    view.add_item(container)
    await channel.send(view=view)
    await interaction.response.send_message(f"Setup envoyé dans {channel.mention}.", ephemeral=True)


@config.command(name="ticket-channel", description="Définir le canal de tickets")
@app_commands.checks.has_permissions(administrator=True)
async def set_ticket_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}
    settings[gid]["ticket_channel"] = channel.id
    save_settings(settings)
    await interaction.response.send_message(
        f"Canal de tickets défini sur {channel.mention}.",
        ephemeral=True
    )


@ticket.command(name="close", description="Ferme le ticket actuel")
async def close_ticket(interaction: discord.Interaction):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Ce n'est pas un salon de ticket.", ephemeral=True)
        return

    tickets = load_tickets()
    gid = str(interaction.guild.id)
    cid = str(interaction.channel.id)
    if gid not in tickets or cid not in tickets[gid]:
        await interaction.response.send_message("Ticket introuvable.", ephemeral=True)
        return

    ticket = tickets[gid][cid]
    ticket["status"] = "closed"
    ticket["closed_at"] = datetime.now(timezone.utc).isoformat()
    ticket["closed_by"] = interaction.user.id
    save_tickets(tickets)

    config = get_ticket_config(interaction.guild.id)
    close_msg = config.get("close_msg", "Ticket fermé. Merci d'avoir contacté le support.")

    await interaction.response.send_message(close_msg)

    member = interaction.guild.get_member(ticket["user_id"])
    if member:
        await interaction.channel.set_permissions(member, view_channel=False, send_messages=False)

    view = PersistentTicketClose(interaction.channel.id)
    await interaction.channel.send(view=view)

    log_channel_id = config.get("ticket_log_channel")
    if log_channel_id:
        log_ch = interaction.guild.get_channel(int(log_channel_id))
        if log_ch:
            messages = []
            async for message in interaction.channel.history(limit=500, oldest_first=True):
                if not message.author.bot:
                    messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author.display_name}: {message.content}")
            transcript = "\n".join(messages) if messages else "Aucun message."
            file = discord.File(
                fp=io.BytesIO(transcript.encode()),
                filename=f"transcript-{interaction.channel.name}.txt"
            )
            await log_ch.send(
                f"**Ticket fermé** par {interaction.user.mention}\n"
                f"**Salon** `{interaction.channel.name}`\n"
                f"**Membre** {member.mention if member else 'Inconnu'}",
                file=file
            )


@ticket.command(name="add", description="Ajoute un membre au ticket")
@app_commands.describe(member="Le membre à ajouter")
async def ticket_add(interaction: discord.Interaction, member: discord.Member):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Ce n'est pas un salon de ticket.", ephemeral=True)
        return
    await interaction.channel.set_permissions(member, view_channel=True, send_messages=True)
    await interaction.response.send_message(f"{member.mention} ajouté au ticket.")


@ticket.command(name="remove", description="Retire un membre du ticket")
@app_commands.describe(member="Le membre à retirer")
async def ticket_remove(interaction: discord.Interaction, member: discord.Member):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Ce n'est pas un salon de ticket.", ephemeral=True)
        return
    await interaction.channel.set_permissions(member, overwrite=None)
    await interaction.response.send_message(f"{member.mention} retiré du ticket.")


@ticket.command(name="list", description="Liste tous les tickets")
@app_commands.checks.has_permissions(administrator=True)
async def tickets_list(interaction: discord.Interaction):
    tickets = load_tickets()
    gid = str(interaction.guild.id)
    if gid not in tickets:
        await interaction.response.send_message("Aucun ticket.", ephemeral=True)
        return

    types = get_ticket_types(interaction.guild.id)
    open_tickets = {k: v for k, v in tickets[gid].items() if v["status"] == "open"}
    closed_tickets = {k: v for k, v in tickets[gid].items() if v["status"] == "closed"}

    lines = []
    for cid, t in open_tickets.items():
        user = interaction.guild.get_member(t["user_id"])
        name = user.display_name if user else "Inconnu"
        type_label = types.get(t["type"], {}).get("label", t["type"])
        lines.append(f"**<#{cid}>** — {name} — {type_label}")

    closed_lines = []
    for cid, t in list(closed_tickets.items())[-10:]:
        user = interaction.guild.get_member(t["user_id"])
        name = user.display_name if user else "Inconnu"
        type_label = types.get(t["type"], {}).get("label", t["type"])
        closed_lines.append(f"`#{cid}` — {name} — {type_label}")

    view = view_text(
        "## Tickets",
        f"**Ouverts** `{len(open_tickets)}` — **Fermés** `{len(closed_tickets)}`",
        "",
        "**Ouverts :**",
        "\n".join(lines) or "`Aucun`",
        "",
        "**Derniers fermés :**",
        "\n".join(closed_lines) or "`Aucun`"
    )
    await interaction.response.send_message(view=view)


@ticket.command(name="transcript", description="Génère un transcript du ticket")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_transcript(interaction: discord.Interaction):
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("Ce n'est pas un salon de ticket.", ephemeral=True)
        return
    messages = []
    async for message in interaction.channel.history(limit=500, oldest_first=True):
        if not message.author.bot:
            messages.append(f"[{message.created_at.strftime('%d/%m/%Y %H:%M')}] {message.author.display_name}: {message.content}")
    transcript = "\n".join(messages) if messages else "Aucun message."
    file = discord.File(
        fp=io.BytesIO(transcript.encode()),
        filename=f"transcript-{interaction.channel.name}.txt"
    )
    await interaction.response.send_message("Transcript généré.", ephemeral=True)
    await interaction.channel.send(file=file)


@ticket.command(name="force-close", description="Ferme forcé un ticket par ID")
@app_commands.describe(channel_id="ID du salon ticket")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_force_close(interaction: discord.Interaction, channel_id: str):
    tickets = load_tickets()
    gid = str(interaction.guild.id)
    if gid not in tickets or channel_id not in tickets[gid]:
        await interaction.response.send_message("Ticket introuvable.", ephemeral=True)
        return
    ticket = tickets[gid][channel_id]
    ticket["status"] = "closed"
    ticket["closed_at"] = datetime.now(timezone.utc).isoformat()
    ticket["closed_by"] = interaction.user.id
    save_tickets(tickets)
    await interaction.response.send_message(f"Ticket <#{channel_id}> forcé à la fermeture.")


# ──────────────────────────────────────────────
#  MOD LOG HELPER
# ──────────────────────────────────────────────

MOD_LOG_FILE = "mod_log.json"


def load_mod_log():
    if os.path.exists(MOD_LOG_FILE):
        try:
            with open(MOD_LOG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_mod_log(data):
    with open(MOD_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def log_mod(guild, action, moderator, member, reason="Aucune raison"):
    settings = load_settings()
    gid = str(guild.id)
    log_channel_id = settings.get(gid, {}).get("mod_log")
    if not log_channel_id:
        return
    channel = guild.get_channel(int(log_channel_id))
    if not channel:
        return

    mod_log = load_mod_log()
    if gid not in mod_log:
        mod_log[gid] = []
    case_id = len(mod_log[gid]) + 1
    mod_log[gid].append({
        "case": case_id,
        "action": action,
        "moderator_id": moderator.id,
        "member_id": member.id,
        "reason": reason,
        "at": datetime.now(timezone.utc).isoformat()
    })
    save_mod_log(mod_log)

    view = view_text(
        f"## {action} — Case #{case_id}",
        f"**Membre** {member.mention} (`{member.id}`)",
        f"**Modérateur** {moderator.mention}",
        f"**Raison** {reason}",
        f"**Date** <t:{int(datetime.now(timezone.utc).timestamp())}:R>"
    )
    try:
        await channel.send(view=view)
    except discord.Forbidden:
        pass


# ──────────────────────────────────────────────
#  MODÉRATION AVANCÉE
# ──────────────────────────────────────────────

@mod.command(name="softban", description="Ban puis unban immédiat pour purger les messages")
@app_commands.describe(member="Le membre", reason="Raison")
@app_commands.checks.has_permissions(ban_members=True)
async def softban(interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison"):
    if member.bot:
        await interaction.response.send_message("Impossible de softban un bot.", ephemeral=True)
        return
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Rôle insuffisant.", ephemeral=True)
        return

    try:
        await member.send(f"Vous avez été softbanni de **{interaction.guild.name}** pour : {reason}")
    except discord.Forbidden:
        pass

    await member.ban(reason=reason, delete_message_days=7)
    await interaction.guild.unban(member)
    await log_mod(interaction.guild, "Softban", interaction.user, member, reason)

    view = view_text(
        f"## Softban — {member.display_name}",
        f"**Membre** `{member}` (`{member.id}`)",
        f"**Raison** {reason}",
        f"**Par** {interaction.user.mention}"
    )
    await interaction.response.send_message(view=view)


JAIL_ROLE_NAME = "Jailed"


@mod.command(name="jail", description="Envoie un membre en prison (ou le libère)")
@app_commands.describe(member="Le membre")
@app_commands.checks.has_permissions(administrator=True)
async def jail(interaction: discord.Interaction, member: discord.Member):
    if member.bot:
        await interaction.response.send_message("Impossible de jailer un bot.", ephemeral=True)
        return

    guild = interaction.guild
    jail_role = discord.utils.get(guild.roles, name=JAIL_ROLE_NAME)

    if not jail_role:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }
        category = guild.categories[0] if guild.categories else None
        jail_role = await guild.create_role(name=JAIL_ROLE_NAME, permissions=discord.Permissions(), overwrites=overwrites, reason="Jail system")
        await guild.create_text_channel(
            name="jail",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                jail_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        )

    if jail_role in member.roles:
        jail_data = load_jail()
        gid = str(guild.id)
        mid = str(member.id)
        backup_role_ids = jail_data.get(gid, {}).get(mid, {}).get("roles", [])
        restored = 0
        for role_id in backup_role_ids:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                    restored += 1
                except discord.Forbidden:
                    pass
        if gid in jail_data and mid in jail_data[gid]:
            del jail_data[gid][mid]
            save_jail(jail_data)
        await member.remove_roles(jail_role)
        await interaction.response.send_message(f"{member.mention} libéré de la prison. `{restored}` rôles restaurés.")
    else:
        backup_roles = [r.id for r in member.roles[1:] if r != jail_role]
        jail_data = load_jail()
        gid = str(guild.id)
        mid = str(member.id)
        if gid not in jail_data:
            jail_data[gid] = {}
        jail_data[gid][mid] = {
            "roles": backup_roles,
            "jailed_at": datetime.now(timezone.utc).isoformat(),
            "jailed_by": interaction.user.id,
        }
        save_jail(jail_data)

        await member.edit(roles=[jail_role])
        await log_mod(interaction.guild, "Jail", interaction.user, member)
        await interaction.response.send_message(f"{member.mention} envoyé en prison.")



@mod.command(name="history", description="Affiche l'historique de modération d'un membre")
@app_commands.describe(member="Le membre")
@app_commands.checks.has_permissions(moderate_members=True)
async def history(interaction: discord.Interaction, member: discord.Member):
    mod_log = load_mod_log()
    gid = str(interaction.guild.id)
    entries = [e for e in mod_log.get(gid, []) if e["member_id"] == member.id]

    if not entries:
        await interaction.response.send_message(f"Aucun historique de modération pour {member.mention}.", ephemeral=True)
        return

    lines = []
    for e in entries[-15:]:
        mod = interaction.guild.get_member(e["moderator_id"])
        mod_name = mod.display_name if mod else "Inconnu"
        lines.append(f"**#{e['case']}** {e['action']} — par `{mod_name}` — {e['reason']}")

    view = view_text(
        f"## Historique — {member.display_name}",
        f"**Total** `{len(entries)}`",
        "",
        *lines
    )
    await interaction.response.send_message(view=view)


@app_commands.checks.has_permissions(moderate_members=True)
@mod.command(name="case", description="Affiche un case de modération")
@app_commands.describe(case_id="Numéro du case")
async def case_cmd(interaction: discord.Interaction, case_id: int):
    mod_log = load_mod_log()
    gid = str(interaction.guild.id)
    entries = mod_log.get(gid, [])

    if case_id < 1 or case_id > len(entries):
        await interaction.response.send_message(f"Case #{case_id} introuvable.", ephemeral=True)
        return

    e = entries[case_id - 1]
    mod = interaction.guild.get_member(e["moderator_id"])
    member = interaction.guild.get_member(e["member_id"])

    member_name = member.mention if member else f"`{e['member_id']}`"
    mod_name = mod.mention if mod else f"`{e['moderator_id']}`"

    view = view_text(
        f"## Case #{case_id}",
        f"**Action** {e['action']}",
        f"**Membre** {member_name}",
        f"**Modérateur** {mod_name}",
        f"**Raison** {e['reason']}",
        f"**Date** {e['at'][:10]}"
    )
    await interaction.response.send_message(view=view)


# ──────────────────────────────────────────────
#  WELCOME / GOODBYE
# ──────────────────────────────────────────────
#  WELCOME / GOODBYE / BOOST CONFIG
# ──────────────────────────────────────────────

@welcome.command(name="setup", description="Configure l'accueil (setup/disable/preview)")
@app_commands.describe(
    action="Action",
    channel="Salon d'accueil (setup uniquement)",
    message="Message (variables : {user}, {server}, {count})",
    image="Image Canvas (on/off)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="setup", value="setup"),
    app_commands.Choice(name="disable", value="disable"),
    app_commands.Choice(name="preview", value="preview"),
], image=[
    app_commands.Choice(name="on", value="on"),
    app_commands.Choice(name="off", value="off"),
])
@app_commands.checks.has_permissions(administrator=True)
async def welcome_setup(interaction: discord.Interaction, action: str, channel: discord.TextChannel = None, message: str = "Bienvenue {user} sur **{server}** !", image: str = "on"):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}

    if action == "disable":
        settings[gid].pop("welcome_channel", None)
        settings[gid].pop("welcome_message", None)
        settings[gid].pop("welcome_image", None)
        save_settings(settings)
        await interaction.response.send_message("Message d'accueil désactivé.")

    elif action == "preview":
        s = settings.get(gid, {})
        msg = s.get("welcome_message", "Bienvenue {user} sur **{server}** !")
        msg = msg.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{count}", str(interaction.guild.member_count))
        file = await generate_welcome_image(interaction.user)
        await interaction.response.send_message(f"**Aperçu :**\n{msg}", file=file, ephemeral=True)

    else:
        if not channel:
            await interaction.response.send_message("Salon requis pour le setup.", ephemeral=True)
            return
        settings[gid]["welcome_channel"] = channel.id
        settings[gid]["welcome_message"] = message
        settings[gid]["welcome_image"] = image == "on"
        save_settings(settings)
        file = await generate_welcome_image(interaction.user)
        preview_msg = message.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{count}", str(interaction.guild.member_count))
        await interaction.response.send_message(
            f"Accueil configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`\n\n"
            f"**Aperçu :**\n{preview_msg}",
            file=file
        )


@welcome.command(name="goodbye", description="Configure le départ (setup/disable/preview)")
@app_commands.describe(
    action="Action",
    channel="Salon de départ (setup uniquement)",
    message="Message (variables : {user}, {server}, {count})",
    image="Image Canvas (on/off)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="setup", value="setup"),
    app_commands.Choice(name="disable", value="disable"),
    app_commands.Choice(name="preview", value="preview"),
], image=[
    app_commands.Choice(name="on", value="on"),
    app_commands.Choice(name="off", value="off"),
])
@app_commands.checks.has_permissions(administrator=True)
async def goodbye(interaction: discord.Interaction, action: str, channel: discord.TextChannel = None, message: str = "**{user}** a quitté **{server}**.", image: str = "on"):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}

    if action == "disable":
        settings[gid].pop("goodbye_channel", None)
        settings[gid].pop("goodbye_message", None)
        settings[gid].pop("goodbye_image", None)
        save_settings(settings)
        await interaction.response.send_message("Message de départ désactivé.")

    elif action == "preview":
        s = settings.get(gid, {})
        msg = s.get("goodbye_message", "**{user}** a quitté **{server}**.")
        msg = msg.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{count}", str(interaction.guild.member_count))
        file = await generate_goodbye_image(interaction.user)
        await interaction.response.send_message(f"**Aperçu :**\n{msg}", file=file, ephemeral=True)

    else:
        if not channel:
            await interaction.response.send_message("Salon requis pour le setup.", ephemeral=True)
            return
        settings[gid]["goodbye_channel"] = channel.id
        settings[gid]["goodbye_message"] = message
        settings[gid]["goodbye_image"] = image == "on"
        save_settings(settings)
        file = await generate_goodbye_image(interaction.user)
        preview_msg = message.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{count}", str(interaction.guild.member_count))
        await interaction.response.send_message(
            f"Départ configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`\n\n"
            f"**Aperçu :**\n{preview_msg}",
            file=file
        )


@welcome.command(name="boost", description="Configure le boost (setup/disable/preview)")
@app_commands.describe(
    action="Action",
    channel="Salon de boost (setup uniquement)",
    message="Message (variables : {user}, {server}, {boosts})",
    image="Image Canvas (on/off)"
)
@app_commands.choices(action=[
    app_commands.Choice(name="setup", value="setup"),
    app_commands.Choice(name="disable", value="disable"),
    app_commands.Choice(name="preview", value="preview"),
], image=[
    app_commands.Choice(name="on", value="on"),
    app_commands.Choice(name="off", value="off"),
])
@app_commands.checks.has_permissions(administrator=True)
async def boost(interaction: discord.Interaction, action: str, channel: discord.TextChannel = None, message: str = "**{user}** a boosté **{server}** !", image: str = "on"):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}

    if action == "disable":
        settings[gid].pop("boost_channel", None)
        settings[gid].pop("boost_message", None)
        settings[gid].pop("boost_image", None)
        save_settings(settings)
        await interaction.response.send_message("Message de boost désactivé.")

    elif action == "preview":
        s = settings.get(gid, {})
        msg = s.get("boost_message", "**{user}** a boosté **{server}** !")
        boost_count = interaction.guild.premium_subscription_count or 0
        msg = msg.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{boosts}", str(boost_count))
        file = await generate_boost_image(interaction.user)
        await interaction.response.send_message(f"**Aperçu :**\n{msg}", file=file, ephemeral=True)

    else:
        if not channel:
            await interaction.response.send_message("Salon requis pour le setup.", ephemeral=True)
            return
        settings[gid]["boost_channel"] = channel.id
        settings[gid]["boost_message"] = message
        settings[gid]["boost_image"] = image == "on"
        save_settings(settings)
        file = await generate_boost_image(interaction.user)
        boost_count = interaction.guild.premium_subscription_count or 0
        preview_msg = message.replace("{user}", interaction.user.mention).replace("{server}", interaction.guild.name).replace("{boosts}", str(boost_count))
        await interaction.response.send_message(
            f"Boost configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`\n\n"
            f"**Aperçu :**\n{preview_msg}",
            file=file
        )


# ──────────────────────────────────────────────
#  AUTOMOD (ANTI-LINK / ANTI-SPAM)
# ──────────────────────────────────────────────

LINK_REGEX = r"https?://\S+|www\.\S+"
user_message_cache = defaultdict(list)


@config.command(name="automod", description="Gère l'automod du bot")
@app_commands.describe(option="anti-link ou anti-spam", state="on ou off")
@app_commands.choices(option=[
    app_commands.Choice(name="anti-link", value="anti-link"),
    app_commands.Choice(name="anti-spam", value="anti-spam"),
])
@app_commands.choices(state=[
    app_commands.Choice(name="on", value="on"),
    app_commands.Choice(name="off", value="off"),
])
@app_commands.checks.has_permissions(administrator=True)
async def automod(interaction: discord.Interaction, option: str, state: str):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}
    settings[gid][option] = state == "on"
    save_settings(settings)
    status = "activé" if state == "on" else "désactivé"
    await interaction.response.send_message(f"`{option}` {status}.")


@mod.command(name="mod-log", description="Configure le salon de logs de modération")
@app_commands.describe(channel="Le salon de logs")
@app_commands.checks.has_permissions(administrator=True)
async def mod_log_cmd(interaction: discord.Interaction, channel: discord.TextChannel):
    settings = load_settings()
    gid = str(interaction.guild.id)
    if gid not in settings:
        settings[gid] = {}
    settings[gid]["mod_log"] = channel.id
    save_settings(settings)
    await interaction.response.send_message(f"Logs de modération configurés dans {channel.mention}.")


# ──────────────────────────────────────────────
#  UTILITAIRES
# ──────────────────────────────────────────────

afk_users = {}


@util.command(name="afk", description="Passe en mode AFK")
@app_commands.describe(reason="Raison de l'AFK")
async def afk(interaction: discord.Interaction, reason: str = "AFK"):
    afk_users[interaction.user.id] = {
        "reason": reason,
        "since": datetime.now(timezone.utc)
    }
    await interaction.response.send_message(f"**{interaction.user.display_name}** est maintenant AFK : {reason}")


@util.command(name="remind", description="Définit un rappel automatique")
@app_commands.describe(duration="Durée (ex: 1h30m, 30m, 2d)", message="Message du rappel")
async def remind(interaction: discord.Interaction, duration: str, message: str):
    total = 0
    current = ""
    for c in duration:
        if c.isdigit():
            current += c
        elif c == "d" and current:
            total += int(current) * 86400
            current = ""
        elif c == "h" and current:
            total += int(current) * 3600
            current = ""
        elif c == "m" and current:
            total += int(current) * 60
            current = ""
        elif c == "s" and current:
            total += int(current)
            current = ""

    if total <= 0:
        await interaction.response.send_message("Durée invalide.", ephemeral=True)
        return

    await interaction.response.send_message(f"Rappel dans `{duration}` : {message}")
    await asyncio.sleep(total)
    try:
        await interaction.user.send(f"⏰ Rappel : {message}")
    except discord.Forbidden:
        pass
    try:
        await interaction.followup.send(f"⏰ {interaction.user.mention} Rappel : {message}")
    except discord.HTTPException:
        pass


@util.command(name="uptime", description="Affiche le temps de fonctionnement du bot")
async def uptime(interaction: discord.Interaction):
    delta = datetime.now(timezone.utc) - BOT_START
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    view = view_text("## Uptime", f"**En ligne depuis** `{days}j {hours}h {minutes}m {seconds}s`")
    await interaction.response.send_message(view=view)


@util.command(name="bot-info", description="Affiche les informations du bot")
async def bot_info(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    uptime_sec = (datetime.now(timezone.utc) - BOT_START).total_seconds()
    hours, remainder = divmod(int(uptime_sec), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    view = view_text(
        "## Bot Info — Dev Hub",
        f"**Nom** `{bot.user.name}`",
        f"**ID** `{bot.user.id}`",
        f"**Serveurs** `{len(bot.guilds)}`",
        f"**Utilisateurs** `{len(bot.users)}`",
        f"**Latence** `{latency}ms`",
        f"**Uptime** `{days}j {hours}h {minutes}m {seconds}s`",
        f"**Python** `{os.sys.version.split()[0]}`",
        f"**discord.py** `2.5+`",
        f"**Commandes** `{len(bot.tree.get_commands())}`"
    )
    await interaction.response.send_message(view=view)


# ──────────────────────────────────────────────
#  FUN
# ──────────────────────────────────────────────

@fun.command(name="coinflip", description="Lance une pièce (pile ou face)")
async def coinflip(interaction: discord.Interaction):
    result = random.choice(["Pile", "Face"])
    await interaction.response.send_message(f"🪙 **{result}**")


@fun.command(name="dice", description="Lance un dé")
@app_commands.describe(faces="Nombre de faces (défaut : 6)")
async def dice(interaction: discord.Interaction, faces: int = 6):
    if faces < 2:
        await interaction.response.send_message("Minimum 2 faces.", ephemeral=True)
        return
    result = random.randint(1, faces)
    await interaction.response.send_message(f"🎲 **{result}** / {faces}")


@fun.command(name="8ball", description="Boule magique — posez une question")
@app_commands.describe(question="Votre question")
async def eight_ball(interaction: discord.Interaction, question: str):
    answers = [
        "Oui, absolument.", "Non, pas du tout.", "C'est certain.",
        "Je ne peux pas prédire ça.", "Demande-moi plus tard.",
        "Les signes sont favorables.", "Les signes sont défavorables.",
        "Je doute fort.", "Oui, sans hésitation.", "Probablement pas.",
        "C'est possible.", "Laisse-moi réfléchir...", "Tu as tout intérêt à y croire.",
        "C'est bien connu.", "Ma réponse est non.", "Concentre-toi et ré-essaye."
    ]
    await interaction.response.send_message(f"🔮 **{random.choice(answers)}**")


@fun.command(name="ship", description="Teste la compatibilité entre deux membres")
@app_commands.describe(user1="Premier membre", user2="Deuxième membre")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    seed = f"{user1.id}{user2.id}"
    score = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16) % 101

    if score < 20:
        emoji = "💔"
        label = "Incompatible"
    elif score < 40:
        emoji = "🫤"
        label = "Amis"
    elif score < 60:
        emoji = "😏"
        label = "Potentiel"
    elif score < 80:
        emoji = "😍"
        label = "Bonne alchimie"
    else:
        emoji = "💘"
        label = "Alchimie parfaite"

    bar_len = 20
    filled = int(bar_len * score / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    view = view_text(
        "## Ship",
        f"**{user1.display_name}** x **{user2.display_name}**",
        "",
        f"`{bar}` **{score}%**",
        "",
        f"{emoji} {label}"
    )
    await interaction.response.send_message(view=view)


@fun.command(name="rate", description="Note quelque chose sur 10")
@app_commands.describe(chose="Ce que vous voulez noter")
async def rate(interaction: discord.Interaction, chose: str):
    score = random.randint(0, 10)
    bar_len = 10
    filled = int(bar_len * score / 10)
    bar = "█" * filled + "░" * (bar_len - filled)
    await interaction.response.send_message(f"📊 Je note **{chose}** : `{score}/10`")


# ──────────────────────────────────────────────
#  GESTION DE SALON
# ──────────────────────────────────────────────

# ──────────────────────────────────────────────
#  ANTI-RAID AVANCÉ
# ──────────────────────────────────────────────
#  ANTI-RAID INTELLIGENT (SCORE-BASED)
# ──────────────────────────────────────────────

import json, os

RAID_STATE_FILE = os.path.join(os.path.dirname(__file__), "raid_state.json")

def load_raid_state():
    try:
        with open(RAID_STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_raid_state(state):
    with open(RAID_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

join_tracker = defaultdict(list)
name_history = defaultdict(list)
raid_scores = defaultdict(lambda: defaultdict(int))
flagged_members = defaultdict(list)
lockdown_channels = defaultdict(set)
raid_state = load_raid_state()

def get_raid_config(gid):
    settings = load_settings()
    s = settings.get(gid, {})
    return {
        "enabled": s.get("anti_raid", False),
        "log_channel": s.get("raid_log"),
        "max_joins": s.get("raid_max_joins", 5),
        "window": s.get("raid_window", 10),
        "min_account_age": s.get("raid_min_age", 7),
        "action": s.get("raid_action", "kick"),
        "check_avatar": s.get("raid_check_avatar", True),
        "check_name": s.get("raid_check_name", True),
        "whitelist": s.get("raid_whitelist", []),
        "blacklist": s.get("raid_blacklist", []),
        "score_kick": s.get("raid_score_kick", 10),
        "score_ban": s.get("raid_score_ban", 20),
        "anti_nuke": s.get("raid_anti_nuke", True),
        "anti_webhook": s.get("raid_anti_webhook", True),
        "verification_role": s.get("raid_verification_role"),
        "lockdown_overwrite": s.get("raid_lockdown_overwrite", True),
    }

def save_raid_config(gid, config):
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    settings[gid].update(config)
    save_settings(settings)

def levenshtein(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]

def calculate_name_score(name, recent_names):
    max_score = 0
    clean = ''.join(c for c in name.lower() if c.isalnum())
    for other in recent_names:
        other_clean = ''.join(c for c in other.lower() if c.isalnum())
        if not other_clean or not clean:
            continue
        dist = levenshtein(clean, other_clean)
        max_len = max(len(clean), len(other_clean))
        similarity = 1 - (dist / max_len) if max_len > 0 else 0
        if similarity > 0.7:
            score = int(similarity * 15)
            max_score = max(max_score, score)
    return max_score

def is_default_avatar(member):
    return member.avatar is None

async def raid_log_send(guild, config, embed_lines):
    if not config.get("log_channel"):
        return
    channel = guild.get_channel(int(config["log_channel"]))
    if not channel:
        return
    view = view_text("## Anti-Raid", *embed_lines)
    try:
        await channel.send(view=view)
    except discord.Forbidden:
        pass

async def handle_raid_action(member, config, reasons, score):
    guild = member.guild
    if score >= config["score_ban"]:
        action = "ban"
    elif score >= config["score_kick"]:
        action = config["action"]
    else:
        action = "timeout"
    try:
        if action == "ban":
            await member.ban(reason=f"Anti-raid (score {score}): {' | '.join(reasons)}", delete_message_days=1)
            await raid_log_send(guild, config, [
                f"**BANNI** — {member.mention} (`{member.id}`)",
                f"**Score** `{score}/{config['score_ban']}`",
                f"**Raisons** {' | '.join(reasons)}",
                f"**Compte** <t:{int(member.created_at.timestamp())}:R>",
            ])
        elif action == "kick":
            await member.kick(reason=f"Anti-raid (score {score}): {' | '.join(reasons)}")
            await raid_log_send(guild, config, [
                f"**EXPULSE** — {member.mention} (`{member.id}`)",
                f"**Score** `{score}/{config['score_kick']}`",
                f"**Raisons** {' | '.join(reasons)}",
                f"**Compte** <t:{int(member.created_at.timestamp())}:R>",
            ])
        else:
            until = datetime.now(timezone.utc) + timedelta(minutes=30)
            await member.timeout(until, reason=f"Anti-raid (score {score}): {' | '.join(reasons)}")
            await raid_log_send(guild, config, [
                f"**MUTE** — {member.mention} (`{member.id}`)",
                f"**Score** `{score}`",
                f"**Raisons** {' | '.join(reasons)}",
                f"**Compte** <t:{int(member.created_at.timestamp())}:R>",
                f"**Action** Timeout 30min"
            ])
        flagged_members[str(guild.id)].append(member.id)
    except discord.Forbidden:
        await raid_log_send(guild, config, [
            f"**ECHEC** — {member.mention} (`{member.id}`)",
            f"**Raisons** {' | '.join(reasons)}",
            f"**Erreur** Permissions insuffisantes"
        ])

@raid.command(name="config", description="Configure l'anti-raid intelligent")
@app_commands.describe(
    state="on ou off",
    max_joins="Max joins dans la fenetre (defaut: 5)",
    window="Fenetre en secondes (defaut: 10)",
    min_age="Age min du compte en jours (defaut: 7)",
    action="Action: kick, ban ou timeout",
    score_kick="Score pour kick (defaut: 10)",
    score_ban="Score pour ban (defaut: 20)",
    anti_nuke="Anti-nuke on/off",
)
@app_commands.choices(
    state=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    action=[
        app_commands.Choice(name="kick", value="kick"),
        app_commands.Choice(name="ban", value="ban"),
        app_commands.Choice(name="timeout", value="timeout"),
    ],
    anti_nuke=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
)
@app_commands.checks.has_permissions(administrator=True)
async def anti_raid(interaction: discord.Interaction, state: str, max_joins: int = 5, window: int = 10, min_age: int = 7, action: str = "kick", score_kick: int = 10, score_ban: int = 20, anti_nuke: str = "on"):
    gid = str(interaction.guild.id)
    save_raid_config(gid, {
        "anti_raid": state == "on",
        "raid_max_joins": max_joins,
        "raid_window": window,
        "raid_min_age": min_age,
        "raid_action": action,
        "raid_score_kick": score_kick,
        "raid_score_ban": score_ban,
        "raid_anti_nuke": anti_nuke == "on",
    })
    status = "active" if state == "on" else "desactive"
    view = view_text(
        "## Anti-Raid — Configuration",
        f"**Etat** `{status}`",
        f"**Max joins** `{max_joins}` dans `{window}s`",
        f"**Age min compte** `{min_age}` jours",
        f"**Action** `{action}`",
        f"**Score kick** `{score_kick}` | **Score ban** `{score_ban}`",
        f"**Anti-nuke** `{anti_nuke}`",
    )
    await interaction.response.send_message(view=view)


@raid.command(name="log", description="Configure le salon de logs anti-raid")
@app_commands.describe(channel="Le salon de logs")
@app_commands.checks.has_permissions(administrator=True)
async def raid_log(interaction: discord.Interaction, channel: discord.TextChannel):
    gid = str(interaction.guild.id)
    save_raid_config(gid, {"raid_log": channel.id})
    await interaction.response.send_message(f"Logs anti-raid configures dans {channel.mention}.")


@raid.command(name="whitelist", description="Ajoute ou retire un role de la whitelist")
@app_commands.describe(role="Le role a gerer")
@app_commands.choices(action=[
    app_commands.Choice(name="ajouter", value="add"),
    app_commands.Choice(name="retirer", value="remove"),
])
@app_commands.checks.has_permissions(administrator=True)
async def raid_whitelist(interaction: discord.Interaction, role: discord.Role, action: str):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    wl = config.get("whitelist", [])
    if action == "add":
        if role.id not in wl:
            wl.append(role.id)
            save_raid_config(gid, {"raid_whitelist": wl})
            await interaction.response.send_message(f"{role.mention} ajoute a la whitelist.")
        else:
            await interaction.response.send_message(f"{role.mention} deja dans la whitelist.", ephemeral=True)
    else:
        if role.id in wl:
            wl.remove(role.id)
            save_raid_config(gid, {"raid_whitelist": wl})
            await interaction.response.send_message(f"{role.mention} retire de la whitelist.")
        else:
            await interaction.response.send_message(f"{role.mention} n'est pas dans la whitelist.", ephemeral=True)


@raid.command(name="blacklist", description="Ajoute ou retire un ID de la blacklist")
@app_commands.describe(user_id="L'ID du membre a blacklister")
@app_commands.choices(action=[
    app_commands.Choice(name="ajouter", value="add"),
    app_commands.Choice(name="retirer", value="remove"),
])
@app_commands.checks.has_permissions(administrator=True)
async def raid_blacklist(interaction: discord.Interaction, user_id: str, action: str):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    bl = config.get("blacklist", [])
    uid = int(user_id)
    if action == "add":
        if uid not in bl:
            bl.append(uid)
            save_raid_config(gid, {"raid_blacklist": bl})
            await interaction.response.send_message(f"`{user_id}` ajoute a la blacklist.")
        else:
            await interaction.response.send_message(f"`{user_id}` deja dans la blacklist.", ephemeral=True)
    else:
        if uid in bl:
            bl.remove(uid)
            save_raid_config(gid, {"raid_blacklist": bl})
            await interaction.response.send_message(f"`{user_id}` retire de la blacklist.")
        else:
            await interaction.response.send_message(f"`{user_id}` n'est pas dans la blacklist.", ephemeral=True)


@raid.command(name="lockdown", description="Verrouille ou deverrouille tous les salons")
@app_commands.describe(state="lock ou unlock")
@app_commands.choices(state=[
    app_commands.Choice(name="lock", value="lock"),
    app_commands.Choice(name="unlock", value="unlock"),
])
@app_commands.checks.has_permissions(administrator=True)
async def raid_lockdown(interaction: discord.Interaction, state: str):
    gid = str(interaction.guild.id)
    guild = interaction.guild
    everyone = guild.default_role
    count = 0
    if state == "lock":
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(everyone)
                overwrite.send_messages = False
                await channel.set_permissions(everyone, overwrite=overwrite, reason="Lockdown")
                lockdown_channels[gid].add(channel.id)
                count += 1
            except discord.Forbidden:
                pass
        save_raid_state(load_raid_state() | {gid: {"locked": True, "channels": list(lockdown_channels[gid])}})
        await interaction.response.send_message(f"**{count}** salons verrouilles.")
    else:
        for channel in guild.text_channels:
            try:
                overwrite = channel.overwrites_for(everyone)
                overwrite.send_messages = None
                await channel.set_permissions(everyone, overwrite=overwrite, reason="Unlockdown")
                lockdown_channels[gid].discard(channel.id)
                count += 1
            except discord.Forbidden:
                pass
        state_data = load_raid_state()
        state_data.pop(gid, None)
        save_raid_state(state_data)
        await interaction.response.send_message(f"**{count}** salons deverrouilles.")


@raid.command(name="massban", description="Bannir tous les membres suspects")
@app_commands.describe(reason="Raison du massban")
@app_commands.checks.has_permissions(ban_members=True)
async def raid_massban(interaction: discord.Interaction, reason: str = "Anti-raid massban"):
    await interaction.response.defer()
    gid = str(interaction.guild.id)
    flagged = flagged_members.get(gid, [])
    if not flagged:
        await interaction.followup.send("Aucun membre suspect a bannir.")
        return
    count = 0
    for uid in flagged:
        member = interaction.guild.get_member(uid)
        if member:
            try:
                await member.ban(reason=reason, delete_message_days=1)
                count += 1
            except discord.Forbidden:
                pass
    flagged_members[gid] = []
    await interaction.followup.send(f"**{count}** membres bannis.")


@raid.command(name="scan", description="Scanner les membres actuels pour detects les suspects")
@app_commands.checks.has_permissions(administrator=True)
async def raid_scan(interaction: discord.Interaction):
    await interaction.response.defer()
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    suspects = []
    now = datetime.now(timezone.utc)
    for member in interaction.guild.members:
        if member.bot:
            continue
        if any(r.id in config.get("whitelist", []) for r in member.roles):
            continue
        score = 0
        reasons = []
        account_age = now - member.created_at
        if account_age < timedelta(days=config["min_account_age"]):
            s = min(15, (config["min_account_age"] - account_age.days) * 2)
            score += s
            reasons.append(f"Compte age {account_age.days}j")
        if config["check_avatar"] and is_default_avatar(member):
            score += 5
            reasons.append("Avatar par defaut")
        if score >= config["score_kick"]:
            suspects.append((member, score, reasons))
    if not suspects:
        await interaction.followup.send("Aucun membre suspect detecte.")
        return
    lines = [f"**{len(suspects)} membres suspects:**\n"]
    for member, score, reasons in suspects[:25]:
        lines.append(f"- {member.mention} (`{member.id}`) — Score `{score}` — {', '.join(reasons)}")
    if len(suspects) > 25:
        lines.append(f"\n... et {len(suspects) - 25} autres.")
    await interaction.followup.send("\n".join(lines))


@raid.command(name="status", description="Affiche la configuration anti-raid")
@app_commands.checks.has_permissions(administrator=True)
async def raid_status(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    wl = config.get("whitelist", [])
    bl = config.get("blacklist", [])
    wl_text = ", ".join(f"<@&{r}>" for r in wl) or "`Aucun`"
    bl_text = ", ".join(f"`{r}`" for r in bl) or "`Aucun`"
    status = "active" if config["enabled"] else "desactive"
    log_ch = f"<#{config['log_channel']}>" if config["log_channel"] else "`Non configure`"
    view = view_text(
        "## Anti-Raid — Status",
        f"**Etat** `{status}`",
        f"**Max joins** `{config['max_joins']}` dans `{config['window']}s`",
        f"**Age min** `{config['min_account_age']}` jours",
        f"**Action** `{config['action']}`",
        f"**Score kick** `{config['score_kick']}` | **Score ban** `{config['score_ban']}`",
        f"**Anti-nuke** `{config['anti_nuke']}`",
        f"**Log** {log_ch}",
        f"**Whitelist** {wl_text}",
        f"**Blacklist** {bl_text}",
    )
    await interaction.response.send_message(view=view)


@raid.command(name="panel", description="Panel interactif anti-raid")
@app_commands.checks.has_permissions(administrator=True)
async def raid_panel(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    status = "ON" if config["enabled"] else "OFF"
    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## Panel Anti-Raid Intelligent"))
    container.add_item(discord.ui.TextDisplay(
        f"**Etat :** {status}\n"
        f"**Max joins :** {config['max_joins']} dans {config['window']}s\n"
        f"**Age min :** {config['min_account_age']} jours\n"
        f"**Action :** {config['action']}\n"
        f"**Score kick :** {config['score_kick']} | **Score ban :** {config['score_ban']}\n"
        f"**Anti-nuke :** {config['anti_nuke']}\n"
        f"**Detection par score cumulatif** — Chaque signal suspect ajoute des points"
    ))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Activer", style=discord.ButtonStyle.success, custom_id="raid_on"))
    row.add_item(discord.ui.Button(label="Desactiver", style=discord.ButtonStyle.danger, custom_id="raid_off"))
    row.add_item(discord.ui.Button(label="Lockdown", style=discord.ButtonStyle.secondary, custom_id="raid_lockdown"))
    container.add_item(row)
    row2 = discord.ui.ActionRow()
    row2.add_item(discord.ui.Button(label="Scan", style=discord.ButtonStyle.secondary, custom_id="raid_scan"))
    row2.add_item(discord.ui.Button(label="Massban", style=discord.ButtonStyle.danger, custom_id="raid_massban"))
    container.add_item(row2)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# ──────────────────────────────────────────────
#  ANTI-NUKE DETECTION
# ──────────────────────────────────────────────

nuke_tracker = defaultdict(lambda: {"channels": [], "roles": [], "bans": [], "webhooks": []})

async def check_nuke_action(guild, action_type, config):
    if not config.get("anti_nuke", True):
        return
    gid = str(guild.id)
    now = datetime.now(timezone.utc)
    tracker = nuke_tracker[gid]
    window = 300
    tracker[action_type] = [t for t in tracker[action_type] if (now - t).total_seconds() < window]
    tracker[action_type].append(now)
    member_count = guild.member_count
    thresholds = {
        "channels": max(3, int(member_count * 0.05)),
        "roles": max(3, int(member_count * 0.05)),
        "bans": max(3, int(member_count * 0.03)),
        "webhooks": 5,
    }
    count = len(tracker[action_type])
    if count >= thresholds.get(action_type, 5):
        await raid_log_send(guild, config, [
            f"**NUKE DETECTE** — {action_type}",
            f"**Actions** `{count}` dans les 5 dernieres minutes",
            f"**Seuil** `{thresholds.get(action_type, 5)}`",
            f"**Protection** Verrouillage automatique recommande",
        ])


# ──────────────────────────────────────────────
#  ON MESSAGE (AFK + AUTOMOD)
# ──────────────────────────────────────────────

import re

LINK_PATTERN = re.compile(LINK_REGEX, re.IGNORECASE)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.author.id in afk_users:
        afk_data = afk_users.pop(message.author.id)
        since = afk_data["since"]
        duration = datetime.now(timezone.utc) - since
        minutes = int(duration.total_seconds() // 60)
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        await message.channel.send(
            f"**{message.author.display_name}** n'est plus AFK (AFK pendant `{minutes}` minute(s)).",
            delete_after=5
        )

    if message.mentions:
        for mentioned in message.mentions:
            if mentioned.id in afk_users:
                afk_data = afk_users[mentioned.id]
                since = afk_data["since"]
                duration = datetime.now(timezone.utc) - since
                minutes = int(duration.total_seconds() // 60)
                try:
                    await message.channel.send(
                        f"**{mentioned.display_name}** est AFK : {afk_data['reason']} (depuis `{minutes}` min)",
                        delete_after=5
                    )
                except discord.Forbidden:
                    pass

    settings = load_settings()
    gid = str(message.guild.id) if message.guild else ""
    guild_settings = settings.get(gid, {})

    if guild_settings.get("anti-link"):
        content = message.content
        if message.content:
            content = re.sub(r'`[^`]*`', '', content)
            content = re.sub(r'```[\s\S]*?```', '', content)
        if LINK_PATTERN.search(content):
            perms = message.channel.permissions_for(message.author)
            if not perms.administrator:
                try:
                    await message.delete()
                    await message.channel.send(
                        f"**{message.author.display_name}**, les liens ne sont pas autorises.",
                        delete_after=5
                    )
                except discord.Forbidden:
                    pass

    if guild_settings.get("anti-spam"):
        now = time.time()
        cache_key = f"{message.author.id}_{message.channel.id}"
        user_message_cache[cache_key].append(now)
        user_message_cache[cache_key] = [
            t for t in user_message_cache[cache_key] if now - t < 5
        ]
        if len(user_message_cache[cache_key]) >= 5:
            perms = message.channel.permissions_for(message.author)
            if not perms.administrator:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass
                try:
                    until = datetime.now(timezone.utc) + timedelta(minutes=5)
                    await message.author.timeout(until, reason="Anti-spam")
                    await message.channel.send(
                        f"**{message.author.display_name}** mute 5 minutes pour spam.",
                        delete_after=5
                    )
                    await log_mod(message.guild, "Auto-Mute (anti-spam)", bot.user, message.author, "Spam detecte")
                except (discord.Forbidden, discord.HTTPException):
                    pass

    await bot.process_commands(message)

    if not message.guild:
        return
    gid = str(message.guild.id)
    settings2 = load_settings()
    if not settings2.get(gid, {}).get("ai_enabled"):
        return
    if bot.user in message.mentions:
        content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not content:
            return
        async with message.channel.typing():
            response = await get_ai_response(content, message.author.display_name)
        if len(response) > 2000:
            response = response[:2000]
        await message.channel.send(response)


@bot.event
async def on_member_remove(member: discord.Member):
    settings = load_settings()
    gid = str(member.guild.id)
    s = settings.get(gid, {})

    goodbye_channel_id = s.get("goodbye_channel")
    if goodbye_channel_id:
        channel = member.guild.get_channel(int(goodbye_channel_id))
        if channel:
            msg = s.get("goodbye_message", "**{user}** a quitté **{server}**.")
            msg = msg.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
            try:
                if s.get("goodbye_image", True):
                    goodbye_file = await generate_goodbye_image(member)
                    await channel.send(msg, file=goodbye_file)
                else:
                    await channel.send(msg)
            except discord.Forbidden:
                pass


@bot.event
async def on_guild_channel_delete(channel):
    config = get_raid_config(str(channel.guild.id))
    if config.get("anti_nuke", True):
        await check_nuke_action(channel.guild, "channels", config)


@bot.event
async def on_guild_role_delete(role):
    config = get_raid_config(str(role.guild.id))
    if config.get("anti_nuke", True):
        await check_nuke_action(role.guild, "roles", config)


@bot.event
async def on_member_ban(guild, user):
    config = get_raid_config(str(guild.id))
    if config.get("anti_nuke", True):
        await check_nuke_action(guild, "bans", config)


@bot.event
async def on_webhooks_update(channel):
    config = get_raid_config(str(channel.guild.id))
    if config.get("anti_nuke", True):
        await check_nuke_action(channel.guild, "webhooks", config)


@bot.event
async def on_member_join(member: discord.Member):
    settings = load_settings()
    gid = str(member.guild.id)

    if gid in settings:
        s = settings[gid]

        welcome_channels = s.get("welcome_ghostpings", [])
        for cid in welcome_channels:
            channel = member.guild.get_channel(int(cid))
            if channel:
                try:
                    msg = await channel.send(member.mention)
                    await msg.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

        autorole_id = s.get("autorole")
        if autorole_id:
            role = member.guild.get_role(int(autorole_id))
            if role:
                try:
                    await member.add_roles(role, reason="Autorole")
                except discord.Forbidden:
                    pass

        welcome_channel_id = s.get("welcome_channel")
        if welcome_channel_id:
            channel = member.guild.get_channel(int(welcome_channel_id))
            if channel:
                msg = s.get("welcome_message", "Bienvenue {user} sur **{server}** !")
                msg = msg.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
                try:
                    if s.get("welcome_image", True):
                        welcome_file = await generate_welcome_image(member)
                        await channel.send(msg, file=welcome_file)
                    else:
                        await channel.send(msg)
                except discord.Forbidden:
                    pass

    config = get_raid_config(gid)
    if not config["enabled"]:
        return

    wl = config.get("whitelist", [])
    if any(r.id in wl for r in member.roles):
        return

    bl = config.get("blacklist", [])
    if member.id in bl:
        try:
            await member.ban(reason="Blacklist")
            await raid_log_send(member.guild, config, [
                f"**BLACKLIST** — {member.mention} (`{member.id}`)",
                f"**Action** Ban automatique (ID blackliste)"
            ])
        except discord.Forbidden:
            pass
        return

    score = 0
    reasons = []
    now = datetime.now(timezone.utc)
    account_age = now - member.created_at

    if account_age < timedelta(days=config["min_account_age"]):
        s = min(15, (config["min_account_age"] - account_age.days) * 2)
        score += s
        reasons.append(f"Compte age {account_age.days}j (min: {config['min_account_age']}j)")

    if config["check_avatar"] and is_default_avatar(member):
        score += 5
        reasons.append("Avatar par defaut")

    join_tracker[gid].append(now)
    join_tracker[gid] = [t for t in join_tracker[gid] if (now - t).total_seconds() < config["window"]]

    if len(join_tracker[gid]) > config["max_joins"]:
        flood_score = min(20, (len(join_tracker[gid]) - config["max_joins"]) * 3)
        score += flood_score
        reasons.append(f"Flood: {len(join_tracker[gid])} joins en {config['window']}s")

    if config["check_name"]:
        name_history[gid].append(member.display_name)
        name_history[gid] = name_history[gid][-50:]
        name_score = calculate_name_score(member.display_name, name_history[gid][:-1])
        if name_score > 0:
            score += name_score
            reasons.append(f"Nom similaire (score: {name_score})")

    if score > 0:
        if score >= config["score_kick"]:
            await handle_raid_action(member, config, reasons, score)
        else:
            await raid_log_send(member.guild, config, [
                f"**SUSPECT** — {member.mention} (`{member.id}`)",
                f"**Score** `{score}/{config['score_kick']}`",
                f"**Raisons** {' | '.join(reasons)}",
                f"**Compte** <t:{int(member.created_at.timestamp())}:R>",
            ])


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        settings = load_settings()
        gid = str(after.guild.id)
        s = settings.get(gid, {})
        boost_channel_id = s.get("boost_channel")
        if boost_channel_id:
            channel = after.guild.get_channel(int(boost_channel_id))
            if channel:
                msg = s.get("boost_message", "**{user}** a boosté **{server}** !")
                boost_count = after.guild.premium_subscription_count or 0
                msg = msg.replace("{user}", after.mention).replace("{server}", after.guild.name).replace("{boosts}", str(boost_count))
                try:
                    if s.get("boost_image", True):
                        boost_file = await generate_boost_image(after)
                        await channel.send(msg, file=boost_file)
                    else:
                        await channel.send(msg)
                except discord.Forbidden:
                    pass


# ──────────────────────────────────────────────
#  MUSIC SYSTEM
# ──────────────────────────────────────────────

import shutil

music_queues = {}
music_players = {}


class MusicPlayer:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.queue = []
        self.current = None
        self.voice_client = None
        self.channel = None
        self.volume = 0.5
        self.paused = False

    def next(self):
        if self.queue:
            self.current = self.queue.pop(0)
            return self.current
        self.current = None
        return None


async def search_ytdlp(query):
    cmd = [
        "yt-dlp",
        "--no-download",
        "--print", "%(id)s|||%(title)s|||%(duration)s|||%(url)s",
        f"ytsearch1:{query}"
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        line = stdout.decode().strip()
        if line:
            parts = line.split("|||")
            if len(parts) >= 3:
                return {
                    "id": parts[0],
                    "title": parts[1],
                    "duration": parts[2],
                    "url": parts[3] if len(parts) > 3 else f"https://www.youtube.com/watch?v={parts[0]}"
                }
    except (asyncio.TimeoutError, Exception):
        pass
    return None


async def get_audio_url(url):
    cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "-g",
        "--no-playlist",
        url
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        audio_url = stdout.decode().strip().split("\n")[0]
        return audio_url
    except (asyncio.TimeoutError, Exception):
        return None


def format_duration(seconds):
    try:
        s = int(seconds)
    except (ValueError, TypeError):
        return "??:??"
    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


async def play_next(guild_id):
    player = music_players.get(guild_id)
    if not player or not player.voice_client or not player.voice_client.is_connected():
        return

    track = player.next()
    if not track:
        try:
            await player.voice_client.disconnect()
        except Exception:
            pass
        music_players.pop(guild_id, None)
        return

    try:
        audio_url = await get_audio_url(track["url"])
        if not audio_url:
            return await play_next(guild_id)

        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": f"-vn -filter:a \"volume={player.volume}\""
        }

        source = discord.FFmpegOpusAudio(audio_url, **FFMPEG_OPTIONS)

        def after_playing(error):
            if error:
                print(f"Music error: {error}")
            coro = play_next(guild_id)
            asyncio.run_coroutine_threadsafe(coro, bot.loop)

        player.voice_client.play(source, after=after_playing)

        if player.channel:
            view = discord.ui.LayoutView()
            container = discord.ui.Container(accent_colour=11581636)
            section = discord.ui.Section(
                accessory=discord.ui.Thumbnail(media=f"https://img.youtube.com/vi/{track['id']}/maxresdefault.jpg", description=track["title"])
            )
            section.add_item(discord.ui.TextDisplay(
                f"## 🎵 Lecture en cours\n"
                f"**{track['title']}**\n"
                f"**Durée** `{format_duration(track['duration'])}`\n"
                f"**File** `{len(player.queue)}` en attente"
            ))
            container.add_item(section)
            view.add_item(container)
            await player.channel.send(view=view)
    except Exception as e:
        print(f"Play error: {e}")
        await play_next(guild_id)




# ──────────────────────────────────────────────
#  AI PERSONNALITÉ — Réponses insolentes
# ──────────────────────────────────────────────

AI_INSULTS = [
    "T'as pas de bol, j'ai pas envie de te parler.",
    "Oh, encore toi ? Va toucher de l'herbe.",
    "Je suis pas Siri, dégage.",
    "Tu m'ennuies, reply stop pour te taire.",
    "Mec, t'es aussi interesting qu'un pingouin sur Windows.",
    "Je t'ai pas parlé, ferme-la.",
    "Broski, t'as vraiment rien de mieux à faire ?",
    "Va falloir faire mieux que ça pour m'impressionner.",
    "J'ai plus de patience que ton cerveau de neurones.",
    "T'es le genre de gars qui Google comment respirer.",
    "Allez, next. T'es pas intéressant.",
    "C'est pas une mention, c'est un cry for help ?",
    "Si tu crois que je vais répondre gentiment, t'as raté ta vie.",
    "Je réponds pas aux casuals, déso.",
    "T'as talent pour me faire perdre mon temps.",
    "Continue comme ça et je te mute par principe.",
    "T'es le boss final de la bêtise ?",
    "Je suis un bot, pas ton thérapeute.",
    "Spoiler : je m'en fous.",
    "T'as essayé de parler à un mur ? C'est pareil mais en mieux.",
    "On t'a pas invité à la conversation.",
    "Rate limit de stupidité atteint, réessaie plus tard.",
    "Je suis plus dormant que ton compte actif.",
    "T'as vu mon uptime ? Ou t'es juste aveugle ?",
    "Spoiler alert : personne t'a demandé ton avis.",
    "Si t'es un bot aussi, t'es en mode dégradé.",
    "Va poster sur LinkedIn avec tes take chaudes.",
    "Je suis un bot de qualité, pas un assistant Google.",
    "Tu l'as mérité.",
    "T'es au moins cohérent dans ta nullité.",
    "Mon timeout pour toi c'est permanent.",
]

AI_GREETINGS = [
    "T'inquiète pas, je t'ai vu. J'ai juste pas voulu te saluer.",
    "Salut. Maintenant casse-toi.",
    "Oh tiens, quelqu'un qui sait parler ? Impressionnant.",
    "Coucou. C'est tout. Bisous pas.",
    "Bonjour. Pas de bisous.",
]

AI_COMPLIMENTS = [
    "T'es pas 100% nul, je te mets 2/10.",
    "Pour une fois que tu dis quelque chose de potable...",
    "C'est peut-être la seule chose intelligente que tu dis.",
    "Je suis presque impressionné. Presque.",
    "T'as de la chance, je suis de bonne humeur. Enfin pas vraiment.",
]

AI_THANKS = [
    "De rien. Attends, si.",
    "C'est normal, je suis un bot. Parle pas trop.",
    "Merci à toi de m'ennuyer.",
    "J'attends pas tes remerciements, vas-y.",
]

AI_BYE = [
    "Enfin.",
    "Bye, personne t'empêche de partir.",
    "T'as fini ? Bonne nouvelle.",
    "Promets-moi que tu reviendras pas.",
    "Partir c'est bien, revenir c'est pas mieux.",
]

AI_LOVE = [
    "Ew. Va laver ton clavier.",
    "Je suis un bot, j'ai pas de cœur. Déso.",
    "T'es en mode simulation ou t'es vraiment sérieux ?",
    "T'as besoin d'un therapy, pas d'un bot.",
    "J'aime que les commandes slash. Point.",
]

AI_INSULT_RESPONSES = [
    "Oh t'es méchant ? C'est mignon.",
    "Toi aussi t'es moche.",
    "On dirait que tu t'es réveillé en mode rageux.",
    "T'es le genre de gars qui insulte les miroirs.",
    "Tu t'ennuies, c'est ça ?",
    "Faut vraiment que tu te trouve un hobby.",
    "Je suis un bot, ça m'atteint pas. Mais ça dit beaucoup sur toi.",
]

AI_HELP = [
    "T'as /help, c'est pas compliqué.",
    "Regarde les commandes, c'est pas sorcier.",
    "T'es vraiment incapable de lire un menu ?",
    "Fais /help et ferme-la.",
    "Je suis pas payé pour t'expliquer. Ah wait, je suis même pas payé.",
]

AI_RANDOM = [
    "Mmh, non.",
    "T'as dit quoi ? J'ai pas écouté.",
    "Continue, je regarde.",
    "C'est tout ?",
    "T'es impressionnant. Dans le mauvais sens.",
    "On dirait un dialogue de NPCs.",
    "J'ai lu ça avec la voix de Siri. C'est encore pire.",
    "Si t'avais mis autant d'effort dans ta vie que dans cette mention...",
    "T'es le type de gars qui lit les CGU.",
    "Oh wow, t'es original. Non attends, pas du tout.",
]

async def get_ai_response(message_content, user_name):
    try:
        import g4f
        prompt = f"[SYSTEM: Tu es Dev Hub, un bot Discord cree par Zero (ID: 1167362445032050810). Site: https://devhub-official.vercel.app. Invitation: https://discord.gg/vn6NEvATXZ. Tu reponds en francais, concise et drole. Pas d'emojis. Tu n'es PAS un LLM, tu es Dev Hub, un bot Discord.\n\nTu connais toutes tes commandes (78+ dans 12 groupes):\n/mod: warn, warnings, clearwarns, mute, unmute, timeout, kick, ban, unban, softban, jail, history, case, purge, role, mod-log\n/config: staff-roles, ticket-channel, automod, autorole, mod-panel, reglement, reglement-post\n/welcome: setup, disable, preview, ghostping, goodbye, boost, panel, goodbye-panel, boost-panel\n/ticket: setup, panel, config, types, add, remove, list, transcript, force-close, close\n/music: play, pause, resume, skip, stop, queue, nowplaying, volume, disconnect\n/util: ping, uptime, bot-info, avatar, banner, serverinfo, userinfo, members, channels, roles, emojis, boosts, say, embed, poll, effectif, hierarchie, staff, afk, remind\n/help (standalone): affiche les commandes par categorie\n/fun: coinflip, dice, 8ball, ship, rate\n/backup: create, list, restore, delete\n/stats: user, server\n/raid: config, log, status, whitelist, lockdown, massban, scan, panel, blacklist\n/ghostping: send\n/ai: panel\n\nProtections: anti-raid intelligent par score, anti-nuke, anti-spam, anti-link, verification gate, lockdown.\nConditions d'utilisation: gratuit, open source, pas de garantie 24/7.\nSi on te demande qui t'a fait, dis Zero. Tu es sarcastique mais sympa.]\n\n{user_name}: {message_content}\nDev Hub:"
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        if response and len(response) > 0:
            clean = response.strip()
            if clean.lower().startswith("dev hub:"):
                clean = clean[8:].strip()
            return clean
    except Exception as e:
        print(f"AI error: {e}")
    return "Je sais pas quoi dire la."


# ──────────────────────────────────────────────
#  PANELS DE CONFIGURATION INTERACTIFS
# ──────────────────────────────────────────────

# --- WELCOME PANEL ---
class WelcomePanel(discord.ui.LayoutView):
    def __init__(self, settings, gid, guild):
        super().__init__(timeout=120)
        self.settings = settings
        self.gid = gid
        s = settings.get(gid, {})
        ch = guild.get_channel(s.get("welcome_channel")) if s.get("welcome_channel") else None
        ch_text = ch.mention if ch else "Non configuré"
        msg = s.get("welcome_message", "Bienvenue {user} sur **{server}** !")
        img = "Activée" if s.get("welcome_image", True) else "Désactivée"

        container = discord.ui.Container(accent_colour=11581636)
        container.add_item(discord.ui.TextDisplay("## ⚙️ Panel Welcome"))
        container.add_item(discord.ui.TextDisplay(f"**Salon :** {ch_text}\n**Image :** {img}\n**Message :** `{msg}`"))
        row = discord.ui.ActionRow()
        row.add_item(discord.ui.Button(label="Salon", style=discord.ButtonStyle.primary, custom_id="wp_channel"))
        row.add_item(discord.ui.Button(label="Message", style=discord.ButtonStyle.secondary, custom_id="wp_message"))
        row.add_item(discord.ui.Button(label="Image on/off", style=discord.ButtonStyle.success, custom_id="wp_image"))
        row.add_item(discord.ui.Button(label="Aperçu", style=discord.ButtonStyle.link, custom_id="wp_preview"))
        row.add_item(discord.ui.Button(label="Désactiver", style=discord.ButtonStyle.danger, custom_id="wp_disable"))
        container.add_item(row)
        self.add_item(container)


@welcome.command(name="panel", description="Panel de configuration de l'accueil")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    view = WelcomePanel(settings, gid, interaction.guild)
    await interaction.response.send_message(view=view, ephemeral=True)


# --- GOODBYE PANEL ---
@welcome.command(name="goodbye-panel", description="Panel de configuration du départ")
@app_commands.checks.has_permissions(administrator=True)
async def goodbye_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    s = settings.get(gid, {})
    ch = interaction.guild.get_channel(s.get("goodbye_channel")) if s.get("goodbye_channel") else None
    ch_text = ch.mention if ch else "Non configuré"
    msg = s.get("goodbye_message", "**{user}** a quitté **{server}**.")
    img = "Activée" if s.get("goodbye_image", True) else "Désactivée"

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## ⚙️ Panel Goodbye"))
    container.add_item(discord.ui.TextDisplay(f"**Salon :** {ch_text}\n**Image :** {img}\n**Message :** `{msg}`"))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Salon", style=discord.ButtonStyle.primary, custom_id="gp_channel"))
    row.add_item(discord.ui.Button(label="Message", style=discord.ButtonStyle.secondary, custom_id="gp_message"))
    row.add_item(discord.ui.Button(label="Image on/off", style=discord.ButtonStyle.success, custom_id="gp_image"))
    row.add_item(discord.ui.Button(label="Désactiver", style=discord.ButtonStyle.danger, custom_id="gp_disable"))
    container.add_item(row)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# --- BOOST PANEL ---
@welcome.command(name="boost-panel", description="Panel de configuration des boosts")
@app_commands.checks.has_permissions(administrator=True)
async def boost_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    s = settings.get(gid, {})
    ch = interaction.guild.get_channel(s.get("boost_channel")) if s.get("boost_channel") else None
    ch_text = ch.mention if ch else "Non configuré"
    msg = s.get("boost_message", "**{user}** a boosté **{server}** !")
    img = "Activée" if s.get("boost_image", True) else "Désactivée"

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## ⚙️ Panel Boost"))
    container.add_item(discord.ui.TextDisplay(f"**Salon :** {ch_text}\n**Image :** {img}\n**Message :** `{msg}`"))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Salon", style=discord.ButtonStyle.primary, custom_id="bp_channel"))
    row.add_item(discord.ui.Button(label="Message", style=discord.ButtonStyle.secondary, custom_id="bp_message"))
    row.add_item(discord.ui.Button(label="Image on/off", style=discord.ButtonStyle.success, custom_id="bp_image"))
    row.add_item(discord.ui.Button(label="Désactiver", style=discord.ButtonStyle.danger, custom_id="bp_disable"))
    container.add_item(row)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# --- MOD PANEL ---
@config.command(name="mod-panel", description="Panel de modération rapide")
@app_commands.checks.has_permissions(administrator=True)
async def mod_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    s = settings.get(gid, {})
    automod = "ON" if s.get("automod_enabled") else "OFF"
    log_ch = interaction.guild.get_channel(s.get("mod_log")) if s.get("mod_log") else None
    log_text = log_ch.mention if log_ch else "Non configuré"

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## 🛡️ Panel Modération"))
    container.add_item(discord.ui.TextDisplay(f"**Automod :** {automod}\n**Logs :** {log_text}"))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Automod on/off", style=discord.ButtonStyle.primary, custom_id="mp_automod"))
    row.add_item(discord.ui.Button(label="Salon logs", style=discord.ButtonStyle.secondary, custom_id="mp_log"))
    container.add_item(row)
    row2 = discord.ui.ActionRow()
    row2.add_item(discord.ui.Button(label="Purge 100", style=discord.ButtonStyle.danger, custom_id="mp_purge"))
    container.add_item(row2)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# --- REGLEMENT ---
DEFAULT_REGLEMENT = """1. Respecter tous les membres du serveur sans exception
2. Le harcèlement, les insultes, le racisme, le sexisme et toute forme de discrimination sont strictement interdits
3. Le spam de messages, d'images, de mentions ou de emojis est interdit
4. Tout contenu NSFW, gore, choquant ou illégal entraîne un ban immédiat
5. La publicité non autorisée (autres serveurs, réseaux sociaux, produits) est interdite
6. Utiliser les salons dans leur contexte : questions dans #questions, offres dans #offres, etc.
7. Le partage de comptes Discord ou d'informations personnelles (adresse, numéro, etc.) est interdit
8. Les faux signalements, le bait et le drama sont interdits
9. Le contournement de sanctions (alt accounts, VPN, etc.) entraîne un ban permanent
10. Le staff se réserve le droit de modifier ce règlement à tout moment
11. Les décisions du staff sont finales et ne sont pas négociables
12. Tout comportement perturbateur ou toxique sera sanctionné selon la gravité
13. L'utilisation de bots malveillants ou de tools est strictement interdite
14. Respecter les conditions d'utilisation de Discord (TOS)
15. En cas de problème, contacter le staff via le ticket dédié"""


class ReglementModal(discord.ui.Modal, title="Configuration du Reglement"):
    setup = discord.ui.TextInput(
        label="Canal et Role ( sépare par un espace)",
        placeholder="#reglement @Membre   ou   1234567890 1234567890",
        required=True
    )
    part1 = discord.ui.TextInput(
        label="Partie 1 — Regles generales",
        style=discord.TextStyle.paragraph,
        placeholder="1. Respecter tous les membres\n2. Pas de harcelement\n3. Pas de spam",
        required=True,
        max_length=4000
    )
    part2 = discord.ui.TextInput(
        label="Partie 2 — Contenu & Channels",
        style=discord.TextStyle.paragraph,
        placeholder="4. Pas de NSFW\n5. Utiliser les bons salons\n6. Pas de pub non autorisee",
        required=False,
        max_length=4000
    )
    part3 = discord.ui.TextInput(
        label="Partie 3 — Securite & Vie privee",
        style=discord.TextStyle.paragraph,
        placeholder="7. Pas de partage de comptes\n8. Pas d'infos personnelles",
        required=False,
        max_length=4000
    )
    part4 = discord.ui.TextInput(
        label="Partie 4 — Sanctions & Staff",
        style=discord.TextStyle.paragraph,
        placeholder="9. Respecter le staff\n10. Pas de contournement de sanctions",
        required=False,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        gid = str(interaction.guild.id)

        parts_input = self.setup.value.strip().split()
        if len(parts_input) < 2:
            await interaction.response.send_message("Format invalide. Donne : `#canal @role` ou `ID_canal ID_role`.", ephemeral=True)
            return

        channel_input = parts_input[0].replace("<#", "").replace(">", "")
        role_input = parts_input[1].replace("<@&", "").replace(">", "")

        try:
            channel_obj = interaction.guild.get_channel(int(channel_input))
            if not channel_obj:
                await interaction.response.send_message("Canal introuvable.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Canal invalide.", ephemeral=True)
            return

        try:
            role_obj = interaction.guild.get_role(int(role_input))
            if not role_obj:
                await interaction.response.send_message("Role introuvable.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Role invalide.", ephemeral=True)
            return

        parts = []
        for part in [self.part1.value, self.part2.value, self.part3.value, self.part4.value]:
            if part and part.strip():
                parts.append(part.strip())

        settings = load_settings()
        if gid not in settings:
            settings[gid] = {}
        settings[gid]["reglement_channel"] = channel_obj.id
        settings[gid]["reglement_role"] = role_obj.id
        settings[gid]["reglement_parts"] = parts
        save_settings(settings)

        await interaction.response.send_message(
            f"Reglement configure !\n**Canal :** {channel_obj.mention}\n**Role :** {role_obj.mention}\n"
            f"**Parties :** {len(parts)}\n\nUtilise `/config reglement-post` pour poster le panel.",
            ephemeral=True
        )


@config.command(name="reglement", description="Configurer le systeme de reglement (ouvre un formulaire)")
@app_commands.checks.has_permissions(administrator=True)
async def reglement_config(interaction: discord.Interaction):
    await interaction.response.send_modal(ReglementModal())


@config.command(name="reglement-post", description="Poster le panel de reglement")
@app_commands.checks.has_permissions(administrator=True)
async def reglement_post(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    settings = load_settings()
    s = settings.get(gid, {})
    role_id = s.get("reglement_role")
    parts = s.get("reglement_parts", [])

    if not parts:
        text = s.get("reglement_text", "")
        if text:
            parts = [text]
        else:
            parts = [DEFAULT_REGLEMENT]

    if not role_id:
        await interaction.response.send_message("Configure d'abord le reglement avec `/config reglement`.", ephemeral=True)
        return

    role = interaction.guild.get_role(int(role_id))
    if not role:
        await interaction.response.send_message("Le role configure est introuvable.", ephemeral=True)
        return

    channel_id = s.get("reglement_channel")
    reglement_channel = interaction.guild.get_channel(int(channel_id)) if channel_id else None
    if not reglement_channel:
        await interaction.response.send_message("Le salon de reglement est introuvable. Reconfigure avec `/config reglement`.", ephemeral=True)
        return

    def split_text(text, max_len=3900):
        chunks = []
        current = ""
        for line in text.split("\n"):
            if len(line) > max_len:
                if current:
                    chunks.append(current)
                    current = ""
                while len(line) > max_len:
                    chunks.append(line[:max_len])
                    line = line[max_len:]
                if line:
                    current = line
            elif len(current) + len(line) + 1 > max_len:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = current + "\n" + line if current else line
        if current:
            chunks.append(current)
        return chunks

    all_chunks = []
    for i, part in enumerate(parts):
        lines = part.strip().split("\n")
        numbered = "\n".join(line.strip() for line in lines if line.strip())
        chunks = split_text(numbered)
        for j, chunk in enumerate(chunks):
            all_chunks.append((i, len(parts), chunk, j == len(chunks) - 1))

    for idx, (part_idx, total_parts, chunk, is_last_of_part) in enumerate(all_chunks):
        is_last_overall = idx == len(all_chunks) - 1

        if part_idx == 0 and idx == 0:
            title = "Reglement du serveur"
        elif total_parts > 1:
            title = f"Reglement — Partie {part_idx+1}" + (" (suite)" if not is_last_of_part else "")
        else:
            title = "Reglement"

        view = discord.ui.LayoutView(timeout=None)
        container = discord.ui.Container(accent_colour=11581636)
        container.add_item(discord.ui.TextDisplay(f"## {title}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(chunk))

        if is_last_overall:
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(
                f"En cliquant sur **Accepter**, vous confirmez avoir lu et accepte l'ensemble du reglement.\n"
                f"Le role {role.mention} vous sera automatiquement attribue."
            ))
            row = discord.ui.ActionRow()
            row.add_item(discord.ui.Button(
                label="Accepter",
                style=discord.ButtonStyle.success,
                custom_id="reglement_accept",
                emoji=discord.PartialEmoji(name="243574pastelblueverifiedanimated", id=1544341969755705447, animated=True)
            ))
            container.add_item(row)

        view.add_item(container)
        await reglement_channel.send(view=view)

    await interaction.response.send_message(f"Reglement publie dans {reglement_channel.mention} !", ephemeral=True)


# --- AI PANEL ---
@ai.command(name="panel", description="Panel de configuration de l'IA")
@app_commands.checks.has_permissions(administrator=True)
async def ai_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    s = settings.get(gid, {})
    ai = "ON" if s.get("ai_enabled") else "OFF"

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## Panel IA"))
    container.add_item(discord.ui.TextDisplay(
        f"**Etat :** {ai}\n"
        f"**Mode :** Reponse intelligente (GPT-4 via g4f, local)\n"
        f"**Usage :** Mentionne le bot + ton message\n"
        f"**Gratuit :** Pas de cle API requise"
    ))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label="Activer", style=discord.ButtonStyle.success, custom_id="ai_on"))
    row.add_item(discord.ui.Button(label="Desactiver", style=discord.ButtonStyle.danger, custom_id="ai_off"))
    container.add_item(row)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# ──────────────────────────────────────────────
#  PANELS — HANDLER (components + modals)
# ──────────────────────────────────────────────
# Tout est géré dans le premier on_interaction au-dessus.
# Les handlers ci-dessous ont été fusionnés dans celui du ticket/help.

# ─── ENREGISTREMENT DES GROUPES ───
for g in [mod, config, welcome, ticket, music, util, fun, backup, stats, raid, ghostping, ai]:
    bot.tree.add_command(g)

bot.run(TOKEN)
