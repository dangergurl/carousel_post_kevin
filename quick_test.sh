#!/bin/bash

# Quick Test Script for TikTok Carousel Automation
# This runs a fast test to verify your setup is working

echo "🚀 TikTok Carousel Automation - Quick Test"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created"
    echo "❗ Please edit .env and add your API keys before running the test"
    echo ""
    echo "Required API keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - REPLICATE_API_TOKEN"
    echo ""
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python --version

# Check if dependencies are installed
echo ""
echo "📦 Checking dependencies..."
python -c "import anthropic, replicate, fal_client; print('✅ All AI libraries installed')" || {
    echo "❌ Dependencies missing"
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
}

# Check FFmpeg
echo ""
echo "🎬 Checking FFmpeg..."
which ffmpeg > /dev/null 2>&1 && echo "✅ FFmpeg installed" || echo "⚠️  FFmpeg not found (text overlays won't work)"

# Test module imports
echo ""
echo "🧪 Testing module imports..."
python -c "from carousel_automation import TikTokCarouselAutomation; print('✅ TikTokCarouselAutomation imported successfully')"

echo ""
echo "=========================================="
echo "🎉 Quick test complete!"
echo ""
echo "Next steps:"
echo "1. Add your API keys to .env file"
echo "2. Run: python run_carousel.py --product 'Test' --price 19.99 --skip-text-overlay"
echo "3. Check output/ directory for results"
echo ""
echo "For full guide, see:"
echo "  - README.md (full documentation)"
echo "  - SETUP_GUIDE.md (step-by-step setup)"
echo "  - WHATS_NEW.md (what's different from your old script)"
echo ""
