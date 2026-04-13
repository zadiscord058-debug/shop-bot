import discord
from discord.ext import commands
import os
import asyncio

# TOKEN iz environment varijable
TOKEN = os.getenv("TOKEN")

# Intenti (važni za membere)
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

# ID role koja smije koristiti komandu
FOUNDER_ROLE_ID = 1435194033558392842


@bot.event
async def on_ready():
    print(f"✅ Bot is logged in as {bot.user}")


@bot.command()
async def dmrole(ctx, role: discord.Role, *, text=None):

    # Provjera permisije
    if not any(r.id == FOUNDER_ROLE_ID for r in ctx.author.roles):
        return await ctx.send("❌ You don't have permission to use this command.")

    # Provjera poruke
    if not text:
        return await ctx.send("❌ Please provide a message.")

    # Fetch svih membera (fix za role.members problem)
    members = []
    async for m in ctx.guild.fetch_members(limit=None):
        if role in m.roles:
            members.append(m)

    print(f"Role: {role}")
    print(f"Members found: {len(members)}")

    if len(members) == 0:
        return await ctx.send("❌ No members in that role.")

    await ctx.send(f"📨 Sending DM to {len(members)} members...")

    sent = 0
    failed = 0

    for member in members:
        try:
            await member.send(text)
            sent += 1
            await asyncio.sleep(1)  # anti rate-limit
        except Exception as e:
            print(f"❌ Failed to DM {member}: {e}")
            failed += 1

    await ctx.send(f"✅ Done! Sent: {sent}, Failed: {failed}")


bot.run(TOKEN)