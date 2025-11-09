# 🎬 TikTok Carousel Automation - Recraft V3 Edition

**AI-Powered VSL Carousel Generator with Product-Realistic Images**

## 🌟 What's New in V2.0

### ✨ Recraft V3 Integration
- **State-of-the-art product placement** with reference images
- **95%+ product accuracy** in generated scenes
- **Natural composition** with real product integration
- **Fast generation** (20-30 seconds per image)

### 🎨 Multiple Product Models
1. **Recraft V3** (Default, Best) - Photorealistic product integration
2. **FLUX img2img** (Improved) - Strength increased from 0.35 → 0.55
3. **FLUX Redux** - Product identity preservation

### 🎯 Features
- **10-slide VSL carousels** with persuasive storytelling
- **Claude-powered scripts** using proven VSL patterns
- **TikTok-style text overlays** matching your reference image
- **Automatic product formatting** to 9:16 aspect ratio
- **Smart error handling** with fallback models

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg (for text overlays)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Required API Keys:**
- OpenAI API key (for DALL-E 3 backup)
- Anthropic API key (for Claude VSL generation)
- Replicate API token (for Recraft V3 & FLUX)

**Optional:**
- FAL_KEY (for Gemini 2.5 Flash & FLUX img2img)

---

## 🚀 Quick Start

### Basic Usage

```bash
python run_carousel.py \
  --product "Ashwagandha Gummies" \
  --brand "Goli" \
  --price 19.99
```

### With Product Reference Image (Recommended)

```bash
python run_carousel.py \
  --product "Ashwagandha Gummies" \
  --brand "Goli" \
  --price 19.99 \
  --product-image ./my_product.jpg
```

This uses **Recraft V3** for slides 8-10 (product photos) with your reference image.

---

## 🎛️ Advanced Options

### Choose Product Model

```bash
# Recraft V3 (default, best)
python run_carousel.py --product "Vitamin C" --product-image ./product.jpg --product-model recraft

# FLUX img2img (improved strength)
python run_carousel.py --product "Vitamin C" --product-image ./product.jpg --product-model flux_img2img

# FLUX Redux (identity preservation)
python run_carousel.py --product "Vitamin C" --product-image ./product.jpg --product-model flux_redux
```

### Image Formatting

```bash
# Cover mode (crop to fill, default)
python run_carousel.py --product "Serum" --product-image ./serum.jpg --format-mode cover

# Contain mode (fit with padding)
python run_carousel.py --product "Serum" --product-image ./serum.jpg --format-mode contain

# Stretch mode (may distort)
python run_carousel.py --product "Serum" --product-image ./serum.jpg --format-mode stretch
```

### Use Gemini for Scene Slides

```bash
# Use Gemini 2.5 Flash for slides 1-7 (faster, cheaper)
python run_carousel.py --product "Collagen" --use-gemini
```

### Skip Text Overlays

```bash
# Get raw AI images without text
python run_carousel.py --product "Protein Powder" --skip-text-overlay
```

---

## 📁 Output Structure

```
output/
└── product_name_vsl_20240108_143022/
    ├── vsl_slide_01.jpg
    ├── vsl_slide_02.jpg
    ├── ...
    ├── vsl_slide_10.jpg
    ├── metadata.json
    └── vsl_script.txt
```

---

## 🎨 How It Works

### Slide Generation Process

**Slides 1-7: Scene Images**
- Generated with FLUX 1.1 Pro or Gemini 2.5 Flash
- Photorealistic lifestyle scenes
- No product images yet

**Slides 8-10: Product Photos**
- Uses your product reference image
- Generated with Recraft V3 (default)
- Product accurately integrated into scenes
- Maintains product appearance

**Text Overlays**
- TikTok-style white text with black outline
- Auto-wrapped at 26 characters per line
- Positioned at 60% down (adjusts for long text)

---

## 🔧 Troubleshooting

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg (see installation section)

### Issue: "Recraft V3 failed"
**Solution:** The system automatically falls back to FLUX img2img

### Issue: Product not recognizable in slides 8-10
**Solution:** 
- Try `--product-model flux_img2img` with higher strength
- Ensure product image is clear and well-lit
- Use `--format-mode contain` to preserve product details

### Issue: Text overlay doesn't look right
**Solution:** Place `ProximaNovaSemibold.otf` in project root, or it will use system font

---

## 🎯 Best Practices

### Product Reference Images
1. **Use high-quality photos** (1080x1920 or higher)
2. **Clear product visibility** (no obstructions)
3. **Good lighting** (natural or professional)
4. **Clean background** (white or simple)

### Model Selection
- **Recraft V3**: Best for most products, natural integration
- **FLUX img2img**: Good for abstract/artistic products
- **FLUX Redux**: Best for maintaining exact product colors

### Performance
- Generation time: **3-5 minutes** for 10 slides
- Recraft V3: ~25 seconds per slide
- FLUX: ~20 seconds per slide
- Gemini: ~15 seconds per slide

---

## 📊 Model Comparison

| Model | Product Accuracy | Speed | Cost | Best For |
|-------|------------------|-------|------|----------|
| **Recraft V3** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Most products |
| **FLUX img2img** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Artistic products |
| **FLUX Redux** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Color accuracy |
| **Gemini** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Scene slides only |

---

## 🤝 Contributing

Found a bug or have a feature request? Please open an issue!

---

## 📄 License

MIT License - feel free to use for commercial projects!

---

## 🎉 Credits

- **Recraft V3** by Recraft AI
- **FLUX** by Black Forest Labs
- **Claude** by Anthropic
- **VSL methodology** from proven TikTok advertising patterns

---

**Happy carousel creating! 🚀**