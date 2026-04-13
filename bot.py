import discord
from discord.ext import commands
import os
import asyncio

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

FOUNDER_ROLE_ID = 1435194033558392842


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def test(ctx):
    await ctx.send("Bot radi ✅")


@bot.command()
async def dmrole(ctx, role: discord.Role, *, text=None):

    print("COMMAND TRIGGERED")

    if not any(r.id == FOUNDER_ROLE_ID for r in ctx.author.roles):
        return await ctx.send("❌ No permission.")

    if not text:
        return await ctx.send("❌ Provide message.")

    members = []
    async for m in ctx.guild.fetch_members(limit=None):
        if role in m.roles:
            members.append(m)

    print(f"Members found: {len(members)}")

    if len(members) == 0:
        return await ctx.send("❌ No members in that role.")

    await ctx.send(f"📨 Sending to {len(members)} members...")

    sent = 0
    failed = 0

    for member in members:
        try:
            await member.send(text)
            sent += 1
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Failed: {member} | {e}")
            failed += 1

    await ctx.send(f"✅ Done! Sent: {sent}, Failed: {failed}")


bot.run(TOKEN)