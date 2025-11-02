import discord
from discord import ui
from typing import Optional, List
import logging

class CategorySelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(value="best_sold", label="Best Sold", emoji="🏆"),
            discord.SelectOption(value="new", label="New", emoji="✨"),
            discord.SelectOption(value="social", label="Social Media Boost", emoji="📱"),
            discord.SelectOption(value="discord", label="Discord", emoji="💬"),
            discord.SelectOption(value="accounts", label="Accounts", emoji="👤"),
            discord.SelectOption(value="services", label="Services", emoji="🛠️")
        ]
        super().__init__(
            placeholder="Select a category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get database manager instance
        from novacore_bot.database.db_manager import DatabaseManager
        import os
        
        db = DatabaseManager(os.getenv('DATABASE_PATH'))
        products = await db.get_products_by_category(self.values[0])
        if not products:
            await interaction.followup.send("❌ No products available in this category.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🛍️ {self.values[0].title()} Products",
            description="Browse our premium selection below.",
            color=0x8b5cf6
        )
        
        for product in products:
            status = "🟢 In Stock" if product['stock'] > 0 else "🔴 Out of Stock"
            embed.add_field(
                name=f"{product['name']} | €{product['price']:.2f}",
                value=f"```{product['description']}```\n**Status:** {status} ({product['stock']} left)",
                inline=False
            )
        
        embed.set_footer(text="Click 'Buy Now' below the product you want to purchase")
        
        view = ProductView(products)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class StockView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CategorySelect())

    @ui.button(label="Show Stock", style=discord.ButtonStyle.primary, custom_id="show_stock")
    async def show_stock(self, interaction: discord.Interaction, button: ui.Button):
        view = ui.View()
        view.add_item(CategorySelect())
        await interaction.response.send_message(
            "Please select a category below to view products:",
            view=view,
            ephemeral=True
        )

class BuyModal(ui.Modal):
    def __init__(self, product: dict):
        super().__init__(title=f"Purchase {product['name']}")
        self.product = product
        
        self.quantity = ui.TextInput(
            label="Quantity",
            placeholder="Enter quantity (1-100)",
            min_length=1,
            max_length=3,
            required=True
        )
        self.add_item(self.quantity)
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantity = int(self.quantity.value)
            if quantity < 1 or quantity > 100:
                raise ValueError("Invalid quantity")
                
            if quantity > self.product['stock']:
                await interaction.response.send_message(
                    "Sorry, not enough stock available.",
                    ephemeral=True
                )
                return
                
            # Show payment method selection
            view = PaymentMethodView(self.product, quantity)
            await interaction.response.send_message(
                "Please select your payment method:",
                view=view,
                ephemeral=True
            )
            
        except ValueError:
            await interaction.response.send_message(
                "Please enter a valid quantity between 1 and 100.",
                ephemeral=True
            )

class PaymentMethodView(ui.View):
    def __init__(self, product: dict, quantity: int):
        super().__init__(timeout=300)
        self.product = product
        self.quantity = quantity
        self.total = product['price'] * quantity

    @ui.button(label="PayPal", style=discord.ButtonStyle.primary)
    async def paypal(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_payment_selection(interaction, "paypal")

    @ui.button(label="Crypto", style=discord.ButtonStyle.primary)
    async def crypto(self, interaction: discord.Interaction, button: ui.Button):
        # Show crypto selection view
        view = CryptoSelectView(self.product, self.quantity, self.total)
        await interaction.response.send_message(
            "Select cryptocurrency:",
            view=view,
            ephemeral=True
        )

class CryptoSelectView(ui.View):
    def __init__(self, product: dict, quantity: int, total: float):
        super().__init__(timeout=300)
        self.product = product
        self.quantity = quantity
        self.total = total

    @ui.select(
        placeholder="Select cryptocurrency...",
        options=[
            discord.SelectOption(value="btc", label="Bitcoin", emoji="₿"),
            discord.SelectOption(value="eth", label="Ethereum", emoji="Ξ"),
            discord.SelectOption(value="ltc", label="Litecoin", emoji="Ł"),
            discord.SelectOption(value="usdt", label="USDT", emoji="₮"),
            discord.SelectOption(value="sol", label="Solana", emoji="◎"),
        ]
    )
    async def crypto_select(self, interaction: discord.Interaction, select: ui.Select):
        await self.handle_payment_selection(interaction, select.values[0])

class ProductView(ui.View):
    def __init__(self, products: List[dict]):
        super().__init__(timeout=300)
        self.products = {p['name']: p for p in products}
        
        # Add Buy Now buttons for each product
        for product in products:
            button = ui.Button(
                label=f"Buy {product['name']}",
                style=discord.ButtonStyle.success,
                custom_id=f"buy_{product['name']}"
            )
            button.callback = lambda i, p=product: self.buy_callback(i, p)
            self.add_item(button)
            
    async def buy_callback(self, interaction: discord.Interaction, product: dict):
        if product['stock'] <= 0:
            await interaction.response.send_message(
                "Sorry, this product is out of stock.",
                ephemeral=True
            )
            return
            
        modal = BuyModal(product)
        await interaction.response.send_modal(modal)