import os
import discord
from discord.ext import commands

# ======================
# CONFIG
# ======================
TICKET_CATEGORY_ID = 1492849115120537750
MM_ROLE_ID = 1492849227414638642
FOUNDER_ROLE_ID = 1492849203599118437

SERVER_NAME = "Eneba"
PURPLE = 0x9b59b6

ticket_data = {}

# ======================
# BOT
# ======================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents)

# ======================
# HELPERS
# ======================
def has_role(user, role_id):
    return any(role.id == role_id for role in user.roles)


def is_mm(user):
    return has_role(user, MM_ROLE_ID)


def extract_member_from_input(guild, input_value):
    if input_value.startswith("<@") and input_value.endswith(">"):
        input_value = input_value.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(input_value))
    return discord.utils.find(lambda m: m.name == input_value, guild.members)


def ticket_ping(guild, creator, other_member=None):
    mm_role = guild.get_role(MM_ROLE_ID)
    parts = []

    # creator uvijek ping
    if creator:
        parts.append(creator.mention)

    # drugi user
    if other_member:
        parts.append(other_member.mention)

    # MM role
    if mm_role:
        parts.append(mm_role.mention)

    return " ".join(parts)


def action_embed(title, user, text):
    return discord.Embed(
        title=f"💜 {SERVER_NAME} | {title}",
        description=(
            f"# {title}\n\n"
            f"{text}\n\n"
            f"**Action by:** {user.mention}"
        ),
        color=PURPLE
    )

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
            description=(
                "# New Middleman Ticket Created\n\n"
                f"**Trade Type:** {self.trade_type}\n"
                f"**Creator:** {interaction.user.mention}\n"
                f"**Other User:** {other_member.mention if other_member else self.other_user.value}\n\n"
                f"**Details:** {self.trade_details.value}\n\n"
                f"**Agreement:** {self.agreement.value}\n\n"
                "Status: Waiting for MM"
            ),
            color=PURPLE
        )

        await channel.send(
            content=ticket_ping(guild, other_member),
            embed=embed,
            view=TicketButtons()
        )

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

        if not is_mm(interaction.user):
            return await interaction.response.send_message("MM only", ephemeral=True)

        ticket_data[interaction.channel.id]["claimer"] = interaction.user.id

        await interaction.channel.send(embed=action_embed(
            "Ticket Claimed",
            interaction.user,
            "This ticket is now handled by a Middleman."
        ))

        await interaction.response.send_message("Claimed", ephemeral=True)

    # UNCLAIM
    @discord.ui.button(label="🔓 unclaim", style=discord.ButtonStyle.secondary)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_mm(interaction.user):
            return await interaction.response.send_message("MM only", ephemeral=True)

        ticket_data[interaction.channel.id]["claimer"] = None

        await interaction.channel.send(embed=action_embed(
            "Ticket Unclaimed",
            interaction.user,
            "Ticket is available again."
        ))

        await interaction.response.send_message("Unclaimed", ephemeral=True)

    # ADD
    @discord.ui.button(label="➕ add", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_mm(interaction.user):
            return await interaction.response.send_message("MM only", ephemeral=True)

        await interaction.response.send_message("$add @user", ephemeral=True)

    # REMOVE
    @discord.ui.button(label="➖ remove", style=discord.ButtonStyle.gray)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_mm(interaction.user):
            return await interaction.response.send_message("MM only", ephemeral=True)

        await interaction.response.send_message("$remove @user", ephemeral=True)

    # CLOSE
    @discord.ui.button(label="❌ close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not is_mm(interaction.user):
            return await interaction.response.send_message("MM only", ephemeral=True)

        await interaction.channel.send(embed=action_embed(
            "Ticket Closed",
            interaction.user,
            "This ticket is now closed and will be deleted."
        ))

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

    "📌 **How it works**\n"
    "• Find someone to trade with\n"
    "• Agree on trade terms\n"
    "• Select trade type from dropdown\n"
    "• Fill in the ticket form\n"
    "• Wait for a staff member (middleman)\n\n"

    "🛡️ **Safety Rules**\n"
    "• Do not attempt scams or fake trades\n"
    "• Follow middleman instructions at all times\n"
    "• Do not spam tickets or staff\n"
    "• Any abuse will result in a permanent ban from service\n\n"

    "💜 **Eneba • Trusted Middleman System**"
    ),
        color=PURPLE
    )

    await ctx.send(embed=embed, view=MMView())

# ======================
# COMMANDS
# ======================
@bot.command()
async def add(ctx, member: discord.Member):

    if not is_mm(ctx.author):
        return await ctx.send("MM only")

    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)

    await ctx.send(embed=action_embed(
        "User Added",
        ctx.author,
        f"{member.mention} added to ticket."
    ))

@bot.command()
async def remove(ctx, member: discord.Member):

    if not is_mm(ctx.author):
        return await ctx.send("MM only")

    await ctx.channel.set_permissions(member, overwrite=None)

    await ctx.send(embed=action_embed(
        "User Removed",
        ctx.author,
        f"{member.mention} removed from ticket."
    ))
    
@bot.command()
async def claim(ctx):

    if not has_role(ctx.author, MM_ROLE_ID):
        return await ctx.send("Only MM can use this.")

    ticket_data[ctx.channel.id]["claimer"] = ctx.author.id

    embed = discord.Embed(
        title=f"💜 {SERVER_NAME} | TICKET CLAIMED",
        description=(
            "# Ticket Claimed\n\n"
            f"This ticket has been claimed by {ctx.author.mention}\n\n"
            "## Status\n"
            "Only this middleman is handling the trade."
        ),
        color=PURPLE
    )

    await ctx.send(embed=embed)


@bot.command()
async def unclaim(ctx):

    if not has_role(ctx.author, MM_ROLE_ID):
        return await ctx.send("Only MM can use this.")

    ticket_data[ctx.channel.id]["claimer"] = None

    embed = discord.Embed(
        title=f"💜 {SERVER_NAME} | TICKET UNCLAIMED",
        description=(
            "# Ticket Unclaimed\n\n"
            f"{ctx.author.mention} has unclaimed this ticket.\n\n"
            "## Status\n"
            "Now available for other middlemen."
        ),
        color=PURPLE
    )

    await ctx.send(embed=embed)
    


# ======================
# RUN
# ======================
bot.run(os.getenv("TOKEN"))