import discord
from discord.ext import commands
from discord import ui
import os
import logging
from datetime import datetime
from database.db_manager import DatabaseManager

class TicketModal(ui.Modal):
    def __init__(self, ticket_type: str, bot):
        super().__init__(title=f"{ticket_type} Ticket")
        self.ticket_type = ticket_type
        self.bot = bot
        
        self.subject = ui.TextInput(
            label="Subject",
            placeholder="Briefly describe your issue...",
            min_length=5,
            max_length=100,
            required=True
        )
        self.add_item(self.subject)
        
        order_id_required = ticket_type != "Others"
        order_id_label = "Order ID" if order_id_required else "Order ID (optional)"
        
        self.order_id = ui.TextInput(
            label=order_id_label,
            placeholder="NC-YYYYMMDD-XXXXXX",
            min_length=0 if not order_id_required else 5,
            max_length=20,
            required=order_id_required
        )
        self.add_item(self.order_id)
        
        self.description = ui.TextInput(
            label="Description",
            placeholder="Provide detailed information...",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=1000,
            required=True
        )
        self.add_item(self.description)
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        category_id = int(os.getenv('TICKET_CATEGORY_ID'))
        category = interaction.guild.get_channel(category_id)
        
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Ticket category not found. Please contact an administrator.", ephemeral=True)
            return
        
        ticket_number = len(category.channels) + 1
        channel_name = f"ticket-{ticket_number:04d}"
        
        staff_role_ids = set(map(int, os.getenv('STAFF_ROLE_IDS').split(',')))
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True)
        }
        
        for role_id in staff_role_ids:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        
        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_number:04d} - {self.ticket_type}",
            description=f"**Subject:** {self.subject.value}\n\n**Description:**\n{self.description.value}",
            color=0x8b5cf6,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Type", value=self.ticket_type, inline=True)
        
        if self.order_id.value:
            db = DatabaseManager(os.getenv('DATABASE_PATH'))
            order = await db.get_order_by_id(self.order_id.value)
            
            if order:
                product = await db.get_product_by_id(order['product_id'])
                status_emoji = {
                    'pending': '🟡',
                    'approved': '🟢',
                    'rejected': '🔴',
                    'completed': '✅'
                }.get(order['status'], '❓')
                
                embed.add_field(name="Order ID", value=f"`{self.order_id.value}`", inline=False)
                embed.add_field(name="Order Status", value=f"{status_emoji} {order['status'].title()}", inline=True)
                if product:
                    embed.add_field(name="Product", value=product['name'], inline=True)
                embed.add_field(name="Total", value=f"€{order['total_price']:.2f}", inline=True)
                embed.add_field(name="Payment Method", value=order['payment_method'].upper(), inline=True)
                
                order_date = datetime.fromisoformat(order['created_at'])
                embed.add_field(name="Order Date", value=order_date.strftime("%Y-%m-%d %H:%M"), inline=True)
            else:
                embed.add_field(name="Order ID", value=f"`{self.order_id.value}` ❌ Not Found", inline=False)
        
        embed.set_footer(text="A staff member will assist you shortly. • © NovaCore")
        
        view = TicketControlView()
        await ticket_channel.send(f"{interaction.user.mention}", embed=embed, view=view)
        
        await interaction.followup.send(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)


class TicketControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        staff_role_ids = set(map(int, os.getenv('STAFF_ROLE_IDS').split(',')))
        is_staff = any(role.id in staff_role_ids for role in interaction.user.roles)
        
        if not is_staff:
            await interaction.response.send_message("❌ Only staff members can close tickets.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}",
            color=0xff0000,
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user.name}")


class TicketPanelView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @ui.button(label="Product Issue", style=discord.ButtonStyle.primary, emoji="🧩", custom_id="ticket_product")
    async def product_issue(self, interaction: discord.Interaction, button: ui.Button):
        modal = TicketModal("Product Issue", self.bot)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Refund Request", style=discord.ButtonStyle.success, emoji="📁", custom_id="ticket_refund")
    async def refund_request(self, interaction: discord.Interaction, button: ui.Button):
        modal = TicketModal("Refund Request", self.bot)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Other Support", style=discord.ButtonStyle.secondary, emoji="💬", custom_id="ticket_other")
    async def other_ticket(self, interaction: discord.Interaction, button: ui.Button):
        modal = TicketModal("Others", self.bot)
        await interaction.response.send_modal(modal)


class TicketManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.panel_message_id = None
        
    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_ticket_panel()
    
    async def setup_ticket_panel(self):
        """Setup the ticket panel in the designated channel"""
        try:
            channel_id = int(os.getenv('TICKET_PANEL_CHANNEL_ID'))
            channel = self.bot.get_channel(channel_id)
            
            if not channel:
                logging.error(f"Ticket panel channel {channel_id} not found")
                return
            
            async for message in channel.history(limit=10):
                if message.author == self.bot.user:
                    try:
                        await message.delete()
                    except:
                        pass
            
            embed = discord.Embed(
                title="🎫 NovaCore Support",
                description="⭐ **Welcome to Premium Support!**\n\n"
                           "<a:ARROW:1434558184927924397> **How to get help**\n"
                           "Select a category below that matches your issue.\n\n"
                           "<a:ARROW:1434558184927924397> **Response Time**\n"
                           "Our team usually responds within 24 hours.\n\n"
                           "<a:ARROW:1434558184927924397> **Terms**\n"
                           "By creating a ticket, you accept our Terms of Service.\n\n"
                           "🎀 Thank you for choosing NovaCore Premium!",
                color=0x5865F2
            )
            embed.set_thumbnail(url="https://i.imgur.com/gGCBKGe.png")
            embed.set_footer(text="© NovaCore • Premium Support")
            
            view = TicketPanelView(self.bot)
            panel_message = await channel.send(embed=embed, view=view)
            self.panel_message_id = panel_message.id
            
            logging.info(f"Ticket panel created in channel {channel_id}")
            
        except Exception as e:
            logging.error(f"Error setting up ticket panel: {e}")


async def setup(bot):
    await bot.add_cog(TicketManagement(bot))
