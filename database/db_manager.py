import aiosqlite
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Products table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    image_url TEXT,
                    deliverables TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Initialize test products
            test_products = [
                # Best Sold Category
                {
                    "name": "⭐ Premium Discord Nitro",
                    "category": "best_sold",
                    "description": "1 Year Discord Nitro subscription with instant delivery. Most popular choice!",
                    "price": 49.99,
                    "stock": 15,
                    "image_url": "https://i.imgur.com/nitro_premium.png",
                    "deliverables": "1x Discord Nitro Gift Link,Instructions for activation"
                },
                # New Category
                {
                    "name": "🆕 Spotify Premium Family",
                    "category": "new",
                    "description": "6 Months Spotify Premium Family Plan. Add up to 6 members!",
                    "price": 29.99,
                    "stock": 10,
                    "image_url": "https://i.imgur.com/spotify_premium.png",
                    "deliverables": "Account credentials,Activation guide,Support for 6 months"
                },
                # Social Media Boost Category
                {
                    "name": "📈 Instagram Growth Package",
                    "category": "social",
                    "description": "Premium Instagram growth package: 5000 followers, 10000 likes, 100 comments",
                    "price": 39.99,
                    "stock": 20,
                    "image_url": "https://i.imgur.com/instagram_boost.png",
                    "deliverables": "Service activation within 24h,Progress tracking link"
                },
                {
                    "name": "🚀 TikTok Viral Package",
                    "category": "social",
                    "description": "Go viral: 100k views, 10k likes, 500 shares for your TikTok video",
                    "price": 24.99,
                    "stock": 25,
                    "image_url": "https://i.imgur.com/tiktok_boost.png",
                    "deliverables": "Service activation code,Instructions PDF"
                },
                # Discord Category
                {
                    "name": "🤖 Custom Discord Bot",
                    "category": "discord",
                    "description": "Custom Discord bot development with your requested features",
                    "price": 99.99,
                    "stock": 5,
                    "image_url": "https://i.imgur.com/discord_bot.png",
                    "deliverables": "Source code,Setup guide,1 month support"
                },
                # Accounts Category
                {
                    "name": "🎮 Netflix Premium 4K",
                    "category": "accounts",
                    "description": "Netflix Premium 4K UHD account - 1 year warranty",
                    "price": 34.99,
                    "stock": 30,
                    "image_url": "https://i.imgur.com/netflix_premium.png",
                    "deliverables": "Account credentials,Warranty information"
                },
                # Services Category
                {
                    "name": "💻 Website Development",
                    "category": "services",
                    "description": "Professional website development with modern design",
                    "price": 199.99,
                    "stock": 3,
                    "image_url": "https://i.imgur.com/web_dev.png",
                    "deliverables": "Website files,Domain setup,SEO optimization"
                }
            ]

            for product in test_products:
                await db.execute('''
                    INSERT OR REPLACE INTO products 
                    (name, category, description, price, stock, image_url, deliverables)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product["name"],
                    product["category"],
                    product["description"],
                    product["price"],
                    product["stock"],
                    product["image_url"],
                    product["deliverables"]
                ))

            # Orders table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_price REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    status TEXT NOT NULL,
                    proof_image TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Sales stats table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS sales_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity_sold INTEGER NOT NULL,
                    revenue REAL NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')

            # Blacklist table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    added_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.commit()

    async def add_product(self, name: str, category: str, price: float, description: str,
                         image_url: str, deliverables: str, stock: int = 0) -> bool:
        """Add a new product or update existing one"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO products (name, category, price, description, image_url, deliverables, stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        category=excluded.category,
                        price=excluded.price,
                        description=excluded.description,
                        image_url=excluded.image_url,
                        deliverables=excluded.deliverables,
                        stock=excluded.stock,
                        updated_at=CURRENT_TIMESTAMP
                ''', (name, category, price, description, image_url, deliverables, stock))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding/updating product: {str(e)}")
            return False

    async def get_products_by_category(self, category: str) -> List[Dict]:
        """Get all products in a category"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM products 
                WHERE category = ? AND is_deleted = FALSE 
                ORDER BY created_at DESC
            ''', (category,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def create_order(self, order_id: str, user_id: str, product_id: int,
                          quantity: int, total_price: float, payment_method: str) -> bool:
        """Create a new order"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO orders (order_id, user_id, product_id, quantity,
                                      total_price, payment_method, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending_proof')
                ''', (order_id, user_id, product_id, quantity, total_price, payment_method))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error creating order: {str(e)}")
            return False

    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status and handle stock/stats updates"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('BEGIN TRANSACTION')
            try:
                # Update order status
                cursor = await db.execute('''
                    UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ? RETURNING product_id, quantity, total_price
                ''', (status, order_id))
                row = await cursor.fetchone()
                
                if not row:
                    raise Exception("Order not found")
                
                product_id, quantity, total_price = row
                
                if status == 'completed':
                    # Update product stock
                    cursor = await db.execute('''
                        UPDATE products 
                        SET stock = stock - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND stock >= ?
                        RETURNING stock
                    ''', (quantity, product_id, quantity))
                    
                    stock_row = await cursor.fetchone()
                    if not stock_row:
                        raise Exception("Insufficient stock")
                    
                    # Update sales stats
                    await db.execute('''
                        INSERT INTO sales_stats (date, product_id, quantity_sold, revenue)
                        VALUES (date('now'), ?, ?, ?)
                    ''', (product_id, quantity, total_price))
                
                await db.commit()
                return True
                
            except Exception as e:
                await db.execute('ROLLBACK')
                logging.error(f"Error updating order: {str(e)}")
                return False

    async def get_sales_stats(self, period: str = 'all') -> Tuple[Dict, List[Dict]]:
        """Get sales statistics for the specified period"""
        date_filter = {
            'daily': 'date = date("now")',
            'weekly': 'date >= date("now", "-7 days")',
            'monthly': 'date >= date("now", "-30 days")',
            'all': '1=1'
        }.get(period, '1=1')

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get summary stats
            cursor = await db.execute(f'''
                SELECT 
                    COUNT(DISTINCT o.id) as total_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'completed' THEN o.id END) as completed_orders,
                    SUM(CASE WHEN o.status = 'completed' THEN o.total_price END) as total_revenue
                FROM orders o
                WHERE {date_filter}
            ''')
            summary = dict(await cursor.fetchone())
            
            # Get best-selling products
            cursor = await db.execute(f'''
                SELECT 
                    p.name,
                    COUNT(o.id) as orders,
                    SUM(o.quantity) as units_sold,
                    SUM(o.total_price) as revenue
                FROM products p
                JOIN orders o ON p.id = o.product_id
                WHERE o.status = 'completed' AND {date_filter}
                GROUP BY p.id
                ORDER BY revenue DESC
                LIMIT 5
            ''')
            best_sellers = [dict(row) for row in cursor]
            
            return summary, best_sellers
    async def get_pending_order(self, user_id: str) -> Optional[Dict]:
        """Get pending order for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM orders 
                WHERE user_id = ? AND status = 'pending_proof'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a product by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM products WHERE id = ?
            ''', (product_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_order_proof(self, order_id: str, proof_url: str) -> bool:
        """Update order with payment proof"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE orders 
                    SET proof_image = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                ''', (proof_url, order_id))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating order proof: {str(e)}")
            return False
