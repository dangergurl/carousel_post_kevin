#!/usr/bin/env python3
"""
TikTok Carousel Automation - Entry Point
Optimized with Recraft V3 for product-realistic carousel posts
"""

import asyncio
import argparse
import sys

from carousel_automation import TikTokCarouselAutomation

async def main():
    parser = argparse.ArgumentParser(
        description='TikTok Shop VSL Carousel Automation with Recraft V3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with product
  python run_carousel.py --product "Ashwagandha Gummies" --brand "Goli" --price 19.99

  # With product reference image (uses Recraft V3 for slides 8-10)
  python run_carousel.py --product "Ashwagandha Gummies" --brand "Goli" --price 19.99 --product-image ./product.jpg

  # Use kie.ai Flux Kontext for UGC-style (default)
  python run_carousel.py --product "Vitamin C Serum" --price 29.99 --product-image ./serum.jpg --product-model kie_flux_kontext

  # Skip text overlays (get raw AI images only)
  python run_carousel.py --product "Collagen Powder" --price 39.99 --skip-text-overlay
        """
    )
    
    # Required arguments
    parser.add_argument('--product', required=True, help='Product name')
    parser.add_argument('--brand', help='Brand name (optional)')
    parser.add_argument('--price', type=float, default=0.0, help='Product price')
    parser.add_argument('--category', default='general', help='Product category')
    
    # Optional arguments
    parser.add_argument('--features', nargs='+', help='Product features')
    parser.add_argument('--target-audience', help='Target audience')
    parser.add_argument('--currency', default='USD', help='Price currency')
    
    # Product image options
    parser.add_argument('--product-image', help='Path to product reference image (for slides 8-10)')
    parser.add_argument('--format-mode', choices=['cover', 'contain', 'stretch'], default='cover',
                       help='Product image formatting: cover (crop to fill), contain (fit with padding), stretch')
    
    # Model selection
    parser.add_argument('--product-model', choices=['kie_flux_kontext', 'recraft', 'flux_img2img', 'flux_redux'], default='kie_flux_kontext',
                       help='Model for product photos (slides 8-10): kie_flux_kontext (UGC-style, default), recraft, flux_img2img, flux_redux')
    parser.add_argument('--use-gemini', action='store_true', 
                       help='Use Gemini 2.5 Flash for scene slides (1-7) instead of FLUX')
    
    # Processing options
    parser.add_argument('--skip-text-overlay', action='store_true', 
                       help='Skip text overlay and return raw generated images')
    
    args = parser.parse_args()
    
    # Build product data
    product_data = {
        'name': args.product,
        'brand': args.brand or '',
        'price': args.price,
        'category': args.category,
        'currency': args.currency,
        'features': args.features or [],
        'target_audience': args.target_audience or 'general consumers',
        'product_image': args.product_image,
        'format_mode': args.format_mode,
        'skip_text_overlay': args.skip_text_overlay
    }
    
    # Print configuration
    print("\n" + "="*60)
    print("🚀 TikTok Carousel Automation - Recraft V3 Edition")
    print("="*60)
    print(f"Product: {args.product}")
    print(f"Brand: {args.brand or 'N/A'}")
    print(f"Price: ${args.price}")
    if args.product_image:
        print(f"Product Image: {args.product_image}")
        print(f"Product Model: {args.product_model.upper()} (for slides 8-10)")
    print(f"Scene Model: {'Gemini 2.5 Flash' if args.use_gemini else 'FLUX'} (for slides 1-7)")
    print(f"Text Overlays: {'Disabled' if args.skip_text_overlay else 'Enabled'}")
    print("="*60 + "\n")
    
    # Create automation system
    automation = TikTokCarouselAutomation(
        use_gemini=args.use_gemini, 
        product_model=args.product_model
    )
    
    try:
        # Generate VSL carousel
        result = await automation.create_carousel(product_data)
        
        # Print results
        print("\n" + "="*60)
        print("🎉 SUCCESS! VSL Carousel Created")
        print("="*60)
        print(f"⏱️  Execution Time: {result['execution_time']:.1f} seconds")
        print(f"📁 Output Directory: {result['output_directory']}")
        print(f"🖼️  Images Generated: {len(result['images'])}")
        print(f"🎯 Style: {result['vsl_info']['style']}")
        print(f"📝 Slides: {result['vsl_info']['slide_count']} VSL slides")
        print(f"🤖 Product Model: {result['vsl_info']['product_model'].upper()}")
        print("="*60)
        
        print("\n📋 Next Steps:")
        print(f"1. Review images in: {result['output_directory']}")
        print(f"2. Check vsl_script.txt for complete script")
        print(f"3. Upload to TikTok Shop as carousel")
        print("\n✨ Happy posting!\n")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 ERROR: {str(e)}")
        print("Check logs/carousel_automation.log for detailed error information\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)