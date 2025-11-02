import discord
from discord.ext import commands
import os
import logging
from datetime import datetime
import random
import string
from typing import Optional
from database.db_manager import DatabaseManager

class OrderManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager(os.getenv('DATABASE_PATH'))
        self._staff_role_ids = set(map(int, os.getenv('STAFF_ROLE_IDS').split(',')))
        self._customer_role_id = int(os.getenv('CUSTOMER_ROLE_ID'))
        self._public_log_channel = int(os.getenv('PUBLIC_LOG_CHANNEL_ID'))
        
    def is_staff(self, member: discord.Member) -> bool:
        """Check if member has staff role"""
        return any(role.id in self._staff_role_ids for role in member.roles)

    def generate_order_id(self) -> str:
        """Generate unique order ID"""
        date = datetime.now().strftime("%Y%m%d")
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"NC-{date}-{random_chars}"

    async def create_payment_embed(self, user: discord.User, order: dict, product: dict) -> discord.Embed:
        """Create payment instructions embed"""
        embed = discord.Embed(
            title="🛍️ Order Details",
            description=f"Order ID: {order['order_id']}",
            color=0x8b5cf6
        )
        
        total = order['total_price']
        embed.add_field(name="Product", value=product['name'], inline=True)
        embed.add_field(name="Quantity", value=str(order['quantity']), inline=True)
        embed.add_field(name="Total", value=f"€{total:.2f}", inline=True)
        
        if order['payment_method'] == 'paypal':
            embed.add_field(
                name="Payment Instructions",
                value=f"""
                Please send €{total:.2f} to:
                PayPal: {os.getenv('PAYPAL_EMAIL')}
                
                Important:
                • Send as Friends & Family
                • Include Order ID ({order['order_id']}) in notes
                """,
                inline=False
            )
        else:
            address_var = f"{order['payment_method'].upper()}_ADDRESS"
            address = os.getenv(address_var)
            
            network = ""
            if order['payment_method'] == 'usdt':
                network = "\nNetwork: Tron (TRC20)"
            
            embed.add_field(
                name="Payment Instructions",
                value=f"""
                Please send €{total:.2f} worth of {order['payment_method'].upper()} to:
                Address: `{address}`{network}
                """,
                inline=False
            )
            
        embed.add_field(
            name="📎 Upload Payment Proof",
            value="Please upload your payment screenshot/proof as a reply to this message.",
            inline=False
        )
        
        embed.set_footer(text="© NovaCore • All Rights Reserved")
        return embed

    async def send_staff_review(self, order: dict, product: dict,
                              proof_url: str, user: discord.User):
        """Send payment proof to staff for review"""
        staff_channel = self.bot.get_channel(int(os.getenv('STAFF_CHANNEL_ID')))
        if not staff_channel:
            logging.error("Staff channel not found")
            return
            
        embed = discord.Embed(
            title="💸 Payment Proof Received",
            color=0x8b5cf6
        )
        
        embed.add_field(name="Order", value=order['order_id'], inline=True)
        embed.add_field(name="Product", value=product['name'], inline=True)
        embed.add_field(name="Quantity", value=str(order['quantity']), inline=True)
        embed.add_field(name="Amount", value=f"€{order['total_price']:.2f}", inline=True)
        embed.add_field(name="Payment Method", value=order['payment_method'].upper(), inline=True)
        embed.add_field(name="Buyer", value=user.mention, inline=True)
        
        if proof_url:
            embed.set_image(url=proof_url)
            
        view = ReviewView(self.bot, order['order_id'], product, user.id, order['quantity'], self._staff_role_ids)
        await staff_channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle payment proof uploads in DMs"""
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return
            
        order = await self.db.get_pending_order(str(message.author.id))
        if not order:
            return
            
        if not message.attachments:
            await message.channel.send(
                "Please upload an image as payment proof."
            )
            return
        
        is_image = False
        for att in message.attachments:
            if att.content_type and att.content_type.startswith('image/'):
                is_image = True
                break
            elif att.filename and att.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                is_image = True
                break
        
        if not is_image:
            await message.channel.send(
                "Please upload an image as payment proof."
            )
            return
            
        proof_url = message.attachments[0].url
        
        product = await self.db.get_product(order['product_id'])
        if not product:
            await message.channel.send(
                "Error: Product not found. Please contact support."
            )
            return
            
        success = await self.db.update_order_proof(
            order['order_id'],
            proof_url
        )
        
        if success:
            await message.channel.send(
                "✅ Payment proof received! Staff will review it shortly."
            )
            await self.send_staff_review(
                order, product, proof_url, message.author
            )
        else:
            await message.channel.send(
                "Error saving payment proof. Please try again or contact support."
            )

class ReviewView(discord.ui.View):
    def __init__(self, bot, order_id: str, product: dict, user_id: int, quantity: int, staff_role_ids: set):
        super().__init__(timeout=None)
        self.bot = bot
        self.order_id = order_id
        self.product = product
        self.user_id = user_id
        self.quantity = quantity
        self._staff_role_ids = staff_role_ids
        self.db = DatabaseManager(os.getenv('DATABASE_PATH'))

    @discord.ui.button(label="✅ Accept Payment",
                      style=discord.ButtonStyle.green,
                      custom_id="accept_payment")
    async def accept_payment(self,
                           interaction: discord.Interaction,
                           button: discord.ui.Button):
        """Handle payment acceptance"""
        if not any(role.id in self._staff_role_ids for role in interaction.user.roles):
            await interaction.response.send_message(
                "You don't have permission to do this.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        success = await self.db.update_order_status(self.order_id, 'completed')
        if not success:
            await interaction.followup.send(
                "Error updating order status. Please try again.",
                ephemeral=True
            )
            return

        try:
            user = self.bot.get_user(self.user_id)
            if user:
                embed = discord.Embed(
                    title="✅ Order Completed",
                    description=f"Order {self.order_id} has been completed!",
                    color=0x8b5cf6
                )
                
                deliverables_str = self.product.get('deliverables', 'Digital product')
                if deliverables_str:
                    deliverables = deliverables_str.split(',')
                    formatted_deliverables = "\n".join(
                        f"• {d.strip()}" for d in deliverables
                    )
                else:
                    formatted_deliverables = "• Digital product delivery"
                
                embed.add_field(
                    name="Your Products",
                    value=formatted_deliverables,
                    inline=False
                )
                
                embed.add_field(
                    name="Thank You!",
                    value="Please leave a vouch in #feedbacks",
                    inline=False
                )
                
                await user.send(embed=embed)

                guild = interaction.guild
                member = guild.get_member(self.user_id)
                if member:
                    role = guild.get_role(int(os.getenv('CUSTOMER_ROLE_ID')))
                    if role and role not in member.roles:
                        await member.add_roles(role)

            public_channel = self.bot.get_channel(
                int(os.getenv('PUBLIC_LOG_CHANNEL_ID'))
            )
            if public_channel:
                embed = discord.Embed(
                    description=f"🧾 A user has purchased {self.product['name']} x{self.quantity}",
                    color=0x8b5cf6
                )
                await public_channel.send(embed=embed)

            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)

            await interaction.followup.send(
                "✅ Order completed successfully!",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Error completing order: {str(e)}")
            await interaction.followup.send(
                "Error completing order. Some actions may have failed.",
                ephemeral=True
            )

    @discord.ui.button(label="❌ Reject Payment",
                      style=discord.ButtonStyle.red,
                      custom_id="reject_payment")
    async def reject_payment(self,
                           interaction: discord.Interaction,
                           button: discord.ui.Button):
        """Handle payment rejection"""
        if not any(role.id in self._staff_role_ids for role in interaction.user.roles):
            await interaction.response.send_message(
                "You don't have permission to do this.",
                ephemeral=True
            )
            return

        modal = RejectModal(self.order_id, self.user_id, self.db)
        await interaction.response.send_modal(modal)

class RejectModal(discord.ui.Modal):
    def __init__(self, order_id: str, user_id: int, db: DatabaseManager):
        super().__init__(title="Reject Payment")
        self.order_id = order_id
        self.user_id = user_id
        self.db = db
        
        self.reason = discord.ui.TextInput(
            label="Rejection Reason",
            placeholder="Enter reason for rejection",
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        success = await self.db.update_order_status(self.order_id, 'rejected')
        if not success:
            await interaction.response.send_message(
                "Error updating order status. Please try again.",
                ephemeral=True
            )
            return

        try:
            user = interaction.client.get_user(self.user_id)
            if user:
                embed = discord.Embed(
                    title="❌ Payment Rejected",
                    description=f"Your payment for order {self.order_id} was rejected.",
                    color=0xff0000
                )
                embed.add_field(
                    name="Reason",
                    value=self.reason.value,
                    inline=False
                )
                embed.add_field(
                    name="What Next?",
                    value="You can:\n• Upload a new payment proof\n• Contact support for assistance",
                    inline=False
                )
                await user.send(embed=embed)

            try:
                for child in interaction.message.view.children:
                    child.disabled = True
                await interaction.message.edit(view=interaction.message.view)
            except:
                pass

            await interaction.response.send_message(
                "✅ Payment rejected and buyer notified.",
                ephemeral=True
            )

        except Exception as e:
            logging.error(f"Error handling rejection: {str(e)}")
            await interaction.response.send_message(
                "Error handling rejection. Some actions may have failed.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(OrderManagement(bot))
