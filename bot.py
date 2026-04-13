import discord
from discord.ext import commands
import os



TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True  # IMPORTANT for role.members

bot = commands.Bot(command_prefix="!", intents=intents)

FOUNDER_ROLE_ID = 1435194033558392842

@bot.command()
async def dmrole(ctx, role: discord.Role, *, text=None):

    if not any(r.id == FOUNDER_ROLE_ID for r in ctx.author.roles):
        return await ctx.send("❌ You don't have permission to use this command.")

    if not text:
        return await ctx.send("❌ Please provide a message.")

    members = role.members
    if len(members) == 0:
        return await ctx.send("❌ No members in that role.")

    await ctx.send(f"📨 Sending DM to {len(members)} members...")

    sent = 0
    failed = 0

    for member in members:
        try:
            await member.send(text)
            sent += 1
        except:
            failed += 1

    await ctx.send(f"✅ Done! Sent: {sent}, Failed: {failed}")

bot.run(TOKEN)