#!/usr/bin/env python3
import argparse
from main import process_product_page, MODEL_PRICING, scrape_webpage, extract_product_info, calculate_cost, print_results

def main():
    parser = argparse.ArgumentParser(description="Scrape product information from a website")
    parser.add_argument("url", help="URL of the product page to scrape")
    parser.add_argument(
        "--model", 
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        choices=list(MODEL_PRICING.keys()), 
        help="Model to use for extraction"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Only output the extracted product information"
    )
    parser.add_argument(
        "--prompt",
        help="Custom prompt to use for extraction. Default is to extract product name, price, description and attributes."
    )
    
    args = parser.parse_args()
    
    # Process the product page with optional custom prompt
    product_info, cost_info = process_product_page(args.url, args.model, args.prompt)
    
    # In quiet mode, only output the extracted information
    if args.quiet and product_info:
        print(product_info["content"])

if __name__ == "__main__":
    main() 