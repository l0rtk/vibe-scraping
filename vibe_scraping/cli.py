#!/usr/bin/env python3
import argparse
import os
import json
from .main import process_product_page, MODEL_PRICING, scrape_webpage, extract_product_info, calculate_cost, print_results

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
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Selenium in headless mode (no visible browser window)"
    )
    parser.add_argument(
        "--save-content",
        help="Save the scraped content to the specified file"
    )
    parser.add_argument(
        "--use-saved",
        help="Use content from a previously saved file instead of scraping"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries for API calls (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Check for conflicting options
    if args.selenium and args.no_selenium:
        print("Error: Cannot use both --selenium and --no-selenium options")
        return
    
    # Check if using saved content
    if args.use_saved:
        if not os.path.exists(args.use_saved):
            print(f"Error: Saved content file '{args.use_saved}' not found")
            return
        
        try:
            with open(args.use_saved, 'r', encoding='utf-8') as f:
                text = f.read()
            
            print(f"Loaded {len(text)} characters from '{args.use_saved}'")
            
            # Process the text through the model
            try:
                product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                cost_info = calculate_cost(product_info["usage"], args.model)
                
                # Print results
                if args.quiet:
                    print(product_info["content"])
                else:
                    print_results(product_info, cost_info, args.model)
            except Exception as e:
                print(f"Error processing content with LLM: {str(e)}")
                print("Content was loaded but could not be processed by the model.")
        except Exception as e:
            print(f"Error reading saved content: {str(e)}")
        
        return
    
    # Process with web scraping
    text = None
    
    if args.selenium:
        # Import selenium_scraper only when needed
        try:
            from .selenium_scraper import scrape_with_selenium
            from bs4 import BeautifulSoup
            
            print(f"Scraping {args.url} with Selenium {'(headless)' if args.headless else '(with browser window)'}...")
            html_content = scrape_with_selenium(args.url, headless=args.headless)
            
            if html_content:
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                print(f"Successfully retrieved {len(text)} characters using Selenium")
                
                # Save content if requested
                if args.save_content:
                    try:
                        with open(args.save_content, 'w', encoding='utf-8') as f:
                            f.write(text)
                        print(f"Saved scraped content to '{args.save_content}'")
                    except Exception as e:
                        print(f"Error saving content: {str(e)}")
                
                # Process the text through the model
                try:
                    product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                    cost_info = calculate_cost(product_info["usage"], args.model)
                    
                    # Print results
                    if args.quiet:
                        print(product_info["content"])
                    else:
                        print_results(product_info, cost_info, args.model)
                except Exception as e:
                    print(f"Error processing content with LLM: {str(e)}")
                    if args.save_content:
                        print(f"Content was saved to '{args.save_content}' but could not be processed by the model.")
                        print(f"You can try again later using: --use-saved {args.save_content}")
            else:
                print("Failed to retrieve content with Selenium")
        except ImportError:
            print("Error: Selenium is not installed. Run 'pip install selenium webdriver-manager' to use this feature.")
        except Exception as e:
            print(f"Error during Selenium scraping: {str(e)}")
    else:
        # Use standard process_product_page with optional selenium fallback
        try:
            # First just get the text content
            text = scrape_webpage(args.url, use_selenium_fallback=not args.no_selenium)
            
            if not text:
                print("Failed to retrieve the page content")
                return
            
            # Save content if requested
            if args.save_content:
                try:
                    with open(args.save_content, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"Saved scraped content to '{args.save_content}'")
                except Exception as e:
                    print(f"Error saving content: {str(e)}")
            
            # Now process with the LLM
            try:
                product_info = extract_product_info(text, args.model, args.prompt, max_retries=args.max_retries)
                cost_info = calculate_cost(product_info["usage"], args.model)
                
                # Print results
                if args.quiet:
                    print(product_info["content"])
                else:
                    print_results(product_info, cost_info, args.model)
            except Exception as e:
                print(f"Error processing content with LLM: {str(e)}")
                if args.save_content:
                    print(f"Content was saved to '{args.save_content}' but could not be processed by the model.")
                    print(f"You can try again later using: --use-saved {args.save_content}")
        except Exception as e:
            print(f"Error during scraping process: {str(e)}")

if __name__ == "__main__":
    main() 