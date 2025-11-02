import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from database.db_manager import DatabaseManager

class PaymentsManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager(os.getenv('DATABASE_PATH'))
        self._owner_role_id = int(os.getenv('OWNER_ROLE_ID'))

    def is_owner(self, member: discord.Member) -> bool:
        """Check if member has owner role"""
        return self._owner_role_id in [r.id for r in member.roles] or \
               member.guild.owner_id == member.id

    @app_commands.command(name="payments")
    @app_commands.describe(
        payment_method="Payment method to configure (paypal/crypto/card)",
        address="Payment address or information"
    )
    @app_commands.choices(payment_method=[
        app_commands.Choice(name="PayPal", value="paypal"),
        app_commands.Choice(name="Cryptocurrency", value="crypto"),
        app_commands.Choice(name="Card", value="card")
    ])
    async def set_payment_method(self, interaction: discord.Interaction, 
                               payment_method: str, address: str):
        """Configure payment method information"""
        if not self.is_owner(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        try:
            # Store payment information in database
            success = await self.db.update_payment_info(payment_method, address)
            
            if success:
                embed = discord.Embed(
                    title="✅ Payment Method Updated",
                    description=f"Successfully updated {payment_method.upper()} payment information.",
                    color=0x00ff00
                )
                embed.add_field(
                    name="Payment Method",
                    value=payment_method.upper(),
                    inline=True
                )
                embed.add_field(
                    name="Address/Info",
                    value=f"||{address}||" if payment_method == "crypto" else address,
                    inline=True
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "Failed to update payment information.",
                    ephemeral=True
                )

        except Exception as e:
            logging.error(f"Error updating payment info: {str(e)}")
            await interaction.response.send_message(
                "An error occurred while updating payment information.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(PaymentsManagement(bot))
