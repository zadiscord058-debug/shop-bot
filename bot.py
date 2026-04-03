import discord
from discord.ext import commands
from discord.ui import View, Select
import os

# ==================== CONFIG ====================
ROLE_ID = 123456789012345678  # ovde ubaci ID role koja sme da koristi $panel i $close
TICKET_CATEGORY_NAME = "══「 🎫 TICKETS 」══"

# 🎀 ROZE BOJA
PINK = discord.Color.from_rgb(255, 105, 180)
MIDDLE_EMBED_COLOR = discord.Color.from_rgb(255, 182, 193)  # svetlija roze za vouch

# Vouch storage
vouches = {}  # {member_id: [user_ids]}

# ==================== INTENTS ====================
intents = discord.Intents.all()
intents.message_content = True  # obavezno za $komande
bot = commands.Bot(command_prefix="$", intents=intents)

# ==================== TICKET DROPDOWN ====================
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Nitro"),
            discord.SelectOption(label="Server Boost"),
            discord.SelectOption(label="Decoration"),
        ]
        super().__init__(placeholder="Choose Purchase", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        choice = self.values[0]

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category
        )

        await channel.set_permissions(guild.default_role, view_channel=False)
        await channel.set_permissions(user, view_channel=True, send_messages=True)

        # EMBED TEKSTOVI
        if choice == "Server Boost":
            text = """<:rocket:1486811539221512353> **Server Boost Ticket**
───────────────────────────
**Thank you for contacting support**
Tell us the type of Server Boost you are looking for.

**Available:** 1 Month | 3 Month | Key
**Price:** $2.00 or €1.75 for 1 Month & $3.50 or €3.05 for 3 Months
"""
        elif choice == "Decoration":
            text = """<:deco:1489693229921337566> **Decoration Ticket**
───────────────────────────
**Thank you for contacting support**
Tell us the type of Decoration you are looking for.

**Available:** Avatars | Effects | Nameplates
**Price:** Depends which Decoration
"""
        else:  # Nitro
            text = """<:pinknitro:1489693388059181228> **Nitro Ticket**
───────────────────────────
**Thank you for contacting support**
Tell us the type of Nitro you are looking for.

**Available:** Nitro Boost | Nitro Basic
**Price:** Depends
"""

        embed = discord.Embed(description=text, color=PINK)
        embed.set_footer(text=f"User: {user}")
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        await channel.send(content=user.mention, embed=embed)
        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ==================== $panel KOMANDA ====================
@bot.command()
async def panel(ctx):
    role = ctx.guild.get_role(ROLE_ID)
    if role not in ctx.author.roles:
        await ctx.send("❌ Nemate dozvolu da koristite ovu komandu")
        return

    text = """## <:pinknitro:1489693388059181228> __N1troHub TICKETS__
**Do you want to open a ticket to contact us?** 
__Choose the reason for your ticket:__

### <:owner:1489693956479647965> TERMS & CONDITIONS
> - Payments are only via PayPal or Ltc
> - If you send money to the wrong PayPal address, no refund will be provided
> - Payments must be sent in € (EUR) if sent in $ (USD) additional fees apply
> - If a Nitro or any other item gets revoked no refund or replacement will be given
> - Buying sellauth and getting Nitro claimed without screen recording = no replacement/refund
> - Advertising in slots/ channels = instant ban
> - Accusing us of scamming = instant ban
> - No refund possible for any purchase

<:cross:1489694275938680994> **BUYING FROM US MEANS ACCEPTING THE TOS**
"""
    embed = discord.Embed(description=text, color=PINK)
    embed.set_footer(text="Select an option below")
    await ctx.send(embed=embed, view=TicketView())

# ==================== $close KOMANDA ====================
@bot.command()
async def close(ctx):
    role = ctx.guild.get_role(ROLE_ID)
    if role not in ctx.author.roles:
        await ctx.send("❌ Nemate dozvolu da koristite ovu komandu")
        return

    if ctx.channel.category and ctx.channel.category.name == TICKET_CATEGORY_NAME:
        await ctx.send("🔒 Closing ticket...")
        await ctx.channel.delete()
    else:
        await ctx.send("❌ Ovu komandu možete koristiti samo u ticket kanalu")

# ==================== $vouch KOMANDA ====================
@bot.command()
async def vouch(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("❌ Please mention a user to vouch")
        return
    if member.id not in vouches:
        vouches[member.id] = []
    vouches[member.id].append(ctx.author.id)

    embed = discord.Embed(
        title="🌟 Vouch!",
        description=f"{ctx.author.mention} vouched for {member.mention}!",
        color=MIDDLE_EMBED_COLOR
    )
    embed.set_footer(text="Thank you for vouching!")
    await ctx.send(embed=embed)

# ==================== $vouches KOMANDA ====================
@bot.command()
async def vouches(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("❌ Please mention a user to see their vouches")
        return
    user_vouches = vouches.get(member.id, [])
    count = len(user_vouches)

    if count == 0:
        text = f"{member.mention} has no vouches yet"
    else:
        names = [ctx.guild.get_member(uid).mention if ctx.guild.get_member(uid) else f"Unknown({uid})" for uid in user_vouches]
        text = f"{member.mention} has {count} vouches:\n" + ", ".join(names)

    embed = discord.Embed(
        title=f"📜 {member.name}'s Vouches",
        description=text,
        color=MIDDLE_EMBED_COLOR
    )
    await ctx.send(embed=embed)

# ==================== ON READY ====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ==================== TOKEN ====================
TOKEN = os.getenv("TOKEN")  # u Railway dodaj varijablu TOKEN sa vrednošću bota
if not TOKEN:
    raise ValueError("TOKEN environment variable not set")
bot.run(TOKEN)