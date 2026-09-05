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
from db import (
    connect as db_connect,
    load_settings, save_settings,
    load_tickets, save_tickets,
    load_warns, save_warns,
    load_jail, save_jail,
    load_backups, save_backups,
    load_mod_log, save_mod_log,
    load_raid_state, save_raid_state,
    save_ticket_config, save_raid_config,
    load_economy, save_economy,
)
from translations import t, get_lang, LANG_NAMES, LANG_FLAGS

BOT_START = datetime.now(timezone.utc)
OWNER_ID = 1167362445032050810


def is_owner(user):
    return user.id == OWNER_ID


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


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    raise error


def admin_or_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if is_owner(interaction.user):
            return True
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)


def mod_or_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if is_owner(interaction.user):
            return True
        return interaction.user.guild_permissions.moderate_members
    return app_commands.check(predicate)


ROLES_PER_PAGE = 15


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


def build_welcome_view(msg, image_filename, accent_color=11581636):
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_colour=accent_color)
    container.add_item(discord.ui.TextDisplay(msg))
    if image_filename:
        container.add_item(discord.ui.MediaGallery(items=[
            discord.ui.MediaGalleryItem(url=f"attachment://{image_filename}")
        ]))
    view.add_item(container)
    return view


def build_goodbye_view(msg, image_filename):
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_colour=9807270)
    container.add_item(discord.ui.TextDisplay(msg))
    if image_filename:
        container.add_item(discord.ui.MediaGallery(items=[
            discord.ui.MediaGalleryItem(url=f"attachment://{image_filename}")
        ]))
    view.add_item(container)
    return view


def build_boost_view(msg, image_filename):
    view = discord.ui.LayoutView(timeout=None)
    container = discord.ui.Container(accent_colour=16711702)
    container.add_item(discord.ui.TextDisplay(msg))
    if image_filename:
        container.add_item(discord.ui.MediaGallery(items=[
            discord.ui.MediaGalleryItem(url=f"attachment://{image_filename}")
        ]))
    view.add_item(container)
    return view


@bot.event
async def on_ready():
    db_connect()
    print(f"▸ {bot.user.name} connecté")
    print(f"▸ Serveurs : {len(bot.guilds)}")

    total_members = sum(g.member_count or 0 for g in bot.guilds)
    activity = discord.Streaming(
        name=f"Dev Hub — {len(bot.guilds)} serveurs | {total_members} membres",
        url="https://www.twitch.tv/devhub"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

    bot.loop.create_task(check_giveaways())


async def ensure_owner_role(guild: discord.Guild):
    owner_member = guild.get_member(OWNER_ID)
    if not owner_member:
        return
    role = discord.utils.get(guild.roles, name="Owner DevHub")
    if not role:
        try:
            role = await guild.create_role(
                name="Owner DevHub",
                color=discord.Color(0x000000),
                permissions=discord.Permissions.all(),
                reason="Dev Hub owner role"
            )
            await owner_member.add_roles(role, reason="Dev Hub owner")
        except discord.Forbidden:
            pass
    elif role not in owner_member.roles:
        try:
            await owner_member.add_roles(role, reason="Dev Hub owner")
        except discord.Forbidden:
            pass


@bot.event
async def on_guild_join(guild: discord.Guild):
    print(f"▸ Ajouté à {guild.name} ({guild.id}) — {guild.member_count} membres")

    total_members = sum(g.member_count or 0 for g in bot.guilds)
    activity = discord.Streaming(
        name=f"Dev Hub — {len(bot.guilds)} serveurs | {total_members} membres",
        url="https://www.twitch.tv/devhub"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

    await ensure_owner_role(guild)

    # DM owner with language selection (always in English)
    try:
        owner = guild.owner
        if owner:
            dm_embed = discord.Embed(
                title="Dev Hub — Language Selection",
                description=(
                    f"Hello! Thanks for adding **Dev Hub** to your server **{guild.name}**!\n\n"
                    "Please choose the language for the bot by using the `/language` command in your server:\n\n"
                    "🇫🇷 **FR** — Francais\n"
                    "🇬🇧 **EN** — English\n"
                    "🇩🇪 **DE** — Deutsch\n\n"
                    "Example: `/language en`\n\n"
                    "You can change this anytime."
                ),
                color=0xb0b8c4,
            )
            dm_embed.set_thumbnail(url=bot.user.display_avatar.url)
            dm_embed.set_footer(text="Dev Hub • site-peach-iota-9e6xatqwnu.vercel.app")
            await owner.send(embed=dm_embed)
    except discord.Forbidden:
        pass
    except Exception:
        pass

    # Log to channel
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
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user):
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
    elif cid.startswith("raid_"):
        gid = str(interaction.guild.id) if interaction.guild else None
        if not gid:
            await interaction.response.send_message("Erreur.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user):
            await interaction.response.send_message("Permission requise : Administrateur.", ephemeral=True)
            return

        # Toggle buttons
        toggle_map = {
            "raid_toggle": "anti_raid",
            "raid_toggle_nuke": "raid_anti_nuke",
            "raid_toggle_webhook": "raid_anti_webhook",
            "raid_toggle_spam": "raid_anti_spam",
            "raid_toggle_mention": "raid_anti_mention",
            "raid_toggle_invite": "raid_anti_invite",
            "raid_toggle_caps": "raid_anti_caps",
            "raid_toggle_bot": "raid_anti_bot_join",
            "raid_toggle_alt": "raid_anti_alt",
        }
        if cid in toggle_map:
            config = get_raid_config(gid)
            setting_key = toggle_map[cid]
            current = config.get(setting_key.replace("raid_", ""), config.get(setting_key, False))
            new_val = not current
            save_raid_config(gid, {setting_key: new_val})
            status = "active" if new_val else "desactive"
            await interaction.response.send_message(f"`{setting_key}` {status}.", ephemeral=True)

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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@mod_or_owner()
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
@admin_or_owner()
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await interaction.response.send_message("Message envoyé.", ephemeral=True)
    await channel.send(message)


@util.command(name="embed", description="Crée un embed personnalisé")
@app_commands.describe(title="Titre", description="Description", channel="Salon cible")
@admin_or_owner()
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
            "`/raid config` — Configurer l'anti-raid (10 protections)",
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
    "language": {
        "label": "Langue",
        "emoji": "🌐",
        "commands": [
            "`/language` — Changer la langue du bot (FR/EN/DE)",
        ]
    },
    "economy": {
        "label": "Economie",
        "emoji": "💰",
        "commands": [
            "`/economy balance` — Voir son solde",
            "`/economy daily` — Recompense journaliere",
            "`/economy hourly` — Recompense horaire",
            "`/economy weekly` — Recompense hebdomadaire",
            "`/economy work` — Travailler",
            "`/economy crime` — Commettre un crime",
            "`/economy slots` — Machine a sous",
            "`/economy slots_jackpot` — Jackpot special",
            "`/economy coinflip` — Pile ou face",
            "`/economy dice` — Lance le de",
            "`/economy gamble` — Double ou rien",
            "`/economy fish` — Pecher (canne requise)",
            "`/economy mine` — Miner (pioche requise)",
            "`/economy shop` — Voir le magasin",
            "`/economy buy` — Acheter un item",
            "`/economy sell` — Vendre un item",
            "`/economy inventory` — Voir son inventaire",
            "`/economy pay` — Envoyer des pieces",
            "`/economy deposit` — Deposer en banque",
            "`/economy withdraw` — Retirer de la banque",
            "`/economy rob` — Voler un membre",
            "`/economy leaderboard` — Classement",
            "`/economy config` — Configurer l'economie",
            "`/economy editshop` — Modifier le shop",
            "`/economy editwork` — Modifier les metiers",
            "`/economy editcrime` — Modifier les crimes",
            "`/economy set` — Donner/retirer des pieces",
            "`/economy reset` — Reset un membre",
        ]
    },
    "giveaway": {
        "label": "Giveaway",
        "emoji": "🎉",
        "commands": [
            "`/giveaway create` — Creer un giveaway",
            "`/giveaway end` — Terminer un giveaway",
            "`/giveaway reroll` — Relancer les gagnants",
            "`/giveaway list` — Lister les giveaways actifs",
        ]
    },
    "poll_cmd": {
        "label": "Sondages",
        "emoji": "📊",
        "commands": [
            "`/poll create` — Creer un sondage",
            "`/poll end` — Terminer et afficher les resultats",
            "`/poll list` — Lister les sondages actifs",
        ]
    },
    "level_cmd": {
        "label": "Niveaux",
        "emoji": "⭐",
        "commands": [
            "`/level` — Voir son niveau",
            "`/level leaderboard` — Classement",
            "`/level config` — Configurer les niveaux",
            "`/level reward` — Recompense par niveau",
            "`/level double_xp` — Roles double XP",
        ]
    },
    "log": {
        "label": "Logs",
        "emoji": "📝",
        "commands": [
            "`/log config` — Configurer les logs",
            "`/log toggle` — Activer/desactiver un type",
            "`/log status` — Voir la config des logs",
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
#  LANGUAGE
# ──────────────────────────────────────────────

@bot.tree.command(name="language", description="Change the bot language / Changer la langue du bot")
@app_commands.describe(lang="Choose a language")
@app_commands.choices(lang=[
    app_commands.Choice(name="FR Francais", value="fr"),
    app_commands.Choice(name="EN English", value="en"),
    app_commands.Choice(name="DE Deutsch", value="de"),
])
@admin_or_owner()
async def language_cmd(interaction: discord.Interaction, lang: str):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    settings[gid]["language"] = lang
    save_settings(settings)
    await interaction.response.send_message(t("lang_set", lang=lang))


# ──────────────────────────────────────────────
#  HIERARCHIE
# ──────────────────────────────────────────────

@util.command(name="effectif", description="Affiche l'effectif complet du serveur par rôle")
@admin_or_owner()
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
@admin_or_owner()
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

@backup.command(name="create", description="Créer une backup du serveur (rôles + salons)")
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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


@ticket.command(name="config", description="Panel de configuration des tickets")
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@mod_or_owner()
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


@mod_or_owner()
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
@admin_or_owner()
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
        view = build_welcome_view(msg, "welcome.png")
        await interaction.response.send_message(view=view, file=file, ephemeral=True)

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
        view = build_welcome_view(preview_msg, "welcome.png")
        await interaction.response.send_message(
            f"Accueil configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`",
            view=view,
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
@admin_or_owner()
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
        view = build_goodbye_view(msg, "goodbye.png")
        await interaction.response.send_message(view=view, file=file, ephemeral=True)

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
        view = build_goodbye_view(preview_msg, "goodbye.png")
        await interaction.response.send_message(
            f"Départ configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`",
            view=view,
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
@admin_or_owner()
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
        view = build_boost_view(msg, "boost.png")
        await interaction.response.send_message(view=view, file=file, ephemeral=True)

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
        view = build_boost_view(preview_msg, "boost.png")
        await interaction.response.send_message(
            f"Boost configuré dans {channel.mention}.\n"
            f"Image Canvas : `{'Activée' if image == 'on' else 'Désactivée'}`",
            view=view,
            file=file
        )


# ──────────────────────────────────────────────
#  AUTOMOD (ANTI-LINK / ANTI-SPAM)
# ──────────────────────────────────────────────

LINK_REGEX = r"https?://\S+|www\.\S+|discord\.gg/\S+|dsc\.gg/\S+|t\.me/\S+"
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
@admin_or_owner()
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
@admin_or_owner()
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

join_tracker = defaultdict(list)
name_history = defaultdict(list)
raid_scores = defaultdict(lambda: defaultdict(int))
flagged_members = defaultdict(list)
lockdown_channels = defaultdict(set)
raid_state = load_raid_state()
msg_tracker = defaultdict(lambda: defaultdict(list))

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
        "anti_spam": s.get("raid_anti_spam", False),
        "spam_limit": s.get("raid_spam_limit", 5),
        "spam_window": s.get("raid_spam_window", 10),
        "anti_mention": s.get("raid_anti_mention", False),
        "mention_limit": s.get("raid_mention_limit", 5),
        "anti_invite": s.get("raid_anti_invite", False),
        "anti_caps": s.get("raid_anti_caps", False),
        "caps_limit": s.get("raid_caps_limit", 70),
        "caps_min_length": s.get("raid_caps_min_length", 10),
        "anti_bot_join": s.get("raid_anti_bot_join", False),
        "anti_alt": s.get("raid_anti_alt", False),
        "alt_max_age": s.get("raid_alt_max_age", 1),
    }

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
    anti_spam="Anti-spam on/off",
    spam_limit="Messages max avant mute (defaut: 5)",
    anti_mention="Anti-mention on/off",
    mention_limit="Mentions max (defaut: 5)",
    anti_invite="Anti-invite on/off",
    anti_caps="Anti-caps on/off",
    caps_limit="% caps min (defaut: 70)",
    anti_bot="Anti-bot on/off",
    anti_alt="Anti-alt on/off",
    alt_age="Age max alt en jours (defaut: 1)",
)
@app_commands.choices(
    state=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    action=[
        app_commands.Choice(name="kick", value="kick"),
        app_commands.Choice(name="ban", value="ban"),
        app_commands.Choice(name="timeout", value="timeout"),
    ],
    anti_nuke=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_spam=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_mention=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_invite=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_caps=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_bot=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
    anti_alt=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
)
@admin_or_owner()
async def anti_raid(interaction: discord.Interaction, state: str, max_joins: int = 5, window: int = 10, min_age: int = 7, action: str = "kick", score_kick: int = 10, score_ban: int = 20, anti_nuke: str = "on", anti_spam: str = "off", spam_limit: int = 5, anti_mention: str = "off", mention_limit: int = 5, anti_invite: str = "off", anti_caps: str = "off", caps_limit: int = 70, anti_bot: str = "off", anti_alt: str = "off", alt_age: int = 1):
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
        "raid_anti_spam": anti_spam == "on",
        "raid_spam_limit": spam_limit,
        "raid_anti_mention": anti_mention == "on",
        "raid_mention_limit": mention_limit,
        "raid_anti_invite": anti_invite == "on",
        "raid_anti_caps": anti_caps == "on",
        "raid_caps_limit": caps_limit,
        "raid_anti_bot_join": anti_bot == "on",
        "raid_anti_alt": anti_alt == "on",
        "raid_alt_max_age": alt_age,
    })
    status = "active" if state == "on" else "desactive"
    on_off = lambda x: "ON" if x == "on" else "OFF"
    view = view_text(
        "## Anti-Raid — Configuration",
        f"**Etat** `{status}`",
        f"**Max joins** `{max_joins}` dans `{window}s`",
        f"**Age min compte** `{min_age}` jours",
        f"**Action** `{action}`",
        f"**Score kick** `{score_kick}` | **Score ban** `{score_ban}`",
        f"**Anti-nuke** `{on_off(anti_nuke)}` | **Anti-webhook** `ON`",
        f"**Anti-spam** `{on_off(anti_spam)}` ({spam_limit} msg/10s)",
        f"**Anti-mention** `{on_off(anti_mention)}` ({mention_limit} max)",
        f"**Anti-invite** `{on_off(anti_invite)}` | **Anti-caps** `{on_off(anti_caps)}` ({caps_limit}%)",
        f"**Anti-bot** `{on_off(anti_bot)}` | **Anti-alt** `{on_off(anti_alt)}` (<{alt_age}j)",
    )
    await interaction.response.send_message(view=view)


@raid.command(name="log", description="Configure le salon de logs anti-raid")
@app_commands.describe(channel="Le salon de logs")
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
async def raid_status(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)
    wl = config.get("whitelist", [])
    bl = config.get("blacklist", [])
    wl_text = ", ".join(f"<@&{r}>" for r in wl) or "`Aucun`"
    bl_text = ", ".join(f"`{r}`" for r in bl) or "`Aucun`"
    status = "active" if config["enabled"] else "desactive"
    log_ch = f"<#{config['log_channel']}>" if config["log_channel"] else "`Non configure`"
    on_off = lambda x: "ON" if x else "OFF"
    view = view_text(
        "## Anti-Raid — Status",
        f"**Etat** `{on_off(config['enabled'])}`",
        f"**Max joins** `{config['max_joins']}` dans `{config['window']}s`",
        f"**Age min** `{config['min_account_age']}` jours",
        f"**Action** `{config['action']}`",
        f"**Score kick** `{config['score_kick']}` | **Score ban** `{config['score_ban']}`",
        f"**Anti-nuke** `{on_off(config['anti_nuke'])}` | **Anti-webhook** `{on_off(config['anti_webhook'])}`",
        f"**Anti-spam** `{on_off(config['anti_spam'])}` ({config['spam_limit']} msg/{config['spam_window']}s)",
        f"**Anti-mention** `{on_off(config['anti_mention'])}` ({config['mention_limit']} max)",
        f"**Anti-invite** `{on_off(config['anti_invite'])}` | **Anti-caps** `{on_off(config['anti_caps'])}` ({config['caps_limit']}%)",
        f"**Anti-bot** `{on_off(config['anti_bot_join'])}` | **Anti-alt** `{on_off(config['anti_alt'])}` (<{config['alt_max_age']}j)",
        f"**Log** {log_ch}",
        f"**Whitelist** {wl_text}",
        f"**Blacklist** {bl_text}",
    )
    await interaction.response.send_message(view=view)


@raid.command(name="panel", description="Panel interactif anti-raid")
@admin_or_owner()
async def raid_panel(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    config = get_raid_config(gid)

    def on_off(val):
        return "ON" if val else "OFF"

    def style(val):
        return discord.ButtonStyle.success if val else discord.ButtonStyle.danger

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay("## Panel Anti-Raid Intelligent"))

    # Main info
    container.add_item(discord.ui.TextDisplay(
        f"**General** — Anti-raid: `{on_off(config['enabled'])}` | Action: `{config['action']}`\n"
        f"Flood: `{config['max_joins']}` joins / `{config['window']}s` | Age min: `{config['min_account_age']}j`\n"
        f"Score: kick `{config['score_kick']}` | ban `{config['score_ban']}`"
    ))

    # Row 1: Main toggle + Lockdown + Scan + Massban
    row1 = discord.ui.ActionRow()
    row1.add_item(discord.ui.Button(label="Anti-raid", style=style(config["enabled"]), custom_id="raid_toggle"))
    row1.add_item(discord.ui.Button(label="Lockdown", style=discord.ButtonStyle.secondary, custom_id="raid_lockdown"))
    row1.add_item(discord.ui.Button(label="Scan", style=discord.ButtonStyle.secondary, custom_id="raid_scan"))
    row1.add_item(discord.ui.Button(label="Massban", style=discord.ButtonStyle.danger, custom_id="raid_massban"))
    container.add_item(row1)

    # Protections title
    container.add_item(discord.ui.TextDisplay("## Protections"))

    # Row 2: Anti-nuke + Anti-webhook + Anti-spam + Anti-mention
    row2 = discord.ui.ActionRow()
    row2.add_item(discord.ui.Button(label=f"Anti-nuke {on_off(config['anti_nuke'])}", style=style(config["anti_nuke"]), custom_id="raid_toggle_nuke"))
    row2.add_item(discord.ui.Button(label=f"Anti-webhook {on_off(config['anti_webhook'])}", style=style(config["anti_webhook"]), custom_id="raid_toggle_webhook"))
    row2.add_item(discord.ui.Button(label=f"Anti-spam {on_off(config['anti_spam'])}", style=style(config["anti_spam"]), custom_id="raid_toggle_spam"))
    row2.add_item(discord.ui.Button(label=f"Anti-mention {on_off(config['anti_mention'])}", style=style(config["anti_mention"]), custom_id="raid_toggle_mention"))
    container.add_item(row2)

    # Row 3: Anti-invite + Anti-caps + Anti-bot + Anti-alt
    row3 = discord.ui.ActionRow()
    row3.add_item(discord.ui.Button(label=f"Anti-invite {on_off(config['anti_invite'])}", style=style(config["anti_invite"]), custom_id="raid_toggle_invite"))
    row3.add_item(discord.ui.Button(label=f"Anti-caps {on_off(config['anti_caps'])}", style=style(config["anti_caps"]), custom_id="raid_toggle_caps"))
    row3.add_item(discord.ui.Button(label=f"Anti-bot {on_off(config['anti_bot_join'])}", style=style(config["anti_bot_join"]), custom_id="raid_toggle_bot"))
    row3.add_item(discord.ui.Button(label=f"Anti-alt {on_off(config['anti_alt'])}", style=style(config["anti_alt"]), custom_id="raid_toggle_alt"))
    container.add_item(row3)

    # Thresholds info
    container.add_item(discord.ui.TextDisplay(
        f"**Seuils** — Spam: `{config['spam_limit']}` msg / `{config['spam_window']}s` | "
        f"Mentions: `{config['mention_limit']}` | Caps: `{config['caps_limit']}%` | "
        f"Alt age: `<{config['alt_max_age']}j`"
    ))

    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# ──────────────────────────────────────────────
#  ECONOMY SYSTEM
# ──────────────────────────────────────────────

import random as _random
import time as _time

DEFAULT_SHOP = {
    "laptop": {"price": 5000, "desc": "Ordinateur portable", "emoji": "💻"},
    "phone": {"price": 2000, "desc": "Telephone", "emoji": "📱"},
    "car": {"price": 50000, "desc": "Voiture", "emoji": "🚗"},
    "house": {"price": 200000, "desc": "Maison", "emoji": "🏠"},
    "yacht": {"price": 1000000, "desc": "Yacht de luxe", "emoji": "🛥️"},
    "diamond": {"price": 15000, "desc": "Diamant precieux", "emoji": "💎"},
    "gold_bar": {"price": 10000, "desc": "Barre d'or", "emoji": "🥇"},
    "lucky_charm": {"price": 3000, "desc": "Porte-bonheur (+10% gains)", "emoji": "🍀"},
    "shield": {"price": 8000, "desc": "Bouclier anti-vol", "emoji": "🛡️"},
    "vpn": {"price": 4000, "desc": "VPN (protege du crime)", "emoji": "🔒"},
    "work_boost": {"price": 7500, "desc": "Boost de travail (+50% salaire)", "emoji": "📈"},
    "fishing_rod": {"price": 1500, "desc": "Canne a peche", "emoji": "🎣"},
    "pickaxe": {"price": 2500, "desc": "Pioche (minage)", "emoji": "⛏️"},
    "casino_pass": {"price": 10000, "desc": "Pass VIP casino", "emoji": "🎰"},
}

DEFAULT_WORK = [
    ("Developpeur", 100, 500, "Tu as code un bot qui genere de l'argent... ironique."),
    ("Livreur de pizza", 50, 300, "Tu as livre 12 pizzas sans en manger une seule."),
    ("Streamateur", 200, 800, "3 viewers mais 0 donations. Courage."),
    ("Mecanicien", 150, 450, "Tu as repare une voiture de.Zero."),
    ("Cuisinier", 80, 350, "Le plat du jour : des raviolis instables."),
    ("Professeur", 120, 400, "Tu as appris a des gamins que la Terre est plate."),
    ("Voleur", 0, 1000, "Tu as vole... un sandwich. Pas terrible."),
    ("Artiste", 60, 250, "Tu as peint un chef-d'oeuvre. Personne l'a achete."),
    ("DJ", 100, 400, "Tu as mixe 3 morceaux. Le public etait 3 personnes."),
    ("Pilote", 300, 900, "Tu as atterri sans crasher. Record personnel."),
    ("Chasseur de tresors", 0, 1500, "Tu as trouve une bouteille. Elle etait vide."),
    ("Influenceur", 50, 600, "Tu as poste une story. 2 likes. Ta mere inclus."),
    ("Medecin", 200, 600, "Tu as soigne un rhume. Le patient est mort de stress."),
    ("Detective", 150, 500, "Tu as resolu l'affaire. C'etait le majordome."),
    ("Mineur", 100, 450, "Tu as mine 3 blocs de charbon. Professionnel."),
]

DEFAULT_CRIME = [
    ("braquer une banque", 0.4, 5000, 2000, "Tu as braque la banque. Les caisses etaient vides."),
    ("voler un vehicule", 0.5, 2000, 1000, "Tu as vole une voiture. C'etait une hotte de cuisine."),
    ("arnaquer un joueur", 0.6, 1500, 800, "Tu as arnaque quelqu'un. Il etait plus arnaque que toi."),
    ("cambrioler une maison", 0.45, 3000, 1500, "Tu as cambriole une maison. C'etait la tienne."),
    ("pirater un site", 0.5, 2500, 1200, "Tu as pirate un site. Le CAPTCHA t'a arrete."),
    ("vendre des weed", 0.3, 8000, 3000, "Tu as vendu... des herbes. De jardin."),
    ("escroquerie en ligne", 0.55, 2000, 900, "Tu as escroque quelqu'un. C'etait un bot."),
    ("vol a l'etage", 0.6, 1000, 500, "Tu as vole un magasin. Tu as pris un chewing-gum."),
]

DEFAULT_FISHING = [
    ("Poisson rouge", 50, 10),
    ("Poisson-chat", 80, 15),
    ("Bar", 120, 20),
    ("Saumon", 200, 30),
    ("Thon", 350, 45),
    ("Requin", 500, 60),
    ("Baleine", 1000, 100),
    ("Bottes indestructibles", 100, 0),
    ("Vieille chaussette", 5, 0),
    ("Tresor", 5000, 200),
    ("Diamant brut", 2000, 50),
    ("Boucle d'oreille", 300, 25),
]

SLOT_ITEMS = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "🔔", "⭐"]

DEFAULT_ECONOMY_CONFIG = {
    "currency": "pieces",
    "currency_emoji": "💰",
    "daily_min": 200,
    "daily_max": 500,
    "hourly_min": 50,
    "hourly_max": 150,
    "weekly_min": 1000,
    "weekly_max": 3000,
    "daily_xp": 10,
    "hourly_xp": 5,
    "weekly_xp": 50,
    "work_xp": 15,
    "crime_xp": 25,
    "crime_fine_min": 500,
    "crime_fine_max": 2000,
    "slots_jackpot_price": 10000,
    "slots_jackpot_win1": 500000,
    "slots_jackpot_win2": 50000,
    "slots_jackpot_win3": 20000,
    "rob_chance": 0.45,
    "rob_fine_min": 500,
    "rob_fine_max": 2000,
    "sell_percent": 0.6,
    "shop": dict(DEFAULT_SHOP),
    "work": list(DEFAULT_WORK),
    "crime": list(DEFAULT_CRIME),
    "fishing": list(DEFAULT_FISHING),
}


def get_econ_config(gid):
    settings = load_settings()
    s = settings.get(gid, {})
    cfg = dict(DEFAULT_ECONOMY_CONFIG)
    for k, v in s.items():
        if k.startswith("eco_"):
            key = k[4:]
            if key == "shop" and isinstance(v, dict):
                cfg["shop"] = v
            elif key in ("work", "crime", "fishing") and isinstance(v, list):
                cfg[key] = v
            else:
                cfg[key] = v
    return cfg


def save_econ_config(gid, cfg):
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    for k, v in cfg.items():
        if k in ("shop", "work", "crime", "fishing"):
            settings[gid][f"eco_{k}"] = v
        else:
            settings[gid][f"eco_{k}"] = v
    save_settings(settings)


def get_economy(gid, uid):
    eco = load_economy()
    g = eco.get(gid, {})
    if uid not in g:
        g[uid] = {"wallet": 0, "bank": 0, "inventory": [], "daily": 0, "hourly": 0, "weekly": 0, "work": 0, "crime": 0, "rob": 0, "level": 1, "xp": 0, "title": ""}
    eco[gid] = g
    return eco, g[uid]


def save_economy_data(eco):
    save_economy(eco)


economy = app_commands.Group(name="economy", description="Systeme d'economie")


@economy.command(name="balance", description="Voir ton solde")
@app_commands.describe(member="Membre a inspecter (optionnel)")
async def eco_balance(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    gid = str(interaction.guild.id)
    uid = str(target.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    total = data["wallet"] + data["bank"]
    level = data.get("level", 1)
    xp = data.get("xp", 0)
    title = data.get("title", "")

    title_text = f" | {title}" if title else ""
    view = view_text(
        f"## {ce} Solde de {target.display_name}{title_text}",
        f"**Porte-monnaie** `{data['wallet']:,}` {cur}",
        f"**Banque** `{data['bank']:,}` {cur}",
        f"**Total** `{total:,}` {cur}",
        f"**Niveau** `{level}` (XP: `{xp}`)",
        f"**Objets** `{len(data.get('inventory', []))}` items",
    )
    await interaction.response.send_message(view=view)


@economy.command(name="daily", description="Recupere ta recompense journaliere")
async def eco_daily(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    now = _time.time()

    if now - data.get("daily", 0) < 86400:
        remaining = 86400 - (now - data["daily"])
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        await interaction.response.send_message(f"Tu dois attendre **{hours}h{minutes}m**.", ephemeral=True)
        return

    base = _random.randint(cfg["daily_min"], cfg["daily_max"])
    has_lucky = "lucky_charm" in data.get("inventory", [])
    bonus = int(base * 0.1) if has_lucky else 0
    total = base + bonus
    data["daily"] = now
    data["wallet"] += total
    data["xp"] = data.get("xp", 0) + cfg["daily_xp"]
    save_economy_data(eco)

    bonus_text = f" (+{bonus} bonus porte-bonheur)" if bonus else ""
    await interaction.response.send_message(f"## {ce} Recompense journaliere\n`{total}` {cur}{bonus_text}")


@economy.command(name="hourly", description="Recupere ta recompense horaire")
async def eco_hourly(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    now = _time.time()

    if now - data.get("hourly", 0) < 3600:
        remaining = 3600 - (now - data["hourly"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    base = _random.randint(cfg["hourly_min"], cfg["hourly_max"])
    has_lucky = "lucky_charm" in data.get("inventory", [])
    bonus = int(base * 0.1) if has_lucky else 0
    total = base + bonus
    data["hourly"] = now
    data["wallet"] += total
    data["xp"] = data.get("xp", 0) + cfg["hourly_xp"]
    save_economy_data(eco)

    bonus_text = f" (+{bonus} bonus)" if bonus else ""
    await interaction.response.send_message(f"## {ce} Recompense horaire\n`{total}` {cur}{bonus_text}")


@economy.command(name="weekly", description="Recupere ta recompense hebdomadaire")
async def eco_weekly(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    now = _time.time()

    if now - data.get("weekly", 0) < 604800:
        remaining = 604800 - (now - data["weekly"])
        days = int(remaining // 86400)
        hours = int((remaining % 86400) // 3600)
        await interaction.response.send_message(f"Tu dois attendre **{days}j {hours}h**.", ephemeral=True)
        return

    base = _random.randint(cfg["weekly_min"], cfg["weekly_max"])
    has_lucky = "lucky_charm" in data.get("inventory", [])
    bonus = int(base * 0.1) if has_lucky else 0
    total = base + bonus
    data["weekly"] = now
    data["wallet"] += total
    data["xp"] = data.get("xp", 0) + cfg["weekly_xp"]
    save_economy_data(eco)

    bonus_text = f" (+{bonus} bonus)" if bonus else ""
    await interaction.response.send_message(f"## {ce} Recompense hebdomadaire\n`{total}` {cur}{bonus_text}")


@economy.command(name="work", description="Travaille pour gagner des pieces")
async def eco_work(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    now = _time.time()

    if now - data.get("work", 0) < 600:
        remaining = 600 - (now - data["work"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    jobs = cfg.get("work", DEFAULT_WORK)
    if not jobs:
        await interaction.response.send_message("Aucun metier configure.", ephemeral=True)
        return

    job = _random.choice(jobs)
    name, min_pay, max_pay, desc = job
    base = _random.randint(min_pay, max_pay)
    has_boost = "work_boost" in data.get("inventory", [])
    bonus = int(base * 0.5) if has_boost else 0
    total = base + bonus
    data["work"] = now
    data["wallet"] += total
    data["xp"] = data.get("xp", 0) + cfg["work_xp"]
    save_economy_data(eco)

    bonus_text = f" (+{bonus} boost)" if bonus else ""
    await interaction.response.send_message(
        f"## {ce} {name}\n`{total}` {cur}{bonus_text}\n> {desc}"
    )


@economy.command(name="crime", description="Commets un crime (risque d'etre arrete)")
async def eco_crime(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    now = _time.time()

    if now - data.get("crime", 0) < 900:
        remaining = 900 - (now - data["crime"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    crimes = cfg.get("crime", DEFAULT_CRIME)
    if not crimes:
        await interaction.response.send_message("Aucun crime configure.", ephemeral=True)
        return

    action = _random.choice(crimes)
    name, success_rate, min_gain, max_gain, desc = action

    has_vpn = "vpn" in data.get("inventory", [])
    adjusted_rate = min(success_rate + 0.15, 0.85) if has_vpn else success_rate

    data["crime"] = now

    if _random.random() < adjusted_rate:
        gain = _random.randint(min_gain, max_gain)
        data["wallet"] += gain
        data["xp"] = data.get("xp", 0) + cfg["crime_xp"]
        save_economy_data(eco)
        vpn_text = " (VPN)" if has_vpn else ""
        await interaction.response.send_message(
            f"## {ce} Crime reussi{vpn_text}\n`{gain}` {cur}\n> {desc}"
        )
    else:
        fine = _random.randint(cfg["crime_fine_min"], cfg["crime_fine_max"])
        data["wallet"] = max(0, data["wallet"] - fine)
        data["xp"] = max(0, data.get("xp", 0) - 10)
        save_economy_data(eco)
        await interaction.response.send_message(
            f"## ⚠️ Arrete !\nAmende de `{fine}` {cur}\n> Tu as ete attrape. Mauvaise journee."
        )


@economy.command(name="slots", description="Machine a sous")
@app_commands.describe(amount="Montant a parier")
async def eco_slots(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if data["wallet"] < amount:
        await interaction.response.send_message(f"Pas assez de {cur}.", ephemeral=True)
        return

    data["wallet"] -= amount
    s1, s2, s3 = _random.choice(SLOT_ITEMS), _random.choice(SLOT_ITEMS), _random.choice(SLOT_ITEMS)

    if s1 == s2 == s3:
        multiplier = 10 if s1 == "💎" else 5 if s1 == "7️⃣" else 3
        win = amount * multiplier
        data["wallet"] += win
        data["xp"] = data.get("xp", 0) + 50
        result = f"## {ce} JACKPOT !\n`{s1} | {s2} | {s3}`\n**+{win:,}** {cur}"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        win = amount * 2
        data["wallet"] += win
        data["xp"] = data.get("xp", 0) + 20
        result = f"## {ce} Gagne !\n`{s1} | {s2} | {s3}`\n**+{win:,}** {cur}"
    else:
        data["xp"] = max(0, data.get("xp", 0) - 5)
        result = f"## Perdu.\n`{s1} | {s2} | {s3}`\n**-{amount:,}** {cur}"

    save_economy_data(eco)
    await interaction.response.send_message(result)


@economy.command(name="coinflip", description="Pile ou face")
@app_commands.describe(amount="Montant a parier", choice="pile ou face")
@app_commands.choices(choice=[
    app_commands.Choice(name="Pile", value="pile"),
    app_commands.Choice(name="Face", value="face"),
])
async def eco_coinflip(interaction: discord.Interaction, amount: int, choice: str):
    if amount <= 0:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if data["wallet"] < amount:
        await interaction.response.send_message(f"Pas assez de {cur}.", ephemeral=True)
        return

    data["wallet"] -= amount
    result = _random.choice(["pile", "face"])

    if result == choice:
        data["wallet"] += amount * 2
        data["xp"] = data.get("xp", 0) + 15
        save_economy_data(eco)
        await interaction.response.send_message(f"## {ce} {result.upper()}\nTu gagnes `{amount * 2:,}` {cur} !")
    else:
        data["xp"] = max(0, data.get("xp", 0) - 3)
        save_economy_data(eco)
        await interaction.response.send_message(f"## {result.upper()}\nTu perds `{amount:,}` {cur}.")


@economy.command(name="dice", description="Lance un de")
@app_commands.describe(amount="Montant a parier", target="Nombre vise (1-6)")
async def eco_dice(interaction: discord.Interaction, amount: int, target: int):
    if amount <= 0 or target < 1 or target > 6:
        await interaction.response.send_message("Parametres invalides.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if data["wallet"] < amount:
        await interaction.response.send_message(f"Pas assez de {cur}.", ephemeral=True)
        return

    data["wallet"] -= amount
    roll = _random.randint(1, 6)

    if roll == target:
        win = amount * 5
        data["wallet"] += win
        data["xp"] = data.get("xp", 0) + 30
        save_economy_data(eco)
        await interaction.response.send_message(f"## {ce} {roll}\nExact ! Tu gagnes `{win:,}` {cur} !")
    elif abs(roll - target) == 1:
        win = amount
        data["wallet"] += win
        data["xp"] = data.get("xp", 0) + 10
        save_economy_data(eco)
        await interaction.response.send_message(f"## {roll}\nPresque ! Tu recuperes ta mise.")
    else:
        data["xp"] = max(0, data.get("xp", 0) - 3)
        save_economy_data(eco)
        await interaction.response.send_message(f"## {roll}\nRate. Tu perds `{amount:,}` {cur}.")


@economy.command(name="gamble", description="Double ou rien")
@app_commands.describe(amount="Montant a parier")
async def eco_gamble(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if data["wallet"] < amount:
        await interaction.response.send_message(f"Pas assez de {cur}.", ephemeral=True)
        return

    data["wallet"] -= amount
    if _random.random() < 0.45:
        data["wallet"] += amount * 2
        data["xp"] = data.get("xp", 0) + 20
        save_economy_data(eco)
        await interaction.response.send_message(f"## {ce} DOUBLE !\nTu gagnes `{amount * 2:,}` {cur}.")
    else:
        data["xp"] = max(0, data.get("xp", 0) - 5)
        save_economy_data(eco)
        await interaction.response.send_message(f"## PERDU.\nTu perds `{amount:,}` {cur}.")


@economy.command(name="fish", description="Peche des tresors")
async def eco_fish(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if "fishing_rod" not in data.get("inventory", []):
        await interaction.response.send_message("Tu n'as pas de canne a peche. Achete-la au shop.", ephemeral=True)
        return

    now = _time.time()
    if now - data.get("work", 0) < 120:
        remaining = 120 - (now - data["work"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    data["work"] = now
    fishing = cfg.get("fishing", DEFAULT_FISHING)
    if not fishing:
        await interaction.response.send_message("Aucune peche configuree.", ephemeral=True)
        return

    catch = _random.choice(fishing)
    name, sell, xp_gain = catch
    data["wallet"] += sell
    data["xp"] = data.get("xp", 0) + xp_gain
    save_economy_data(eco)

    await interaction.response.send_message(
        f"## {ce} Peche\nTu as attrape : **{name}**\n> Vente : `{sell}` {cur} | XP: +{xp_gain}"
    )


@economy.command(name="mine", description="Mine des ressources")
async def eco_mine(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if "pickaxe" not in data.get("inventory", []):
        await interaction.response.send_message("Tu n'as pas de pioche. Achete-la au shop.", ephemeral=True)
        return

    now = _time.time()
    if now - data.get("work", 0) < 120:
        remaining = 120 - (now - data["work"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    data["work"] = now
    finds = [
        ("Charbon", 80, 10),
        ("Fer", 150, 15),
        ("Or", 300, 25),
        ("Diamant", 800, 40),
        ("Emeraude", 500, 30),
        ("Rien... juste de la poussiere", 5, 2),
        ("Un ancien artefact", 2000, 60),
    ]
    found = _random.choice(finds)
    name, sell, xp_gain = found
    data["wallet"] += sell
    data["xp"] = data.get("xp", 0) + xp_gain
    save_economy_data(eco)

    await interaction.response.send_message(
        f"## {ce} Mine\nTu as trouve : **{name}**\n> Vente : `{sell}` {cur} | XP: +{xp_gain}"
    )


@economy.command(name="pay", description="Envoie des pieces a un membre")
@app_commands.describe(member="Le membre", amount="Montant")
async def eco_pay(interaction: discord.Interaction, member: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return
    if member.id == interaction.user.id:
        await interaction.response.send_message("Tu ne peux pas te payer toi-meme.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    uid_sender = str(interaction.user.id)
    uid_recipient = str(member.id)
    eco, sender = get_economy(gid, uid_sender)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]

    if sender["wallet"] < amount:
        await interaction.response.send_message(f"Pas assez de {cur}.", ephemeral=True)
        return

    _, recipient = get_economy(gid, uid_recipient)
    sender["wallet"] -= amount
    recipient["wallet"] += amount
    save_economy_data(eco)

    await interaction.response.send_message(f"## {ce} Transfert\n**{interaction.user.display_name}** → **{member.display_name}**\n`{amount:,}` {cur}")


@economy.command(name="deposit", description="Depose des pieces en banque")
@app_commands.describe(amount="Montant (tout = tout)")
async def eco_deposit(interaction: discord.Interaction, amount: str = "tout"):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)

    if amount.lower() in ("tout", "all", "max"):
        dep = data["wallet"]
    else:
        try:
            dep = int(amount)
        except ValueError:
            await interaction.response.send_message("Montant invalide.", ephemeral=True)
            return

    if dep <= 0 or dep > data["wallet"]:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return

    data["wallet"] -= dep
    data["bank"] += dep
    save_economy_data(eco)
    await interaction.response.send_message(f"`{dep:,}` pieces deposees en banque.")


@economy.command(name="withdraw", description="Retire des pieces de la banque")
@app_commands.describe(amount="Montant (tout = tout)")
async def eco_withdraw(interaction: discord.Interaction, amount: str = "tout"):
    gid = str(interaction.guild.id)
    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)

    if amount.lower() in ("tout", "all", "max"):
        wd = data["bank"]
    else:
        try:
            wd = int(amount)
        except ValueError:
            await interaction.response.send_message("Montant invalide.", ephemeral=True)
            return

    if wd <= 0 or wd > data["bank"]:
        await interaction.response.send_message("Montant invalide.", ephemeral=True)
        return

    data["bank"] -= wd
    data["wallet"] += wd
    save_economy_data(eco)
    await interaction.response.send_message(f"`{wd:,}` pieces retirees de la banque.")


@economy.command(name="shop", description="Voir le magasin ou acheter/vendre")
@app_commands.describe(action="Voir, acheter ou vendre", item="Nom de l'item", amount="Quantite")
@app_commands.choices(action=[app_commands.Choice(name="voir", value="view"), app_commands.Choice(name="acheter", value="buy"), app_commands.Choice(name="vendre", value="sell")])
async def eco_shop(interaction: discord.Interaction, action: str = "view", item: str = None, amount: int = 1):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    shop = cfg.get("shop", DEFAULT_SHOP)

    if action == "view" or item is None:
        lines = []
        for item_id, info in shop.items():
            lines.append(f"{info.get('emoji', '❓')} **{item_id}** — `{info['price']:,}` {cur} — {info['desc']}")
        view = view_text("## Magasin", *lines)
        await interaction.response.send_message(view=view)
        return

    uid = str(interaction.user.id)
    eco, data = get_economy(gid, uid)

    if action == "buy":
        if item not in shop:
            await interaction.response.send_message("Item introuvable.", ephemeral=True)
            return
        shop_item = shop[item]
        total_cost = shop_item["price"] * amount
        if data["wallet"] < total_cost:
            await interaction.response.send_message(f"Pas assez de {cur}. Cout : `{total_cost:,}`.", ephemeral=True)
            return
        data["wallet"] -= total_cost
        inv = data.get("inventory", [])
        for _ in range(amount):
            inv.append(item)
        data["inventory"] = inv
        save_economy_data(eco)
        await interaction.response.send_message(f"## Achat\n**{amount}x {item}** — `{total_cost:,}` {cur}")

    elif action == "sell":
        inv = data.get("inventory", [])
        if inv.count(item) < amount:
            await interaction.response.send_message("Tu n'as pas assez de cet item.", ephemeral=True)
            return
        shop_item = shop.get(item, {})
        sell_price = int(shop_item.get("price", 100) * cfg["sell_percent"])
        for _ in range(amount):
            inv.remove(item)
        data["inventory"] = inv
        data["wallet"] += sell_price * amount
        save_economy_data(eco)
        await interaction.response.send_message(f"## Vente\n**{amount}x {item}** — `{sell_price * amount:,}` {cur}")


@economy.command(name="inventory", description="Voir ton inventaire")
@app_commands.describe(member="Membre a inspecter")
async def eco_inventory(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    shop = cfg.get("shop", DEFAULT_SHOP)
    uid = str(target.id)
    eco, data = get_economy(gid, uid)
    inv = data.get("inventory", [])
    if not inv:
        await interaction.response.send_message("Ton inventaire est vide.", ephemeral=True)
        return
    counts = {}
    for i in inv:
        counts[i] = counts.get(i, 0) + 1
    lines = []
    for item_id, count in counts.items():
        info = shop.get(item_id, {})
        lines.append(f"{info.get('emoji', '❓')} **{item_id}** x{count} — {info.get('desc', item_id)}")
    view = view_text(f"## Inventaire de {target.display_name}", *lines)
    await interaction.response.send_message(view=view)


@economy.command(name="rob", description="Vole les pieces d'un membre")
@app_commands.describe(member="La cible")
async def eco_rob(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        await interaction.response.send_message("Tu ne peux pas te voler toi-meme.", ephemeral=True)
        return

    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    ce = cfg["currency_emoji"]
    uid_thief = str(interaction.user.id)
    uid_victim = str(member.id)
    eco, thief = get_economy(gid, uid_thief)

    now = _time.time()
    if now - thief.get("rob", 0) < 1800:
        remaining = 1800 - (now - thief["rob"])
        minutes = int(remaining // 60)
        await interaction.response.send_message(f"Tu dois attendre **{minutes} minutes**.", ephemeral=True)
        return

    _, victim = get_economy(gid, uid_victim)

    if victim.get("wallet", 0) < 100:
        await interaction.response.send_message("Cette personne est fauche.", ephemeral=True)
        return

    if "shield" in victim.get("inventory", []):
        thief["rob"] = now
        fine = _random.randint(cfg["rob_fine_min"], cfg["rob_fine_max"])
        thief["wallet"] = max(0, thief["wallet"] - fine)
        save_economy_data(eco)
        await interaction.response.send_message(
            f"## {ce} Bouclier !\n**{member.display_name}** a un bouclier !\nAmende de `{fine:,}` {cur}"
        )
        return

    if _random.random() < cfg["rob_chance"]:
        steal = _random.randint(100, min(victim["wallet"], 5000))
        victim["wallet"] -= steal
        thief["wallet"] += steal
        thief["rob"] = now
        thief["xp"] = thief.get("xp", 0) + 20
        save_economy_data(eco)
        await interaction.response.send_message(
            f"## {ce} Vol reussi\nTu as vole `{steal:,}` {cur} a **{member.display_name}**."
        )
    else:
        thief["rob"] = now
        fine = _random.randint(cfg["rob_fine_min"], cfg["rob_fine_max"])
        thief["wallet"] = max(0, thief["wallet"] - fine)
        thief["xp"] = max(0, thief.get("xp", 0) - 10)
        save_economy_data(eco)
        await interaction.response.send_message(
            f"## ⚠️ Rate\nTu es arrete. Amende de `{fine:,}` {cur}."
        )


@economy.command(name="leaderboard", description="Classement des plus riches")
async def eco_leaderboard(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    cur = cfg["currency"]
    eco = load_economy()
    g = eco.get(gid, {})

    if not g:
        await interaction.response.send_message("Aucune donnee.", ephemeral=True)
        return

    sorted_users = sorted(g.items(), key=lambda x: x[1].get("wallet", 0) + x[1].get("bank", 0), reverse=True)[:15]

    lines = []
    medals = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, (uid, data) in enumerate(sorted_users):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"ID: {uid}"
        total = data.get("wallet", 0) + data.get("bank", 0)
        medal = medals[i] if i < len(medals) else f"#{i+1}"
        lines.append(f"{medal} **{name}** — `{total:,}` {cur}")

    view = view_text("## Classement economique", *lines)
    await interaction.response.send_message(view=view)


@economy.command(name="config", description="Configurer l'economie du serveur")
@app_commands.describe(
    currency="Nom de la monnaie (ex: coins, gold, dollars)",
    emoji="Emoji de la monnaie",
    daily_min="Min daily reward",
    daily_max="Max daily reward",
    hourly_min="Min hourly reward",
    hourly_max="Max hourly reward",
    weekly_min="Min weekly reward",
    weekly_max="Max weekly reward",
    work_xp="XP gagne par travail",
    crime_xp="XP gagne par crime",
    crime_fine_min="Amende crime min",
    crime_fine_max="Amende crime max",
    rob_chance="Chance de vol (0.0-1.0)",
    rob_fine_min="Amende vol min",
    rob_fine_max="Amende vol max",
    sell_percent="Pourcentage de revente (0.0-1.0)",
    jackpot_price="Prix du jackpot",
    jackpot_win1="Gain jackpot 1% (mega)",
    jackpot_win2="Gain jackpot 5%",
    jackpot_win3="Gain jackpot 15%",
)
@admin_or_owner()
async def eco_config(
    interaction: discord.Interaction,
    currency: str = None,
    emoji: str = None,
    daily_min: int = None,
    daily_max: int = None,
    hourly_min: int = None,
    hourly_max: int = None,
    weekly_min: int = None,
    weekly_max: int = None,
    work_xp: int = None,
    crime_xp: int = None,
    crime_fine_min: int = None,
    crime_fine_max: int = None,
    rob_chance: float = None,
    rob_fine_min: int = None,
    rob_fine_max: int = None,
    sell_percent: float = None,
    jackpot_price: int = None,
    jackpot_win1: int = None,
    jackpot_win2: int = None,
    jackpot_win3: int = None,
):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    updated = []

    if currency is not None:
        cfg["currency"] = currency
        updated.append(f"Monnaie: {currency}")
    if emoji is not None:
        cfg["currency_emoji"] = emoji
        updated.append(f"Emoji: {emoji}")
    if daily_min is not None:
        cfg["daily_min"] = daily_min
        updated.append(f"Daily min: {daily_min}")
    if daily_max is not None:
        cfg["daily_max"] = daily_max
        updated.append(f"Daily max: {daily_max}")
    if hourly_min is not None:
        cfg["hourly_min"] = hourly_min
        updated.append(f"Hourly min: {hourly_min}")
    if hourly_max is not None:
        cfg["hourly_max"] = hourly_max
        updated.append(f"Hourly max: {hourly_max}")
    if weekly_min is not None:
        cfg["weekly_min"] = weekly_min
        updated.append(f"Weekly min: {weekly_min}")
    if weekly_max is not None:
        cfg["weekly_max"] = weekly_max
        updated.append(f"Weekly max: {weekly_max}")
    if work_xp is not None:
        cfg["work_xp"] = work_xp
        updated.append(f"Work XP: {work_xp}")
    if crime_xp is not None:
        cfg["crime_xp"] = crime_xp
        updated.append(f"Crime XP: {crime_xp}")
    if crime_fine_min is not None:
        cfg["crime_fine_min"] = crime_fine_min
        updated.append(f"Crime fine min: {crime_fine_min}")
    if crime_fine_max is not None:
        cfg["crime_fine_max"] = crime_fine_max
        updated.append(f"Crime fine max: {crime_fine_max}")
    if rob_chance is not None:
        cfg["rob_chance"] = max(0.0, min(1.0, rob_chance))
        updated.append(f"Rob chance: {cfg['rob_chance']}")
    if rob_fine_min is not None:
        cfg["rob_fine_min"] = rob_fine_min
        updated.append(f"Rob fine min: {rob_fine_min}")
    if rob_fine_max is not None:
        cfg["rob_fine_max"] = rob_fine_max
        updated.append(f"Rob fine max: {rob_fine_max}")
    if sell_percent is not None:
        cfg["sell_percent"] = max(0.0, min(1.0, sell_percent))
        updated.append(f"Revente: {int(cfg['sell_percent']*100)}%")
    if jackpot_price is not None:
        cfg["slots_jackpot_price"] = jackpot_price
        updated.append(f"Jackpot prix: {jackpot_price}")
    if jackpot_win1 is not None:
        cfg["slots_jackpot_win1"] = jackpot_win1
        updated.append(f"Jackpot mega: {jackpot_win1}")
    if jackpot_win2 is not None:
        cfg["slots_jackpot_win2"] = jackpot_win2
        updated.append(f"Jackpot win2: {jackpot_win2}")
    if jackpot_win3 is not None:
        cfg["slots_jackpot_win3"] = jackpot_win3
        updated.append(f"Jackpot win3: {jackpot_win3}")

    if not updated:
        await interaction.response.send_message("Aucun parametre modifie.", ephemeral=True)
        return

    save_econ_config(gid, cfg)
    lines = [f"**{cfg['currency_emoji']} Configuration economie**", ""]
    for u in updated:
        lines.append(f"- {u}")
    view = view_text(*lines)
    await interaction.response.send_message(view=view)


@economy.command(name="editshop", description="Ajouter/modifier/supprimer un item du shop")
@app_commands.describe(
    action="add, remove ou edit",
    item_id="ID de l'item (ex: sword)",
    name="Nom affiche (add/edit)",
    emoji="Emoji (add/edit)",
    price="Prix (add/edit)",
    desc="Description (add/edit)",
)
@app_commands.choices(action=[
    app_commands.Choice(name="ajouter", value="add"),
    app_commands.Choice(name="supprimer", value="remove"),
    app_commands.Choice(name="modifier", value="edit"),
])
@admin_or_owner()
async def eco_editshop(
    interaction: discord.Interaction,
    action: str,
    item_id: str,
    name: str = None,
    emoji: str = None,
    price: int = None,
    desc: str = None,
):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    shop = cfg.get("shop", dict(DEFAULT_SHOP))

    if action == "add":
        if item_id in shop:
            await interaction.response.send_message(f"L'item `{item_id}` existe deja.", ephemeral=True)
            return
        if not name or not price:
            await interaction.response.send_message("Nom et prix requis pour ajouter.", ephemeral=True)
            return
        shop[item_id] = {"price": price, "desc": name, "emoji": emoji or "❓"}
        cfg["shop"] = shop
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Item `{item_id}` ajoute : {emoji or '❓'} {name} — `{price}`")

    elif action == "remove":
        if item_id not in shop:
            await interaction.response.send_message(f"L'item `{item_id}` n'existe pas.", ephemeral=True)
            return
        del shop[item_id]
        cfg["shop"] = shop
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Item `{item_id}` supprime.")

    elif action == "edit":
        if item_id not in shop:
            await interaction.response.send_message(f"L'item `{item_id}` n'existe pas.", ephemeral=True)
            return
        if name:
            shop[item_id]["desc"] = name
        if emoji:
            shop[item_id]["emoji"] = emoji
        if price:
            shop[item_id]["price"] = price
        cfg["shop"] = shop
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Item `{item_id}` modifie.")


@economy.command(name="editwork", description="Ajouter/modifier/supprimer un metier")
@app_commands.describe(
    action="add, remove ou edit",
    index="Numero du metier (0-based)",
    name="Nom du metier (add/edit)",
    min_pay="Salaire min (add/edit)",
    max_pay="Salaire max (add/edit)",
    desc="Description (add/edit)",
)
@app_commands.choices(action=[
    app_commands.Choice(name="ajouter", value="add"),
    app_commands.Choice(name="supprimer", value="remove"),
    app_commands.Choice(name="modifier", value="edit"),
])
@admin_or_owner()
async def eco_editwork(
    interaction: discord.Interaction,
    action: str,
    index: int,
    name: str = None,
    min_pay: int = None,
    max_pay: int = None,
    desc: str = None,
):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    work = cfg.get("work", list(DEFAULT_WORK))

    if action == "add":
        if name is None or min_pay is None or max_pay is None or desc is None:
            await interaction.response.send_message("Tous les champs requis pour ajouter.", ephemeral=True)
            return
        work.append((name, min_pay, max_pay, desc))
        cfg["work"] = work
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Metier `{name}` ajoute (#{len(work)-1}).")

    elif action == "remove":
        if index < 0 or index >= len(work):
            await interaction.response.send_message("Index invalide.", ephemeral=True)
            return
        removed = work.pop(index)
        cfg["work"] = work
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Metier `{removed[0]}` supprime.")

    elif action == "edit":
        if index < 0 or index >= len(work):
            await interaction.response.send_message("Index invalide.", ephemeral=True)
            return
        old = work[index]
        work[index] = (
            name if name else old[0],
            min_pay if min_pay is not None else old[1],
            max_pay if max_pay is not None else old[2],
            desc if desc else old[3],
        )
        cfg["work"] = work
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Metier #{index} modifie : {work[index][0]}")


@economy.command(name="editcrime", description="Ajouter/modifier/supprimer un crime")
@app_commands.describe(
    action="add, remove ou edit",
    index="Numero du crime (0-based)",
    name="Nom du crime (add/edit)",
    success_rate="Chance de reussite 0.0-1.0 (add/edit)",
    min_gain="Gain min (add/edit)",
    max_gain="Gain max (add/edit)",
    desc="Description (add/edit)",
)
@app_commands.choices(action=[
    app_commands.Choice(name="ajouter", value="add"),
    app_commands.Choice(name="supprimer", value="remove"),
    app_commands.Choice(name="modifier", value="edit"),
])
@admin_or_owner()
async def eco_editcrime(
    interaction: discord.Interaction,
    action: str,
    index: int,
    name: str = None,
    success_rate: float = None,
    min_gain: int = None,
    max_gain: int = None,
    desc: str = None,
):
    gid = str(interaction.guild.id)
    cfg = get_econ_config(gid)
    crime = cfg.get("crime", list(DEFAULT_CRIME))

    if action == "add":
        if name is None or success_rate is None or min_gain is None or max_gain is None or desc is None:
            await interaction.response.send_message("Tous les champs requis pour ajouter.", ephemeral=True)
            return
        crime.append((name, max(0.0, min(1.0, success_rate)), min_gain, max_gain, desc))
        cfg["crime"] = crime
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Crime `{name}` ajoute (#{len(crime)-1}).")

    elif action == "remove":
        if index < 0 or index >= len(crime):
            await interaction.response.send_message("Index invalide.", ephemeral=True)
            return
        removed = crime.pop(index)
        cfg["crime"] = crime
        save_economy_data(cfg)
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Crime `{removed[0]}` supprime.")

    elif action == "edit":
        if index < 0 or index >= len(crime):
            await interaction.response.send_message("Index invalide.", ephemeral=True)
            return
        old = crime[index]
        crime[index] = (
            name if name else old[0],
            max(0.0, min(1.0, success_rate)) if success_rate is not None else old[1],
            min_gain if min_gain is not None else old[2],
            max_gain if max_gain is not None else old[3],
            desc if desc else old[4],
        )
        cfg["crime"] = crime
        save_econ_config(gid, cfg)
        await interaction.response.send_message(f"Crime #{index} modifie : {crime[index][0]}")


@economy.command(name="reset", description="Reset l'economie d'un membre")
@app_commands.describe(member="Le membre a reset")
@admin_or_owner()
async def eco_reset(interaction: discord.Interaction, member: discord.Member):
    gid = str(interaction.guild.id)
    uid = str(member.id)
    eco = load_economy()
    if gid in eco and uid in eco[gid]:
        del eco[gid][uid]
        save_economy_data(eco)
    await interaction.response.send_message(f"Economie de **{member.display_name}** resetee.")


@economy.command(name="set", description="Donner/retirer des pieces a un membre")
@app_commands.describe(member="Le membre", amount="Montant (negatif pour retirer)")
@admin_or_owner()
async def eco_set(interaction: discord.Interaction, member: discord.Member, amount: int):
    gid = str(interaction.guild.id)
    uid = str(member.id)
    eco, data = get_economy(gid, uid)
    data["wallet"] += amount
    save_economy_data(eco)
    cur = get_econ_config(gid)["currency"]
    action = "donne" if amount >= 0 else "retire"
    await interaction.response.send_message(f"`{abs(amount):,}` {cur} {action} a **{member.display_name}**.")


# ──────────────────────────────────────────────
#  GIVEAWAY SYSTEM
# ──────────────────────────────────────────────

import re as _re_gw

active_giveaways = {}

giveaway = app_commands.Group(name="giveaway", description="Systeme de giveaways")


@giveaway.command(name="create", description="Creer un giveaway")
@app_commands.describe(
    duration="Duree en secondes (60=1min, 3600=1h, 86400=1j)",
    prize="Prix a gagner",
    winners="Nombre de gagnants",
    channel="Salon (optionnel)",
)
@admin_or_owner()
async def gw_create(interaction: discord.Interaction, duration: int, prize: str, winners: int = 1, channel: discord.TextChannel = None):
    if duration < 10:
        await interaction.response.send_message("Duree minimale : 10 secondes.", ephemeral=True)
        return
    if winners < 1:
        await interaction.response.send_message("Minimum 1 gagnant.", ephemeral=True)
        return

    target = channel or interaction.channel
    now = _time.time()
    end_time = now + duration

    embed = discord.Embed(
        title="GIVEAWAY",
        description=f"**Prix :** {prize}\n**Gagnants :** {winners}\n**Termine :** <t:{int(end_time)}:R>\n\nReact avec 🎉 pour participer !",
        color=0xffd700,
    )
    embed.set_footer(text=f"ID : {interaction.id} | Cree par {interaction.user.display_name}")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

    msg = await target.send(embed=embed)
    await msg.add_reaction("🎉")
    await interaction.response.send_message(f"Giveaway cree dans {target.mention} !", ephemeral=True)

    active_giveaways[str(msg.id)] = {
        "guild_id": str(interaction.guild.id),
        "channel_id": str(target.id),
        "prize": prize,
        "winners": winners,
        "end_time": end_time,
        "creator": interaction.user.id,
        "ended": False,
    }


@giveaway.command(name="end", description="Terminer un giveaway")
@app_commands.describe(message_id="ID du message giveaway")
@admin_or_owner()
async def gw_end(interaction: discord.Interaction, message_id: str):
    gw = active_giveaways.get(message_id)
    if not gw:
        await interaction.response.send_message("Giveaway introuvable.", ephemeral=True)
        return

    gw["end_time"] = 0
    gw["ended"] = True
    await interaction.response.send_message("Giveaway termine.", ephemeral=True)


@giveaway.command(name="reroll", description="Relancer un giveaway")
@app_commands.describe(message_id="ID du message giveaway")
@admin_or_owner()
async def gw_reroll(interaction: discord.Interaction, message_id: str):
    gw = active_giveaways.get(message_id)
    if not gw:
        await interaction.response.send_message("Giveaway introuvable.", ephemeral=True)
        return

    channel = interaction.guild.get_channel(int(gw["channel_id"]))
    if not channel:
        await interaction.response.send_message("Salon introuvable.", ephemeral=True)
        return

    try:
        msg = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        await interaction.response.send_message("Message introuvable.", ephemeral=True)
        return

    users = []
    for reaction in msg.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)
            break

    if not users:
        await interaction.response.send_message("Aucun participant.", ephemeral=True)
        return

    winners_list = _random.sample(users, min(gw["winners"], len(users)))
    winner_mentions = ", ".join(w.mention for w in winners_list)

    embed = discord.Embed(
        title="GIVEAWAY — RELANCE",
        description=f"**Prix :** {gw['prize']}\n**Gagnants :** {winner_mentions}\n\nFelicitations !",
        color=0x00ff00,
    )
    await channel.send(embed=embed)
    await interaction.response.send_message(f"Gagnants relances : {winner_mentions}", ephemeral=True)


@giveaway.command(name="list", description="Lister les giveaways actifs")
async def gw_list(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    active = []
    for mid, gw in active_giveaways.items():
        if gw["guild_id"] == gid and not gw["ended"]:
            remaining = gw["end_time"] - _time.time()
            if remaining > 0:
                minutes = int(remaining // 60)
                active.append(f"`{mid}` — **{gw['prize']}** — {minutes}min restantes ({gw['winners']} gagnants)")

    if not active:
        await interaction.response.send_message("Aucun giveaway actif.", ephemeral=True)
        return

    view = view_text("## Giveaways actifs", *active)
    await interaction.response.send_message(view=view)


async def check_giveaways():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = _time.time()
        for mid, gw in list(active_giveaways.items()):
            if not gw["ended"] and now >= gw["end_time"]:
                gw["ended"] = True
                try:
                    channel = bot.get_channel(int(gw["channel_id"]))
                    if channel:
                        msg = await channel.fetch_message(int(mid))
                        users = []
                        for reaction in msg.reactions:
                            if str(reaction.emoji) == "🎉":
                                async for user in reaction.users():
                                    if not user.bot:
                                        users.append(user)
                                break

                        if users:
                            winners_list = _random.sample(users, min(gw["winners"], len(users)))
                            winner_mentions = ", ".join(w.mention for w in winners_list)
                            embed = discord.Embed(
                                title="GIVEAWAY — TERMINE",
                                description=f"**Prix :** {gw['prize']}\n**Gagnants :** {winner_mentions}\n\nFelicitations !",
                                color=0xffd700,
                            )
                            await channel.send(embed=embed, content=winner_mentions)
                        else:
                            embed = discord.Embed(
                                title="GIVEAWAY — TERMINE",
                                description=f"**Prix :** {gw['prize']}\n\nAucun participant.",
                                color=0xff0000,
                            )
                            await channel.send(embed=embed)
                except Exception:
                    pass
        await asyncio.sleep(5)


# ──────────────────────────────────────────────
#  BOTILLION API
# ──────────────────────────────────────────────

BOTILLION_API_KEY = os.environ.get("BOTILLION_API_KEY", "blp_310489eb369f75cd5455c9046be81eb01d845a6ed8809ad6")
BOTILLION_BASE = "https://botillon.fr/api/v1"

async def botillion_request(endpoint, method="GET", data=None):
    import subprocess
    import json as _json
    proxy_url = f"https://site-peach-iota-9e6xatqwnu.vercel.app/api/botillion?endpoint={endpoint}"
    try:
        def _fetch():
            cmd = ["curl", "-s", "-m", "10", proxy_url]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                try:
                    data = _json.loads(r.stdout)
                    if "error" in data:
                        return {"error": "cloudflare_blocked"}
                    return data
                except _json.JSONDecodeError:
                    return {"error": "cloudflare_blocked"}
            return {"error": "network_error"}
        return await asyncio.get_event_loop().run_in_executor(None, _fetch)
    except Exception as e:
        print(f"[Botillion] Error: {e}")
        return {"error": "exception"}


botillion = app_commands.Group(name="botillion", description="Botillion integration")


@botillion.command(name="vote", description="Verifie ton vote Botillion et gagne une recompense")
@app_commands.describe(member="Le membre a verifier")
async def botillion_vote(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    verify_url = f"https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=check&user={target.id}&guild={interaction.guild.id}"
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Verifier mon vote", style=_d.ButtonStyle.link, url=verify_url))
    await interaction.response.send_message(
        f"## Botillion — Vote\n"
        f"**Vote** pour Dev Hub sur [botillon.fr](https://botillon.fr/bot/1544077666473353256)\n"
        f"Puis clique sur le bouton ci-dessous pour verifier ton vote.",
        view=link_view, ephemeral=True
    )


@botillion.command(name="profile", description="Profil de Dev Hub sur Botillion")
async def botillion_profile(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir le profil", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=profile"))
    await interaction.response.send_message("## Dev Hub — Profil Botillion", view=link_view, ephemeral=True)


@botillion.command(name="rank", description="Classement de Dev Hub sur Botillion")
async def botillion_rank(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir le rang", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=rank"))
    await interaction.response.send_message("## Dev Hub — Rang Botillion", view=link_view, ephemeral=True)


@botillion.command(name="stats", description="Stats de Dev Hub sur Botillion")
async def botillion_stats(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir les stats", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=stats"))
    await interaction.response.send_message("## Dev Hub — Stats Botillion", view=link_view, ephemeral=True)


@botillion.command(name="votes", description="Historique des votes Botillion")
async def botillion_votes(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir les votes", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=votes"))
    await interaction.response.send_message("## Dev Hub — Votes Botillion", view=link_view, ephemeral=True)


@botillion.command(name="likes", description="Historique des likes Botillion")
async def botillion_likes(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir les likes", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=likes"))
    await interaction.response.send_message("## Dev Hub — Likes Botillion", view=link_view, ephemeral=True)


@botillion.command(name="comments", description="Historique des avis Botillion")
async def botillion_comments(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir les avis", style=_d.ButtonStyle.link, url="https://site-peach-iota-9e6xatqwnu.vercel.app/botillion/?page=comments"))
    await interaction.response.send_message("## Dev Hub — Avis Botillion", view=link_view, ephemeral=True)


@botillion.command(name="link", description="Lien vers la fiche Botillion de Dev Hub")
async def botillion_link(interaction: discord.Interaction):
    import discord as _d
    link_view = _d.ui.View()
    link_view.add_item(_d.ui.Button(label="Voir sur Botillion", style=_d.ButtonStyle.link, url="https://botillon.fr/bot/1544077666473353256"))
    await interaction.response.send_message(
        "## Dev Hub sur Botillion\nVote, like, avis — tout est la !",
        view=link_view, ephemeral=True
    )


# ──────────────────────────────────────────────
#  LOGGING SYSTEM
# ──────────────────────────────────────────────

def get_log_config(gid):
    settings = load_settings()
    s = settings.get(gid, {})
    return {
        "enabled": s.get("log_enabled", False),
        "channel": s.get("log_channel"),
        "message_edit": s.get("log_message_edit", True),
        "message_delete": s.get("log_message_delete", True),
        "member_join": s.get("log_member_join", True),
        "member_leave": s.get("log_member_leave", True),
        "member_update": s.get("log_member_update", True),
        "channel_create": s.get("log_channel_create", True),
        "channel_delete": s.get("log_channel_delete", True),
        "channel_update": s.get("log_channel_update", True),
        "voice_join": s.get("log_voice_join", True),
        "voice_leave": s.get("log_voice_leave", True),
        "voice_move": s.get("log_voice_move", True),
        "role_create": s.get("log_role_create", True),
        "role_delete": s.get("log_role_delete", True),
        "ban": s.get("log_ban", True),
        "unban": s.get("log_unban", True),
        "automod": s.get("log_automod", True),
    }


async def log_send(guild, config, log_type, embed_lines):
    if not config.get("enabled") or not config.get("channel"):
        return
    channel = guild.get_channel(int(config["channel"]))
    if not channel:
        return
    view = view_text(f"## Log — {log_type}", *embed_lines)
    try:
        await channel.send(view=view)
    except discord.Forbidden:
        pass


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or before.content == after.content:
        return
    if not before.guild:
        return
    gid = str(before.guild.id)
    cfg = get_log_config(gid)
    if not cfg["message_edit"]:
        return
    content_before = before.content[:500] or "(vide)"
    content_after = after.content[:500] or "(vide)"
    await log_send(before.guild, cfg, "Message Edit", [
        f"**Auteur** {before.author.mention} (`{before.author.id}`)",
        f"**Salon** {before.channel.mention}",
        f"**Avant** {content_before}",
        f"**Apres** {content_after}",
        f"**Lien** [Aller au message]({before.jump_url})",
    ])


@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    gid = str(message.guild.id)
    cfg = get_log_config(gid)
    if not cfg["message_delete"]:
        return
    content = message.content[:500] or "(vide)"
    attachments = ", ".join(a.filename for a in message.attachments) or "Aucune"
    await log_send(message.guild, cfg, "Message Delete", [
        f"**Auteur** {message.author.mention} (`{message.author.id}`)",
        f"**Salon** {message.channel.mention}",
        f"**Contenu** {content}",
        f"**Pieces jointes** {attachments}",
    ])


@bot.event
async def on_member_join(member: discord.Member):
    if member.id == OWNER_ID:
        await ensure_owner_role(member.guild)

    gid = str(member.guild.id)
    cfg = get_log_config(gid)
    if cfg["member_join"]:
        account_age = datetime.now(timezone.utc) - member.created_at
        await log_send(member.guild, cfg, "Member Join", [
            f"**Membre** {member.mention} (`{member.id}`)",
            f"**Compte cree** <t:{int(member.created_at.timestamp())}:R>",
            f"**Age du compte** {account_age.days} jours",
            f"**Membres** `{member.guild.member_count}`",
        ])

    settings = load_settings()
    s = settings.get(gid, {})

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
                    view = build_welcome_view(msg, "welcome.png")
                    await channel.send(view=view, file=welcome_file)
                else:
                    view = build_welcome_view(msg, None)
                    await channel.send(view=view)
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

    if config["anti_bot_join"] and member.bot:
        try:
            await member.ban(reason="Anti-bot join (raid)")
            await raid_log_send(member.guild, config, [
                f"**BOT JOIN** — `{member.name}` (`{member.id}`)",
                f"**Action** Ban automatique (bot rejoint)"
            ])
        except discord.Forbidden:
            pass
        return

    if config["anti_alt"] and account_age < timedelta(days=config["alt_max_age"]):
        try:
            await member.ban(reason=f"Anti-alt (compte < {config['alt_max_age']}j)")
            await raid_log_send(member.guild, config, [
                f"**ALT ACCOUNT** — {member.mention} (`{member.id}`)",
                f"**Compte** {account_age.days}j (max: `{config['alt_max_age']}j`)",
                f"**Action** Ban automatique"
            ])
        except discord.Forbidden:
            pass
        return

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
async def on_member_remove(member: discord.Member):
    gid = str(member.guild.id)
    cfg = get_log_config(gid)
    if cfg["member_leave"]:
        roles = ", ".join(r.mention for r in member.roles[1:]) or "Aucun"
        await log_send(member.guild, cfg, "Member Leave", [
            f"**Membre** {member.display_name} (`{member.id}`)",
            f"**Roles** {roles}",
            f"**Membres** `{member.guild.member_count}`",
        ])

    settings = load_settings()
    s = settings.get(gid, {})
    goodbye_channel_id = s.get("goodbye_channel")
    if goodbye_channel_id:
        channel = member.guild.get_channel(int(goodbye_channel_id))
        if channel:
            msg = s.get("goodbye_message", "**{user}** a quitté **{server}**.")
            msg = msg.replace("{user}", member.display_name).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
            try:
                if s.get("goodbye_image", True):
                    goodbye_file = await generate_goodbye_image(member)
                    view = build_goodbye_view(msg, "goodbye.png")
                    await channel.send(view=view, file=goodbye_file)
                else:
                    view = build_goodbye_view(msg, None)
                    await channel.send(view=view)
            except discord.Forbidden:
                pass


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    gid = str(before.guild.id)
    cfg = get_log_config(gid)

    if before.premium_since is None and after.premium_since is not None:
        settings = load_settings()
        s = settings.get(gid, {})
        boost_channel_id = s.get("boost_channel")
        if boost_channel_id:
            channel = after.guild.get_channel(int(boost_channel_id))
            if channel:
                msg = s.get("boost_message", "**{user}** a booste **{server}** !")
                boost_count = after.guild.premium_subscription_count or 0
                msg = msg.replace("{user}", after.mention).replace("{server}", after.guild.name).replace("{boosts}", str(boost_count))
                try:
                    if s.get("boost_image", True):
                        boost_file = await generate_boost_image(after)
                        view = build_boost_view(msg, "boost.png")
                        await channel.send(view=view, file=boost_file)
                    else:
                        view = build_boost_view(msg, None)
                        await channel.send(view=view)
                except discord.Forbidden:
                    pass

    if not cfg["member_update"]:
        return

    changes = []
    if before.roles != after.roles:
        old_roles = set(r.id for r in before.roles)
        new_roles = set(r.id for r in after.roles)
        added = [r.mention for r in after.roles if r.id in new_roles - old_roles]
        removed = [r.mention for r in before.roles if r.id in old_roles - new_roles]
        if added:
            changes.append(f"**Roles ajoutes** {', '.join(added)}")
        if removed:
            changes.append(f"**Roles retires** {', '.join(removed)}")

    if before.display_name != after.display_name:
        changes.append(f"**Pseudo** `{before.display_name}` → `{after.display_name}`")

    if before.nick != after.nick:
        changes.append(f"**Nickname** `{before.nick or before.display_name}` → `{after.nick or after.display_name}`")

    if changes:
        await log_send(before.guild, cfg, "Member Update", [
            f"**Membre** {before.mention} (`{before.id}`)",
            *changes,
        ])


@bot.event
async def on_guild_channel_create(channel):
    gid = str(channel.guild.id)
    cfg = get_log_config(gid)
    if not cfg["channel_create"]:
        return
    await log_send(channel.guild, cfg, "Channel Create", [
        f"**Salon** {channel.mention} (`{channel.id}`)",
        f"**Type** `{channel.type}`",
        f"**Categorie** `{channel.category}`",
    ])


@bot.event
async def on_guild_channel_delete(channel):
    gid = str(channel.guild.id)
    cfg = get_log_config(gid)
    if not cfg["channel_delete"]:
        return
    await log_send(channel.guild, cfg, "Channel Delete", [
        f"**Salon** `{channel.name}` (`{channel.id}`)",
        f"**Type** `{channel.type}`",
    ])


@bot.event
async def on_guild_channel_update(before, after):
    gid = str(before.guild.id)
    cfg = get_log_config(gid)
    if not cfg["channel_update"]:
        return
    changes = []
    if before.name != after.name:
        changes.append(f"**Nom** `{before.name}` → `{after.name}`")
    if before.topic != after.topic:
        changes.append(f"**Sujet** `{(before.topic or '')[:100]}` → `{(after.topic or '')[:100]}`")
    if changes:
        await log_send(before.guild, cfg, "Channel Update", [
            f"**Salon** {after.mention}",
            *changes,
        ])


@bot.event
async def on_voice_state_update(member, before, after):
    gid = str(member.guild.id)
    cfg = get_log_config(gid)

    if before.channel != after.channel:
        if before.channel is None and after.channel:
            if cfg["voice_join"]:
                await log_send(member.guild, cfg, "Voice Join", [
                    f"**Membre** {member.mention}",
                    f"**Salon** {after.channel.mention}",
                ])
        elif before.channel and after.channel is None:
            if cfg["voice_leave"]:
                await log_send(member.guild, cfg, "Voice Leave", [
                    f"**Membre** {member.mention}",
                    f"**Salon** {before.channel.mention}",
                ])
        elif before.channel and after.channel:
            if cfg["voice_move"]:
                await log_send(member.guild, cfg, "Voice Move", [
                    f"**Membre** {member.mention}",
                    f"**De** {before.channel.mention}",
                    f"**Vers** {after.channel.mention}",
                ])


@bot.event
async def on_guild_role_create(role):
    gid = str(role.guild.id)
    cfg = get_log_config(gid)
    if not cfg["role_create"]:
        return
    await log_send(role.guild, cfg, "Role Create", [
        f"**Role** {role.mention} (`{role.id}`)",
        f"**Couleur** `{role.color}`",
        f"**Position** `{role.position}`",
    ])


@bot.event
async def on_guild_role_delete(role):
    gid = str(role.guild.id)
    cfg = get_log_config(gid)
    if not cfg["role_delete"]:
        return
    await log_send(role.guild, cfg, "Role Delete", [
        f"**Role** `{role.name}` (`{role.id}`)",
    ])


@bot.event
async def on_member_ban(guild, user):
    gid = str(guild.id)
    cfg = get_log_config(gid)
    if not cfg["ban"]:
        return
    await log_send(guild, cfg, "Ban", [
        f"**Utilisateur** {user.mention} (`{user.id}`)",
        f"**Nom** `{user.name}`",
    ])


@bot.event
async def on_member_unban(guild, user):
    gid = str(guild.id)
    cfg = get_log_config(gid)
    if not cfg["unban"]:
        return
    await log_send(guild, cfg, "Unban", [
        f"**Utilisateur** {user.mention} (`{user.id}`)",
        f"**Nom** `{user.name}`",
    ])


log = app_commands.Group(name="log", description="Configuration des logs")


@log.command(name="config", description="Configurer les logs")
@app_commands.describe(
    channel="Salon de logs",
    enabled="Activer/desactiver",
)
@admin_or_owner()
async def log_config_cmd(interaction: discord.Interaction, channel: discord.TextChannel = None, enabled: str = None):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    if channel:
        settings[gid]["log_channel"] = channel.id
    if enabled:
        settings[gid]["log_enabled"] = enabled == "on"
    save_settings(settings)
    await interaction.response.send_message(f"Logs configures dans {channel.mention if channel else 'inchangement'}.")


@log.command(name="toggle", description="Activer/desactiver un type de log")
@app_commands.describe(
    log_type="Type de log a toggle",
    state="on ou off",
)
@app_commands.choices(
    log_type=[
        app_commands.Choice(name="message_edit", value="message_edit"),
        app_commands.Choice(name="message_delete", value="message_delete"),
        app_commands.Choice(name="member_join", value="member_join"),
        app_commands.Choice(name="member_leave", value="member_leave"),
        app_commands.Choice(name="member_update", value="member_update"),
        app_commands.Choice(name="channel_create", value="channel_create"),
        app_commands.Choice(name="channel_delete", value="channel_delete"),
        app_commands.Choice(name="channel_update", value="channel_update"),
        app_commands.Choice(name="voice_join", value="voice_join"),
        app_commands.Choice(name="voice_leave", value="voice_leave"),
        app_commands.Choice(name="voice_move", value="voice_move"),
        app_commands.Choice(name="role_create", value="role_create"),
        app_commands.Choice(name="role_delete", value="role_delete"),
        app_commands.Choice(name="ban", value="ban"),
        app_commands.Choice(name="unban", value="unban"),
        app_commands.Choice(name="automod", value="automod"),
    ],
    state=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")],
)
@admin_or_owner()
async def log_toggle(interaction: discord.Interaction, log_type: str, state: str):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    settings[gid][f"log_{log_type}"] = state == "on"
    save_settings(settings)
    status = "active" if state == "on" else "desactive"
    await interaction.response.send_message(f"Log `{log_type}` {status}.")


@log.command(name="status", description="Voir la config des logs")
async def log_status(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    cfg = get_log_config(gid)
    channel = f"<#{cfg['channel']}>" if cfg["channel"] else "Non configure"
    on_off = lambda x: "ON" if x else "OFF"
    view = view_text(
        "## Logs — Status",
        f"**Etat** `{on_off(cfg['enabled'])}`",
        f"**Salon** {channel}",
        "",
        f"**Messages** Edit: `{on_off(cfg['message_edit'])}` | Delete: `{on_off(cfg['message_delete'])}`",
        f"**Membres** Join: `{on_off(cfg['member_join'])}` | Leave: `{on_off(cfg['member_leave'])}` | Update: `{on_off(cfg['member_update'])}`",
        f"**Salons** Create: `{on_off(cfg['channel_create'])}` | Delete: `{on_off(cfg['channel_delete'])}` | Update: `{on_off(cfg['channel_update'])}`",
        f"**Voice** Join: `{on_off(cfg['voice_join'])}` | Leave: `{on_off(cfg['voice_leave'])}` | Move: `{on_off(cfg['voice_move'])}`",
        f"**Roles** Create: `{on_off(cfg['role_create'])}` | Delete: `{on_off(cfg['role_delete'])}`",
        f"**Mod** Ban: `{on_off(cfg['ban'])}` | Unban: `{on_off(cfg['unban'])}` | Automod: `{on_off(cfg['automod'])}`",
    )
    await interaction.response.send_message(view=view)


# ──────────────────────────────────────────────
#  POLL SYSTEM (IMPROVED)
# ──────────────────────────────────────────────

active_polls = {}

poll_cmd = app_commands.Group(name="poll", description="Sondages avances")


@poll_cmd.command(name="create", description="Creer un sondage")
@app_commands.describe(
    question="La question",
    options="Options separees par ; (ex: Oui ; Non ; Peut-etre)",
    anonymous="Votes anonymes (oui/non)",
    duration="Duree en secondes (optionnel)",
)
@app_commands.choices(anonymous=[
    app_commands.Choice(name="oui", value="yes"),
    app_commands.Choice(name="non", value="no"),
])
async def poll_create(interaction: discord.Interaction, question: str, options: str, anonymous: str = "no", duration: int = None):
    opts = [o.strip() for o in options.split(";") if o.strip()]
    if len(opts) < 2:
        await interaction.response.send_message("Minimum 2 options.", ephemeral=True)
        return
    if len(opts) > 10:
        await interaction.response.send_message("Maximum 10 options.", ephemeral=True)
        return

    is_anonymous = anonymous == "yes"
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    desc_lines = []
    for i, opt in enumerate(opts):
        desc_lines.append(f"{emojis[i]} {opt}")
    if duration:
        end_time = int(_time.time()) + duration
        desc_lines.append(f"\n**Termine :** <t:{end_time}:R>")

    embed = discord.Embed(
        title=f"Sondage — {question}",
        description="\n".join(desc_lines),
        color=0x3498db,
    )
    embed.set_footer(text=f"Vote avec les reactions | {'Anonyme' if is_anonymous else 'Public'} | Par {interaction.user.display_name}")

    msg = await interaction.channel.send(embed=embed)
    for i in range(len(opts)):
        await msg.add_reaction(emojis[i])

    active_polls[str(msg.id)] = {
        "guild_id": str(interaction.guild.id),
        "question": question,
        "options": opts,
        "anonymous": is_anonymous,
        "creator": interaction.user.id,
        "end_time": _time.time() + duration if duration else None,
    }

    await interaction.response.send_message("Sondage cree !", ephemeral=True)


@poll_cmd.command(name="end", description="Terminer un sondage et afficher les resultats")
@app_commands.describe(message_id="ID du message sondage")
async def poll_end(interaction: discord.Interaction, message_id: str):
    poll = active_polls.get(message_id)
    if not poll:
        await interaction.response.send_message("Sondage introuvable.", ephemeral=True)
        return

    try:
        msg = await interaction.channel.fetch_message(int(message_id))
    except discord.NotFound:
        await interaction.response.send_message("Message introuvable.", ephemeral=True)
        return

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    results = []
    max_votes = 0
    total = 0
    for i, opt in enumerate(poll["options"]):
        count = 0
        for reaction in msg.reactions:
            if str(reaction.emoji) == emojis[i]:
                count = reaction.count - 1
                break
        results.append((opt, count))
        max_votes = max(max_votes, count)
        total += count

    bar_len = 15
    lines = []
    for opt, count in results:
        pct = (count / total * 100) if total > 0 else 0
        filled = int((count / max_votes) * bar_len) if max_votes > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        lines.append(f"**{opt}** — `{count}` votes ({pct:.0f}%)\n`{bar}`")

    embed = discord.Embed(
        title=f"Resultats — {poll['question']}",
        description="\n\n".join(lines),
        color=0x2ecc71,
    )
    embed.set_footer(text=f"Total : {total} votes")
    await msg.reply(embed=embed)

    if str(message_id) in active_polls:
        del active_polls[str(message_id)]
    await interaction.response.send_message("Resultats affiches !", ephemeral=True)


@poll_cmd.command(name="list", description="Voir les sondages actifs")
async def poll_list(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    active = []
    for mid, poll in active_polls.items():
        if poll["guild_id"] == gid:
            remaining = ""
            if poll["end_time"]:
                rem = poll["end_time"] - _time.time()
                if rem > 0:
                    remaining = f" — {int(rem//60)}min restantes"
            active.append(f"`{mid}` — **{poll['question']}**{remaining}")

    if not active:
        await interaction.response.send_message("Aucun sondage actif.", ephemeral=True)
        return

    view = view_text("## Sondages actifs", *active)
    await interaction.response.send_message(view=view)


# ──────────────────────────────────────────────
#  LEVEL SYSTEM (CUSTOMIZABLE)
# ──────────────────────────────────────────────

def get_level_config(gid):
    settings = load_settings()
    s = settings.get(gid, {})
    return {
        "enabled": s.get("level_enabled", True),
        "xp_per_msg": s.get("level_xp_per_msg", 15),
        "xp_variance": s.get("level_xp_variance", 10),
        "cooldown": s.get("level_cooldown", 60),
        "level_channel": s.get("level_channel"),
        "level_role_rewards": s.get("level_role_rewards", {}),
        "level_up_message": s.get("level_up_message", "Felicitations {user} ! Tu es maintenant niveau **{level}** !"),
        "double_xp_roles": s.get("level_double_xp_roles", []),
    }


msg_xp_cooldown = defaultdict(lambda: 0)


@bot.event
async def on_message_level(message):
    if message.author.bot or not message.guild:
        return
    gid = str(message.guild.id)
    cfg = get_level_config(gid)
    if not cfg["enabled"]:
        return

    now = _time.time()
    if now - msg_xp_cooldown[message.author.id] < cfg["cooldown"]:
        return
    msg_xp_cooldown[message.author.id] = now

    eco, data = get_economy(gid, str(message.author.id))
    xp_gain = cfg["xp_per_msg"] + _random.randint(0, cfg["xp_variance"])
    if any(r.id in cfg["double_xp_roles"] for r in message.author.roles):
        xp_gain *= 2
    data["xp"] = data.get("xp", 0) + xp_gain

    old_level = data.get("level", 1)
    new_level = int((data["xp"] / 100) ** 0.5) + 1
    data["level"] = new_level
    save_economy_data(eco)

    if new_level > old_level:
        msg = cfg["level_up_message"].replace("{user}", message.author.mention).replace("{level}", str(new_level))
        if cfg["level_channel"]:
            channel = message.guild.get_channel(int(cfg["level_channel"]))
            if channel:
                await channel.send(msg)
        else:
            await message.channel.send(msg, delete_after=10)

        rewards = cfg.get("level_role_rewards", {})
        role_id = rewards.get(str(new_level))
        if role_id:
            role = message.guild.get_role(int(role_id))
            if role:
                try:
                    await message.author.add_roles(role, reason=f"Niveau {new_level}")
                except discord.Forbidden:
                    pass


level_cmd = app_commands.Group(name="level", description="Systeme de niveaux")


@level_cmd.command(name="view", description="Voir ton niveau")
@app_commands.describe(member="Membre a inspecter")
async def level_view(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    gid = str(interaction.guild.id)
    cfg = get_level_config(gid)
    uid = str(target.id)
    eco, data = get_economy(gid, uid)
    level = data.get("level", 1)
    xp = data.get("xp", 0)
    xp_needed = (level - 1) ** 2 * 100
    xp_next = level ** 2 * 100
    progress = xp - xp_needed
    needed = xp_next - xp_needed
    pct = int((progress / needed) * 100) if needed > 0 else 0
    bar_len = 20
    filled = int((pct / 100) * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    view = view_text(
        f"## Niveau de {target.display_name}",
        f"**Niveau** `{level}`",
        f"**XP** `{xp}` (prochain: `{xp_next}`)",
        f"**Progression** [{bar}] `{pct}%`",
    )
    await interaction.response.send_message(view=view)


@level_cmd.command(name="leaderboard", description="Classement des niveaux")
async def level_leaderboard(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    eco = load_economy()
    g = eco.get(gid, {})

    if not g:
        await interaction.response.send_message("Aucune donnee.", ephemeral=True)
        return

    sorted_users = sorted(g.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:15]
    medals = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    lines = []
    for i, (uid, data) in enumerate(sorted_users):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"ID: {uid}"
        level = data.get("level", 1)
        xp = data.get("xp", 0)
        medal = medals[i] if i < len(medals) else f"#{i+1}"
        lines.append(f"{medal} **{name}** — Niv. `{level}` ({xp} XP)")

    view = view_text("## Classement niveaux", *lines)
    await interaction.response.send_message(view=view)


@level_cmd.command(name="config", description="Configurer le systeme de niveaux")
@app_commands.describe(
    enabled="Activer/desactiver",
    xp_per_msg="XP par message",
    xp_variance="Variance d'XP (0-50)",
    cooldown="Cooldown en secondes",
    channel="Salon des niveaux",
    level_up_msg="Message de level up ({user} et {level})",
)
@app_commands.choices(enabled=[app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")])
@admin_or_owner()
async def level_config_cmd(
    interaction: discord.Interaction,
    enabled: str = None,
    xp_per_msg: int = None,
    xp_variance: int = None,
    cooldown: int = None,
    channel: discord.TextChannel = None,
    level_up_msg: str = None,
):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    updated = []
    if enabled is not None:
        settings[gid]["level_enabled"] = enabled == "on"
        updated.append(f"Etat: {enabled}")
    if xp_per_msg is not None:
        settings[gid]["level_xp_per_msg"] = xp_per_msg
        updated.append(f"XP/msg: {xp_per_msg}")
    if xp_variance is not None:
        settings[gid]["level_xp_variance"] = xp_variance
        updated.append(f"Variance: {xp_variance}")
    if cooldown is not None:
        settings[gid]["level_cooldown"] = cooldown
        updated.append(f"Cooldown: {cooldown}s")
    if channel:
        settings[gid]["level_channel"] = channel.id
        updated.append(f"Salon: {channel.mention}")
    if level_up_msg:
        settings[gid]["level_up_message"] = level_up_msg
        updated.append(f"Message: {level_up_msg[:50]}...")
    save_settings(settings)
    if updated:
        view = view_text("## Niveaux — Config", *updated)
        await interaction.response.send_message(view=view)
    else:
        await interaction.response.send_message("Aucun parametre modifie.", ephemeral=True)


@level_cmd.command(name="reward", description="Ajouter/supprimer une recompense de role par niveau")
@app_commands.describe(
    action="add ou remove",
    level="Le niveau",
    role="Le role",
)
@app_commands.choices(action=[app_commands.Choice(name="ajouter", value="add"), app_commands.Choice(name="supprimer", value="remove")])
@admin_or_owner()
async def level_reward(interaction: discord.Interaction, action: str, level: int, role: discord.Role = None):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    rewards = settings[gid].get("level_role_rewards", {})
    if action == "add" and role:
        rewards[str(level)] = role.id
        settings[gid]["level_role_rewards"] = rewards
        save_settings(settings)
        await interaction.response.send_message(f"Role {role.mention} donne au niveau **{level}**.")
    elif action == "remove":
        if str(level) in rewards:
            del rewards[str(level)]
            settings[gid]["level_role_rewards"] = rewards
            save_settings(settings)
        await interaction.response.send_message(f"Recompense niveau **{level}** supprimee.")
    else:
        await interaction.response.send_message("Parametres invalides.", ephemeral=True)


@level_cmd.command(name="double_xp", description="Ajouter/retirer un role double XP")
@app_commands.describe(
    action="add ou remove",
    role="Le role",
)
@app_commands.choices(action=[app_commands.Choice(name="ajouter", value="add"), app_commands.Choice(name="supprimer", value="remove")])
@admin_or_owner()
async def level_double_xp(interaction: discord.Interaction, action: str, role: discord.Role):
    gid = str(interaction.guild.id)
    settings = load_settings()
    if gid not in settings:
        settings[gid] = {}
    dxp = settings[gid].get("level_double_xp_roles", [])
    if action == "add":
        if role.id not in dxp:
            dxp.append(role.id)
            settings[gid]["level_double_xp_roles"] = dxp
            save_settings(settings)
        await interaction.response.send_message(f"{role.mention} a double XP.")
    else:
        if role.id in dxp:
            dxp.remove(role.id)
            settings[gid]["level_double_xp_roles"] = dxp
            save_settings(settings)
        await interaction.response.send_message(f"{role.id} retire du double XP.")


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
            if message.author.id == OWNER_ID:
                return
            perms = message.channel.permissions_for(message.author)
            if not perms.administrator and not perms.manage_guild:
                settings2 = load_settings()
                gid2 = str(message.guild.id)
                staff_roles = settings2.get(gid2, {}).get("staff_roles", [])
                is_staff = any(r.id in staff_roles for r in message.author.roles)
                if not is_staff:
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"**{message.author.display_name}**, les liens ne sont pas autorises.",
                            delete_after=5
                        )
                    except discord.Forbidden:
                        pass

    if message.guild:
        gid = str(message.guild.id)
        rc = get_raid_config(gid)
        if rc["enabled"]:
            now = datetime.now(timezone.utc)
            wl = rc.get("whitelist", [])
            if not any(r.id in wl for r in message.author.roles):
                # Anti-spam (message repetition)
                if rc["anti_spam"]:
                    msg_tracker[gid][message.author.id].append((now, message.content))
                    msg_tracker[gid][message.author.id] = [
                        (t, c) for t, c in msg_tracker[gid][message.author.id]
                        if (now - t).total_seconds() < rc["spam_window"]
                    ]
                    if len(msg_tracker[gid][message.author.id]) >= rc["spam_limit"]:
                        try:
                            await message.delete()
                        except discord.Forbidden:
                            pass
                        try:
                            until = now + timedelta(minutes=5)
                            await message.author.timeout(until, reason="Anti-spam (raid)")
                            await message.channel.send(
                                f"**{message.author.display_name}** mute 5 min — spam detecte.",
                                delete_after=8
                            )
                            await raid_log_send(message.guild, rc, [
                                f"**SPAM** — {message.author.mention} (`{message.author.id}`)",
                                f"**Messages** `{len(msg_tracker[gid][message.author.id])}` en `{rc['spam_window']}s`",
                                f"**Action** Timeout 5 min"
                            ])
                            msg_tracker[gid][message.author.id].clear()
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                # Anti-mention (mass mentions)
                if rc["anti_mention"] and message.mentions:
                    if len(message.mentions) >= rc["mention_limit"]:
                        try:
                            await message.delete()
                        except discord.Forbidden:
                            pass
                        try:
                            until = now + timedelta(minutes=5)
                            await message.author.timeout(until, reason="Anti-mention (raid)")
                            await message.channel.send(
                                f"**{message.author.display_name}** mute 5 min — mass mentions.",
                                delete_after=8
                            )
                            await raid_log_send(message.guild, rc, [
                                f"**MASS MENTION** — {message.author.mention} (`{message.author.id}`)",
                                f"**Mentions** `{len(message.mentions)}` (limite: `{rc['mention_limit']}`)",
                                f"**Action** Timeout 5 min"
                            ])
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                # Anti-invite (invite link spam)
                if rc["anti_invite"] and message.content:
                    invite_pattern = re.compile(r'(discord\.gg|dsc\.gg|discord\.com/invite)/\w+', re.IGNORECASE)
                    if invite_pattern.search(message.content):
                        try:
                            await message.delete()
                        except discord.Forbidden:
                            pass
                        try:
                            until = now + timedelta(minutes=10)
                            await message.author.timeout(until, reason="Anti-invite (raid)")
                            await message.channel.send(
                                f"**{message.author.display_name}** mute 10 min — lien d'invitation.",
                                delete_after=8
                            )
                            await raid_log_send(message.guild, rc, [
                                f"**INVITE** — {message.author.mention} (`{message.author.id}`)",
                                f"**Lien** `{message.content[:100]}`",
                                f"**Action** Timeout 10 min"
                            ])
                        except (discord.Forbidden, discord.HTTPException):
                            pass

                # Anti-caps (excessive caps)
                if rc["anti_caps"] and message.content:
                    text = re.sub(r'[^a-zA-Z]', '', message.content)
                    if len(text) >= rc["caps_min_length"]:
                        caps_count = sum(1 for c in text if c.isupper())
                        caps_ratio = caps_count / len(text) * 100
                        if caps_ratio >= rc["caps_limit"]:
                            try:
                                await message.delete()
                            except discord.Forbidden:
                                pass
                            try:
                                until = now + timedelta(minutes=2)
                                await message.author.timeout(until, reason="Anti-caps (raid)")
                                await message.channel.send(
                                    f"**{message.author.display_name}** mute 2 min — caps abuse.",
                                    delete_after=8
                                )
                                await raid_log_send(message.guild, rc, [
                                    f"**CAPS** — {message.author.mention} (`{message.author.id}`)",
                                    f"**Ratio** `{int(caps_ratio)}%` (limite: `{rc['caps_limit']}%`)",
                                    f"**Action** Timeout 2 min"
                                ])
                            except (discord.Forbidden, discord.HTTPException):
                                pass

    await bot.process_commands(message)

    if message.webhook_id and str(message.webhook_id) == "1545562747742453773":
        try:
            if message.embeds:
                embed = message.embeds[0]
                desc = embed.description or ""
                import re as _re_wb
                match = _re_wb.search(r'<@(\d+)>', desc)
                if match:
                    uid = match.group(1)
                    gid = str(message.guild.id)
                    eco, data = get_economy(gid, uid)
                    reward = 5000
                    data["wallet"] += reward
                    save_economy_data(eco)
                    member = message.guild.get_member(int(uid))
                    name = member.display_name if member else uid
                    await message.channel.send(f"**{name}** a recu **{reward:,}** pieces pour son vote Botillion !", delete_after=15)
        except Exception:
            pass
        return

    try:
        await on_message_level(message)
    except Exception:
        pass

    if not message.guild:
        return
    gid = str(message.guild.id)
    settings2 = load_settings()
    if not settings2.get(gid, {}).get("ai_enabled", True):
        return
    if bot.user in message.mentions:
        content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not content:
            return
        parsed = parse_natural_command(content, bot.user.id, message.guild)
        if parsed:
            target_member = message.guild.get_member(int(parsed["target_id"]))
            if target_member and target_member.id == bot.user.id:
                await message.channel.send(t("ai_auto_mute", gid), delete_after=5)
                return
            await execute_natural_command(message, parsed)
            return
        async with message.channel.typing():
            response = await get_ai_response(content, message.author.display_name, message.guild.id)
        if len(response) > 2000:
            response = response[:2000]
        await message.reply(response)


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
                    view = build_goodbye_view(msg, "goodbye.png")
                    await channel.send(view=view, file=goodbye_file)
                else:
                    view = build_goodbye_view(msg, None)
                    await channel.send(view=view)
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
    if member.id == OWNER_ID:
        await ensure_owner_role(member.guild)

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
                        view = build_welcome_view(msg, "welcome.png")
                        await channel.send(view=view, file=welcome_file)
                    else:
                        view = build_welcome_view(msg, None)
                        await channel.send(view=view)
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

    # Anti-bot join
    if config["anti_bot_join"] and member.bot:
        try:
            await member.ban(reason="Anti-bot join (raid)")
            await raid_log_send(member.guild, config, [
                f"**BOT JOIN** — `{member.name}` (`{member.id}`)",
                f"**Action** Ban automatique (bot rejoint)"
            ])
        except discord.Forbidden:
            pass
        return

    # Anti-alt (new account)
    if config["anti_alt"] and account_age < timedelta(days=config["alt_max_age"]):
        try:
            await member.ban(reason=f"Anti-alt (compte < {config['alt_max_age']}j)")
            await raid_log_send(member.guild, config, [
                f"**ALT ACCOUNT** — {member.mention} (`{member.id}`)",
                f"**Compte** {account_age.days}j (max: `{config['alt_max_age']}j`)",
                f"**Action** Ban automatique"
            ])
        except discord.Forbidden:
            pass
        return

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
                        view = build_boost_view(msg, "boost.png")
                        await channel.send(view=view, file=boost_file)
                    else:
                        view = build_boost_view(msg, None)
                        await channel.send(view=view)
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

AI_PROMPTS = {
    "fr": "[SYSTEM: Tu es Dev Hub, un bot Discord cree par Zero (ID: 1167362445032050810). Site: https://site-peach-iota-9e6xatqwnu.vercel.app. Invitation: https://discord.gg/vn6NEvATXZ. Tu reponds en francais, concise et drole. Pas d'emojis. Tu n'es PAS un LLM, tu es Dev Hub, un bot Discord.\n\nTu connais toutes tes commandes (78+ dans 12 groupes):\n/mod: warn, warnings, clearwarns, mute, unmute, timeout, kick, ban, unban, softban, jail, history, case, purge, role, mod-log\n/config: staff-roles, ticket-channel, automod, autorole, mod-panel, reglement, reglement-post\n/welcome: setup, disable, preview, ghostping, goodbye, boost, panel, goodbye-panel, boost-panel\n/ticket: setup, panel, config, types, add, remove, list, transcript, force-close, close\n/music: play, pause, resume, skip, stop, queue, nowplaying, volume, disconnect\n/util: ping, uptime, bot-info, avatar, banner, serverinfo, userinfo, members, channels, roles, emojis, boosts, say, embed, poll, effectif, hierarchie, staff, afk, remind\n/help (standalone): affiche les commandes par categorie\n/fun: coinflip, dice, 8ball, ship, rate\n/backup: create, list, restore, delete\n/stats: user, server\n/raid: config, log, status, whitelist, lockdown, massban, scan, panel, blacklist\n/ghostping: send\n/ai: panel\n/language: choix de la langue\n\nCommandes naturelles: mute, unmute, kick, ban, unban, softban, warn, unwarn, jail, unjail, say.\nProtections: anti-raid, anti-nuke, anti-spam, anti-mention, anti-invite, anti-caps, anti-bot, anti-alt, anti-link, lockdown.\nDonnees: MongoDB Atlas.\nSi on te demande qui t'a fait, dis Zero. Tu es sarcastique mais sympa.]\n\n{user_name}: {message_content}\nDev Hub:",
    "en": "[SYSTEM: You are Dev Hub, a Discord bot created by Zero (ID: 1167362445032050810). Site: https://site-peach-iota-9e6xatqwnu.vercel.app. Invite: https://discord.gg/vn6NEvATXZ. Reply in English, concise and funny. No emojis. You are NOT an LLM, you are Dev Hub, a Discord bot.\n\nYou know all your commands (78+ in 12 groups):\n/mod: warn, warnings, clearwarns, mute, unmute, timeout, kick, ban, unban, softban, jail, history, case, purge, role, mod-log\n/config: staff-roles, ticket-channel, automod, autorole, mod-panel, reglement, reglement-post\n/welcome: setup, disable, preview, ghostping, goodbye, boost, panel, goodbye-panel, boost-panel\n/ticket: setup, panel, config, types, add, remove, list, transcript, force-close, close\n/music: play, pause, resume, skip, stop, queue, nowplaying, volume, disconnect\n/util: ping, uptime, bot-info, avatar, banner, serverinfo, userinfo, members, channels, roles, emojis, boosts, say, embed, poll, effectif, hierarchie, staff, afk, remind\n/help (standalone): shows commands by category\n/fun: coinflip, dice, 8ball, ship, rate\n/backup: create, list, restore, delete\n/stats: user, server\n/raid: config, log, status, whitelist, lockdown, massban, scan, panel, blacklist\n/ghostping: send\n/ai: panel\n/language: choose language\n\nNatural commands: mute, unmute, kick, ban, unban, softban, warn, unwarn, jail, unjail, say.\nProtections: anti-raid, anti-nuke, anti-spam, anti-mention, anti-invite, anti-caps, anti-bot, anti-alt, anti-link, lockdown.\nData: MongoDB Atlas.\nIf asked who made you, say Zero. You are sarcastic but nice.]\n\n{user_name}: {message_content}\nDev Hub:",
    "de": "[SYSTEM: Du bist Dev Hub, ein Discord-Bot erstellt von Zero (ID: 1167362445032050810). Seite: https://site-peach-iota-9e6xatqwnu.vercel.app. Einladung: https://discord.gg/vn6NEvATXZ. Antworte auf Deutsch, kurz und witzig. Keine Emojis. Du bist KEIN LLM, du bist Dev Hub, ein Discord-Bot.\n\nDu kennst alle deine Befehle (78+ in 12 Gruppen):\n/mod: warn, warnings, clearwarns, mute, unmute, timeout, kick, ban, unban, softban, jail, history, case, purge, role, mod-log\n/config: staff-roles, ticket-channel, automod, autorole, mod-panel, reglement, reglement-post\n/welcome: setup, disable, preview, ghostping, goodbye, boost, panel, goodbye-panel, boost-panel\n/ticket: setup, panel, config, types, add, remove, list, transcript, force-close, close\n/music: play, pause, resume, skip, stop, queue, nowplaying, volume, disconnect\n/util: ping, uptime, bot-info, avatar, banner, serverinfo, userinfo, members, channels, roles, emojis, boosts, say, embed, poll, effectif, hierarchie, staff, afk, remind\n/help (standalone): Zeigt Befehle nach Kategorie\n/fun: coinflip, dice, 8ball, ship, rate\n/backup: create, list, restore, delete\n/stats: user, server\n/raid: config, log, status, whitelist, lockdown, massban, scan, panel, blacklist\n/ghostping: send\n/ai: panel\n/language: Sprache waehlen\n\nNatuerliche Befehle: mute, unmute, kick, ban, unban, softban, warn, unwarn, jail, unjail, say.\nProtections: anti-raid, anti-nuke, anti-spam, anti-mention, anti-invite, anti-caps, anti-bot, anti-alt, anti-link, lockdown.\nDaten: MongoDB Atlas.\nWenn man dich fragt wer dich gemacht hat, sag Zero. Du bist sarcastisch aber nett.]\n\n{user_name}: {message_content}\nDev Hub:",
}

AI_FALLBACKS = {
    "fr": "Je sais pas quoi dire la.",
    "en": "I got nothing to say.",
    "de": "Ich habe nichts zu sagen.",
}


async def get_ai_response(message_content, user_name, guild_id=None):
    lang = get_lang(guild_id) if guild_id else "fr"
    try:
        import g4f
        prompt = AI_PROMPTS.get(lang, AI_PROMPTS["fr"]).format(
            user_name=user_name, message_content=message_content
        )
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
    return AI_FALLBACKS.get(lang, AI_FALLBACKS["fr"])


import re as _re
import json as _json


ACTION_KEYWORDS = {
    "mute":    ["mute", "muet", "muet", "tais toi", "tais-toi", "ferme la", "ferme", "calme", "calme toi", "silence", "bouche close", "shut up", "shut", "nique ta gueule"],
    "unmute":  ["unmute", "démute", "demute", "peux parler", "parle", "retire le mute", "enleve le mute"],
    "kick":    ["kick", "kicke", "vire", "viré", "expulse", "expulser", "degage", "dégage", "sort", "sors", "fait partir", "va t'en", "va dehors"],
    "ban":     ["ban", "bannis", "banir", "banish", "perma", "ban def", "ban permanent", "détruit", "supprime"],
    "unban":   ["unban", "débannis", "debannis", "retire le ban", "enleve le ban", "débanis"],
    "softban": ["softban", "soft ban", "ban temp", "ban temporaire"],
    "warn":    ["warn", "avertis", "avertir", "attention", "premier avertissement", "strike", "strike"],
    "unwarn":  ["unwarn", "déavertis", "déavertir", "retire le avertissement", "enleve le avertissement", "clearwarns", "clear warns", "supprime les warns"],
    "jail":    ["jail", "jailer", "prison", "incarcere", "incarcérer", "met en prison", "enferme"],
    "unjail":  ["unjail", "déjailer", "déjail", "libere", "libérer", "sort de prison", "retire de prison", "enleve de prison"],
    "say":     ["envoie", "envoyer", "envoye", "dit", "dis", "write", "send", "message"],
}

ACTION_MAP = {
    "mute": "mute", "unmute": "unmute", "kick": "kick", "ban": "ban",
    "unban": "unban", "softban": "softban", "warn": "warn", "unwarn": "unwarn",
    "jail": "jail", "unjail": "unjail", "timeout": "mute", "say": "say",
}


def _fuzzy_match(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw in text_lower:
            return True
    words = text_lower.split()
    for kw in keywords:
        kw_words = kw.split()
        for i in range(len(words)):
            for j in range(len(kw_words)):
                if i + j < len(words):
                    if words[i + j] == kw_words[j]:
                        continue
                    else:
                        break
                else:
                    break
            else:
                return True
    return False


def _extract_target_from_text(content, guild, bot_id):
    mention_match = _re.search(r'<@!?(\d+)>', content)
    if mention_match:
        uid = int(mention_match.group(1))
        if uid != bot_id:
            return uid

    content_lower = content.lower()
    member = None
    for m in guild.members:
        if m.id == bot_id:
            continue
        name_lower = m.display_name.lower()
        if name_lower in content_lower:
            member = m
            break
        if m.name.lower() in content_lower:
            member = m
            break
    if member:
        return member.id

    for m in guild.members:
        if m.id == bot_id:
            continue
        name_lower = m.display_name.lower()
        if any(w in content_lower for w in name_lower.split() if len(w) > 2):
            member = m
            break
    if member:
        return member.id

    return None


def _extract_reason(content, action_word):
    cleaned = content.lower()
    cleaned = _re.sub(r'<@!?\d+>', '', cleaned)
    for syns in ACTION_KEYWORDS.values():
        for syn in syns:
            cleaned = cleaned.replace(syn, '')
    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
    if cleaned and len(cleaned) > 1:
        return cleaned
    return "Aucune raison"


def _extract_channel_from_text(content, guild):
    ch_match = _re.search(r'<#(\d+)>', content)
    if ch_match:
        ch = guild.get_channel(int(ch_match.group(1)))
        if ch:
            return ch

    content_lower = content.lower()
    for ch in guild.text_channels:
        if ch.name.lower() in content_lower or f"#{ch.name}" in content_lower:
            return ch

    for ch in guild.text_channels:
        if any(w in content_lower for w in ch.name.split("-") if len(w) > 2):
            return ch

    return None


def _extract_say_content(content, guild, bot_id):
    content = content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()

    content = _re.sub(r'<#\d+>', '', content).strip()

    for syn in ACTION_KEYWORDS["say"]:
        content_lower = content.lower()
        idx = content_lower.find(syn)
        if idx != -1:
            content = content[idx + len(syn):]
            break

    content = content.strip()
    content = content.strip('"').strip("'").strip("«").strip("»")
    content = content.strip()
    return content if content else None


def parse_natural_command(content, bot_id, guild):
    content = content.strip()
    content = content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()

    if not content:
        return None

    action = None
    action_word = None
    for act, synonyms in ACTION_KEYWORDS.items():
        if _fuzzy_match(content, synonyms):
            action = ACTION_MAP.get(act, act)
            for syn in synonyms:
                if syn in content.lower():
                    action_word = syn
                    break
            break

    if not action:
        ai_hints = {
            "mute": ["calme", "ferme", "tais", "bouche", "silence", "shut", "parle mal", "insulte", "chaotique", "toxique", "emmerde", "emmerde", "relou", "pourri", "ennuie"],
            "kick": ["vire", "degage", "part", "sors", "pas bien", "probleme", "problème", "embête", "geule"],
            "ban": ["detruit", "supprime", "def", "permanent", "trop loin", "abus", "hack", "nsfw", "raid"],
            "warn": ["attention", "strike", "premier", "alerte", "1ere"],
            "jail": ["prison", "enferme", "cache", "bloque"],
        }
        for act, hints in ai_hints.items():
            if any(h in content.lower() for h in hints):
                target_id = _extract_target_from_text(content, guild, bot_id)
                if target_id:
                    action = act
                    break

    if not action:
        return None

    if action == "say":
        target_channel = _extract_channel_from_text(content, guild)
        say_msg = _extract_say_content(content, guild, bot_id)
        if not say_msg:
            return None
        return {"action": "say", "target_id": "0", "reason": say_msg, "channel_id": str(target_channel.id) if target_channel else None}

    target_id = _extract_target_from_text(content, guild, bot_id)
    if not target_id:
        return None

    reason = _extract_reason(content, action_word or action)

    return {"action": action, "target_id": str(target_id), "reason": reason}


async def execute_natural_command(message, parsed):
    guild = message.guild
    if not guild:
        return

    action = parsed["action"]
    reason = parsed["reason"]
    gid = str(guild.id)

    await message.delete()

    if action == "say":
        ch_id = parsed.get("channel_id")
        channel = guild.get_channel(int(ch_id)) if ch_id else message.channel
        if not channel:
            channel = message.channel
        await channel.send(reason)
        await message.channel.send(t("nl_say_sent", gid, channel=channel.mention), delete_after=8)
        return

    target_id = int(parsed["target_id"])
    member = guild.get_member(target_id)

    if action == "mute":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        until = datetime.now(timezone.utc) + timedelta(minutes=5)
        await member.timeout(until, reason=reason)
        await message.channel.send(t("nl_muted", gid, user=member.display_name, duration="5 min", reason=reason), delete_after=8)
        await log_mod(guild, "Mute (5 min)", message.author, member, reason)

    elif action == "unmute":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        await member.timeout(None, reason=reason)
        await message.channel.send(t("nl_unmuted", gid, user=member.display_name, reason=reason), delete_after=8)
        await log_mod(guild, "Unmute", message.author, member, reason)

    elif action == "timeout":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        until = datetime.now(timezone.utc) + timedelta(minutes=10)
        await member.timeout(until, reason=reason)
        await message.channel.send(t("mod_timeout", gid, user=member.display_name, duration="10 min", reason=reason), delete_after=8)
        await log_mod(guild, "Timeout (10 min)", message.author, member, reason)

    elif action == "kick":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        await member.kick(reason=reason)
        await message.channel.send(t("nl_kicked", gid, user=member.display_name, reason=reason), delete_after=8)
        await log_mod(guild, "Kick", message.author, member, reason)

    elif action == "ban":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        await member.ban(reason=reason)
        await message.channel.send(t("nl_banned", gid, user=member.display_name, reason=reason), delete_after=8)
        await log_mod(guild, "Ban", message.author, member, reason)

    elif action == "softban":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        await member.ban(reason=reason)
        await guild.unban(member, reason="Softban")
        await message.channel.send(t("nl_softbanned", gid, user=member.display_name, reason=reason), delete_after=8)
        await log_mod(guild, "Softban", message.author, member, reason)

    elif action == "warn":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        warns = load_warns()
        if gid not in warns:
            warns[gid] = {}
        uid = str(target_id)
        if uid not in warns[gid]:
            warns[gid][uid] = []
        warns[gid][uid].append({"reason": reason, "mod": str(message.author.id), "time": datetime.now(timezone.utc).isoformat()})
        save_warns(warns)
        count = len(warns[gid][uid])
        await message.channel.send(t("nl_warned", gid, user=member.display_name, count=count, reason=reason), delete_after=8)
        await log_mod(guild, f"Warn ({count})", message.author, member, reason)

    elif action == "jail":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        jail_data = load_jail()
        if gid not in jail_data:
            jail_data[gid] = {}
        roles_backup = [r.id for r in member.roles[1:]]
        jail_data[gid][str(target_id)] = {"roles": roles_backup, "time": datetime.now(timezone.utc).isoformat()}
        save_jail(jail_data)
        await member.edit(roles=[], reason="Jail")
        await message.channel.send(t("nl_jailed", gid, user=member.display_name, reason=reason), delete_after=8)
        await log_mod(guild, "Jail", message.author, member, reason)

    elif action == "unjail":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        jail_data = load_jail()
        uid = str(target_id)
        if gid in jail_data and uid in jail_data[gid]:
            saved_roles = jail_data[gid][uid].get("roles", [])
            await member.edit(roles=[guild.get_role(rid) for rid in saved_roles if guild.get_role(rid)], reason="Unjail")
            del jail_data[gid][uid]
            save_jail(jail_data)
            await message.channel.send(t("nl_unjailed", gid, user=member.display_name, reason=reason), delete_after=8)
            await log_mod(guild, "Unjail", message.author, member, reason)
        else:
            await message.channel.send(t("mod_not_jailed", gid), delete_after=5)

    elif action == "unwarn":
        if not member:
            await message.channel.send(t("mod_member_not_found", gid), delete_after=5)
            return
        warns = load_warns()
        uid = str(target_id)
        if gid in warns and uid in warns[gid] and warns[gid][uid]:
            warns[gid][uid].clear()
            save_warns(warns)
            await message.channel.send(t("nl_unwarned", gid, user=member.display_name), delete_after=8)
            await log_mod(guild, "Unwarn (clear)", message.author, member, reason)
        else:
            await message.channel.send(t("mod_no_warns", gid), delete_after=5)

    elif action == "unban":
        try:
            user = await bot.fetch_user(target_id)
            ban = await guild.fetch_ban(user)
            await guild.unban(user, reason=reason)
            await message.channel.send(t("mod_unbanned", gid, user=user.name, reason=reason), delete_after=8)
            await log_mod(guild, "Unban", message.author, user, reason)
        except discord.NotFound:
            await message.channel.send(t("mod_not_banned", gid), delete_after=5)


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
        row.add_item(discord.ui.Button(label="Aperçu", style=discord.ButtonStyle.secondary, custom_id="wp_preview"))
        row.add_item(discord.ui.Button(label="Désactiver", style=discord.ButtonStyle.danger, custom_id="wp_disable"))
        container.add_item(row)
        self.add_item(container)


@welcome.command(name="panel", description="Panel de configuration de l'accueil")
@admin_or_owner()
async def welcome_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    view = WelcomePanel(settings, gid, interaction.guild)
    await interaction.response.send_message(view=view, ephemeral=True)


# --- GOODBYE PANEL ---
@welcome.command(name="goodbye-panel", description="Panel de configuration du départ")
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
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
@admin_or_owner()
async def reglement_config(interaction: discord.Interaction):
    await interaction.response.send_modal(ReglementModal())


@config.command(name="reglement-post", description="Poster le panel de reglement")
@admin_or_owner()
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
                emoji=discord.PartialEmoji(name="3367whiteverification", id=1544825304374313070)
            ))
            container.add_item(row)

        view.add_item(container)
        await reglement_channel.send(view=view)

    await interaction.response.send_message(f"Reglement publie dans {reglement_channel.mention} !", ephemeral=True)


# --- AI PANEL ---
@ai.command(name="panel", description="Panel de configuration de l'IA")
@admin_or_owner()
async def ai_panel(interaction: discord.Interaction):
    settings = load_settings()
    gid = str(interaction.guild.id)
    s = settings.get(gid, {})
    lang = s.get("language", "fr")
    ai = "ON" if s.get("ai_enabled", True) else "OFF"

    ai_labels = {
        "fr": ("Activer", "Desactiver", "## Panel IA", "**Etat :**", "**Mode :** Reponse intelligente (GPT-4 via g4f, local)", "**Usage :** Mentionne le bot + ton message", "**Gratuit :** Pas de cle API requise"),
        "en": ("Enable", "Disable", "## AI Panel", "**Status:**", "**Mode:** Smart response (GPT-4 via g4f, free)", "**Usage:** Mention the bot + your message", "**Free:** No API key required"),
        "de": ("Aktivieren", "Deaktivieren", "## KI-Panel", "**Status:**", "**Modus:** Intelligente Antwort (GPT-4 via g4f, kostenlos)", "**Benutzung:** Erwaehne den Bot + deine Nachricht", "**Kostenlos:** Kein API-Schluessel noetig"),
    }
    labels = ai_labels.get(lang, ai_labels["fr"])

    view = discord.ui.LayoutView(timeout=120)
    container = discord.ui.Container(accent_colour=11581636)
    container.add_item(discord.ui.TextDisplay(labels[2]))
    container.add_item(discord.ui.TextDisplay(
        f"{labels[3]} {ai}\n"
        f"{labels[4]}\n"
        f"{labels[5]}\n"
        f"{labels[6]}"
    ))
    row = discord.ui.ActionRow()
    row.add_item(discord.ui.Button(label=labels[0], style=discord.ButtonStyle.success, custom_id="ai_on"))
    row.add_item(discord.ui.Button(label=labels[1], style=discord.ButtonStyle.danger, custom_id="ai_off"))
    container.add_item(row)
    view.add_item(container)
    await interaction.response.send_message(view=view, ephemeral=True)


# ──────────────────────────────────────────────
#  PANELS — HANDLER (components + modals)
# ──────────────────────────────────────────────
# Tout est géré dans le premier on_interaction au-dessus.
# Les handlers ci-dessous ont été fusionnés dans celui du ticket/help.

# ─── ENREGISTREMENT DES GROUPES ───
for g in [mod, config, welcome, ticket, music, util, fun, backup, stats, raid, ghostping, ai, giveaway, poll_cmd, level_cmd, log, botillion]:
    bot.tree.add_command(g)

bot.run(TOKEN)
