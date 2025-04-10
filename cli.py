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
    parser.add_argument(
        "--selenium",
        action="store_true",
        help="Force using Selenium for scraping (for JavaScript-heavy sites)"
    )
    parser.add_argument(
        "--no-selenium",
        action="store_true",
        help="Disable Selenium fallback (use only regular requests)"
    )
    
    args = parser.parse_args()
    
    # Check for conflicting options
    if args.selenium and args.no_selenium:
        print("Error: Cannot use both --selenium and --no-selenium options")
        return
    
    # Process the product page with optional custom prompt
    if args.selenium:
        # Import selenium_scraper only when needed
        try:
            from selenium_scraper import scrape_with_selenium
            from bs4 import BeautifulSoup
            
            print(f"Scraping {args.url} with Selenium...")
            html_content = scrape_with_selenium(args.url)
            
            if html_content:
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                print(f"Successfully retrieved {len(text)} characters using Selenium")
                
                # Process the text through the model
                product_info = extract_product_info(text, args.model, args.prompt)
                cost_info = calculate_cost(product_info["usage"], args.model)
                
                # Print results
                if args.quiet:
                    print(product_info["content"])
                else:
                    print_results(product_info, cost_info, args.model)
            else:
                print("Failed to retrieve content with Selenium")
        except ImportError:
            print("Error: Selenium is not installed. Run 'pip install selenium webdriver-manager' to use this feature.")
        except Exception as e:
            print(f"Error during Selenium scraping: {str(e)}")
    else:
        # Use standard process_product_page with optional selenium fallback
        product_info, cost_info = process_product_page(
            args.url, 
            args.model, 
            args.prompt, 
            use_selenium_fallback=not args.no_selenium
        )
        
        # In quiet mode, only output the extracted information
        if args.quiet and product_info:
            print(product_info["content"])

if __name__ == "__main__":
    main() 