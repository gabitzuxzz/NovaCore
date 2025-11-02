import discord
from discord import ui
from typing import Optional, List
import logging
import os

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
        
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager(os.getenv('DATABASE_PATH'))
        products = await db.get_products_by_category(self.values[0])
        if not products:
            await interaction.followup.send("❌ No products available in this category.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🛍️ {self.values[0].replace('_', ' ').title()} Products",
            description="Browse our premium selection below. Click the **Buy** button to purchase.",
            color=0x8b5cf6
        )
        
        for product in products:
            status = "🟢 In Stock" if product['stock'] > 0 else "🔴 Out of Stock"
            embed.add_field(
                name=f"**{product['name']}** - €{product['price']:.2f}",
                value=f"{product['description'][:100]}...\n**Status:** {status} ({product['stock']} units available)",
                inline=False
            )
            if product.get('image_url'):
                embed.set_thumbnail(url=product['image_url'])
        
        embed.set_footer(text="💡 Click 'Buy' button below to purchase your product")
        
        view = ProductView(products)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class StockView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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

    async def handle_payment_selection(self, interaction: discord.Interaction, payment_method: str):
        from database.db_manager import DatabaseManager
        import random
        import string
        from datetime import datetime
        
        db = DatabaseManager(os.getenv('DATABASE_PATH'))
        
        date = datetime.now().strftime("%Y%m%d")
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        order_id = f"NC-{date}-{random_chars}"
        
        success = await db.create_order(
            order_id=order_id,
            user_id=str(interaction.user.id),
            product_id=self.product['id'],
            quantity=self.quantity,
            total_price=self.total,
            payment_method=payment_method
        )
        
        if not success:
            await interaction.response.send_message(
                "❌ Failed to create order. Please try again.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🛍️ Order Created Successfully",
            description=f"Order ID: **{order_id}**",
            color=0x8b5cf6
        )
        
        embed.add_field(name="Product", value=self.product['name'], inline=True)
        embed.add_field(name="Quantity", value=str(self.quantity), inline=True)
        embed.add_field(name="Total", value=f"€{self.total:.2f}", inline=True)
        
        if payment_method == 'paypal':
            embed.add_field(
                name="💳 PayPal Payment Instructions",
                value=f"""
                Please send **€{self.total:.2f}** to:
                **PayPal:** {os.getenv('PAYPAL_EMAIL')}
                
                **Important:**
                • Send as Friends & Family
                • Include Order ID (**{order_id}**) in the payment notes
                • After payment, send proof of payment so our staff can review your order
                """,
                inline=False
            )
        else:
            address_var = f"{payment_method.upper()}_ADDRESS"
            address = os.getenv(address_var, "Contact staff for address")
            
            network_info = ""
            if payment_method == 'usdt':
                network_info = "\n**Network:** Tron (TRC20)"
            
            embed.add_field(
                name=f"💰 {payment_method.upper()} Payment Instructions",
                value=f"""
                Please send **€{self.total:.2f}** worth of {payment_method.upper()} to:
                **Address:** `{address}`{network_info}
                
                **Important:**
                • Include Order ID (**{order_id}**) in transaction notes if possible
                • After payment, send proof of payment so our staff can review your order
                """,
                inline=False
            )
        
        embed.set_footer(text="Send proof of payment so our staff can review your order")
        embed.timestamp = discord.utils.utcnow()
        
        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message(
                "✅ Order created! Check your DMs for payment instructions.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I couldn't send you a DM. Please enable DMs from server members and try again.",
                ephemeral=True
            )

    @ui.button(label="PayPal", style=discord.ButtonStyle.primary, emoji="💳")
    async def paypal(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_payment_selection(interaction, "paypal")

    @ui.button(label="Crypto", style=discord.ButtonStyle.primary, emoji="💰")
    async def crypto(self, interaction: discord.Interaction, button: ui.Button):
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

    async def handle_payment_selection(self, interaction: discord.Interaction, payment_method: str):
        payment_view = PaymentMethodView(self.product, self.quantity)
        await payment_view.handle_payment_selection(interaction, payment_method)

    @ui.select(
        placeholder="Select cryptocurrency...",
        options=[
            discord.SelectOption(value="btc", label="Bitcoin", emoji="🪙"),
            discord.SelectOption(value="eth", label="Ethereum", emoji="💎"),
            discord.SelectOption(value="ltc", label="Litecoin", emoji="🔷"),
            discord.SelectOption(value="usdt", label="USDT", emoji="💵"),
            discord.SelectOption(value="sol", label="Solana", emoji="☀️"),
        ]
    )
    async def crypto_select(self, interaction: discord.Interaction, select: ui.Select):
        await self.handle_payment_selection(interaction, select.values[0])

class ProductView(ui.View):
    def __init__(self, products: List[dict]):
        super().__init__(timeout=300)
        self.products = {p['name']: p for p in products}
        
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
