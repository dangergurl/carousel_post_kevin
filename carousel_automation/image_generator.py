import asyncio
import aiohttp
import aiofiles
import logging
from typing import Dict, Any, Optional, List
import openai
import replicate
import fal_client
import os
from .config import Config
from .utils import download_image, retry_with_backoff


class ImageGenerator:
    def __init__(self, use_gemini=False, product_model='recraft'):
        self.openai_client = openai.AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
        self.replicate_client = replicate.Client(api_token=Config.REPLICATE_API_TOKEN)
        self.use_gemini = use_gemini
        self.product_model = product_model  # 'recraft' (NEW!), 'flux_img2img', or 'flux_redux'
        
        # Configure FAL.ai if API key is available
        if Config.FAL_KEY:
            os.environ["FAL_KEY"] = Config.FAL_KEY
        
        self.logger = logging.getLogger(__name__)
        
    async def generate_vsl_images(self, slides: List[Any], product_image_path: Optional[str] = None) -> List[str]:
        """Generate all images for carousel slides"""
        
        service_name = "Gemini 2.5 Flash" if self.use_gemini else "Flux"
        self.logger.info(f"🎨 Generating {len(slides)} VSL images using {service_name}")
        
        if product_image_path:
            self.logger.info(f"🖼️  Product reference image: {product_image_path}")
            self.logger.info(f"📌 Using {self.product_model.upper()} for product slides (8, 9, 10)")
        
        # Generate images concurrently for speed
        tasks = []
        for slide in slides:
            # Use product image for last 3 slides (slides 8, 9, 10)
            use_product_ref = product_image_path and slide.slide_number >= 8
            task = self.generate_slide_image(slide, product_image_path if use_product_ref else None)
            tasks.append(task)
        
        # Wait for all images to complete
        image_paths = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any failures
        successful_paths = []
        for i, result in enumerate(image_paths):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Failed to generate slide {i+1}: {result}")
                # Generate fallback image
                fallback_path = await self._generate_fallback_image(slides[i])
                successful_paths.append(fallback_path)
            else:
                successful_paths.append(result)
        
        return successful_paths
    
    @retry_with_backoff(max_retries=3)
    async def generate_slide_image(self, slide: Any, product_image_path: Optional[str] = None) -> str:
        """Generate single slide image using selected service"""
        
        # If product reference is provided, use the selected product model
        if product_image_path:
            if self.product_model == 'kie_flux_kontext':
                self.logger.info(f"🎨 Slide {slide.slide_number} → kie.ai Flux Kontext (UGC-style Product Integration)")
                try:
                    return await self._generate_kie_flux_kontext(slide, product_image_path)
                except Exception as e:
                    self.logger.warning(f"⚠️  kie.ai Flux Kontext failed: {e}, falling back to DALL-E 3")
                    return await self._generate_dalle3(slide)
            
            elif self.product_model == 'recraft':
                self.logger.info(f"🎨 Slide {slide.slide_number} → Recraft V3 (Product Integration)")
                try:
                    return await self._generate_recraft_v3(slide, product_image_path)
                except Exception as e:
                    self.logger.warning(f"⚠️  Recraft V3 failed: {e}, falling back to FLUX img2img")
                    return await self._generate_fal_flux_img2img(slide, product_image_path)
            
            elif self.product_model == 'flux_redux':
                self.logger.info(f"🎨 Slide {slide.slide_number} → FLUX Redux (Product Identity)")
                try:
                    return await self._generate_flux_redux(slide, product_image_path)
                except Exception as e:
                    self.logger.warning(f"⚠️  FLUX Redux failed: {e}, falling back to img2img")
                    return await self._generate_fal_flux_img2img(slide, product_image_path)
            
            else:  # flux_img2img (default)
                self.logger.info(f"🎨 Slide {slide.slide_number} → FLUX img2img")
                try:
                    return await self._generate_fal_flux_img2img(slide, product_image_path)
                except Exception as e:
                    self.logger.warning(f"⚠️  FLUX img2img failed: {e}, falling back to Gemini")
                    return await self._generate_gemini(slide, None)
        
        # Use Gemini for regular slides (no product reference)
        elif self.use_gemini:
            service = 'Gemini 2.5 Flash'
            self.logger.info(f"🎨 Slide {slide.slide_number} → {service}")
            
            try:
                return await self._generate_gemini(slide, None)
            except Exception as e:
                self.logger.warning(f"⚠️  Gemini failed: {e}, falling back to FLUX")
                return await self._generate_replicate_flux(slide, None)
        else:
            service = 'FLUX'
            self.logger.info(f"🎨 Slide {slide.slide_number} → {service}")
            
            try:
                return await self._generate_replicate_flux(slide, product_image_path)
            except Exception as e:
                self.logger.warning(f"⚠️  FLUX failed: {e}, falling back to DALL-E 3")
                return await self._generate_dalle3(slide)
    
    async def _generate_recraft_v3(self, slide: Any, product_image_path: str) -> str:
        """🌟 NEW: Generate image using Recraft V3 with product reference (BEST for product integration)"""
        
        # Enhance prompt for Recraft V3
        enhanced_prompt = self._enhance_prompt_for_recraft(slide.dalle_prompt)
        enhanced_prompt = f"{enhanced_prompt}. The scene prominently features the exact product from the reference image in a natural, engaging way."
        
        self.logger.info(f"🎨 Recraft V3 prompt for slide {slide.slide_number}: {enhanced_prompt[:100]}...")
        
        try:
            # Upload product reference image to Replicate
            self.logger.info(f"📤 Uploading product reference to Replicate...")
            
            # Read and upload file
            with open(product_image_path, 'rb') as f:
                product_file = replicate.Client().files.create(file=f)
            
            product_url = product_file.urls['get']
            self.logger.info(f"✅ Product reference uploaded")
            
            # Generate with Recraft V3 using image reference
            output = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.replicate_client.run(
                    "recraft-ai/recraft-v3",
                    input={
                        "prompt": enhanced_prompt,
                        "image": product_url,
                        "style": "realistic_image",  # Photorealistic style
                        "size": "1365x2048",  # 9:16 aspect ratio
                        "image_influence": 0.65,  # Balance between prompt and product (0.5-0.8 recommended)
                        "output_format": "jpg",
                        "output_quality": 90
                    }
                )
            )
            
            # Get image URL
            image_url = output[0] if isinstance(output, list) else output
            
            # Download and save
            filename = f"slide_{slide.slide_number}_recraft.jpg"
            local_path = await download_image(image_url, Config.TEMP_DIRECTORY, filename)
            
            self.logger.info(f"✅ Recraft V3 generated: {local_path}")
            return local_path
            
        except Exception as e:
            self.logger.error(f"❌ Recraft V3 generation failed: {e}")
            raise
    
    async def _generate_flux_redux(self, slide: Any, product_image_path: str) -> str:
        """Generate image using FLUX Redux for product identity preservation"""
        
        enhanced_prompt = self._enhance_prompt_for_flux(slide.dalle_prompt)
        enhanced_prompt = f"{enhanced_prompt}. Feature the exact product prominently in the scene."
        
        self.logger.info(f"🎨 FLUX Redux for slide {slide.slide_number}")
        
        try:
            # FLUX Redux requires uploading the product image
            with open(product_image_path, 'rb') as f:
                product_file = replicate.Client().files.create(file=f)
            product_url = product_file.urls['get']
            
            # Generate with FLUX Redux
            output = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.replicate_client.run(
                    "black-forest-labs/flux-1.1-pro",
                    input={
                        "prompt": enhanced_prompt,
                        "aspect_ratio": "9:16",
                        "output_format": "jpg",
                        "output_quality": 90,
                        "safety_tolerance": 2
                    }
                )
            )
            
            image_url = output[0] if isinstance(output, list) else output
            filename = f"slide_{slide.slide_number}_flux_redux.jpg"
            local_path = await download_image(image_url, Config.TEMP_DIRECTORY, filename)
            
            return local_path
            
        except Exception as e:
            self.logger.error(f"❌ FLUX Redux failed: {e}")
            raise
    
    async def _generate_fal_flux_img2img(self, slide: Any, product_image_path: str) -> str:
        """Generate image using FAL.ai FLUX with img2img (IMPROVED strength)"""
        
        enhanced_prompt = self._enhance_prompt_for_flux(slide.dalle_prompt)
        enhanced_prompt = f"{enhanced_prompt}. Prominently feature the exact product shown in the reference image."
        
        self.logger.info(f"🎨 FAL FLUX img2img for slide {slide.slide_number}")
        
        try:
            # Upload product reference
            self.logger.info(f"📤 Uploading product reference to FAL.ai...")
            image_url = fal_client.upload_file(product_image_path)
            self.logger.info(f"✅ Uploaded to FAL.ai")
            
            # OPTIMIZED: Lower strength creates SCENE with product, not just product
            request_data = {
                "prompt": enhanced_prompt,
                "image_url": image_url,
                "strength": 0.40,  # Lower = more scene generation, product integrated naturally
                "num_inference_steps": 35,  # Increased for better quality
                "guidance_scale": 4.5,
                "image_size": {
                    "width": 1080,
                    "height": 1920
                },
                "enable_safety_checker": False
            }
            
            self.logger.info(f"🚀 Calling FAL.ai FLUX img2img (strength=0.55)")
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: fal_client.subscribe(
                    "fal-ai/flux-general/image-to-image",
                    arguments=request_data
                )
            )
            
            if result and 'images' in result and len(result['images']) > 0:
                output_url = result['images'][0]['url']
            else:
                raise Exception("No image returned from FAL.ai")
            
            filename = f"slide_{slide.slide_number}_flux_img2img.jpg"
            local_path = await download_image(output_url, Config.TEMP_DIRECTORY, filename)
            
            self.logger.info(f"✅ Generated: {local_path}")
            return local_path
            
        except Exception as e:
            self.logger.error(f"❌ FLUX img2img failed: {e}")
            raise
    
    async def _generate_dalle3(self, slide: Any) -> str:
        """Generate image using DALL-E 3"""
        
        enhanced_prompt = self._enhance_prompt_for_dalle3(slide.dalle_prompt)
        
        response = await self.openai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size="1024x1792",  # 9:16 aspect ratio
            quality="hd",
            style="natural"
        )
        
        image_url = response.data[0].url
        filename = f"slide_{slide.slide_number}_dalle3.jpg"
        local_path = await download_image(image_url, Config.TEMP_DIRECTORY, filename)
        
        # Ensure exact 1080x1920 size
        from PIL import Image as PILImage
        img = PILImage.open(local_path)
        if img.size != (1080, 1920):
            self.logger.info(f"📐 Resizing DALL-E image to 1080x1920...")
            img = img.resize((1080, 1920), PILImage.Resampling.LANCZOS)
            img.save(local_path, 'JPEG', quality=95)
        
        return local_path
    
    async def _generate_replicate_flux(self, slide: Any, product_image_path: Optional[str] = None) -> str:
        """Generate image using FLUX Pro via Replicate"""
        
        enhanced_prompt = self._enhance_prompt_for_flux(slide.dalle_prompt)
        
        flux_input = {
            "prompt": enhanced_prompt,
            "aspect_ratio": "9:16",
            "output_format": "jpg",
            "output_quality": 90,
            "safety_tolerance": 2
        }
        
        output = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.replicate_client.run(
                "black-forest-labs/flux-1.1-pro",
                input=flux_input
            )
        )
        
        image_url = output[0] if isinstance(output, list) else output
        filename = f"slide_{slide.slide_number}_flux.jpg"
        local_path = await download_image(image_url, Config.TEMP_DIRECTORY, filename)
        
        # Ensure exact 1080x1920 size
        from PIL import Image as PILImage
        img = PILImage.open(local_path)
        if img.size != (1080, 1920):
            self.logger.info(f"📐 Resizing FLUX image to 1080x1920...")
            img = img.resize((1080, 1920), PILImage.Resampling.LANCZOS)
            img.save(local_path, 'JPEG', quality=95)
        
        return local_path
    
    async def _generate_gemini(self, slide: Any, product_image_path: Optional[str] = None, custom_prompt: str = None) -> str:
        """Generate image using Gemini 2.5 Flash via FAL.ai"""
        
        if custom_prompt:
            enhanced_prompt = custom_prompt
        else:
            enhanced_prompt = self._enhance_prompt_for_gemini(slide.dalle_prompt)
        
        try:
            request_data = {
                "prompt": enhanced_prompt,
                "aspect_ratio": "9:16",
                "num_inference_steps": 28,
                "enable_safety_checker": False
            }
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: fal_client.subscribe(
                    "fal-ai/gemini-25-flash-image",
                    arguments=request_data
                )
            )
            
            if result and 'images' in result and len(result['images']) > 0:
                image_url = result['images'][0]['url']
            else:
                raise Exception("No image returned from Gemini")
            
            filename = f"slide_{slide.slide_number}_gemini.jpg"
            local_path = await download_image(image_url, Config.TEMP_DIRECTORY, filename)
            
            # ALWAYS ensure exact 1080x1920 size
            from PIL import Image as PILImage
            img = PILImage.open(local_path)
            width, height = img.size
            target_width = 1080
            target_height = 1920
            
            if width != target_width or height != target_height:
                self.logger.info(f"📐 Resizing from {width}x{height} to {target_width}x{target_height}...")
                resized = img.resize((target_width, target_height), PILImage.Resampling.LANCZOS)
                resized.save(local_path, 'JPEG', quality=95)
                self.logger.info(f"✅ Resized to exact 1080x1920")
            
            return local_path
            
        except Exception as e:
            self.logger.error(f"❌ Gemini generation failed: {e}")
            raise
    
    def _enhance_prompt_for_recraft(self, base_prompt: str) -> str:
        """Enhance prompt for Recraft V3"""
        
        recraft_enhancements = [
            "professional photography",
            "9:16 vertical format",
            "commercial quality",
            "sharp focus",
            "natural lighting",
            "product photography style"
        ]
        
        return f"{base_prompt}, {', '.join(recraft_enhancements)}"
    
    def _enhance_prompt_for_gemini(self, base_prompt: str) -> str:
        """Enhance prompt for Gemini 2.5 Flash"""
        
        enhancements = [
            "professional photography",
            "9:16 vertical format",
            "commercial quality",
            "sharp focus",
            "natural colors",
            "photorealistic"
        ]
        
        return f"{base_prompt}, {', '.join(enhancements)}"
    
    def _enhance_prompt_for_dalle3(self, base_prompt: str) -> str:
        """Enhance prompt for DALL-E 3"""
        
        enhancements = [
            "high quality professional photography",
            "9:16 aspect ratio",
            "clean composition",
            "good lighting",
            "sharp focus",
            "commercial product photography style"
        ]
        
        return f"{base_prompt}, {', '.join(enhancements)}"
    
    def _enhance_prompt_for_flux(self, base_prompt: str) -> str:
        """Enhance prompt for FLUX"""
        
        flux_enhancements = [
            "professional photography",
            "9:16 vertical format",
            "commercial quality",
            "sharp focus",
            "natural colors"
        ]
        
        return f"{base_prompt}, {', '.join(flux_enhancements)}"
    
    async def _generate_fallback_image(self, slide: Any) -> str:
        """Generate simple fallback image if all services fail"""
        
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = 1080, 1920
        
        colors = {
            'hook': '#FF6B6B',
            'product': '#4ECDC4', 
            'benefit': '#45B7D1',
            'social': '#96CEB4',
            'cta': '#FFEAA7'
        }
        
        purpose = getattr(slide, 'purpose', 'general').lower()
        bg_color = colors.get(purpose, '#95A5A6')
        
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        text = f"Slide {slide.slide_number}\nGeneration Failed"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font, align='center')
        
        filename = f"slide_{slide.slide_number}_fallback.jpg"
        filepath = f"{Config.TEMP_DIRECTORY}/{filename}"
        img.save(filepath, 'JPEG', quality=90)
        
        return filepath
