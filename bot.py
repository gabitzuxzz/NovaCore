import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from pathlib import Path
from ui.components import StockView

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/novacore.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

REQUIRED_ENV_VARS = [
    'DISCORD_TOKEN',
    'MAIN_CHANNEL_ID',
    'STAFF_CHANNEL_ID',
    'PUBLIC_LOG_CHANNEL_ID',
    'CUSTOMER_ROLE_ID',
    'STAFF_ROLE_IDS',
    'PAYPAL_EMAIL',
    'DATABASE_PATH',
    'LOG_DIR'
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

Path(os.getenv('LOG_DIR')).mkdir(parents=True, exist_ok=True)
Path(os.path.dirname(os.getenv('DATABASE_PATH'))).mkdir(parents=True, exist_ok=True)

async def init_database():
    """Initialize database tables"""
    from database.db_manager import DatabaseManager
    db = DatabaseManager(os.getenv('DATABASE_PATH'))
    await db.init_db()
    logging.info('Database initialized successfully')

async def load_extensions():
    """Load all cog extensions"""
    for filename in Path('./cogs').glob('*.py'):
        if filename.stem != '__init__':
            try:
                await bot.load_extension(f'cogs.{filename.stem}')
                logging.info(f'Loaded extension {filename.stem}')
            except Exception as e:
                logging.error(f'Failed to load extension {filename.stem}: {str(e)}')

@bot.event
async def setup_hook():
    """Setup hook called before bot starts"""
    await init_database()
    await load_extensions()

@bot.event
async def on_ready():
    """Handler for when bot is ready"""
    logging.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    await bot.tree.sync()
    
    try:
        channel = bot.get_channel(int(os.getenv('MAIN_CHANNEL_ID')))
        if channel:
            async for message in channel.history(limit=100):
                if message.author == bot.user and "💼 NovaCore Stock" in message.content:
                    return
                
            embed = discord.Embed(
                title="💼 NovaCore Products",
                description="Welcome to our exclusive products catalog! Browse through our categories below to discover our premium offerings.",
                color=0x8b5cf6
            )
            embed.set_thumbnail(url="https://i.imgur.com/OpQROuS.png")
            embed.add_field(
                name="🛒 How to Purchase",
                value="1. Click `Show Stock`\n2. Select a category\n3. Choose your product\n4. Complete checkout",
                inline=False
            )
            embed.set_footer(text="© NovaCore | Premium Digital Products")
            
            view = StockView()
            await channel.send(embed=embed, view=view)
    except Exception as e:
        logging.error(f'Error setting up stock panel: {str(e)}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f}s")
    else:
        logging.error(f'Unhandled error: {str(error)}')
        await ctx.send("An error occurred. Please try again later.")

def main():
    """Main entry point for the bot"""
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logging.critical(f'Fatal error: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main()
