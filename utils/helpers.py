import asyncio
import os
import logging
from typing import List, Optional, Dict
import aiosqlite
from datetime import datetime
import aiofiles
from pathlib import Path

class Validators:
    @staticmethod
    def validate_env_vars() -> List[str]:
        """
        Validate required environment variables
        Returns list of missing variables
        """
        required_vars = [
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
        
        optional_vars = [
            'PRODUCT_CATEGORY_ID',
            'BTC_ADDRESS',
            'LTC_ADDRESS',
            'USDT_ADDRESS',
            'SOL_ADDRESS',
            'ETH_ADDRESS'
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
                
        return missing

class ImageManager:
    @staticmethod
    async def save_proof_image(order_id: str, image_url: str, log_dir: str) -> Optional[str]:
        """
        Save proof image to disk
        Returns saved file path or None if failed
        """
        try:
            # Create proof images directory if not exists
            proof_dir = Path(log_dir) / "proofs"
            proof_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{order_id}_{timestamp}.png"
            filepath = proof_dir / filename
            
            async with aiofiles.open(filepath, mode='wb') as f:
                # Download and save image
                # Implementation depends on how image_url is provided
                # This is a placeholder
                pass
                
            return str(filepath)
            
        except Exception as e:
            logging.error(f"Error saving proof image: {str(e)}")
            return None

class DatabaseLock:
    """Simple async lock for database operations"""
    def __init__(self):
        self._locks = {}
        
    async def acquire(self, key: str):
        """Acquire lock for given key"""
        while self._locks.get(key):
            await asyncio.sleep(0.1)
        self._locks[key] = True
        
    def release(self, key: str):
        """Release lock for given key"""
        self._locks.pop(key, None)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Global database lock instance
db_lock = DatabaseLock()