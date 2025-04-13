#!/usr/bin/env python3
"""
Example usage of the product scraping library.
This script shows how to use the library for multiple product pages.
"""
from vibe_scraping import process_product_page, scrape_webpage, extract_product_info, calculate_cost
import json
import argparse

def save_product_info(url, output_file="product_info.json", custom_prompt=None, use_selenium=False):
    """Process a product page and save the result to a JSON file."""
    print(f"Processing {url}...")
    product_info, cost_info = process_product_page(url, custom_prompt=custom_prompt, use_selenium_fallback=use_selenium)
    
    # Create a dictionary with all the information
    result = {
        "url": url,
        "product_info": product_info["content"] if product_info else "Failed to retrieve content",
        "token_usage": product_info["usage"] if product_info else None,
        "cost": cost_info if cost_info and cost_info["has_pricing"] else "Not available",
        "used_selenium": use_selenium
    }
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Saved information to {output_file}")
    return result

def compare_multiple_products(urls, use_selenium=False):
    """Process multiple product pages and extract their information."""
    results = []
    
    for url in urls:
        print(f"Processing {url}...")
        text = scrape_webpage(url, use_selenium_fallback=use_selenium)
        if not text:
            print(f"Failed to retrieve {url}")
            continue
            
        # Extract product info
        product_info = extract_product_info(text)
        
        # Calculate cost
        cost_info = calculate_cost(product_info["usage"], "meta-llama/llama-4-scout-17b-16e-instruct")
        
        results.append({
            "url": url,
            "info": product_info["content"],
            "cost": cost_info["total_cost"] if cost_info["has_pricing"] else "N/A",
            "used_selenium": use_selenium
        })
    
    return results

def compare_with_different_prompts(url, use_selenium=False):
    """Compare results using different prompts on the same product page."""
    print(f"Analyzing {url} with different prompts...")
    
    prompts = [
        "Extract only the technical specifications and features from",
        "Extract only the price and availability information from",
        "Provide a brief summary of the product from",
        "List all accessories and compatible products mentioned in"
    ]
    
    results = []
    for prompt in prompts:
        print(f"\nUsing prompt: '{prompt}'")
        product_info, cost_info = process_product_page(
            url, 
            custom_prompt=prompt, 
            use_selenium_fallback=use_selenium
        )
        
        if not product_info:
            print(f"Failed to process with prompt: {prompt}")
            continue
            
        results.append({
            "prompt": prompt,
            "result": product_info["content"],
            "tokens": product_info["usage"]["total_tokens"],
            "cost": cost_info["total_cost"] if cost_info["has_pricing"] else "N/A",
            "used_selenium": use_selenium
        })
    
    return results

def compare_regular_vs_selenium(url, prompt=None):
    """Compare results between regular scraping and Selenium-based scraping."""
    print(f"Comparing regular requests vs Selenium for {url}...")
    
    # Get results with regular requests
    print("\nUsing regular requests:")
    regular_product_info, regular_cost_info = process_product_page(
        url, 
        custom_prompt=prompt, 
        use_selenium_fallback=False
    )
    
    # Get results with Selenium
    print("\nUsing Selenium:")
    try:
        selenium_product_info, selenium_cost_info = process_product_page(
            url, 
            custom_prompt=prompt, 
            use_selenium_fallback=True
        )
        
        # Create comparison result
        comparison = {
            "url": url,
            "prompt": prompt,
            "regular_result": {
                "content": regular_product_info["content"] if regular_product_info else "Failed to retrieve",
                "tokens": regular_product_info["usage"]["total_tokens"] if regular_product_info else 0,
                "cost": regular_cost_info["total_cost"] if regular_cost_info and regular_cost_info["has_pricing"] else "N/A",
                "success": regular_product_info is not None
            },
            "selenium_result": {
                "content": selenium_product_info["content"] if selenium_product_info else "Failed to retrieve",
                "tokens": selenium_product_info["usage"]["total_tokens"] if selenium_product_info else 0,
                "cost": selenium_cost_info["total_cost"] if selenium_cost_info and selenium_cost_info["has_pricing"] else "N/A",
                "success": selenium_product_info is not None
            }
        }
        
        # Save comparison to JSON
        with open("scraping_method_comparison.json", "w") as f:
            json.dump(comparison, f, indent=2)
        
        print("\nSaved scraping method comparison to scraping_method_comparison.json")
        return comparison
    except Exception as e:
        print(f"Error during Selenium comparison: {e}")
        print("Selenium comparison failed.")
        return None

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run examples with optional Selenium usage")
    parser.add_argument("--selenium", action="store_true", help="Use Selenium for scraping")
    parser.add_argument("--url", default="https://alta.ge/home-appliance/kitchen-appliances/microwaves/toshiba-mm-eg24p-bm-black.html", 
                       help="URL to scrape (default: Alta.ge microwave product)")
    args = parser.parse_args()
    
    use_selenium = args.selenium
    scraping_method = "Selenium-assisted" if use_selenium else "standard requests"
    print(f"Running examples using {scraping_method} for scraping")
    
    # Example 1: Process a single product and save to JSON
    save_product_info(args.url, use_selenium=use_selenium)
    
    # Example 2: Compare different prompts on the same product
    print("\n\nAnalyzing a product with different prompts:")
    prompt_results = compare_with_different_prompts(args.url, use_selenium=use_selenium)
    
    # Save prompt comparison to JSON
    if prompt_results:
        with open("prompt_comparison.json", "w") as f:
            json.dump(prompt_results, f, indent=2)
        print("\nSaved prompt comparison results to prompt_comparison.json")
    
    # Example 3: Compare regular vs Selenium scraping (only if not already using Selenium)
    if not use_selenium:
        print("\n\nComparing regular requests vs Selenium scraping:")
        compare_regular_vs_selenium(args.url, prompt="Extract only the technical specifications from") 