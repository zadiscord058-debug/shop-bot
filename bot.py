FOUNDER_ROLE_ID = 123456789012345678  # put your founder role ID here

@bot.command()
async def dmrole(ctx, role: discord.Role, *, text=None):

    # Check if user has the founder role
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
