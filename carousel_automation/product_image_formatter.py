from PIL import Image
import os
import logging
from typing import Literal

class ProductImageFormatter:
    """Format product images to 9:16 aspect ratio"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.target_width = 1080
        self.target_height = 1920
        self.target_ratio = 9 / 16
    
    def format_image(self, image_path: str, mode: Literal['cover', 'contain', 'stretch'] = 'cover') -> str:
        """Format image to 9:16 aspect ratio"""
        
        self.logger.info(f"📐 Formatting image: {image_path} (mode: {mode})")
        
        img = Image.open(image_path)
        width, height = img.size
        current_ratio = width / height
        
        # Generate output filename
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_9x16{ext}"
        
        if mode == 'cover':
            # Crop to fill (default)
            result = self._cover_mode(img)
        elif mode == 'contain':
            # Fit with padding
            result = self._contain_mode(img)
        elif mode == 'stretch':
            # Stretch to fit
            result = self._stretch_mode(img)
        else:
            result = self._cover_mode(img)
        
        result.save(output_path, 'JPEG', quality=95)
        self.logger.info(f"✅ Formatted image saved: {output_path}")
        
        return output_path
    
    def _cover_mode(self, img: Image.Image) -> Image.Image:
        """Crop image to fill 9:16 (center crop)"""
        
        width, height = img.size
        current_ratio = width / height
        
        if current_ratio > self.target_ratio:
            # Image is wider - crop width
            new_width = int(height * self.target_ratio)
            left = (width - new_width) // 2
            img = img.crop((left, 0, left + new_width, height))
        else:
            # Image is taller - crop height
            new_height = int(width / self.target_ratio)
            top = (height - new_height) // 2
            img = img.crop((0, top, width, top + new_height))
        
        # Resize to target dimensions
        return img.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)
    
    def _contain_mode(self, img: Image.Image) -> Image.Image:
        """Fit image with padding (letterbox)"""
        
        img.thumbnail((self.target_width, self.target_height), Image.Resampling.LANCZOS)
        
        # Create white background
        result = Image.new('RGB', (self.target_width, self.target_height), 'white')
        
        # Paste image centered
        x = (self.target_width - img.width) // 2
        y = (self.target_height - img.height) // 2
        result.paste(img, (x, y))
        
        return result
    
    def _stretch_mode(self, img: Image.Image) -> Image.Image:
        """Stretch image to fit (may distort)"""
        
        return img.resize((self.target_width, self.target_height), Image.Resampling.LANCZOS)

def sanitize_filename(filename: str) -> str:
    """Remove spaces and special characters from filename"""
    import re
    from pathlib import Path
    
    path = Path(filename)
    name = path.stem
    ext = path.suffix
    
    clean_name = re.sub(r'[^\w\-_]', '_', name)
    clean_name = re.sub(r'_+', '_', clean_name)
    
    return str(path.parent / f"{clean_name}{ext}")