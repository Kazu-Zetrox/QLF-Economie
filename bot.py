import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))
import random
import asyncio
import time
import io
import html
import re
import aiohttp
from aiohttp import web
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import db

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)
bot.remove_command('help')

COOLDOWNS = {
    'work': 600,    # 10 minutes
    'slut': 900,    # 15 minutes
    'steal': 1800,  # 30 minutes
    'blackjack': 600,  # 10 minutes
    'daily': 86400,  # 24 hours
    'weekly': 604800,  # 7 days
    'crime': 1200,  # 20 minutes
}

SHOP_ITEMS = {
    'sky': {'name': 'Ciel Clair', 'description': 'Une touche légère et lumineuse.', 'price': 100, 'color': '#87CEEB', 'gif': ''},
    'ocean': {'name': 'Marée Bleue', 'description': 'Un style frais comme la mer.', 'price': 300, 'color': '#3498DB', 'gif': ''},
    'rose': {'name': 'Pink District', 'description': 'Une signature rose bien visible.', 'price': 500, 'color': '#E91E63', 'gif': ''},
    'gold': {'name': 'Fortune Dorée', 'description': 'Pour afficher tes premiers gros billets.', 'price': 1500, 'color': '#F1C40F', 'gif': ''},
    'matrix': {'name': 'Code Vert', 'description': 'Le style des joueurs qui calculent tout.', 'price': 2500, 'color': '#2ECC71', 'gif': ''},
    'rainbow': {
        'name': 'Arc-en-ciel animé',
        'description': 'Une bannière GIF colorée qui attire le regard.',
        'price': 5000,
        'color': '#FF4FD8',
        'gif': 'https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif',
    },
    'galaxy': {
        'name': 'Nébuleuse violette',
        'description': 'Un profil qui semble venir d’une autre galaxie.',
        'price': 10000,
        'color': '#8E44AD',
        'gif': 'https://media.giphy.com/media/26BRzozg4TCBXv6QU/giphy.gif',
    },
    'diamond': {'name': 'Cristal Azur', 'description': 'Brillant, rare et difficile à manquer.', 'price': 25000, 'color': '#00E5FF', 'gif': ''},
    'royal': {'name': 'Couronne Impériale', 'description': 'Le profil réservé aux grosses fortunes.', 'price': 50000, 'color': '#9B59B6', 'gif': ''},
    'cosmic': {
        'name': 'Cosmos QLF',
        'description': 'Un effet spatial pour les profils ambitieux.',
        'price': 100000,
        'color': '#111827',
        'gif': 'https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif',
    },
    'obsidian': {'name': 'Obsidienne Noire', 'description': 'Sobre, sombre et extrêmement chère.', 'price': 250000, 'color': '#17202A', 'gif': ''},
    'infinity': {'name': 'Infini Bleu', 'description': 'Un éclat réservé aux millionnaires.', 'price': 1000000, 'color': '#00BFFF', 'gif': ''},
    'qlf_royal': {'name': 'Trône QLF', 'description': 'Le symbole des plus grandes fortunes du serveur.', 'price': 5000000, 'color': '#FFD700', 'gif': ''},
    'qlf_legend': {'name': 'Légende QLF', 'description': 'Le niveau ultime du shop officiel QLF.', 'price': 10000000, 'color': '#FF4500', 'gif': ''},
}

QLF_BLUE = 0x5865F2
ADMIN_MENU_CHANNEL_ID = 1539936706130612254

async def resolve_video_url(url: str):
    clean_url = url.lower().split('?')[0]
    if clean_url.endswith(('.mp4', '.webm', '.mov')) or 'tenor.com/' not in clean_url:
        return url
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {'User-Agent': 'Mozilla/5.0 QLF-Economy-Bot'}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return url
                page = await response.text()
        patterns = (
            r'<meta[^>]+property=["\']og:video(?::url)?["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:video(?::url)?["\']',
        )
        for pattern in patterns:
            match = re.search(pattern, page, re.IGNORECASE)
            if match:
                media_url = html.unescape(match.group(1)).replace('\\u0026', '&')
                if media_url.lower().split('?')[0].endswith(('.mp4', '.webm', '.mov')):
                    return media_url
    except (aiohttp.ClientError, asyncio.TimeoutError):
        pass
    return url

SHOP_TITLES = {
    'sky': 'Nouveau du QLF', 'ocean': 'Marin QLF', 'rose': 'Icône Rose', 'gold': 'Golden Boss',
    'matrix': 'Codeur Vert', 'rainbow': 'Spectre Arc-en-ciel', 'galaxy': 'Voyageur Stellaire',
    'diamond': 'Cristal Vivant', 'royal': 'Roi du QLF', 'cosmic': 'Seigneur Cosmos',
    'obsidian': 'Ombre QLF', 'infinity': 'Infini QLF', 'qlf_royal': 'Souverain QLF', 'qlf_legend': 'Légende QLF',
}
for shop_item_id, shop_item in SHOP_ITEMS.items():
    shop_item['title'] = SHOP_TITLES.get(shop_item_id, shop_item['name'])

ITEM_EMOJIS = {
    'sky': '☁️', 'ocean': '🌊', 'rose': '🌹', 'gold': '🪙', 'matrix': '🟢',
    'rainbow': '🌈', 'galaxy': '🌌', 'diamond': '💎', 'royal': '👑', 'cosmic': '🚀',
    'obsidian': '🖤', 'infinity': '♾️', 'qlf_royal': '🏰', 'qlf_legend': '🏆',
}

SHOP_FRAMES = {
    'sky': '☁️ Cadre Ciel', 'ocean': '🌊 Cadre Vagues', 'rose': '🌹 Cadre Rose',
    'gold': '🪙 Cadre Doré', 'matrix': '🟢 Cadre Digital', 'rainbow': '🌈 Cadre Arc-en-ciel',
    'galaxy': '🌌 Cadre Galaxie', 'diamond': '💎 Cadre Cristal', 'royal': '👑 Cadre Royal',
    'cosmic': '🚀 Cadre Cosmos', 'obsidian': '🖤 Cadre Obsidienne', 'infinity': '♾️ Cadre Infini',
    'qlf_royal': '🏰 Cadre Trône QLF', 'qlf_legend': '🏆 Cadre Légende QLF',
}
for shop_item_id, shop_item in SHOP_ITEMS.items():
    shop_item['frame'] = SHOP_FRAMES.get(shop_item_id, '✨ Cadre QLF classique')

def get_item_rarity(price: int):
    if price <= 2500:
        return '⚪ Commun'
    if price <= 100000:
        return '🔵 Premium'
    if price <= 1000000:
        return '🟣 Épique'
    return '🟡 Légendaire QLF'

ACHIEVEMENTS = {
    'first_steps': ('Premiers billets', 'Atteindre $100 de richesse', lambda user, items: user['cash'] + user['bank'] >= 100),
    'worker': ('Travailleur', 'Atteindre $1,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 1000),
    'saver': ('Économe', 'Atteindre $5,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 5000),
    'rich': ('Riche', 'Atteindre $10,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 10000),
    'tycoon': ('Magnat', 'Atteindre $50,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 50000),
    'ultra_rich': ('Très riche', 'Atteindre $100,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 100000),
    'legend': ('Légende', 'Atteindre $500,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 500000),
    'millionaire': ('Millionnaire', 'Atteindre $1,000,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 1000000),
    'multi_millionaire': ('Multi-millionnaire', 'Atteindre $10,000,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 10000000),
    'billionaire': ('Fortune colossale', 'Atteindre $100,000,000 de richesse', lambda user, items: user['cash'] + user['bank'] >= 100000000),
    'banker': ('Gros banquier', 'Avoir $10,000 en banque', lambda user, items: user['bank'] >= 10000),
    'vault': ('Coffre-fort vivant', 'Avoir $100,000 en banque', lambda user, items: user['bank'] >= 100000),
    'bank_empire': ('Empire bancaire', 'Avoir $1,000,000 en banque', lambda user, items: user['bank'] >= 1000000),
    'cash_king': ('Roi du liquide', 'Avoir $10,000 sur soi', lambda user, items: user['cash'] >= 10000),
    'cash_lord': ('Seigneur du liquide', 'Avoir $100,000 sur soi', lambda user, items: user['cash'] >= 100000),
    'cash_mountain': ('Montagne de billets', 'Avoir $1,000,000 sur soi', lambda user, items: user['cash'] >= 1000000),
    'first_purchase': ('Premier achat', 'Posséder 1 objet de la boutique', lambda user, items: len(items) >= 1),
    'collector': ('Collectionneur', 'Posséder 3 objets de la boutique', lambda user, items: len(items) >= 3),
    'fashionista': ('Fashionista', 'Posséder 5 objets de la boutique', lambda user, items: len(items) >= 5),
    'wardrobe': ('Garde-robe complète', 'Posséder 8 objets de la boutique', lambda user, items: len(items) >= 8),
    'shopaholic': ('Accro à la boutique', 'Posséder 10 objets de la boutique', lambda user, items: len(items) >= 10),
    'complete_collection': ('Collection complète', 'Posséder tous les objets de la boutique', lambda user, items: len(items) >= len(SHOP_ITEMS)),
    'gif_fan': ('Fan de GIF', 'Posséder une bannière GIF', lambda user, items: any(item in items for item in ('rainbow', 'galaxy', 'cosmic'))),
    'diamond': ('Diamant brut', 'Posséder le thème Diamant', lambda user, items: 'diamond' in items),
    'royal': ('Sang royal', 'Posséder le thème Royal', lambda user, items: 'royal' in items),
    'rainbow': ('Arc-en-ciel', 'Posséder la bannière Arc-en-ciel', lambda user, items: 'rainbow' in items),
    'galaxy': ('Voyageur stellaire', 'Posséder la bannière Galaxie', lambda user, items: 'galaxy' in items),
    'cosmic': ('Au-delà des étoiles', 'Posséder la bannière Cosmic', lambda user, items: 'cosmic' in items),
    'premium_trio': ('Trio premium', 'Posséder Diamant, Royal et Cosmic', lambda user, items: all(item in items for item in ('diamond', 'royal', 'cosmic'))),
    'ultimate_style': ('Style ultime', 'Posséder 10 objets et $1,000,000 de richesse', lambda user, items: len(items) >= 10 and user['cash'] + user['bank'] >= 1000000),
}

ACHIEVEMENT_CATEGORIES = {
    'first_steps': 'Richesse', 'worker': 'Richesse', 'saver': 'Richesse', 'rich': 'Richesse',
    'tycoon': 'Richesse', 'ultra_rich': 'Richesse', 'legend': 'Richesse', 'millionaire': 'Richesse', 'multi_millionaire': 'Richesse', 'billionaire': 'Richesse',
    'banker': 'Banque & cash', 'vault': 'Banque & cash', 'bank_empire': 'Banque & cash', 'cash_king': 'Banque & cash', 'cash_lord': 'Banque & cash', 'cash_mountain': 'Banque & cash',
    'first_purchase': 'Collection', 'collector': 'Collection', 'fashionista': 'Collection',
    'wardrobe': 'Collection', 'shopaholic': 'Collection', 'complete_collection': 'Collection', 'gif_fan': 'Prestige',
    'diamond': 'Prestige', 'royal': 'Prestige', 'rainbow': 'Prestige', 'galaxy': 'Prestige', 'cosmic': 'Prestige', 'premium_trio': 'Prestige', 'ultimate_style': 'Prestige',
}

PENDING_DUELS = {}

async def action_dm(member: discord.Member, action: str, moderator: discord.Member, reason: str, server_name: str, duration: str = None, extra_text: str = None):
    if not member or member.bot:
        return
    embed = discord.Embed(
        title=f"Tu as été {action} sur {server_name}",
        description=f"Raison : **{reason}**",
        color=discord.Color.dark_red() if action in ('banni', 'expulsé', 'warn') else discord.Color.orange(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    if duration:
        embed.add_field(name='⏳ Durée', value=duration, inline=True)
    joined_at = member.joined_at
    if joined_at:
        joined_ts = int(joined_at.timestamp())
        embed.add_field(name='📅 Arrivé le', value=f"<t:{joined_ts}:F>", inline=True)
        delta = datetime.utcnow() - joined_at.replace(tzinfo=None)
        embed.add_field(name='⏱️ Temps sur le serveur', value=f"{humanize_duration(int(delta.total_seconds()))}", inline=True)
    embed.add_field(name='👑 Modérateur', value=moderator.mention, inline=True)
    if extra_text:
        embed.add_field(name='ℹ️ Info', value=extra_text, inline=False)
    embed.set_footer(text='Contacte un administrateur pour toute question.')
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

@bot.event
async def on_ready():
    await db.init_db()
    try:
        for guild in bot.guilds:
            await bot.tree.sync(guild=guild)
    except Exception:
        pass
    print(f'Logged in as {bot.user}')

def check_cooldown(user_id: int, command: str):
    async def inner():
        last = await db.get_cooldown(user_id, command)
        now = int(time.time())
        cd = COOLDOWNS.get(command, 0)
        if now - last < cd:
            return cd - (now - last)
        return 0
    return inner

def video_view(video_url: str):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label='Ouvrir la vidéo', emoji='▶️', style=discord.ButtonStyle.link, url=video_url))
    return view


def humanize_duration(seconds: int):
    if seconds <= 0:
        return '0 seconde'
    parts = []
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        parts.append(f'{days}j')
    if hours:
        parts.append(f'{hours}h')
    if minutes:
        parts.append(f'{minutes}min')
    if secs and not parts:
        parts.append(f'{secs}s')
    return ' '.join(parts) if parts else '0 seconde'


async def notify_member_action(member: discord.Member, action: str, moderator: discord.Member, reason: str, server_name: str, duration: str = None):
    if not member or member.bot:
        return
    embed = discord.Embed(
        title=f"Tu as été {action} de {server_name}",
        description=f"Raison : **{reason}**",
        color=discord.Color.dark_red() if action in ('banni', 'expulsé') else discord.Color.orange(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    joined_at = member.joined_at
    if joined_at:
        joined_ts = int(joined_at.timestamp())
        delta = datetime.utcnow() - joined_at.replace(tzinfo=None)
        embed.add_field(name='⏱️ Temps sur le serveur', value=f"{humanize_duration(int(delta.total_seconds()))}", inline=True)
        embed.add_field(name='📅 Arrivé le', value=f"<t:{joined_ts}:F>", inline=True)
    embed.add_field(name='👑 Modérateur', value=moderator.mention, inline=True)
    embed.add_field(name='🆔 ID', value=str(member.id), inline=True)
    if duration:
        embed.add_field(name='⏳ Durée', value=duration, inline=True)
    embed.set_footer(text='Si tu veux contester cette décision, contacte un administrateur.')
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass


@bot.command()
async def balance(ctx):
    u = await db.get_user(ctx.author.id)
    await ctx.send(f"Argent sur toi: ${u['cash']} | Bank: ${u['bank']}")

@bot.command(name='profile')
async def profile(ctx):
    user = await db.get_user(ctx.author.id)
    customization = await db.get_profile(ctx.author.id)
    stats = await db.get_stats(ctx.author.id)
    total = user['cash'] + user['bank']
    equipped_item = SHOP_ITEMS.get(customization['equipped_item'])
    has_customization = equipped_item is not None and customization['equipped_item'] in await db.get_inventory(ctx.author.id)
    try:
        embed_color = int(customization['color'].lstrip('#'), 16) if has_customization else 0x2B2D31
    except (AttributeError, ValueError):
        embed_color = 0x2B2D31
    if has_customization:
        profile_title = f"{ITEM_EMOJIS.get(customization['equipped_item'], '✨')} Profil QLF · {ctx.author.display_name}"
        profile_description = f"**{equipped_item['name']}** · {get_item_rarity(equipped_item['price'])}"
    else:
        profile_title = f"Profil QLF · {ctx.author.display_name}"
        profile_description = "Profil vierge · achète un objet dans `!shop` pour débloquer les effets."
    embed = discord.Embed(title=profile_title, description=profile_description, color=embed_color)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    equipped_emoji = ITEM_EMOJIS.get(customization['equipped_item'], '✨') if has_customization else '▫️'
    title_value = f"**{customization['title']}**" if has_customization else '*Aucun titre personnalisé*'
    frame_value = f"**{customization['frame']}**" if has_customization else '*Cadre classique*'
    embed.add_field(name='💰 Argent', value=f"Cash **${user['cash']}** · Bank **${user['bank']}**\nTotal **${total}**", inline=False)
    embed.add_field(name=f'{equipped_emoji} Personnalisation', value=f"Titre : {title_value}\nCadre : {frame_value}", inline=True)
    members = [member for member in ctx.guild.members if not member.bot]
    rows = await db.get_balances([member.id for member in members])
    server_balances = {user_id: cash + bank for user_id, cash, bank in rows}
    ranked_ids = sorted((member.id for member in members), key=lambda user_id: server_balances.get(user_id, 0), reverse=True)
    rank = ranked_ids.index(ctx.author.id) + 1 if ctx.author.id in ranked_ids else len(ranked_ids)
    if rank == 1:
        rank_title = '👑 Empereur QLF'
    elif rank <= 3:
        rank_title = '💎 Élite QLF'
    elif total >= 1000000:
        rank_title = '🏦 Magnat QLF'
    else:
        rank_title = '💵 Joueur QLF'
    embed.add_field(name='🏆 Classement', value=f"**#{rank}**/{len(ranked_ids)}\n{rank_title}", inline=True)
    items = await db.get_inventory(ctx.author.id)
    collection_emojis = ''.join(ITEM_EMOJIS.get(item_id, '✨') for item_id in items) or 'Aucun objet'
    effect_name = equipped_item['name'] if has_customization else 'Aucun effet équipé'
    collection_label = f"{len(items)}/{len(SHOP_ITEMS)} objets\n{collection_emojis}" if items else 'Aucun objet acheté\n`!shop` pour commencer'
    embed.add_field(name='🎨 Collection', value=collection_label, inline=True)
    embed.add_field(name='✨ Effet actif', value=f"{equipped_emoji} **{effect_name}**", inline=True)
    media_url = customization['video_url'] or customization['gif_url']
    video_url = await resolve_video_url(media_url) if customization['video_url'] else media_url
    if video_url and video_url != customization['video_url']:
        await db.set_custom_video(ctx.author.id, video_url)
    if video_url:
        embed.add_field(name='🎬 Vidéo du profil', value='Utilise le bouton sous la carte pour la regarder.', inline=False)
    unlocked = sum(condition(user, items) for _, _, condition in ACHIEVEMENTS.values())
    embed.add_field(name='🏆 Progression', value=f"Achievements **{unlocked}/{len(ACHIEVEMENTS)}**\nMembre depuis <t:{int((ctx.author.joined_at or ctx.author.created_at).timestamp())}:D>", inline=False)
    embed.add_field(
        name='🎰 Statistiques',
        value=(
            f"Gains **${stats['total_gains']:,}** · Pertes **${stats['total_losses']:,}**\n"
            f"Record **${stats['biggest_gain']:,}**"
        ).replace(',', ' '),
        inline=True,
    )
    embed.add_field(
        name='😈 Activités',
        value=(
            f"Vols **{stats['steals_success']} réussis / {stats['steals_failed']} ratés**\n"
            f"Crimes **{stats['crimes_success']} réussis / {stats['crimes_failed']} ratés**"
        ),
        inline=True,
    )
    if media_url:
        embed.set_footer(text='Vidéo personnalisée · ouvre le lien pour la lire')
    else:
        embed.set_footer(text='Profil vierge QLF · achète un objet avec !buy <objet>')
    await ctx.send(embed=embed, view=video_view(video_url) if media_url else None)

@bot.command(name='achievements')
async def achievements(ctx):
    user = await db.get_user(ctx.author.id)
    items = await db.get_inventory(ctx.author.id)
    unlocked = []
    locked = []
    categories = {}
    for achievement_id, (name, description, condition) in ACHIEVEMENTS.items():
        category = ACHIEVEMENT_CATEGORIES.get(achievement_id, 'Autres')
        categories.setdefault(category, {'unlocked': [], 'locked': []})
        line = f"**{name}**\n> **Objectif :** {description}"
        if condition(user, items):
            unlocked.append(line)
            categories[category]['unlocked'].append(line)
        else:
            locked.append(line)
            categories[category]['locked'].append(line)
    embed = discord.Embed(
        title=f"🏆 Achievements QLF · {ctx.author.display_name}",
        description=(
            f"Progression : **{len(unlocked)}/{len(ACHIEVEMENTS)}** débloqués\n"
            "✅ = débloqué · 🔒 = encore à débloquer"
        ),
        color=QLF_BLUE,
    )
    for category, values in categories.items():
        done = len(values['unlocked'])
        total = done + len(values['locked'])
        embed.add_field(name=f"📌 {category} · {done}/{total}", value='Voir les objectifs ci-dessous.', inline=False)
        for label, icon, lines in (
            ('Débloqués', '✅', values['unlocked']),
            ('À débloquer', '🔒', values['locked']),
        ):
            if lines:
                short_lines = [f"{icon} {line.replace(chr(10) + '> **Objectif :** ', ' · ')}" for line in lines]
                embed.add_field(name=label, value='\n'.join(short_lines), inline=False)
    embed.set_footer(text='Achievements du serveur QLF · Continue à jouer pour tout débloquer')
    await ctx.send(embed=embed)

@bot.command(name='shop')
async def shop(ctx):
    tiers = {'Départ': [], 'Premium': [], 'Légendaire QLF': []}
    for item_id, item in SHOP_ITEMS.items():
        item_emoji = ITEM_EMOJIS.get(item_id, '✨')
        line = (
            f"{item_emoji} **{item['name']}** · **${item['price']:,}** · {get_item_rarity(item['price'])}"
            f"\n*{item['title']}* · `!buy {item_id}` / `!equip {item_id}`"
        ).replace(',', ' ')
        if item['price'] <= 2500:
            tiers['Départ'].append(line)
        elif item['price'] <= 100000:
            tiers['Premium'].append(line)
        else:
            tiers['Légendaire QLF'].append(line)
    embed = discord.Embed(
        title='🛍️ Shop de QLF',
        description='**Achète** avec ton cash, puis **équipe** l’objet. Prix en argent liquide.',
        color=QLF_BLUE,
    )
    for tier_name, lines in tiers.items():
        if lines:
            embed.add_field(name=tier_name, value='\n\n'.join(lines), inline=False)
    embed.add_field(name='Exemple rapide', value='`!buy galaxy`  →  `!equip galaxy`  →  `!profile`', inline=False)
    embed.set_footer(text='Shop officiel du serveur QLF · !achievements pour progresser')
    await ctx.send(embed=embed)

@bot.command(name='inventory', aliases=['inventaire', 'items'])
async def inventory(ctx):
    owned_items = await db.get_inventory(ctx.author.id)
    profile_data = await db.get_profile(ctx.author.id)
    embed = discord.Embed(
        title=f"🎒 Inventaire QLF · {ctx.author.display_name}",
        description=f"**{len(owned_items)}/{len(SHOP_ITEMS)}** objets possédés",
        color=QLF_BLUE,
    )
    if not owned_items:
        embed.add_field(
            name='Inventaire vide',
            value='Tu ne possèdes encore aucun objet.\nUtilise `!shop` pour commencer.',
            inline=False,
        )
    else:
        lines = []
        for item_id in owned_items:
            item = SHOP_ITEMS.get(item_id)
            if not item:
                continue
            equipped = ' ✅ équipé' if item_id == profile_data['equipped_item'] else ''
            lines.append(
                f"{ITEM_EMOJIS.get(item_id, '✨')} **{item['name']}**{equipped}\n"
                f"{get_item_rarity(item['price'])} · {item['frame']} · Titre : *{item['title']}*"
            )
        embed.add_field(name='Objets possédés', value='\n\n'.join(lines), inline=False)
    equipped_item = SHOP_ITEMS.get(profile_data['equipped_item'])
    if equipped_item:
        embed.add_field(
            name='✨ Équipement actuel',
            value=f"{ITEM_EMOJIS.get(profile_data['equipped_item'], '✨')} **{equipped_item['name']}**\n`!equip <objet>` pour changer",
            inline=False,
        )
    embed.set_footer(text='Inventaire du serveur QLF · !shop pour voir les nouveautés')
    await ctx.send(embed=embed)

@bot.command(name='buy')
async def buy(ctx, item_id: str):
    item_id = item_id.lower()
    item = SHOP_ITEMS.get(item_id)
    if not item:
        await ctx.send("Objet inconnu. Utilise `!shop` pour voir la boutique.")
        return
    result = await db.buy_item(ctx.author.id, item_id, item['price'])
    if result == 'owned':
        await ctx.send("Tu possèdes déjà cet objet.")
    elif result == 'insufficient':
        await ctx.send(f"Tu n'as pas assez d'argent liquide. Prix : ${item['price']}.")
    else:
        await db.equip_item(ctx.author.id, item_id, item['color'], item['gif'], item['title'], item['frame'])
        item_emoji = ITEM_EMOJIS.get(item_id, '✨')
        await ctx.send(
            f"Shop QLF : {item_emoji} **{item['name']}** acheté et équipé !\n"
            f"Rareté : **{get_item_rarity(item['price'])}** · Cadre : **{item['frame']}**\n"
            f"Titre : **{item['title']}** · `!profile` pour voir le résultat."
        )

@bot.command(name='equip')
async def equip(ctx, item_id: str):
    item_id = item_id.lower()
    item = SHOP_ITEMS.get(item_id)
    if not item:
        await ctx.send("Objet inconnu. Utilise `!shop` pour voir la boutique.")
        return
    if await db.equip_item(ctx.author.id, item_id, item['color'], item['gif'], item['title'], item['frame']):
        await ctx.send(f"QLF : **{item['name']}** est équipé. Ton titre est maintenant **{item['title']}**.")
    else:
        await ctx.send(f"Tu ne possèdes pas `{item_id}`. Achète-le avec `!buy {item_id}`.")

@bot.command(name='setgif')
async def setgif(ctx, gif_url: str = None):
    if not gif_url:
        await ctx.send("Usage : `!setgif <lien>` ou `!setgif off`.")
        return
    if gif_url.lower() == 'off':
        await db.set_custom_gif(ctx.author.id, '')
        await ctx.send("GIF retiré.")
        return
    if not gif_url.startswith(('http://', 'https://')):
        await ctx.send("Le lien doit commencer par `https://`.")
        return
    await db.set_custom_gif(ctx.author.id, gif_url)
    await ctx.send("GIF enregistré. ✅")

@bot.command(name='setvideo')
async def setvideo(ctx, video_url: str = None):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('video/'):
            await ctx.send("Joins une vidéo `.mp4`, `.webm` ou `.mov`.")
            return
        await db.set_custom_video(ctx.author.id, attachment.url)
        await ctx.send("Vidéo enregistrée. ✅")
        return
    if not video_url:
        await ctx.send("Usage : joins une vidéo ou utilise `!setvideo <lien Tenor>`.")
        return
    if video_url.lower() == 'off':
        await db.set_custom_video(ctx.author.id, '')
        await ctx.send("Vidéo retirée.")
        return
    if not video_url.startswith(('http://', 'https://')):
        await ctx.send("Le lien doit commencer par `https://`.")
        return
    clean_url = video_url.lower().split('?')[0]
    is_tenor_link = 'tenor.com/' in clean_url
    is_direct_video = clean_url.endswith(('.mp4', '.webm', '.mov'))
    if not is_tenor_link and not is_direct_video:
        await ctx.send("Lien Tenor ou vidéo directe `.mp4`, `.webm`, `.mov` requis.")
        return
    resolved_url = await resolve_video_url(video_url)
    await db.set_custom_video(ctx.author.id, resolved_url)
    if resolved_url != video_url:
        await ctx.send("Vidéo Tenor convertie et enregistrée. ✅")
    else:
        await ctx.send("Vidéo enregistrée. ✅")

@bot.tree.command(name='kick', description='Expulser un membre du serveur')
@app_commands.describe(member='Le membre à expulser', reason='Raison de l\'expulsion')
@app_commands.checks.has_permissions(administrator=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie'):
    await interaction.guild.kick(member, reason=reason)
    await notify_member_action(member, 'expulsé', interaction.user, reason, interaction.guild.name)
    await interaction.response.send_message(f'{member.mention} a été expulsé pour : {reason}', ephemeral=True)


@bot.tree.command(name='ban', description='Bannir un membre du serveur')
@app_commands.describe(member='Le membre à bannir', reason='Raison du bannissement', delete_days='Nombre de jours de messages à supprimer')
@app_commands.checks.has_permissions(administrator=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie', delete_days: int = 0):
    await interaction.guild.ban(member, reason=reason, delete_message_days=max(0, min(delete_days, 7)))
    await notify_member_action(member, 'banni', interaction.user, reason, interaction.guild.name)
    await interaction.response.send_message(f'{member.mention} a été banni pour : {reason}', ephemeral=True)


@bot.tree.command(name='mute', description='Rendre un membre muet temporairement')
@app_commands.describe(member='Le membre à rendre muet', duration='Durée du mute, par exemple 10m, 1h, 24h', reason='Raison du mute')
@app_commands.checks.has_permissions(administrator=True)
async def slash_mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = 'Aucune raison fournie'):
    value = duration.strip().lower()
    multiplier = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    match = re.fullmatch(r'(?i)(\d+)([smhd])', value)
    if not match:
        await interaction.response.send_message('Format invalide. Exemple : `10m`, `1h`, `24h`.', ephemeral=True)
        return
    amount = int(match.group(1))
    unit = match.group(2).lower()
    seconds = amount * multiplier[unit]
    timeout_delta = timedelta(seconds=seconds)
    try:
        await member.timeout(timeout_delta, reason=reason)
    except Exception:
        await interaction.response.send_message('Je ne peux pas mute ce membre.', ephemeral=True)
        return
    await notify_member_action(member, 'mis en mute', interaction.user, reason, interaction.guild.name, f'{amount}{unit}')
    await interaction.response.send_message(f'{member.mention} a été mute pendant {amount}{unit} pour : {reason}', ephemeral=True)


@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f"Pong ! Latence: {round(bot.latency * 1000)} ms")


async def parse_duration(value: str):
    value = value.strip().lower()
    if not value:
        return None
    match = re.fullmatch(r'(\d+)([smhd])', value)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    return amount * multipliers[unit]


@bot.command(name='ban', aliases=['bannir'])
@commands.has_permissions(administrator=True)
async def ban_cmd(ctx, member: discord.Member = None, *, reason: str = 'Aucune raison fournie'):
    if member is None:
        await ctx.send('Utilise : `!ban @membre [raison]`')
        return
    if member.id == ctx.author.id:
        await ctx.send('Tu ne peux pas te bannir toi-même.')
        return
    await ctx.guild.ban(member, reason=reason, delete_message_days=0)
    await action_dm(member, 'banni', ctx.author, reason, ctx.guild.name)
    await ctx.send(f'{member.mention} a été banni pour : {reason}')


@bot.command(name='kick', aliases=['expulser'])
@commands.has_permissions(administrator=True)
async def kick_cmd(ctx, member: discord.Member = None, *, reason: str = 'Aucune raison fournie'):
    if member is None:
        await ctx.send('Utilise : `!kick @membre [raison]`')
        return
    if member.id == ctx.author.id:
        await ctx.send('Tu ne peux pas te kicker toi-même.')
        return
    await ctx.guild.kick(member, reason=reason)
    await action_dm(member, 'expulsé', ctx.author, reason, ctx.guild.name)
    await ctx.send(f'{member.mention} a été expulsé pour : {reason}')


@bot.command(name='mute', aliases=['muter'])
@commands.has_permissions(administrator=True)
async def mute_cmd(ctx, member: discord.Member = None, duration: str = None, *, reason: str = 'Aucune raison fournie'):
    if member is None:
        await ctx.send('Utilise : `!mute @membre 10m [raison]`')
        return
    if duration is None:
        await ctx.send('Précise une durée : `10m`, `1h`, `24h`.')
        return
    seconds = await parse_duration(duration)
    if seconds is None:
        await ctx.send('Format invalide. Exemple : `10m`, `1h`, `24h`.')
        return
    try:
        await member.timeout(timedelta(seconds=seconds), reason=reason)
    except Exception:
        await ctx.send('Je ne peux pas mute ce membre.')
        return
    await action_dm(member, 'mis en mute', ctx.author, reason, ctx.guild.name, duration)
    await ctx.send(f'{member.mention} a été mute pendant {duration} pour : {reason}')


@bot.command(name='unmute', aliases=['demute'])
@commands.has_permissions(administrator=True)
async def unmute_cmd(ctx, member: discord.Member = None, *, reason: str = 'Aucune raison fournie'):
    if member is None:
        await ctx.send('Utilise : `!unmute @membre [raison]`')
        return
    try:
        await member.timeout(None, reason=reason)
    except Exception:
        await ctx.send('Je ne peux pas unmute ce membre.')
        return
    await action_dm(member, 'unmute', ctx.author, reason, ctx.guild.name, extra_text='Tu as été rétabli sur le serveur.')
    await ctx.send(f'{member.mention} a été unmute pour : {reason}')


@bot.command(name='warn', aliases=['warm'])
@commands.has_permissions(administrator=True)
async def warn_cmd(ctx, member: discord.Member = None, *, reason: str = 'Aucune raison fournie'):
    if member is None:
        await ctx.send('Utilise : `!warn @membre [raison]`')
        return
    await action_dm(member, 'warn', ctx.author, reason, ctx.guild.name, extra_text='Ceci est un avertissement officiel du serveur.')
    await ctx.send(f'{member.mention} a reçu un avertissement : {reason}')


@bot.command(name='clear', aliases=['purge'])
@commands.has_permissions(administrator=True)
async def clear_cmd(ctx, amount: int = 0):
    if amount <= 0:
        await ctx.send('Utilise : `!clear 12` pour supprimer les 12 derniers messages.')
        return
    if amount > 100:
        await ctx.send('Le nombre max est 100 messages.')
        return
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f'🧹 {len(deleted)} messages supprimés.', delete_after=3)


@bot.tree.command(name='clear', description='Supprimer un nombre de messages du salon')
@app_commands.describe(count='Nombre de messages à supprimer')
@app_commands.checks.has_permissions(administrator=True)
async def slash_clear(interaction: discord.Interaction, count: int):
    if count <= 0:
        await interaction.response.send_message('Le nombre doit être supérieur à 0.', ephemeral=True)
        return
    if count > 100:
        await interaction.response.send_message('Le nombre max est 100 messages.', ephemeral=True)
        return
    deleted = await interaction.channel.purge(limit=count)
    await interaction.response.send_message(f'🧹 {len(deleted)} messages supprimés.', ephemeral=True)


def normalize_choice(value: str):
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned in ('pair', 'paire', 'even', 'p', '0'):
        return 'pair'
    if cleaned in ('impair', 'odd', 'i', '1'):
        return 'impair'
    return None


def draw_visual_card():
    value = random.randint(1, 13)
    suit = random.choice(['♠', '♥', '♦', '♣'])
    parity = 'pair' if value % 2 == 0 else 'impair'
    return value, suit, parity


@bot.command(name='duel')
async def duel(ctx, member: discord.Member = None, bet: str = '100', choice: str = None):
    if member is None:
        await ctx.send('Tu dois mentionner un membre avec `!duel @pseudo 100 pair`.')
        return
    if member.bot or member.id == ctx.author.id:
        await ctx.send('Tu dois défier un autre membre du serveur.')
        return
    choice = normalize_choice(choice)
    if choice is None:
        await ctx.send('Choisis ton côté : `pair` ou `impair`. Exemple : `!duel @pseudo 100 pair`.')
        return
    try:
        stake = int(bet)
    except ValueError:
        await ctx.send('La mise doit être un nombre. Exemple : `!duel @pseudo 250 pair`.')
        return
    if stake <= 0:
        await ctx.send('La mise doit être supérieure à 0.')
        return
    challenger = await db.get_user(ctx.author.id)
    if challenger['cash'] < stake:
        await ctx.send(f'Tu n’as pas assez d’argent pour miser ${stake}.')
        return
    PENDING_DUELS[ctx.author.id] = {'target_id': member.id, 'stake': stake, 'choice': choice}
    await ctx.send(
        f'{ctx.author.mention} défie {member.mention} en duel pour **${stake}** avec **{choice}** !\n'
        f'{member.mention}, accepte avec `!acc duel {ctx.author.mention} {"impair" if choice == "pair" else "pair"}`\n'
        f'Ou refuse avec `!dec duel {ctx.author.mention}`.'
    )


@bot.command(name='acc', aliases=['accept'])
async def accept_duel(ctx, *args):
    if len(args) < 3 or args[0].lower() != 'duel':
        await ctx.send('Utilise : `!acc duel @pseudo pair`')
        return
    try:
        target = await commands.MemberConverter().convert(ctx, ' '.join(args[1:-1]))
    except commands.BadArgument:
        await ctx.send('Membre introuvable. Utilise `!acc duel @pseudo pair`.')
        return
    accept_choice = normalize_choice(args[-1])
    if accept_choice is None:
        await ctx.send('Choisis une option valide : `pair` ou `impair`.')
        return
    duel_request = PENDING_DUELS.get(target.id)
    if not duel_request or duel_request['target_id'] != ctx.author.id:
        await ctx.send('Aucun duel en attente avec ce membre.')
        return
    if accept_choice == duel_request['choice']:
        await ctx.send(f'{ctx.author.mention}, tu dois choisir l’autre côté que {target.mention}. Le défi demande **{("impair" if duel_request["choice"] == "pair" else "pair")}**.')
        return
    stake = duel_request['stake']
    target_user = await db.get_user(target.id)
    if target_user['cash'] < stake:
        await ctx.send(f'{target.mention} n’a pas assez d’argent pour miser ${stake}.')
        del PENDING_DUELS[target.id]
        return
    if (await db.get_user(ctx.author.id))['cash'] < stake:
        await ctx.send(f'{ctx.author.mention} n’a pas assez d’argent pour miser ${stake}.')
        del PENDING_DUELS[target.id]
        return
    del PENDING_DUELS[target.id]
    if not await db.remove_cash(target.id, stake):
        await ctx.send(f'{target.mention} n’a plus assez d’argent pour ce duel.')
        return
    if not await db.remove_cash(ctx.author.id, stake):
        await ctx.send(f'{ctx.author.mention} n’a plus assez d’argent pour ce duel.')
        return
    card_value, card_suit, result = draw_visual_card()
    pot = stake * 2
    winner_id = target.id if result == duel_request['choice'] else ctx.author.id
    await db.change_cash(winner_id, pot)
    await db.record_gain(winner_id, pot)
    await db.log_duel(target.id, ctx.author.id, duel_request['choice'], accept_choice, stake, result, winner_id)
    winner_mention = ctx.guild.get_member(winner_id).mention if ctx.guild.get_member(winner_id) else target.mention
    await ctx.send(
        f'{ctx.author.mention} a accepté le duel !\n'
        f'🃏 Carte tirée : **{card_value}{card_suit}** -> **{result}**\n'
        f'Gagnant : {winner_mention}\n'
        f'Pot : **${pot}**'
    )


@bot.command(name='dec', aliases=['decline'])
async def decline_duel(ctx, *args):
    if len(args) < 2 or args[0].lower() != 'duel':
        await ctx.send('Utilise : `!dec duel @pseudo`')
        return
    try:
        target = await commands.MemberConverter().convert(ctx, ' '.join(args[1:]))
    except commands.BadArgument:
        await ctx.send('Membre introuvable. Utilise `!dec duel @pseudo`.')
        return
    duel_request = PENDING_DUELS.get(target.id)
    if not duel_request or duel_request['target_id'] != ctx.author.id:
        await ctx.send('Aucun duel en attente avec ce membre.')
        return
    del PENDING_DUELS[target.id]
    await ctx.send(f'{ctx.author.mention} a refusé le duel de {target.mention}.')


@bot.tree.command(name='duel', description='Défier un joueur en duel avec une mise d\'argent')
@app_commands.describe(member='Le membre à défier', bet='Mise en argent du duel', choice='Choisis pair ou impair')
async def slash_duel(interaction: discord.Interaction, member: discord.Member, bet: int, choice: str):
    normalized_choice = normalize_choice(choice)
    if normalized_choice is None:
        await interaction.response.send_message('Choisis `pair` ou `impair`.', ephemeral=True)
        return
    if member.bot or member.id == interaction.user.id:
        await interaction.response.send_message('Tu dois défier un autre membre du serveur.', ephemeral=True)
        return
    if bet <= 0:
        await interaction.response.send_message('La mise doit être positive.', ephemeral=True)
        return
    user = await db.get_user(interaction.user.id)
    if user['cash'] < bet:
        await interaction.response.send_message(f'Tu n’as pas assez d’argent pour miser ${bet}.', ephemeral=True)
        return
    PENDING_DUELS[interaction.user.id] = {'target_id': member.id, 'stake': bet, 'choice': normalized_choice}
    await interaction.response.send_message(
        f'{interaction.user.mention} défie {member.mention} en duel pour **${bet}** avec **{normalized_choice}** !\n'
        f'{member.mention}, accepte avec `/acceptduel {interaction.user.mention} {"impair" if normalized_choice == "pair" else "pair"}`\n'
        f'Ou refuse avec `/declineduel {interaction.user.mention}`.',
        ephemeral=False,
    )


@bot.tree.command(name='acceptduel', description='Accepter un duel avec pair ou impair')
@app_commands.describe(member='Le membre qui a défié', choice='Choisis pair ou impair')
async def slash_acceptduel(interaction: discord.Interaction, member: discord.Member, choice: str):
    accept_choice = normalize_choice(choice)
    if accept_choice is None:
        await interaction.response.send_message('Choisis `pair` ou `impair`.', ephemeral=True)
        return
    duel_request = PENDING_DUELS.get(member.id)
    if not duel_request or duel_request['target_id'] != interaction.user.id:
        await interaction.response.send_message('Aucun duel en attente avec ce membre.', ephemeral=True)
        return
    if accept_choice == duel_request['choice']:
        await interaction.response.send_message(f'Tu dois choisir l’autre côté. Le défi demandait **{("impair" if duel_request["choice"] == "pair" else "pair")}**.', ephemeral=True)
        return
    stake = duel_request['stake']
    if (await db.get_user(member.id))['cash'] < stake:
        await interaction.response.send_message(f'{member.mention} n’a pas assez d’argent pour ce duel.', ephemeral=True)
        del PENDING_DUELS[member.id]
        return
    if (await db.get_user(interaction.user.id))['cash'] < stake:
        await interaction.response.send_message(f'Tu n’as pas assez d’argent pour ce duel.', ephemeral=True)
        del PENDING_DUELS[member.id]
        return
    if not await db.remove_cash(member.id, stake):
        await interaction.response.send_message(f'{member.mention} n’a plus assez d’argent pour ce duel.', ephemeral=True)
        return
    if not await db.remove_cash(interaction.user.id, stake):
        await interaction.response.send_message(f'Tu n’as plus assez d’argent pour ce duel.', ephemeral=True)
        return
    del PENDING_DUELS[member.id]
    card_value, card_suit, result = draw_visual_card()
    pot = stake * 2
    winner_id = member.id if result == duel_request['choice'] else interaction.user.id
    await db.change_cash(winner_id, pot)
    await db.record_gain(winner_id, pot)
    await db.log_duel(member.id, interaction.user.id, duel_request['choice'], accept_choice, stake, result, winner_id)
    winner_name = interaction.guild.get_member(winner_id).mention if interaction.guild.get_member(winner_id) else member.mention
    await interaction.response.send_message(
        f'{interaction.user.mention} a accepté le duel !\n'
        f'🃏 Carte tirée : **{card_value}{card_suit}** -> **{result}**\n'
        f'Gagnant : {winner_name}\n'
        f'Pot : **${pot}**'
    )


@bot.tree.command(name='declineduel', description='Refuser un duel')
@app_commands.describe(member='Le membre qui a défié')
async def slash_declineduel(interaction: discord.Interaction, member: discord.Member):
    duel_request = PENDING_DUELS.get(member.id)
    if not duel_request or duel_request['target_id'] != interaction.user.id:
        await interaction.response.send_message('Aucun duel en attente avec ce membre.', ephemeral=True)
        return
    del PENDING_DUELS[member.id]
    await interaction.response.send_message(f'{interaction.user.mention} a refusé le duel de {member.mention}.')


@bot.tree.command(name='kick', description='Expulser un membre du serveur')
@app_commands.describe(member='Le membre à expulser', reason='Raison de l\'expulsion')
@app_commands.checks.has_permissions(administrator=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie'):
    await interaction.guild.kick(member, reason=reason)
    await action_dm(member, 'expulsé', interaction.user, reason, interaction.guild.name)
    await interaction.response.send_message(f'{member.mention} a été expulsé pour : {reason}', ephemeral=True)


@bot.tree.command(name='ban', description='Bannir un membre du serveur')
@app_commands.describe(member='Le membre à bannir', reason='Raison du bannissement', delete_days='Nombre de jours de messages à supprimer')
@app_commands.checks.has_permissions(administrator=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie', delete_days: int = 0):
    await interaction.guild.ban(member, reason=reason, delete_message_days=max(0, min(delete_days, 7)))
    await action_dm(member, 'banni', interaction.user, reason, interaction.guild.name)
    await interaction.response.send_message(f'{member.mention} a été banni pour : {reason}', ephemeral=True)


@bot.tree.command(name='mute', description='Rendre un membre muet temporairement')
@app_commands.describe(member='Le membre à rendre muet', duration='Durée du mute, exemple : 10m, 1h, 24h', reason='Raison du mute')
@app_commands.checks.has_permissions(administrator=True)
async def slash_mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = 'Aucune raison fournie'):
    seconds = await parse_duration(duration)
    if seconds is None:
        await interaction.response.send_message('Format invalide. Exemple : `10m`, `1h`, `24h`.', ephemeral=True)
        return
    try:
        await member.timeout(timedelta(seconds=seconds), reason=reason)
    except Exception:
        await interaction.response.send_message('Je ne peux pas mute ce membre.', ephemeral=True)
        return
    await action_dm(member, 'mis en mute', interaction.user, reason, interaction.guild.name, duration)
    await interaction.response.send_message(f'{member.mention} a été mute pendant {duration} pour : {reason}', ephemeral=True)


@bot.tree.command(name='unmute', description='Retirer le mute d\'un membre')
@app_commands.describe(member='Le membre dont on retire le mute', reason='Raison du unmute')
@app_commands.checks.has_permissions(administrator=True)
async def slash_unmute(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie'):
    try:
        await member.timeout(None, reason=reason)
    except Exception:
        await interaction.response.send_message('Je ne peux pas unmute ce membre.', ephemeral=True)
        return
    await action_dm(member, 'unmute', interaction.user, reason, interaction.guild.name, extra_text='Tu as été rétabli sur le serveur.')
    await interaction.response.send_message(f'{member.mention} a été unmute pour : {reason}', ephemeral=True)


@bot.tree.command(name='warn', description='Envoyer un avertissement à un membre')
@app_commands.describe(member='Le membre à avertir', reason='Raison de l\'avertissement')
@app_commands.checks.has_permissions(administrator=True)
async def slash_warn(interaction: discord.Interaction, member: discord.Member, reason: str = 'Aucune raison fournie'):
    await action_dm(member, 'warn', interaction.user, reason, interaction.guild.name, extra_text='Ceci est un avertissement officiel du serveur.')
    await interaction.response.send_message(f'{member.mention} a reçu un avertissement : {reason}', ephemeral=True)


@bot.command(name='duelhistory', aliases=['duelhistory', 'historyduel', 'duel_historique'])
async def duel_history(ctx):
    rows = await db.get_duel_history(10)
    if not rows:
        await ctx.send('Aucun duel enregistré pour le moment.')
        return
    embed = discord.Embed(title='📜 Historique des duels', description='Les 10 derniers duels du serveur', color=QLF_BLUE)
    lines = []
    for challenger_id, opponent_id, challenger_choice, opponent_choice, stake, result, winner_id, created_at in rows:
        challenger = ctx.guild.get_member(challenger_id)
        opponent = ctx.guild.get_member(opponent_id)
        winner = ctx.guild.get_member(winner_id)
        challenger_name = challenger.mention if challenger else f'<@{challenger_id}>'
        opponent_name = opponent.mention if opponent else f'<@{opponent_id}>'
        winner_name = winner.mention if winner else f'<@{winner_id}>'
        lines.append(f"{challenger_name} **{challenger_choice}** vs {opponent_name} **{opponent_choice}** · mise **${stake}** · gagnant {winner_name} · {result}")
    embed.add_field(name='Derniers duels', value='\n'.join(lines[:10]), inline=False)
    await ctx.send(embed=embed)


@bot.command(name='duelstats', aliases=['duel_stats', 'duelstat', 'duelstats'])
async def duel_stats(ctx, member: discord.Member = None):
    target = member or ctx.author
    stats = await db.get_duel_stats(target.id)
    embed = discord.Embed(
        title=f'⚔️ Stats de duel · {target.display_name}',
        description=f'Nombre de duels : **{stats["total"]}**',
        color=QLF_BLUE,
    )
    embed.add_field(name='🏆 Victoires', value=str(stats['wins']), inline=True)
    embed.add_field(name='💀 Défaites', value=str(stats['losses']), inline=True)
    embed.add_field(name='📈 Winrate', value=f'{stats["winrate"]}%', inline=True)
    await ctx.send(embed=embed)


@bot.command(name='adminmenu', aliases=['menuadmin'])
@commands.has_permissions(administrator=True)
async def admin_menu(ctx):
    guild = ctx.guild
    target_channel = guild.get_channel(ADMIN_MENU_CHANNEL_ID)
    embed = discord.Embed(
        title='🛡️ Menu d\'administration QLF',
        description='Liste des commandes admin disponibles sur le serveur.',
        color=discord.Color.dark_orange(),
    )
    embed.add_field(name='⚠️ Avertissements', value='`!warn @membre [raison]`\n`/warn`', inline=False)
    embed.add_field(name='🔇 Mute', value='`!mute @membre 10m [raison]`\n`/mute @membre 10m [raison]`', inline=False)
    embed.add_field(name='🔊 Unmute', value='`!unmute @membre [raison]`\n`/unmute @membre [raison]`', inline=False)
    embed.add_field(name='👢 Kick', value='`!kick @membre [raison]`\n`/kick @membre [raison]`', inline=False)
    embed.add_field(name='⛔ Ban', value='`!ban @membre [raison]`\n`/ban @membre [raison]`', inline=False)
    embed.add_field(name='🧹 Clear', value='`!clear 12`\n`/clear 12`', inline=False)
    embed.set_footer(text='QLF admin menu · commandes réservées aux admins')
    if target_channel is not None:
        await target_channel.send(embed=embed)
        await ctx.send('📣 Menu admin envoyé dans le salon prévu.', delete_after=5)
    else:
        await ctx.send(embed=embed)


@bot.command(name='leaderboard')
async def leaderboard(ctx):
    try:
        members = [member async for member in ctx.guild.fetch_members(limit=None) if not member.bot]
    except discord.Forbidden:
        await ctx.send("Active **Server Members Intent** dans le portail Discord, puis relance le bot.")
        return
    for member in members:
        await db.ensure_user(member.id)
    rows = await db.get_balances([member.id for member in members])
    balances = {user_id: cash + bank for user_id, cash, bank in rows}
    ranked = sorted(members, key=lambda member: balances.get(member.id, 0), reverse=True)
    lines = []
    medals = ('🥇', '🥈', '🥉')
    for index, member in enumerate(ranked[:10], 1):
        medal = medals[index - 1] if index <= 3 else f'**{index}.**'
        lines.append(f"{medal} {member.display_name} · **${balances.get(member.id, 0):,}**".replace(',', ' '))
    author_rank = next((index for index, member in enumerate(ranked, 1) if member.id == ctx.author.id), None)
    embed = discord.Embed(
        title='🏆 Richesse du serveur QLF',
        description=f"Top **{min(10, len(ranked))}** · **{len(ranked)}** membres classés",
        color=QLF_BLUE,
    )
    embed.add_field(name='Classement', value='\n'.join(lines) or 'Aucun membre.', inline=False)
    if author_rank:
        embed.add_field(name='Ton rang', value=f"**#{author_rank}** · **${balances.get(ctx.author.id, 0):,}**".replace(',', ' '), inline=False)
    embed.set_footer(text='Classement économique QLF · cash + banque')
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    embed = discord.Embed(
        title='📖 Aide du bot économie QLF',
        description='Commandes du serveur QLF · préfixe `!`',
        color=QLF_BLUE,
    )
    embed.add_field(
        name='👤 Ton profil',
        value='`!profile`  Profil complet\n`!balance`  Cash + banque\n`!achievements`  Progression',
        inline=True,
    )
    embed.add_field(
        name='💵 Gagner',
        value='`!work`  $50-$150 · 10 min\n`!slut`  gagner/perdre · 15 min\n`!crime` / `!crim`  jackpot · 20 min\n`!daily` / `!weekly`  récompenses',
        inline=True,
    )
    embed.add_field(
        name='🏦 Banque & transferts',
        value='`!bank all`  Tout déposer\n`!deposit 500` / `!deposer 500`\n`!withdraw 500` / `!retirer 500`\n`!withdraw all`  Tout retirer\n`!pay @membre 100` / `!donner @membre 100`',
        inline=False,
    )
    embed.add_field(
        name='🎲 Risque & interaction',
        value='`!blackjack 100`  Miser $100\n`!steal @membre`  Voler après 5 h\n`!ping`  Latence',
        inline=True,
    )
    embed.add_field(
        name='🎨 Personnaliser',
        value='`!shop`  Objets\n`!inventory`  Inventaire\n`!buy galaxy`  Acheter + équiper\n`!equip galaxy`  Changer\n`!setvideo` + vidéo jointe  Afficher\n`!setvideo <lien Tenor>`  Lien vidéo\n`!setvideo off`  Retirer',
        inline=True,
    )
    embed.add_field(
        name='🎮 Mini-jeu : duel',
        value='`!duel @membre 100 pair`  Défi un joueur avec mise\n`!acc duel @membre impair`  Accepter le duel\n`!dec duel @membre`  Refuser le duel\n`!duelhistory`  Historique des derniers duels\n`!duelstats` / `!duelstats @membre`  Stats des duels\n`/duel @membre 100 pair`  Version slash',
        inline=False,
    )
    embed.add_field(
        name='🛡️ Modération',
        value='`!warn @membre [raison]` / `/warn`\n`!mute @membre 10m [raison]` / `/mute`\n`!unmute @membre [raison]` / `/unmute`\n`!kick @membre [raison]` / `/kick`\n`!ban @membre [raison]` / `/ban`',
        inline=False,
    )
    embed.set_footer(text='QLF · !daily puis !work pour commencer')
    await ctx.send(embed=embed)

@bot.command(name='work')
async def work(ctx):
    wait = await check_cooldown(ctx.author.id, 'work')()
    if wait:
        await ctx.send(f"Cooldown: attends {wait} secondes.")
        return
    amount = random.randint(50, 150)
    await db.change_cash(ctx.author.id, amount)
    await db.record_gain(ctx.author.id, amount)
    await db.set_cooldown(ctx.author.id, 'work')
    await ctx.send(f"Tu as travaillé et gagné ${amount}.")

@bot.command(name='slut')
async def slut(ctx):
    wait = await check_cooldown(ctx.author.id, 'slut')()
    if wait:
        await ctx.send(f"Cooldown: attends {wait} secondes.")
        return
    amount = random.randint(20, 120)
    lose = random.random() < (1/3)
    if lose:
        # lose money
        # ensure not negative
        u = await db.get_user(ctx.author.id)
        loss = min(amount, u['cash'])
        if loss > 0:
            await db.change_cash(ctx.author.id, -loss)
            await db.record_loss(ctx.author.id, loss)
        await ctx.send(f"Mauvaise chance : tu as perdu ${loss}.")
    else:
        await db.change_cash(ctx.author.id, amount)
        await db.record_gain(ctx.author.id, amount)
        await ctx.send(f"Bonne pioche : tu as gagné ${amount}.")
    await db.set_cooldown(ctx.author.id, 'slut')

@bot.command(name='daily')
async def daily(ctx):
    wait = await check_cooldown(ctx.author.id, 'daily')()
    if wait:
        await ctx.send(f"Récompense quotidienne disponible dans {wait // 3600}h {(wait % 3600) // 60}min.")
        return
    reward = 250
    await db.change_cash(ctx.author.id, reward)
    await db.record_gain(ctx.author.id, reward)
    await db.set_cooldown(ctx.author.id, 'daily')
    await ctx.send(f"Récompense quotidienne récupérée : ${reward} !")

@bot.command(name='weekly')
async def weekly(ctx):
    wait = await check_cooldown(ctx.author.id, 'weekly')()
    if wait:
        await ctx.send(f"Récompense hebdomadaire disponible dans {wait // 86400}j {(wait % 86400) // 3600}h.")
        return
    reward = 1500
    await db.change_cash(ctx.author.id, reward)
    await db.record_gain(ctx.author.id, reward)
    await db.set_cooldown(ctx.author.id, 'weekly')
    await ctx.send(f"Récompense hebdomadaire récupérée : ${reward} !")

@bot.command(name='crime', aliases=['crim'])
async def crime(ctx):
    wait = await check_cooldown(ctx.author.id, 'crime')()
    if wait:
        await ctx.send(f"Crime indisponible pendant encore {wait // 60} minutes.")
        return
    await db.set_cooldown(ctx.author.id, 'crime')
    outcome = random.random()
    if outcome < 0.05:
        reward = random.randint(2000, 5000)
        message = f"💎 JACKPOT : le crime de QLF est une réussite incroyable ! Tu gagnes **${reward}** !"
        success = True
    elif outcome < 0.6:
        reward = random.randint(150, 700)
        message = f"😈 Crime réussi sur QLF : tu gagnes **${reward}** !"
        success = True
    else:
        reward = 0
        message = ''
        success = False
    if success:
        await db.change_cash(ctx.author.id, reward)
        await db.record_gain(ctx.author.id, reward)
        await db.record_activity(ctx.author.id, 'crime', True)
        await ctx.send(message)
    else:
        user = await db.get_user(ctx.author.id)
        loss = min(user['cash'], random.randint(50, 300))
        if loss:
            await db.change_cash(ctx.author.id, -loss)
            await db.record_loss(ctx.author.id, loss)
        await db.record_activity(ctx.author.id, 'crime', False)
        await ctx.send(f"🚨 Crime raté : tu perds **${loss}** et la police te surveille.")

@bot.command(name='bank')
async def bank_cmd(ctx, what: str = None):
    if what == 'all':
        moved = await db.deposit_all(ctx.author.id)
        if moved:
            await ctx.send(f"Tu as tout déposé: ${moved}.")
        else:
            await ctx.send("Tu n'as rien à déposer.")
    else:
        u = await db.get_user(ctx.author.id)
        await ctx.send(f"Argent sur toi: {u['cash']} | Bank: {u['bank']}")

@bot.command(name='deposit', aliases=['deposer'])
async def deposit_cmd(ctx, amount: int = None):
    if amount is None:
        await ctx.send("**Montant obligatoire.** Utilise `!deposit 500` ou `!deposer 500`.")
        return
    if amount <= 0:
        await ctx.send("Le montant à déposer doit être supérieur à $0.")
        return
    moved = await db.deposit(ctx.author.id, amount)
    if moved:
        await ctx.send(f"Tu as déposé ${moved} à la banque.")
    else:
        await ctx.send("Tu n'as pas assez d'argent liquide.")

@bot.command(name='withdraw', aliases=['retirer'])
async def withdraw_cmd(ctx, amount: str = None):
    if amount is None:
        await ctx.send("**Montant obligatoire.** Utilise `!withdraw 500`, `!retirer 500` ou `!withdraw all`.")
        return
    if amount.lower() == 'all':
        user = await db.get_user(ctx.author.id)
        amount = str(user['bank'])
    try:
        amount = int(amount)
    except ValueError:
        await ctx.send("Utilise `!withdraw <montant>` ou `!withdraw all`.")
        return
    if amount <= 0:
        await ctx.send("Montant invalide.")
        return
    got = await db.withdraw(ctx.author.id, amount)
    if got:
        await ctx.send(f"Tu as retiré ${got}.")
    else:
        await ctx.send("Pas assez d'argent en banque.")

@bot.command(name='pay', aliases=['donner'])
async def pay(ctx, member: discord.Member = None, amount: int = None):
    if member is None or amount is None:
        await ctx.send("**Membre et montant obligatoires.** Utilise `!pay @membre 100` ou `!donner @membre 100`.")
        return
    if member.bot or member.id == ctx.author.id:
        await ctx.send("Tu dois choisir un autre membre, pas un bot.")
        return
    if amount <= 0:
        await ctx.send("Le montant doit être supérieur à $0.")
        return
    if await db.transfer_cash(ctx.author.id, member.id, amount):
        await ctx.send(f"Tu as donné ${amount} à {member.display_name}.")
    else:
        await ctx.send("Tu n'as pas assez d'argent liquide.")

@bot.command(name='blackjack')
async def blackjack(ctx, bet: int = 100):
    wait = await check_cooldown(ctx.author.id, 'blackjack')()
    if wait:
        await ctx.send(f"Cooldown: attends {wait} secondes.")
        return
    if bet <= 0:
        await ctx.send("La mise doit être supérieure à $0.")
        return
    if not await db.remove_cash(ctx.author.id, bet):
        await ctx.send("Tu n'as pas assez d'argent liquide pour cette mise.")
        return

    player = random.randint(15, 21)
    dealer = random.randint(15, 21)
    await db.set_cooldown(ctx.author.id, 'blackjack')
    if player > dealer or dealer > 21:
        await db.change_cash(ctx.author.id, bet * 2)
        await db.record_gain(ctx.author.id, bet)
        await ctx.send(f"Blackjack : tu fais {player}, le croupier {dealer}. Tu gagnes ${bet} !")
    elif player == dealer:
        await db.change_cash(ctx.author.id, bet)
        await ctx.send(f"Égalité : vous faites {player}. Mise remboursée (${bet}).")
    else:
        await db.record_loss(ctx.author.id, bet)
        await ctx.send(f"Tu fais {player}, le croupier {dealer}. Tu perds ${bet}.")

@bot.command(name='steal')
async def steal(ctx, member: discord.Member):
    wait = await check_cooldown(ctx.author.id, 'steal')()
    if wait:
        await ctx.send(f"Cooldown: attends {wait} secondes.")
        return
    if member.bot:
        await db.record_activity(ctx.author.id, 'steal', False)
        await ctx.send("Tu ne peux pas voler un bot.")
        return
    target = await db.get_user(member.id)
    if target['cash'] <= 0:
        await db.record_activity(ctx.author.id, 'steal', False)
        await ctx.send("La cible n'a pas d'argent sur elle.")
        return

    # Cash is protected for five hours after the last cash movement.
    now = int(time.time())
    protection_seconds = 5 * 3600
    age = now - target['last_cash_change']
    if age < protection_seconds:
        await db.record_activity(ctx.author.id, 'steal', False)
        remaining_minutes = (protection_seconds - age + 59) // 60
        await ctx.send(f"L'argent de {member.display_name} est protégé encore {remaining_minutes} minutes.")
        return

    # Only cash is stealable; money in the bank remains protected.
    portion = random.uniform(0.2, 0.5)
    amount = int(target['cash'] * portion)
    amount = max(1, amount)
    # transfer
    await db.change_cash(member.id, -amount)
    await db.change_cash(ctx.author.id, amount)
    await db.record_activity(ctx.author.id, 'steal', True)
    await db.record_gain(ctx.author.id, amount)
    await db.record_loss(member.id, amount)
    await db.set_cooldown(ctx.author.id, 'steal')
    await ctx.send(f"Tu as volé ${amount} à {member.display_name} !")

async def render_health(request):
    return web.Response(text='QLF Economy Bot is running')

async def start_render_server():
    app = web.Application()
    app.router.add_get('/', render_health)
    app.router.add_get('/health', render_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', '10000'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f'Render health server listening on port {port}')

async def run_bot():
    token = os.getenv('DISCORD_TOKEN', '').strip()
    if not token:
        print('ERREUR: DISCORD_TOKEN est absent.')
        return
    await start_render_server()
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print('ERREUR: token Discord invalide ou révoqué.')

if __name__ == '__main__':
    asyncio.run(run_bot())
