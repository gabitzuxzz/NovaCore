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
            # Categories table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT UNIQUE NOT NULL,
                    label TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default categories if table is empty
            cursor = await db.execute('SELECT COUNT(*) FROM categories')
            count_row = await cursor.fetchone()
            if count_row and count_row[0] == 0:
                default_categories = [
                    ("best_sold", "Best Sold", "🏆"),
                    ("new", "New", "✨"),
                    ("social", "Social Media Boost", "📱"),
                    ("discord", "Discord", "💬"),
                    ("accounts", "Accounts", "👤"),
                    ("services", "Services", "🛠️")
                ]
                await db.executemany('''
                    INSERT INTO categories (value, label, emoji)
                    VALUES (?, ?, ?)
                ''', default_categories)
            
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

            # Payment methods table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method_name TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await db.commit()

    async def get_all_categories(self) -> List[Dict]:
        """Get all categories"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM categories 
                ORDER BY created_at ASC
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_category(self, value: str, label: str, emoji: str) -> bool:
        """Add a new category"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO categories (value, label, emoji)
                    VALUES (?, ?, ?)
                ''', (value, label, emoji))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding category: {str(e)}")
            return False

    async def update_category(self, category_id: int, value: str, label: str, emoji: str) -> bool:
        """Update an existing category"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE categories 
                    SET value = ?, label = ?, emoji = ?
                    WHERE id = ?
                ''', (value, label, emoji, category_id))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating category: {str(e)}")
            return False

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM categories WHERE id = ?', (category_id,))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error deleting category: {str(e)}")
            return False

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

    async def get_all_products(self) -> List[Dict]:
        """Get all products"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM products 
                WHERE is_deleted = FALSE 
                ORDER BY created_at DESC
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def remove_product(self, name: str) -> bool:
        """Remove a product (soft delete)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE products 
                    SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (name,))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error removing product: {str(e)}")
            return False

    async def update_stock(self, name: str, amount: int) -> bool:
        """Update stock for a product"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE products 
                    SET stock = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (amount, name))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating stock: {str(e)}")
            return False

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
            'daily': "date(o.created_at) = date('now')",
            'weekly': "date(o.created_at) >= date('now', '-7 days')",
            'monthly': "date(o.created_at) >= date('now', '-30 days')",
            'all': '1=1'
        }.get(period, '1=1')

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Get summary stats
            cursor = await db.execute(f'''
                SELECT 
                    COUNT(DISTINCT o.id) as total_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'completed' THEN o.id END) as completed_orders,
                    COALESCE(SUM(CASE WHEN o.status = 'completed' THEN o.total_price END), 0) as total_revenue
                FROM orders o
                WHERE {date_filter}
            ''')
            summary_row = await cursor.fetchone()
            summary = dict(summary_row) if summary_row else {"total_orders": 0, "completed_orders": 0, "total_revenue": 0}
            
            # Get time series data for chart
            cursor = await db.execute(f'''
                SELECT 
                    date(o.created_at) as date,
                    COALESCE(SUM(CASE WHEN o.status = 'completed' THEN o.total_price END), 0) as revenue
                FROM orders o
                WHERE {date_filter}
                GROUP BY date(o.created_at)
                ORDER BY date(o.created_at) ASC
            ''')
            time_series = [dict(row) for row in await cursor.fetchall()]
            
            return summary, time_series

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

    async def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """Get order details by order ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT o.*, p.name as product_name, p.category as product_category
                FROM orders o
                LEFT JOIN products p ON o.product_id = p.id
                WHERE o.order_id = ?
            ''', (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_payment_info(self, method_name: str, address: str) -> bool:
        """Add or update payment method information"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO payment_methods (method_name, address)
                    VALUES (?, ?)
                    ON CONFLICT(method_name) DO UPDATE SET
                        address=excluded.address,
                        updated_at=CURRENT_TIMESTAMP
                ''', (method_name, address))
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating payment info: {str(e)}")
            return False

    async def get_payment_info(self, method_name: str) -> Optional[str]:
        """Get payment address for a specific method"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT address FROM payment_methods 
                WHERE method_name = ?
            ''', (method_name,))
            row = await cursor.fetchone()
            if row:
                return row['address']
            return os.getenv(f"{method_name.upper()}_ADDRESS")

    async def get_all_payment_info(self) -> List[Dict]:
        """Get all payment methods"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM payment_methods 
                ORDER BY created_at DESC
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_product_by_name(self, name: str) -> Optional[Dict]:
        """Get a product by name"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM products 
                WHERE name = ? AND is_deleted = FALSE
            ''', (name,))
            row = await cursor.fetchone()
            return dict(row) if row else None
