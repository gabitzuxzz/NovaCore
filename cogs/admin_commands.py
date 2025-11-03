import discord
from discord.ext import commands
from discord import app_commands
import os
import logging

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="msg", description="Send a custom message to a channel")
    @app_commands.describe(
        channel="The channel to send the message to",
        message="The message content",
        author="The author/sender name"
    )
    async def send_message(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        message: str,
        author: str
    ):
        staff_role_ids = set(map(int, os.getenv('STAFF_ROLE_IDS', '').split(',')))
        owner_role_id = int(os.getenv('OWNER_ROLE_ID', '0'))
        
        user_role_ids = {role.id for role in interaction.user.roles}
        is_authorized = owner_role_id in user_role_ids or bool(staff_role_ids & user_role_ids)
        
        if not is_authorized:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return
        
        embed = discord.Embed(
            description=f"{message}\n\n*-sent by {author}*",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="© NovaCore")
        
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ Message sent successfully to {channel.mention}", 
                ephemeral=True
            )
            logging.info(f"{interaction.user} sent message to {channel.name} as {author}")
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to send message: {str(e)}", 
                ephemeral=True
            )
            logging.error(f"Error sending message: {e}")


async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
