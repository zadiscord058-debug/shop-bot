import os
import discord
from discord.ext import commands

# ======================
# CONFIG
# ======================
TICKET_CATEGORY_ID = 1492849115120537750
MM_ROLE_ID = 1492849227414638642

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
def extract_member_from_input(guild, input_value):
    if input_value.startswith("<@") and input_value.endswith(">"):
        input_value = input_value.replace("<@", "").replace("!", "").replace(">", "")
        return guild.get_member(int(input_value))
    return discord.utils.find(lambda m: m.name == input_value, guild.members)

# ======================
# EMBED BUILDER
# ======================
def make_ticket_embed(data):
    return discord.Embed(
        title="💜 Middleman Ticket Panel",
        description=(
            f"**Trade Type:** {data.get('trade_type')}\n"
            f"**Creator:** <@{data.get('creator_id')}>\n"
            f"**Other User:** {data.get('other_user_mention')}\n\n"
            f"**Details:**\n{data.get('trade_details')}\n\n"
            f"**Status:** {data.get('status')}\n"
            f"**Claimed by:** {f'<@{data['claimer_id']}>' if data.get('claimer_id') else 'None'}"
        ),
        color=PURPLE
    )

# ======================
# SELECT
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
        self.agreement = discord.ui.TextInput(label="Agreement (YES)", required=True)

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
            "creator_id": interaction.user.id,
            "other_user_mention": other_member.mention if other_member else self.other_user.value,
            "claimer_id": None,
            "trade_type": self.trade_type,
            "trade_details": self.trade_details.value,
            "status": "🟡 Waiting for claim",
        }

        msg = await channel.send(
            content=interaction.user.mention,
            embed=make_ticket_embed(ticket_data[channel.id]),
            view=TicketButtons()
        )

        ticket_data[channel.id]["message_id"] = msg.id

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

# ======================
# BUTTONS
# ======================
class TicketButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update(self, channel):
        data = ticket_data[channel.id]
        msg = await channel.fetch_message(data["message_id"])
        await msg.edit(embed=make_ticket_embed(data))

    @discord.ui.button(label="claim", style=discord.ButtonStyle.success, emoji="🎫")
    async def claim(self, interaction, button):

        if MM_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("no permission", ephemeral=True)

        data = ticket_data[interaction.channel.id]
        data["claimer_id"] = interaction.user.id
        data["status"] = "🟢 Claimed"

        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)

        await self.update(interaction.channel)
        await interaction.response.send_message("claimed", ephemeral=True)

    @discord.ui.button(label="unclaim", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def unclaim(self, interaction, button):

        data = ticket_data[interaction.channel.id]
        data["claimer_id"] = None
        data["status"] = "🟡 Waiting for claim"

        await self.update(interaction.channel)
        await interaction.response.send_message("unclaimed", ephemeral=True)

    @discord.ui.button(label="add", style=discord.ButtonStyle.primary, emoji="➕")
    async def add(self, interaction, button):

        await interaction.response.send_message("use $add @user", ephemeral=True)

    @discord.ui.button(label="remove", style=discord.ButtonStyle.danger, emoji="➖")
    async def remove(self, interaction, button):

        await interaction.response.send_message("use $remove @user", ephemeral=True)

    @discord.ui.button(label="close", style=discord.ButtonStyle.red, emoji="❌")
    async def close(self, interaction, button):
        await interaction.channel.delete()

# ======================
# COMMANDS
# ======================
@bot.command()
async def add(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, view_channel=True, send_messages=True)
    await ctx.send(f"➕ added {member.mention}")

@bot.command()
async def remove(ctx, member: discord.Member):
    await ctx.channel.set_permissions(member, overwrite=None)
    await ctx.send(f"➖ removed {member.mention}")

@bot.command()
async def claim(ctx):
    ticket_data[ctx.channel.id]["claimer_id"] = ctx.author.id
    await ctx.send(f"🎫 claimed by {ctx.author.mention}")

@bot.command()
async def unclaim(ctx):
    ticket_data[ctx.channel.id]["claimer_id"] = None
    await ctx.send("🔄 unclaimed")

@bot.command()
async def close(ctx):
    await ctx.channel.delete()

# ======================
# PANEL
# ======================
@bot.command()
async def panel(ctx):

    embed = discord.Embed(
        title="💜 Middleman Service",
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

    await ctx.send(embed=embed, view=MMView())

# ======================
# RUN
# ======================
bot.run(os.getenv("TOKEN"))