#!/usr/bin/env python3
"""
Quickstart example for vibe-scraping package
"""
import os
from dotenv import load_dotenv
from vibe_scraping import process_product_page, calculate_cost

# Load environment variables from .env file
load_dotenv()

def main():
    # Make sure the GROQ_API_KEY is set in the environment
    if "GROQ_API_KEY" not in os.environ:
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Please create a .env file with your Groq API key or set it in your environment.")
        return
        
    # URLs to analyze
    url = "https://www.amazon.com/dp/B09V3KXJPB"  # Example product URL
    
    print(f"Processing {url}...")
    
    # Process the product page
    product_info, cost_info = process_product_page(
        url,
        custom_prompt="Extract the product name, price, features, and specifications from",
        use_selenium_fallback=True
    )
    
    if product_info:
        # Print the extracted information
        print("\nExtracted Product Information:")
        print("-" * 40)
        print(product_info["content"])
        print("-" * 40)
        
        # Print token usage and cost information
        print("\nToken Usage:")
        print(f"Input tokens: {product_info['usage']['input_tokens']}")
        print(f"Output tokens: {product_info['usage']['output_tokens']}")
        print(f"Total tokens: {product_info['usage']['total_tokens']}")
        
        if cost_info and cost_info["has_pricing"]:
            print(f"\nEstimated cost: ${cost_info['total_cost']:.6f}")
    else:
        print("Failed to process the product page.")

if __name__ == "__main__":
    main() 