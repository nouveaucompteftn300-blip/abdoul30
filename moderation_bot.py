import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import json
import os

# ============ CONFIGURATION PRINCIPALE ============
TOKEN = "YOUR_TOKEN_HERE"
PREFIX = "+"
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
bot.remove_command('help')

# ============ CONFIGURATION LOGS ============
LOG_CHANNEL_ID = 1494719071416225994

# Fichier de configuration des logs
LOG_CONFIG_FILE = "log_config.json"

# Configuration des logs par défaut
DEFAULT_LOG_CONFIG = {
    "mod_ban": True, "mod_kick": True, "mod_mute": True,
    "mod_unmute": True, "mod_unban": True, "mod_clear": True,
}

def load_log_config():
    if os.path.exists(LOG_CONFIG_FILE):
        try:
            with open(LOG_CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_LOG_CONFIG.copy()
    return DEFAULT_LOG_CONFIG.copy()

def save_log_config(config):
    with open(LOG_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

log_config = load_log_config()

# Couleurs personnalisées pour les logs - ROSE
COLORS = {
    "moderation": discord.Color.from_rgb(255, 105, 180),
}

def create_log_embed(bot_user, user, action, description, color=None):
    color = color or discord.Color.from_rgb(255, 105, 180)
    embed = discord.Embed(description=description, color=color, timestamp=datetime.datetime.now())
    embed.set_author(name=f"{user.name} - {action}", icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.set_footer(text=bot_user.name, icon_url=bot_user.avatar.url if bot_user.avatar else bot_user.default_avatar.url)
    return embed

def time_converter(duration: str) -> int:
    """Convertit une durée (ex: 1h, 30m, 2d) en secondes"""
    import re
    time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    match = re.match(r'(\d+)([smhd])', duration.lower())
    return int(match.group(1)) * time_units[match.group(2)] if match else None

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

# ============ MODÉRATION - BAN ============
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, raison=None):
    """Bannir un membre du serveur"""
    if not ctx.guild.me.guild_permissions.ban_members:
        return await ctx.send("Je n'ai pas la permission de bannir !", ephemeral=True)
    if member == ctx.author:
        return await ctx.send("Tu ne peux pas te bannir toi-même !", ephemeral=True)
    try:
        await member.ban(reason=raison)
        await ctx.send(f"{member.mention} a été banni par {ctx.author.mention}\nRaison: {raison or 'Aucune'}")
        try:
            await member.send(f"Tu as été banni de **{ctx.guild.name}**\nRaison: {raison or 'Aucune'}")
        except:
            pass
        if log_config.get("mod_ban", True):
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = create_log_embed(bot.user, member, "banni", f"Banni par {ctx.author.mention}\nRaison: {raison or 'Aucune'}", COLORS["moderation"])
                await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Erreur : {e}", ephemeral=True)

# ============ MODÉRATION - KICK ============
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, raison=None):
    """Expulser un membre du serveur"""
    if not ctx.guild.me.guild_permissions.kick_members:
        return await ctx.send("Je n'ai pas la permission d'expulser !", ephemeral=True)
    if member == ctx.author:
        return await ctx.send("Tu ne peux pas t'expulser toi-même !", ephemeral=True)
    try:
        await member.kick(reason=raison)
        await ctx.send(f"{member.mention} a été expulsé par {ctx.author.mention}\nRaison: {raison or 'Aucune'}")
        try:
            await member.send(f"Tu as été expulsé de **{ctx.guild.name}**\nRaison: {raison or 'Aucune'}")
        except:
            pass
        if log_config.get("mod_kick", True):
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = create_log_embed(bot.user, member, "expulsé", f"Expulsé par {ctx.author.mention}\nRaison: {raison or 'Aucune'}", COLORS["moderation"])
                await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Erreur : {e}", ephemeral=True)

# ============ MODÉRATION - MUTE ============
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duree: str = None, *, raison=None):
    """Rendre muet un membre (avec durée optionnelle)"""
    if member == ctx.author:
        return await ctx.send("Tu ne peux pas te mute toi-même !", ephemeral=True)
    
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        try:
            muted_role = await ctx.guild.create_role(
                name="Muted",
                permissions=discord.Permissions(send_messages=False, speak=False, add_reactions=False)
            )
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
                except:
                    pass
        except:
            return await ctx.send("Impossible de créer le rôle Muted !", ephemeral=True)
    
    if muted_role in member.roles:
        return await ctx.send(f"{member.mention} est déjà mute !", ephemeral=True)
    
    seconds = None
    duree_texte = "indéfiniment"
    if duree:
        seconds = time_converter(duree)
        duree_texte = duree if seconds else "indéfiniment"
    
    try:
        await member.add_roles(muted_role)
        await ctx.send(f"{member.mention} a été rendu muet par {ctx.author.mention}\nDurée: {duree_texte}\nRaison: {raison or 'Aucune'}")
        try:
            await member.send(f"Tu as été mute de **{ctx.guild.name}** pendant `{duree_texte}`\nRaison: {raison or 'Aucune'}")
        except:
            pass
        if log_config.get("mod_mute", True):
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = create_log_embed(bot.user, member, "mute", f"Mute par {ctx.author.mention}\nDurée: {duree_texte}\nRaison: {raison or 'Aucune'}", COLORS["moderation"])
                await log_channel.send(embed=embed)
        
        if seconds:
            async def auto_unmute():
                await asyncio.sleep(seconds)
                if muted_role in member.roles:
                    try:
                        await member.remove_roles(muted_role)
                        await member.send(f"Ton mute sur **{ctx.guild.name}** est terminé !")
                    except:
                        pass
            bot.loop.create_task(auto_unmute())
    except Exception as e:
        await ctx.send(f"Erreur : {e}", ephemeral=True)

# ============ MODÉRATION - UNMUTE ============
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    """Retirer le mute d'un membre"""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role or muted_role not in member.roles:
        return await ctx.send(f"{member.mention} n'est pas mute !", ephemeral=True)
    try:
        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} n'est plus muet ! Démuté par {ctx.author.mention}")
        try:
            await member.send(f"Ton mute sur **{ctx.guild.name}** a été levé !")
        except:
            pass
        if log_config.get("mod_unmute", True):
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = create_log_embed(bot.user, member, "unmute", f"Démuté par {ctx.author.mention}", COLORS["moderation"])
                await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Erreur : {e}", ephemeral=True)

# ============ MODÉRATION - UNBAN ============
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, recherche: str):
    """Débannir un membre (par ID ou par nom)"""
    banned_users = [entry async for entry in ctx.guild.bans()]
    if not banned_users:
        return await ctx.send("Aucun membre banni", ephemeral=True)
    try:
        user_id = int(recherche)
        for ban_entry in banned_users:
            if ban_entry.user.id == user_id:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"{ban_entry.user.mention} a été débanni par {ctx.author.mention}")
                if log_config.get("mod_unban", True):
                    log_channel = bot.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        embed = create_log_embed(bot.user, ban_entry.user, "débanni", f"Débanni par {ctx.author.mention}", COLORS["moderation"])
                        await log_channel.send(embed=embed)
                return
        await ctx.send(f"ID `{recherche}` non trouvé", ephemeral=True)
    except ValueError:
        found = [entry.user for entry in banned_users if recherche.lower() in entry.user.name.lower()]
        if not found:
            return await ctx.send("Aucun banni trouvé", ephemeral=True)
        elif len(found) == 1:
            await ctx.guild.unban(found[0])
            await ctx.send(f"{found[0].mention} a été débanni par {ctx.author.mention}")
            if log_config.get("mod_unban", True):
                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed = create_log_embed(bot.user, found[0], "débanni", f"Débanni par {ctx.author.mention}", COLORS["moderation"])
                    await log_channel.send(embed=embed)
        else:
            await ctx.send("Trop de résultats. Utilise l'ID directement", ephemeral=True)

# ============ MODÉRATION - CLEAR ============
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, nombre: int = None, *, raison=None):
    """Supprimer un nombre de messages (entre 1 et 100)"""
    if not nombre or nombre < 1 or nombre > 100:
        return await ctx.send("Entre 1 et 100 messages !", ephemeral=True)
    try:
        deleted = await ctx.channel.purge(limit=nombre + 1)
        msg = await ctx.send(f"{len(deleted) - 1} messages supprimés par {ctx.author.mention}\nRaison: {raison or 'Aucune'}")
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
        if log_config.get("mod_clear", True):
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                embed = create_log_embed(bot.user, ctx.author, "purge", f"A supprimé {len(deleted) - 1} messages dans {ctx.channel.mention}\nRaison: {raison or 'Aucune'}", COLORS["moderation"])
                await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Erreur : {e}", ephemeral=True)

# ============ LANCEMENT ============
bot.run(TOKEN)
