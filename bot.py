import os
import discord
from discord.ext import commands

# ======================
# 🔧 CONFIG
# ======================
TICKET_CATEGORY_ID = 1492849115120537750
MM_ROLE_ID = 1492849227414638642
FOUNDER_ROLE_ID = 1492849203599118437

PURPLE = 0x9b59b6
ticket_data = {}

# ======================
# BOT SETUP
# ======================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

# ======================
# 🔒 CHECK
# ======================
def is_founder():
    async def predicate(ctx):
        return any(role.id == FOUNDER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ======================
# HELPERS
# ======================
def extract_member_from_input(guild, input_value):
    if input_value.startswith("<@") and input_value.endswith(">"):
        input_value = input_value.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(input_value))
    return discord.utils.find(lambda m: m.name == input_value, guild.members)

# ======================
# SELECT MENU
# ======================
class MMSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🎮 In Game Items"),
            discord.SelectOption(label="🪙 Crypto"),
            discord.SelectOption(label="💳 PayPal"),
        ]

        super().__init__(
            placeholder="Select trade type",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MMModal(self.values[0]))

class MMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())

# ======================
# MODAL
# ======================
class MMModal(discord.ui.Modal):

    def __init__(self, trade_type):
        super().__init__(title="Middleman Ticket")

        self.trade_type = trade_type

        self.other_user = discord.ui.TextInput(
            label="Other User",
            required=True
        )

        self.trade_details = discord.ui.TextInput(
            label="Trade Details",
            style=discord.TextStyle.paragraph,
            required=True
        )

        self.agreement = discord.ui.TextInput(
            label="Agreement (YES/NO)",
            required=True
        )

        self.add_item(self.other_user)
        self.add_item(self.trade_details)
        self.add_item(self.agreement)

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        mm_role = guild.get_role(MM_ROLE_ID)

        other_member = extract_member_from_input(guild, self.other_user.value)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if other_member:
            overwrites[other_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        if mm_role:
            overwrites[mm_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}".lower(),
            category=category,
            overwrites=overwrites
        )

        ticket_data[channel.id] = {
            "creator": interaction.user.id,
            "other": other_member.id if other_member else None,
            "claimer": None,
            "trade": self.trade_type
        }

        embed = discord.Embed(
            title="💜 new middleman ticket",
            description=(
                f"**trade type:** {self.trade_type}\n"
                f"**user:** {interaction.user.mention}\n"
                f"**other:** {other_member.mention if other_member else self.other_user.value}\n\n"
                f"**details:**\n{self.trade_details.value}\n\n"
                f"**status:** waiting for claim"
            ),
            color=PURPLE
        )

        await channel.send(embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"ticket created: {channel.mention}", ephemeral=True)

# ======================
# BUTTONS
# ======================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def big_embed(self, title, desc, user):
        return discord.Embed(
            title=title,
            description=desc,
            color=PURPLE
        ).set_footer(text=f"action by {user}")

    # CLAIM
    @discord.ui.button(label="🎫 claim", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        ticket_data[interaction.channel.id]["claimer"] = interaction.user.id

        embed = self.big_embed(
            "🎫 ticket claimed",
            f"claimed by {interaction.user.mention}",
            interaction.user
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("claimed", ephemeral=True)

    # UNCLAIM
    @discord.ui.button(label="🔄 unclaim", style=discord.ButtonStyle.secondary)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        ticket_data[interaction.channel.id]["claimer"] = None

        embed = self.big_embed(
            "🔄 ticket unclaimed",
            f"unclaimed by {interaction.user.mention}",
            interaction.user
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("unclaimed", ephemeral=True)

    # ADD
    @discord.ui.button(label="➕ add", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = self.big_embed(
            "➕ user added",
            f"use command `$add @user`",
            interaction.user
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("use $add command", ephemeral=True)

    # REMOVE
    @discord.ui.button(label="➖ remove", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = self.big_embed(
            "➖ user removed",
            f"use command `$remove @user`",
            interaction.user
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("use $remove command", ephemeral=True)

    # CLOSE
    @discord.ui.button(label="❌ close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = self.big_embed(
            "❌ ticket closed",
            "this ticket is now closed",
            interaction.user
        )

        await interaction.channel.send(embed=embed)
        await interaction.channel.delete()

# ======================
# COMMANDS
# ======================
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)

    embed = discord.Embed(
        title="➕ user added",
        description=f"{member.mention} was added",
        color=PURPLE
    )

    await ctx.send(embed=embed)

@bot.command()
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)

    embed = discord.Embed(
        title="➖ user removed",
        description=f"{member.mention} was removed",
        color=PURPLE
    )

    await ctx.send(embed=embed)

@bot.command()
async def claim(ctx):
    ticket_data[ctx.channel.id]["claimer"] = ctx.author.id
    await ctx.send(f"🎫 claimed by {ctx.author.mention}")

@bot.command()
async def unclaim(ctx):
    ticket_data[ctx.channel.id]["claimer"] = None
    await ctx.send("🔄 unclaimed")

@bot.command()
async def close(ctx):
    await ctx.channel.delete()

# ======================
# PANEL
# ======================
@bot.command()
@is_founder()
async def panel(ctx):

    embed = discord.Embed(
        title="💜 middleman service",
        description=(
            "welcome to middleman service\n\n"
            "safe trading system for all users\n\n"
            "steps:\n"
            "• choose trade type\n"
            "• fill form\n"
            "• wait staff\n"
        ),
        color=PURPLE
    )

    await ctx.send(embed=embed, view=MMView())

# ======================
# RUN
# ======================
bot.run(os.getenv("TOKEN"))