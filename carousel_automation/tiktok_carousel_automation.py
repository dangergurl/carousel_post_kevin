import asyncio
import argparse
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

from .config import Config
from .autonomous_claude_vsl_generator import AutonomousClaudeVSLGenerator
from .image_generator import ImageGenerator
from .tiktok_style_text_overlay import TikTokStyleTextOverlay
from .product_image_formatter import ProductImageFormatter, sanitize_filename
from .utils import setup_logging, validate_image_file
import shutil

class TikTokCarouselAutomation:
    def __init__(self, use_gemini=False, product_model='recraft'):
        # Validate configuration
        Config.validate()
        
        # Set up logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.vsl_generator = AutonomousClaudeVSLGenerator()
        self.image_generator = ImageGenerator(use_gemini=use_gemini, product_model=product_model)
        self.text_processor = TikTokStyleTextOverlay()
        
    async def create_carousel(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to create complete VSL carousel"""
        
        start_time = datetime.now()
        self.logger.info(f"🚀 Starting VSL carousel creation for {product_data.get('name')}")
        self.logger.info(f"📦 Product Model: {self.image_generator.product_model.upper()}")
        
        try:
            # Step 1: Generate VSL strategy and slides
            self.logger.info("📝 Generating VSL strategy and slides...")
            vsl_strategy = await self.vsl_generator.generate_vsl_carousel(
                product_data.get('brand', ''), 
                product_data.get('name', '')
            )
            vsl_slides = vsl_strategy.slides
            self.logger.info(f"✅ VSL strategy generated with {len(vsl_slides)} slides")
            
            # Step 2: Sanitize and format product image if provided
            product_image_path = product_data.get('product_image')
            if product_image_path:
                from pathlib import Path
                
                original_path = Path(product_image_path).resolve()
                self.logger.info(f"📸 Looking for product image: {original_path.name}")
                
                # Smart file detection
                if not original_path.exists():
                    parent_dir = original_path.parent
                    target_name = original_path.name
                    
                    if parent_dir.exists():
                        all_files = list(parent_dir.glob('*'))
                        for file in all_files:
                            import unicodedata
                            norm_file = unicodedata.normalize('NFKD', file.name).lower().replace(' ', '')
                            norm_target = unicodedata.normalize('NFKD', target_name).lower().replace(' ', '')
                            
                            if norm_file == norm_target:
                                self.logger.info(f"🔍 Found similar file: {file.name}")
                                original_path = file
                                break
                
                if original_path.exists():
                    sanitized_path = Path(sanitize_filename(str(original_path)))
                    
                    if sanitized_path != original_path:
                        self.logger.info(f"🔧 Sanitizing filename: {original_path.name} → {sanitized_path.name}")
                        try:
                            original_path.rename(sanitized_path)
                            product_image_path = str(sanitized_path)
                            self.logger.info(f"✅ File renamed to: {sanitized_path.name}")
                        except Exception as e:
                            self.logger.warning(f"⚠️  Could not rename file: {e}")
                            product_image_path = str(original_path)
                    else:
                        product_image_path = str(original_path)
                    
                    # Format image to 9:16
                    format_mode = product_data.get('format_mode', 'cover')
                    self.logger.info(f"📐 Formatting product image to 9:16 (mode: {format_mode})...")
                    formatter = ProductImageFormatter()
                    try:
                        product_image_path = formatter.format_image(product_image_path, mode=format_mode)
                        self.logger.info(f"✅ Product image formatted: {product_image_path}")
                    except Exception as e:
                        self.logger.warning(f"⚠️  Could not format image: {e}")
                else:
                    self.logger.warning(f"⚠️  Product image not found: {original_path}")
            
            # Step 3: Generate images for VSL slides
            self.logger.info("🎨 Generating VSL images...")
            image_paths = await self.image_generator.generate_vsl_images(vsl_slides, product_image_path)
            self.logger.info(f"✅ Generated {len(image_paths)} images")
            
            # Validate generated images
            valid_images = [path for path in image_paths if path and validate_image_file(path)]
            if len(valid_images) != len(image_paths):
                self.logger.warning(f"⚠️  Only {len(valid_images)}/{len(image_paths)} images are valid")
            
            # Step 4: Add TikTok-style text overlays
            if product_data.get('skip_text_overlay', False):
                self.logger.info("⏭️  Skipping text overlay (user preference)")
                final_images = valid_images
            else:
                self.logger.info("✏️  Adding TikTok-style text overlays...")
                final_images = await self.text_processor.process_vsl_slides(valid_images, vsl_slides)
                self.logger.info(f"✅ Processed {len(final_images)} final images with overlays")
            
            # Step 5: Generate metadata
            metadata = self._generate_vsl_metadata(vsl_slides, product_data)
            
            # Step 6: Save results
            output_dir = self._save_results(final_images, metadata, product_data)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "success",
                "execution_time": execution_time,
                "output_directory": output_dir,
                "images": final_images,
                "metadata": metadata,
                "vsl_info": {
                    "slide_count": len(vsl_slides),
                    "style": "TikTok VSL with professional text overlays",
                    "product_model": self.image_generator.product_model
                }
            }
            
            self.logger.info(f"🎉 VSL carousel creation completed in {execution_time:.1f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"💥 VSL carousel creation failed: {str(e)}")
            raise
    
    def _generate_vsl_metadata(self, vsl_slides: list, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for the VSL carousel"""
        
        return {
            "product_name": product_data.get('name'),
            "product_price": product_data.get('price'),
            "product_category": product_data.get('category'),
            "brand": product_data.get('brand', ''),
            "slide_count": len(vsl_slides),
            "created_at": datetime.now().isoformat(),
            "overlay_style": "TikTok-style (white text with dark outline)",
            "product_model": self.image_generator.product_model,
            "slides": [
                {
                    "slide_number": slide.slide_number,
                    "script": slide.script,
                    "image_prompt": getattr(slide, 'dalle_prompt', 'No prompt available'),
                    "purpose": f'VSL Slide {slide.slide_number}'
                }
                for slide in vsl_slides
            ]
        }
    
    def _save_results(self, images: list, metadata: Dict[str, Any], product_data: Dict[str, Any]) -> str:
        """Save VSL carousel results to organized directory"""
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        product_name = product_data.get('name', 'product').replace(' ', '_').lower()
        output_dir = f"{Config.OUTPUT_DIRECTORY}/{product_name}_vsl_{timestamp}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy final images to output directory
        for i, image_path in enumerate(images):
            if os.path.exists(image_path):
                new_path = f"{output_dir}/vsl_slide_{i+1:02d}.jpg"
                shutil.copy2(image_path, new_path)
        
        # Save metadata
        metadata_path = f"{output_dir}/metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save VSL script
        script_content = self._generate_vsl_script(metadata)
        script_path = f"{output_dir}/vsl_script.txt"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        self.logger.info(f"📁 Results saved to: {output_dir}")
        return output_dir
    
    def _generate_vsl_script(self, metadata: Dict[str, Any]) -> str:
        """Generate complete VSL script for reference"""
        
        script = f"""
VSL Script for {metadata['product_name']}
{'=' * 50}

Product: {metadata['product_name']}
Brand: {metadata.get('brand', 'N/A')}
Price: ${metadata['product_price']}
Category: {metadata['product_category']}
Style: {metadata['overlay_style']}
Product Model: {metadata['product_model'].upper()}

SLIDES:
"""
        
        for slide in metadata['slides']:
            script += f"""
Slide {slide['slide_number']}:
Purpose: {slide['purpose']}
Script: {slide['script']}
Image Prompt: {slide['image_prompt']}
---
"""
        
        script += f"""

UPLOAD INSTRUCTIONS:
1. Upload slides in order (vsl_slide_01.jpg, vsl_slide_02.jpg, etc.)
2. Use TikTok Shop carousel format
3. Each slide has professional text overlay with TikTok-style formatting
4. Monitor engagement and adjust posting strategy as needed

Created: {metadata['created_at']}
"""
        
        return script
