import asyncio
import os
import re
import logging
from typing import List
from .config import Config

class TikTokStyleTextOverlay:
    """TikTok-style text overlay processor using FFmpeg"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # TikTok-style configuration (ADJUSTED FOR REAL IMAGES)
        self.font_size = 75  # 75px for optimal readability
        self.font_path = "/app/ProximaNovaSemibold.otf"  # Proxima Nova Semibold
        self.outline_width = 6  # 6px outline (extra bold for impact)
        self.line_spacing = 12  # Tight spacing for punch
        
        # TikTok margins (centered, impactful)
        self.margin_percent = 0.15  # 15% margin on each side (70% width)
        self.y_position_factor = 0.50  # Centered vertically (50% down from top)
        
    async def process_vsl_slides(self, image_paths: List[str], vsl_slides) -> List[str]:
        """Process VSL slides with TikTok-style text overlays"""
        
        self.logger.info(f"✏️  Processing {len(image_paths)} slides with TikTok-style text overlays")
        
        processed_images = []
        
        for i, (image_path, slide) in enumerate(zip(image_paths, vsl_slides)):
            try:
                if image_path and os.path.exists(image_path):
                    output_path = f"{Config.OUTPUT_DIRECTORY}/vsl_slide_{slide.slide_number:02d}_final.jpg"
                    
                    await self._add_tiktok_text_overlay(
                        image_path, 
                        slide.script, 
                        output_path,
                        slide.slide_number
                    )
                    
                    processed_images.append(output_path)
                    self.logger.info(f"✅ Processed slide {slide.slide_number} with text overlay")
                else:
                    self.logger.warning(f"⚠️  Skipping missing image for slide {i+1}")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to process slide {i+1}: {e}")
                # Copy original as fallback
                if image_path and os.path.exists(image_path):
                    import shutil
                    fallback_path = f"{Config.OUTPUT_DIRECTORY}/vsl_slide_{slide.slide_number:02d}_fallback.jpg"
                    shutil.copy2(image_path, fallback_path)
                    processed_images.append(fallback_path)
        
        self.logger.info(f"✅ Successfully processed {len(processed_images)} slides")
        return processed_images
    
    async def _add_tiktok_text_overlay(self, image_path: str, text: str, output_path: str, slide_number: int):
        """Add TikTok-style text overlay with optimized line wrapping"""
        
        # Clean text for FFmpeg
        safe_text = self._prepare_text_for_ffmpeg(text)
        
        # Split into lines (26 chars per line)
        text_lines = self._wrap_text_for_tiktok(safe_text)
        
        # Calculate positioning
        pixels_per_line = self.font_size + self.line_spacing
        total_lines = len(text_lines)
        
        # Adjust starting position for longer text
        if total_lines > 6:
            extra_lines = total_lines - 6
            percent_adjustment = extra_lines * 0.03
            start_y_factor = max(0.40, self.y_position_factor - percent_adjustment)
        elif total_lines > 4:
            start_y_factor = self.y_position_factor - 0.02
        else:
            start_y_factor = self.y_position_factor
        
        # Create drawtext filters for each line
        drawtext_filters = []
        
        # Check if custom font exists, otherwise use system font
        font_file = self.font_path if os.path.exists(self.font_path) else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        for i, line in enumerate(text_lines):
            line_y_offset = i * pixels_per_line
            y_position = f"(h*{start_y_factor})-(text_h/2)+{line_y_offset}"
            
            # TikTok style: white text with thick black outline
            drawtext_filter = f"drawtext=fontfile='{font_file}':text='{line}':fontcolor=white:fontsize={self.font_size}:x=(w-text_w)/2:y={y_position}:borderw={self.outline_width}:bordercolor=black:shadowx=2:shadowy=2:shadowcolor=black"
            drawtext_filters.append(drawtext_filter)
        
        filter_complex = ",".join(drawtext_filters) if len(drawtext_filters) > 1 else drawtext_filters[0]
        
        # FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', image_path,
            '-vf', filter_complex,
            '-q:v', '2',  # High quality
            output_path
        ]
        
        try:
            self.logger.info(f"📝 Adding text overlay to slide {slide_number} ({len(text_lines)} lines)")
            
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
                self.logger.error(f"❌ FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"❌ Text overlay failed for slide {slide_number}: {e}")
            # Copy original as fallback
            import shutil
            shutil.copy2(image_path, output_path)
    
    def _remove_emojis(self, text: str) -> str:
        """Remove all emoji characters that can't be rendered by the font"""
        # Emoji pattern covering most common emoji ranges
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U00002600-\U000026FF"  # Miscellaneous Symbols
            "]+", 
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)
    
    def _prepare_text_for_ffmpeg(self, text: str) -> str:
        """Prepare text for FFmpeg with robust escaping"""
        
        # First remove emojis
        safe_text = self._remove_emojis(text)
        
        # Remove problematic characters
        safe_text = safe_text.replace("'", "")
        safe_text = safe_text.replace('"', "")
        safe_text = safe_text.replace(':', " ")
        safe_text = safe_text.replace('[', "")
        safe_text = safe_text.replace(']', "")
        safe_text = safe_text.replace('=', " ")
        safe_text = safe_text.replace('-', " ")
        
        return safe_text.strip()
    
    def _wrap_text_for_tiktok(self, text: str) -> list:
        """Split text based on CHARACTER LENGTH for consistent visual line length"""
        
        words = text.split()
        lines = []
        current_line = ""
        max_chars_per_line = 27  # 27 characters per line (balanced with 75px font)
        
        for word in words:
            # Test if adding this word would exceed the character limit
            test_line = current_line + " " + word if current_line else word
            
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                # Line would be too long, save current line and start new one
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    # Single word is longer than max, still add it
                    lines.append(word)
                    current_line = ""
        
        # Add the last line if there's content
        if current_line:
            lines.append(current_line)
        
        return lines