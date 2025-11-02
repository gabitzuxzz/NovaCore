import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
from typing import Optional
from database.db_manager import DatabaseManager
from datetime import datetime
import matplotlib.pyplot as plt
import io

class ProductManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager(os.getenv('DATABASE_PATH'))
        self._staff_role_ids = set(map(int, os.getenv('STAFF_ROLE_IDS').split(',')))
        self._owner_role_id = int(os.getenv('OWNER_ROLE_ID'))

    def is_staff(self, member: discord.Member) -> bool:
        """Check if member has staff role"""
        return any(role.id in self._staff_role_ids for role in member.roles) or \
               member.guild_permissions.administrator

    def is_owner(self, member: discord.Member) -> bool:
        """Check if member has owner role"""
        return self._owner_role_id in [r.id for r in member.roles] or \
               member.guild.owner_id == member.id

    @app_commands.command(name="addproduct")
    @app_commands.describe(
        category="Product category",
        product="Product name",
        price="Product price in EUR",
        description="Product description",
        deliverables="Comma-separated deliverables or file URL",
        image_url="Product image URL",
        stock="Initial stock amount"
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def addproduct(self, interaction: discord.Interaction, category: str,
                        product: str, price: float, description: str,
                        deliverables: str, image_url: str, stock: int = 0):
        """Add or update a product in stock"""
        if not self.is_owner(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        valid_categories = ["best_sold", "new", "social", "discord", "accounts", "services"]
        if category.lower() not in valid_categories:
            categories_str = ", ".join(valid_categories)
            await interaction.response.send_message(
                f"Invalid category. Please use one of: {categories_str}",
                ephemeral=True
            )
            return

        if price <= 0:
            await interaction.response.send_message(
                "Price must be greater than 0.",
                ephemeral=True
            )
            return

        success = await self.db.add_product(
            product, category, price, description,
            image_url, deliverables, stock
        )

        if success:
            embed = discord.Embed(
                title="✅ Product Added Successfully",
                description=f"**{product}** has been added to the store!",
                color=0x00ff00
            )
            if image_url and image_url.startswith(('http://', 'https://')):
                embed.set_thumbnail(url=image_url)
            embed.add_field(name="📁 Category", value=f"`{category.title()}`", inline=True)
            embed.add_field(name="💰 Price", value=f"**€{price:.2f}**", inline=True)
            embed.add_field(name="📦 Stock", value=f"`{stock}` units", inline=True)
            embed.add_field(name="📝 Description", value=description, inline=False)
            embed.add_field(name="🎁 Deliverables", value=deliverables, inline=False)
            embed.set_footer(text=f"Added by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                "Failed to add/update product. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="removestock")
    @app_commands.describe(product="Product name to remove")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def removestock(self, interaction: discord.Interaction, product: str):
        """Remove a product from stock"""
        if not self.is_owner(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        success = await self.db.remove_product(product)
        if success:
            await interaction.response.send_message(
                f"✅ Successfully removed {product} from stock."
            )
        else:
            await interaction.response.send_message(
                f"Failed to remove {product}. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="setstock")
    @app_commands.describe(
        product="Product name",
        amount="New stock amount"
    )
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def setstock(self, interaction: discord.Interaction,
                      product: str, amount: int):
        """Set stock amount for a product"""
        if not self.is_staff(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        if amount < 0:
            await interaction.response.send_message(
                "Stock amount cannot be negative.",
                ephemeral=True
            )
            return

        success = await self.db.update_stock(product, amount)
        if success:
            await interaction.response.send_message(
                f"✅ Updated stock for {product} to {amount}"
            )
        else:
            await interaction.response.send_message(
                f"Failed to update stock for {product}. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="stats")
    @app_commands.describe(
        period="Statistics period (daily/weekly/monthly/all)"
    )
    @app_commands.choices(period=[
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
        app_commands.Choice(name="Monthly", value="monthly"),
        app_commands.Choice(name="All Time", value="all")
    ])
    async def stats(self, interaction: discord.Interaction,
                   period: str = "all"):
        """View sales statistics"""
        if not self.is_staff(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            summary, best_sellers = await self.db.get_sales_stats(period)

            # Create matplotlib chart
            plt.figure(figsize=(10, 6))
            plt.style.use('dark_background')
            
            dates = [b['date'] for b in best_sellers]
            revenues = [b['revenue'] for b in best_sellers]
            
            plt.plot(dates, revenues, marker='o', color='#8b5cf6')
            plt.title(f'Revenue Over Time ({period.title()})')
            plt.xlabel('Date')
            plt.ylabel('Revenue (€)')
            plt.grid(True, alpha=0.3)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Save chart
            chart_path = os.path.join(
                os.getenv('LOG_DIR'),
                f'stats_{period}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            )
            plt.savefig(chart_path, bbox_inches='tight', dpi=300)
            plt.close()

            # Create embed
            embed = discord.Embed(
                title=f"📊 Sales Statistics ({period.title()})",
                color=0x8b5cf6
            )
            
            embed.add_field(
                name="Summary",
                value=f"""
                Total Orders: {summary['total_orders']}
                Completed Orders: {summary['completed_orders']}
                Total Revenue: €{summary['total_revenue']:.2f}
                """,
                inline=False
            )

            if best_sellers:
                best_products = "\n".join(
                    f"• {b['name']}: {b['units_sold']} sold, €{b['revenue']:.2f}"
                    for b in best_sellers[:5]
                )
                embed.add_field(
                    name="Best Selling Products",
                    value=best_products or "No sales data",
                    inline=False
                )

            # Attach chart
            file = discord.File(chart_path, filename="stats_chart.png")
            embed.set_image(url="attachment://stats_chart.png")

            await interaction.followup.send(
                embed=embed,
                file=file
            )

        except Exception as e:
            logging.error(f"Error generating stats: {str(e)}")
            await interaction.followup.send(
                "Failed to generate statistics. Please try again.",
                ephemeral=True
            )

    @app_commands.command(name="listproducts")
    @app_commands.describe(category="Optional category filter")
    async def listproducts(self, interaction: discord.Interaction,
                          category: Optional[str] = None):
        """List all products or products in a category"""
        if not self.is_staff(interaction.user):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
            return

        products = await self.db.get_products_by_category(category) if category \
                  else await self.db.get_all_products()

        if not products:
            await interaction.response.send_message(
                f"No products found{f' in category {category}' if category else ''}.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📦 Product List{f' - {category}' if category else ''}",
            color=0x8b5cf6
        )

        for product in products:
            embed.add_field(
                name=product['name'],
                value=f"""
                Category: {product['category']}
                Price: €{product['price']:.2f}
                Stock: {product['stock']}
                """,
                inline=True
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vouch")
    @app_commands.describe(
        stars="Rating stars (1-5)",
        description="Vouch description",
        proof="Optional proof link (image/screenshot)"
    )
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def vouch(self, interaction: discord.Interaction, stars: int,
                   description: str, proof: Optional[str] = None):
        """Submit a vouch/review for the server"""
        if stars < 1 or stars > 5:
            await interaction.response.send_message(
                "Stars must be between 1 and 5.",
                ephemeral=True
            )
            return

        star_display = "⭐" * stars + "☆" * (5 - stars)
        
        embed = discord.Embed(
            title="✨ New Vouch Received!",
            description=description,
            color=0xFFD700 if stars >= 4 else 0x8b5cf6
        )
        
        embed.add_field(name="Rating", value=star_display, inline=False)
        embed.set_author(
            name=f"{interaction.user.name}#{interaction.user.discriminator}",
            icon_url=interaction.user.display_avatar.url
        )
        
        if proof:
            if proof.startswith('http'):
                embed.set_image(url=proof)
            else:
                embed.add_field(name="Proof", value=proof, inline=False)
        
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        embed.timestamp = discord.utils.utcnow()

        vouch_channel_id = os.getenv('VOUCH_CHANNEL_ID')
        if vouch_channel_id:
            vouch_channel = interaction.guild.get_channel(int(vouch_channel_id))
            if vouch_channel:
                await vouch_channel.send(embed=embed)
        
        await interaction.response.send_message(
            "✅ Thank you for your vouch! It has been submitted successfully.",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ProductManagement(bot))
