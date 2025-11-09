import asyncio
import json
import logging
import re
from typing import Dict, List, Any
from dataclasses import dataclass
import anthropic
from .config import Config

@dataclass
class VSLSlide:
    slide_number: int
    script: str
    dalle_prompt: str

@dataclass
class VSLCarouselStrategy:
    slides: List[VSLSlide]
    brand: str
    product_type: str
    methodology: str = "Relatable VSL"

class AutonomousClaudeVSLGenerator:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.logger = logging.getLogger(__name__)
        
        # Updated VSL methodology with new image specifications
        self.vsl_methodology = """
**TikTok Carousel Ad Creation Tool**

**Objective:** Generate a complete TikTok carousel ad with both script and DALL-E image prompts in one pass.

**Reference Materials:**
- 10 example carousel ads (file: "AI mini vsls")
- VSL Bible guidelines (included in instructions)

**Input Required:**
- Target audience/niche
- Product/service (will be revealed in slide 9)
- Desired visual style (e.g., realistic, cinematic, illustrated, etc.)

**Script Requirements:**
- 10 text segments total
- **Product mention only allowed in slide 9 and 10**
- **MUST include specific, relatable personal story elements**
- **Balance high relatability with VSL Bible psychological triggers**

**Enhanced Script Guidelines - The "Relatable VSL" Method:**

1. **Structure as relatable mini-VSL:**
   - **Slide 1:** Specific relatable struggle + curiosity element (e.g., "forgot my password 3 times in one day")
   - **Slide 2:** Universal problem agitation with personal details (walking into rooms, losing words mid-sentence)
   - **Slide 3:** Problem amplification + hidden truth ("what doctors don't tell you," "while I was struggling...")
   - **Slide 4:** Personal discovery moment + authority building (friend's recommendation, medical backing)
   - **Slide 5:** Science/proof + credibility stacking (Nobel Prize, medical use, specific research)
   - **Slide 6:** Personal transformation with SPECIFIC timeline ("Day 3: X happened, Day 7: Y happened, Week 2: Z happened")
   - **Slide 7:** Authentic social proof with family/friend stories ("my skeptical husband," "my mom says")
   - **Slide 8:** Benefit stacking with personal results ("I now have X, Y, and Z")
   - **Slide 9:** Product reveal + quality/authority positioning
   - **Slide 10:** Urgency + emotional consequence with personal stakes

2. **MANDATORY Personal Story Elements:**
   - Include specific, believable personal struggles (numbers, times, exact scenarios)
   - Add authentic transformation timeline with specific days/weeks
   - Include family/friend social proof that feels real and relatable
   - Use first-person language that makes audience think "that's exactly how I feel"
   - Share skeptical-to-believer conversion stories

3. **VSL Bible Integration:**
   - Weave authority and credibility throughout the personal story
   - Use curiosity gaps about "hidden" or "suppressed" information
   - Include emotional triggers tied to personal experiences
   - Build scarcity around the specific product quality/availability
   - Create urgency with personal emotional consequences

4. **TikTok Optimization:**
   - Mobile-first writing with thumb-stopping personal hooks
   - Conversational tone that feels like sharing with a friend
   - Each slide builds curiosity for the next part of the story

**Image Prompt Structure:**
Each DALL-E prompt will include:
- Clear main visual concept (30-40 words maximum)
- Scene setting that supports the emotional tone of the script
- **Photorealistic specifications:** "ultra photorealistic, 16k, natural lighting, HDR, high resolution, shot on [Canon EOS R5/IMAX Laser], [Canon RF 50mm f/1.2L USM/intricate details], depth of field, --s 750"
- Consistent style descriptor throughout all 10 images
- **All images must be 9:16 vertical format**

**Deliverable:**
- Complete carousel ad with 10 script segments using personal story + VSL method
- 10 corresponding DALL-E image prompts (30-40 words each, 9:16 format)
- Each image prompt includes photorealistic camera specifications
- Specific personal transformation timeline included
- Authentic social proof elements
- Product reveal at slide 9 only
"""

        # Your proven VSL examples for pattern matching
        self.example_vsls = """
EXAMPLE VSL PATTERNS:

1. Natural Hair Regrowth Serum:
"My husband started losing his hair at 35. He tried everything—special shampoos, pills, even those expensive laser caps—but nothing worked. He was embarrassed to go out without a hat. Then, I stumbled on a centuries-old formula used by royalty in ancient India..."

2. Teeth Whitening Toothpaste:
"My best friend was always self-conscious about her teeth. Years of drinking coffee and red wine had left them stained yellow, and no matter how much she brushed, they never got whiter. Then, on a trip to Thailand, she discovered a secret..."

3. Detox Tea Blend:
"My cousin couldn't lose weight no matter how much she exercised. She felt bloated all the time and started losing confidence in herself. Then I found an article about a secret detox tea used by supermodels before fashion week..."

4. Energy-Boosting Gummies:
"My brother used to struggle to stay awake during his 9-to-5 job. No matter how much coffee he drank, he still felt sluggish. Then I came across FocusFuel Gummies..."

5. Acne-Clearing Spot Treatment:
"My teenage daughter struggled with acne for years. Every time she looked in the mirror, she felt like crying. We tried everything—drugstore products, dermatologist creams, even antibiotics—but nothing worked..."

PATTERN ANALYSIS:
- Always start with family member/friend struggle
- Include specific failed attempts ("tried everything")
- Discovery moment with authority/exotic origin
- Specific transformation timeline with days/weeks
- Product reveal with quality positioning
- Urgency with scarcity/selling out
"""

        # VSL Bible psychological principles
        self.vsl_principles = """
VSL BIBLE CORE PRINCIPLES:

1. CREDIBILITY STACKING:
   - Medical backing (hospitals, doctors, research)
   - Historical use (centuries-old, royalty, ancient)
   - Awards/recognition (Nobel Prize, medical approval)
   - Exclusivity (only available, pharmaceutical-grade)

2. EMOTIONAL TRIGGERS:
   - Embarrassment/shame (afraid to go out, self-conscious)
   - Frustration (tried everything, nothing worked)
   - Hope/discovery (stumbled on, discovered secret)
   - Transformation (couldn't believe, life-changing)

3. CURIOSITY GAPS:
   - "What doctors don't tell you"
   - "Secret used by [authority group]"
   - "Hidden truth about [problem]"
   - "While I was struggling, [solution] already existed"

4. SOCIAL PROOF PATTERNS:
   - Skeptical conversion ("my skeptical husband")
   - Family transformation ("my mom says")
   - Visible results ("people started complimenting")
   - Authentic details (specific conversations, reactions)

5. URGENCY/SCARCITY:
   - Limited availability ("sells out every few weeks")
   - Quality exclusivity ("only pharmaceutical-grade")
   - Emotional consequence ("don't wait until worse")
   - Personal stakes ("I wish I'd found this years ago")
"""
        
    async def generate_vsl_carousel(self, brand: str, product_type: str) -> VSLCarouselStrategy:
        """Generate complete VSL carousel using updated methodology with photorealistic specs"""
        
        self.logger.info(f"Generating VSL carousel for {brand} {product_type}")
        
        # Build comprehensive prompt with updated image specifications
        prompt = self._build_vsl_prompt(brand, product_type)
        
        # Get VSL from Claude using updated methodology
        response = await self._call_claude_vsl(prompt)
        
        # Parse response into structured slides
        slides = self._parse_vsl_response(response)
        
        return VSLCarouselStrategy(
            slides=slides,
            brand=brand,
            product_type=product_type
        )
    
    def _build_vsl_prompt(self, brand: str, product_type: str) -> str:
        """Build comprehensive prompt with updated photorealistic image specifications"""
        
        prompt = f"""
{self.vsl_methodology}

{self.example_vsls}

{self.vsl_principles}

**TASK:**
Create a complete TikTok carousel ad for:
- Brand: {brand}
- Product: {product_type}

**REQUIREMENTS:**
1. Follow the exact "Relatable VSL" method structure
2. Use patterns from the example VSLs
3. Apply VSL Bible psychological principles
4. Create 10 slides with both script and DALL-E prompts
5. Product mention ONLY in slides 9-10
6. Include specific personal transformation timeline
7. Add authentic family/friend social proof
8. **CRITICAL:** Each DALL-E prompt must include photorealistic camera specifications
9. **CRITICAL:** All images must be 9:16 vertical format
10. Keep DALL-E prompts to 30-40 words maximum

**OUTPUT FORMAT:**
### **Slide 1**
**Script:** [Your relatable struggle script here]
**DALL-E Prompt:** [30-40 word prompt with photorealistic specs and 9:16 format]

### **Slide 2**
**Script:** [Your script here]
**DALL-E Prompt:** [30-40 word prompt with photorealistic specs and 9:16 format]

[Continue for all 10 slides...]

**IMPORTANT:** 
- Make the personal story feel authentic and relatable
- Include specific timelines ("Day 3: X, Day 7: Y, Week 2: Z")
- Use family/friend social proof that feels real
- Apply curiosity gaps and credibility stacking
- Build urgency with emotional stakes
- **EVERY DALL-E prompt must include:** "ultra photorealistic, 16k, natural lighting, HDR, high resolution, shot on Canon EOS R5, Canon RF 50mm f/1.2L USM, depth of field, --s 750, 9:16 vertical format"

Generate the complete carousel now:
"""
        
        return prompt
    
    async def _call_claude_vsl(self, prompt: str) -> str:
        """Call Claude API with updated VSL methodology"""
        
        try:
            message = await self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude VSL API error: {str(e)}")
            raise
    
    def _parse_vsl_response(self, response: str) -> List[VSLSlide]:
        """Parse Claude's response into structured VSL slides"""
        
        slides = []
        
        # Split response into slide sections
        slide_sections = re.split(r'### \*\*Slide (\d+)\*\*', response)
        
        for i in range(1, len(slide_sections), 2):
            if i + 1 < len(slide_sections):
                slide_number = int(slide_sections[i])
                slide_content = slide_sections[i + 1]
                
                # Extract script and DALL-E prompt
                script_match = re.search(r'\*\*Script:\*\* (.+?)(?=\*\*DALL-E Prompt:\*\*)', slide_content, re.DOTALL)
                dalle_match = re.search(r'\*\*DALL-E Prompt:\*\* (.+?)(?=\n\n|\Z)', slide_content, re.DOTALL)
                
                if script_match and dalle_match:
                    script = script_match.group(1).strip().strip('"')
                    dalle_prompt = dalle_match.group(1).strip()
                    
                    slides.append(VSLSlide(
                        slide_number=slide_number,
                        script=script,
                        dalle_prompt=dalle_prompt
                    ))
        
        # Fallback parsing if regex fails
        if not slides:
            slides = self._fallback_parse(response)
        
        self.logger.info(f"Parsed {len(slides)} VSL slides with updated photorealistic specs")
        return slides
    
    def _fallback_parse(self, response: str) -> List[VSLSlide]:
        """Fallback parsing method if regex fails"""
        
        slides = []
        lines = response.split('\n')
        current_slide = None
        current_script = ""
        current_dalle = ""
        in_script = False
        in_dalle = False
        
        for line in lines:
            if 'Slide' in line and ('**' in line or '#' in line):
                # Save previous slide
                if current_slide and current_script and current_dalle:
                    slides.append(VSLSlide(
                        slide_number=current_slide,
                        script=current_script.strip().strip('"'),
                        dalle_prompt=current_dalle.strip()
                    ))
                
                # Start new slide
                slide_match = re.search(r'(\d+)', line)
                if slide_match:
                    current_slide = int(slide_match.group(1))
                    current_script = ""
                    current_dalle = ""
                    in_script = False
                    in_dalle = False
            
            elif 'Script:' in line:
                in_script = True
                in_dalle = False
                script_text = line.split('Script:')[-1].strip()
                current_script = script_text
            
            elif 'DALL-E Prompt:' in line or 'Prompt:' in line:
                in_script = False
                in_dalle = True
                dalle_text = line.split('Prompt:')[-1].strip()
                current_dalle = dalle_text
            
            elif in_script and line.strip():
                current_script += " " + line.strip()
            
            elif in_dalle and line.strip():
                current_dalle += " " + line.strip()
        
        # Save last slide
        if current_slide and current_script and current_dalle:
            slides.append(VSLSlide(
                slide_number=current_slide,
                script=current_script.strip().strip('"'),
                dalle_prompt=current_dalle.strip()
            ))
        
        return slides
