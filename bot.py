import os
import discord
from discord.ext import commands

# ======================
# 🔧 CONFIG (ROLE IDS)
# ======================
TICKET_CATEGORY_ID = 1492849115120537750
MM_ROLE_ID = 1492849227414638642
FOUNDER_ROLE_ID = 1492849203599118437
OWNER_ROLE_ID = 1492849203599118437

SERVER_NAME = "Eneba"
PURPLE = 0x9b59b6

ticket_data = {}

# ======================
# BOT SETUP
# ======================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

# ======================
# HELPERS
# ======================
def extract_member_from_input(guild, input_value):
    if input_value.startswith("<@") and input_value.endswith(">"):
        input_value = input_value.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(input_value))
    return discord.utils.find(lambda m: m.name == input_value, guild.members)

def has_role(user, role_id):
    return any(role.id == role_id for role in user.roles)

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
            placeholder="Select trade type below",
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

        self.other_user = discord.ui.TextInput(label="Other User", required=True)
        self.trade_details = discord.ui.TextInput(label="Trade Details", style=discord.TextStyle.paragraph, required=True)
        self.agreement = discord.ui.TextInput(label="Agreement (YES/NO)", required=True)

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
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
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
            "creator_id": interaction.user.id,
            "other_id": other_member.id if other_member else None,
            "claimer": None
        }

        embed = discord.Embed(
            title=f"💜 {SERVER_NAME} | NEW TICKET",
            description=
            "# New Middleman Ticket Created\n\n"
            "A new secure trade request has been submitted.\n\n"
            "## Ticket Information\n"
            f"**Trade Type:** {self.trade_type}\n"
            f"**Creator:** {interaction.user.mention}\n"
            f"**Other User:** {other_member.mention if other_member else self.other_user.value}\n\n"
            "## Trade Details\n"
            f"{self.trade_details.value}\n\n"
            "## Agreement\n"
            f"{self.agreement.value}\n\n"
            "## Status\n"
            "Waiting for a middleman to claim this ticket.",
            color=PURPLE
        )

        await channel.send(embed=embed, view=TicketButtons())

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

# ======================
# BUTTONS
# ======================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # CLAIM
    @discord.ui.button(label="✔ claim", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not has_role(interaction.user, MM_ROLE_ID):
            return await interaction.response.send_message("Only MM can claim tickets.", ephemeral=True)

        ticket_data[interaction.channel.id]["claimer"] = interaction.user.id

        embed = discord.Embed(
            title=f"💜 {SERVER_NAME} | TICKET CLAIMED",
            description=
            "# Ticket Claimed\n\n"
            f"This ticket has been claimed by {interaction.user.mention}\n\n"
            "## Status\n"
            "Only this middleman is now handling the trade.",
            color=PURPLE
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Claimed", ephemeral=True)

    # UNCLAIM
    @discord.ui.button(label="🔓 unclaim", style=discord.ButtonStyle.secondary)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        ticket_data[interaction.channel.id]["claimer"] = None

        embed = discord.Embed(
            title=f"💜 {SERVER_NAME} | TICKET UNCLAIMED",
            description=
            "# Ticket Unclaimed\n\n"
            f"{interaction.user.mention} has released this ticket.\n\n"
            "## Status\n"
            "It is now available for other middlemen.",
            color=PURPLE
        )

        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Unclaimed", ephemeral=True)

    # ADD
    @discord.ui.button(label="➕ add", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use command: $add @user", ephemeral=True)

    # REMOVE
    @discord.ui.button(label="➖ remove", style=discord.ButtonStyle.gray)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use command: $remove @user", ephemeral=True)

    # CLOSE
    @discord.ui.button(label="❌ close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        embed = discord.Embed(
            title=f"💜 {SERVER_NAME} | TICKET CLOSED",
            description=
            "# Ticket Closed\n\n"
            f"Closed by {interaction.user.mention}\n\n"
            "This ticket has been permanently closed.",
            color=PURPLE
        )

        await interaction.channel.send(embed=embed)
        await interaction.channel.delete()

# ======================
# PANEL
# ======================
@bot.command()
async def panel(ctx):

    if not has_role(ctx.author, FOUNDER_ROLE_ID):
        return await ctx.send("No permission")

    embed = discord.Embed(
        title="💜 Middleman Panel",
        description=(
    "Welcome to our middleman service centre.\n\n"

    "At **Eneba**, we provide a safe and secure way to exchange your goods, "
    "whether it's in-game items, crypto or digital assets.\n\n"

    "Our trusted middleman team ensures that both parties receive exactly what they agreed upon "
    "with **zero risk of scams**.\n\n"

    "**If you've found a trade and want to ensure your safety, "
    "you can use our FREE middleman service by following the steps below.**\n\n"

    "*Note: Large trades may include a small service fee.*\n\n"

    "📌 **Usage Conditions**\n"
    "• Find someone to trade with\n"
    "• Agree on the trade terms\n"
    "• Click the dropdown below\n"
    "• Wait for a staff member\n\n"

    "**Eneba • Trusted Middleman System**"
    ),

    await ctx.send(embed=embed, view=MMView())

# ======================
# COMMANDS
# ======================
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"Added {member.mention}")

@bot.command()
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"Removed {member.mention}")

bot.run(os.getenv("TOKEN"))