"""
Migration script to convert old deliverables format to new JSON format

Run this once to convert all existing products from comma-separated strings
to the new JSON format with types and emojis.
"""

import asyncio
import aiosqlite
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

async def migrate_deliverables():
    """Migrate old deliverables to new JSON format"""
    db_path = os.getenv('DATABASE_PATH', 'data/novacore.db')
    
    print(f"🔄 Starting migration for database: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Get all products
        cursor = await db.execute('SELECT id, name, deliverables FROM products')
        products = await cursor.fetchall()
        
        print(f"📦 Found {len(products)} products to migrate")
        
        for product in products:
            product_id = product['id']
            name = product['name']
            old_deliverables = product['deliverables']
            
            # Check if already JSON
            try:
                json.loads(old_deliverables)
                print(f"✅ {name} - Already in JSON format, skipping")
                continue
            except:
                pass
            
            # Convert comma-separated to JSON
            if old_deliverables:
                items = [item.strip() for item in old_deliverables.split(',')]
                
                # Try to guess types based on keywords
                new_deliverables = []
                for item in items:
                    item_lower = item.lower()
                    
                    # Guess type based on keywords
                    if any(word in item_lower for word in ['code', 'key', 'link', 'gift']):
                        item_type = 'code'
                    elif any(word in item_lower for word in ['account', 'credential', 'login']):
                        item_type = 'account'
                    elif any(word in item_lower for word in ['file', 'source', 'website']):
                        item_type = 'file'
                    elif any(word in item_lower for word in ['guide', 'instruction', 'tutorial']):
                        item_type = 'guide'
                    elif any(word in item_lower for word in ['support', 'help', 'assistance']):
                        item_type = 'support'
                    elif any(word in item_lower for word in ['warranty', 'guarantee']):
                        item_type = 'warranty'
                    elif any(word in item_lower for word in ['service', 'activation', 'follower', 'like', 'view']):
                        item_type = 'service'
                    else:
                        item_type = 'service'
                    
                    new_deliverables.append({
                        "item": item,
                        "type": item_type
                    })
                
                new_json = json.dumps(new_deliverables)
                
                # Update database
                await db.execute('''
                    UPDATE products 
                    SET deliverables = ?
                    WHERE id = ?
                ''', (new_json, product_id))
                
                print(f"✅ {name}")
                print(f"   Old: {old_deliverables}")
                print(f"   New: {new_json}\n")
        
        await db.commit()
        print("🎉 Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_deliverables())
