import os
import asyncio
import aiohttp
import aiofiles
import logging
from functools import wraps
from typing import Callable, Any

async def download_image(url: str, directory: str, filename: str) -> str:
    """Download image from URL to local file"""
    
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                return filepath
            else:
                raise Exception(f"Failed to download image: HTTP {response.status}")

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0):
    """Decorator for retrying functions with exponential backoff"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logging.error(f"All {max_retries} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator

def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration"""
    
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/carousel_automation.log'),
            logging.StreamHandler()
        ]
    )

def validate_image_file(filepath: str) -> bool:
    """Validate that file is a valid image"""
    
    if not os.path.exists(filepath):
        return False
    
    # Check file size
    if os.path.getsize(filepath) < 1024:  # Less than 1KB
        return False
    
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png']
    _, ext = os.path.splitext(filepath.lower())
    
    return ext in valid_extensions

def sanitize_filename(filename: str) -> str:
    """Remove spaces and special characters from filename"""
    import re
    from pathlib import Path
    
    path = Path(filename)
    name = path.stem
    ext = path.suffix
    
    # Remove spaces and special characters
    clean_name = re.sub(r'[^\w\-_]', '_', name)
    clean_name = re.sub(r'_+', '_', clean_name)  # Replace multiple underscores
    
    return str(path.parent / f"{clean_name}{ext}")