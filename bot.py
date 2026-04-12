import os
import discord
from discord.ext import commands

# ======================
# 🔧 CONFIG (ROLE IDS)
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
# 🔒 ROLE CHECK (FOUNDER)
# ======================
def is_founder():
    async def predicate(ctx):
        return any(role.id == FOUNDER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ======================
# 🔍 HELPERS
# ======================
def extract_member_from_input(guild, input_value):
    if input_value.startswith("<@") and input_value.endswith(">"):
        input_value = input_value.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(input_value))
    return discord.utils.find(lambda m: m.name == input_value, guild.members)

# ======================
# 🎛️ SELECT MENU
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
            options=options,
            custom_id="mm_select_trade_type"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MMModal(self.values[0]))

# ======================
# 🎛️ VIEW
# ======================
class MMView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MMSelect())

# ======================
# 📩 MODAL
# ======================
class MMModal(discord.ui.Modal):

    def __init__(self, trade_type):
        super().__init__(title="Middleman Ticket")

        self.trade_type = trade_type

        self.other_user = discord.ui.TextInput(
            label="Other User (mention or name)",
            required=True
        )

        self.trade_details = discord.ui.TextInput(
            label="Trade Details",
            style=discord.TextStyle.paragraph,
            required=True
        )

        self.agreement = discord.ui.TextInput(
            label="Do both users agree?",
            placeholder="Type YES if both agreed",
            required=True
        )

        self.add_item(self.other_user)
        self.add_item(self.trade_details)
        self.add_item(self.agreement)

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category is None:
            return await interaction.response.send_message(
                "❌ Ticket category not set.",
                ephemeral=True
            )

        mm_role = guild.get_role(MM_ROLE_ID)
        other_member = extract_member_from_input(guild, self.other_user.value)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }

        if other_member:
            overwrites[other_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        if mm_role:
            overwrites[mm_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await guild.create_text_channel(
            name=f"mm-{interaction.user.name}".lower().replace(" ", "-"),
            category=category,
            overwrites=overwrites
        )

        ticket_data[channel.id] = {
            "creator_id": interaction.user.id,
            "other_user_id": other_member.id if other_member else None,
            "claimer_id": None,
            "trade_type": self.trade_type,
            "trade_details": self.trade_details.value,
            "agreement": self.agreement.value
        }

        other_text = other_member.mention if other_member else self.other_user.value

        embed = discord.Embed(
            title="💜 Eneba | New Middleman Ticket",
            description=(
                "# New Ticket Created\n\n"
                f"**Trade Type:** {self.trade_type}\n"
                f"**Other User:** {other_text}\n"
                f"**Agreement:** {self.agreement.value}\n\n"
                f"**Trade Details:** {self.trade_details.value}\n\n"
                "**Status:** Waiting for middleman"
            ),
            color=PURPLE
        )

        embed.set_footer(text="Eneba | Ticket System")

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=TicketButtons()
        )

        await interaction.response.send_message(
            f"✅ Ticket created: {channel.mention}",
            ephemeral=True
        )

# ======================
# 🎫 BUTTONS
# ======================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 claim", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data[interaction.channel.id]["claimer_id"] = interaction.user.id
        await interaction.channel.send(f"🎫 Claimed by {interaction.user.mention}")

    @discord.ui.button(label="🔄 unclaim", style=discord.ButtonStyle.secondary)
    async def unclaim(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data[interaction.channel.id]["claimer_id"] = None
        await interaction.channel.send("🔄 Unclaimed")

    @discord.ui.button(label="➕ add", style=discord.ButtonStyle.primary)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("➕ use $add @user")

    @discord.ui.button(label="➖ remove", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("➖ use $remove @user")

    @discord.ui.button(label="❌ close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

# ======================
# COMMANDS
# ======================
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ Added {member.mention}")

@bot.command()
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"➖ Removed {member.mention}")

@bot.command()
async def claim(ctx):
    ticket_data[ctx.channel.id]["claimer_id"] = ctx.author.id
    await ctx.send(f"🎫 Claimed by {ctx.author.mention}")

@bot.command()
async def unclaim(ctx):
    ticket_data[ctx.channel.id]["claimer_id"] = None
    await ctx.send("🔄 Unclaimed")

@bot.command()
async def close(ctx):
    await ctx.channel.delete()

# ======================
# PANEL (FOUNDER ROLE ONLY)
# ======================
@bot.command()
@is_founder()
async def panel(ctx):

    embed = discord.Embed(
        title="💜 Eneba | Middleman Service",
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
        color=PURPLE
    )

    embed.set_footer(text="Eneba | Official System")

    await ctx.send(embed=embed, view=MMView())

# ======================
# RUN
# ======================
bot.run(os.getenv("TOKEN"))