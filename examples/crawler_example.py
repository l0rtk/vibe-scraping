#!/usr/bin/env python3
"""
Example usage of the web crawler functionality in Vibe Scraping
"""
import os
import json
from vibe_scraping import WebCrawler, extract_product_info, calculate_cost

def main():
    # Configuration
    start_url = "https://books.toscrape.com/"  # Example website safe for scraping
    output_dir = "crawled_books"
    max_depth = 2
    max_pages = 20
    
    print(f"Starting crawl from {start_url}")
    print(f"Saving data to {output_dir}")
    print(f"Max depth: {max_depth}, Max pages: {max_pages}")
    
    # Create and configure the crawler
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        delay=1.5,  # Be polite with a 1.5 second delay
        save_path=output_dir,
        crawl_method="breadth",  # Use breadth-first search
        url_pattern=r"books.toscrape.com/catalogue/.*",  # Only follow catalog pages
        selenium_fallback=False,  # No need for Selenium on this site
        follow_subdomains=False,  # Stay on the same domain
        delay_randomize=True  # Add randomization to delays for more human-like behavior
    )
    
    # Start the crawl
    crawler.crawl()
    
    # Get and print statistics
    stats = crawler.get_crawl_stats()
    print("\nCrawl completed:")
    print(f"Pages crawled: {stats['pages_crawled']}")
    print(f"Domain: {stats['domain']}")
    
    # Example of processing the crawled content
    if stats['pages_crawled'] > 0:
        process_crawled_data(output_dir)

def process_crawled_data(data_dir):
    """Process the crawled data to extract book information"""
    print("\nProcessing crawled book data...")
    
    # Find all pages in the crawled data
    book_pages = []
    for root, dirs, files in os.walk(data_dir):
        for dir_name in dirs:
            # Skip the metadata directory
            if dir_name == "metadata.json":
                continue
                
            meta_file = os.path.join(root, dir_name, "metadata.json")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, 'r') as f:
                        page_meta = json.load(f)
                        
                    # Check if it's a book page (contains "catalogue" in URL)
                    if "catalogue" in page_meta["url"]:
                        book_pages.append({
                            "url": page_meta["url"],
                            "dir": os.path.join(root, dir_name)
                        })
                except Exception as e:
                    print(f"Error reading metadata from {meta_file}: {e}")
    
    print(f"Found {len(book_pages)} book pages")
    
    # Process a few book pages as examples
    for i, book in enumerate(book_pages[:3]):  # Process first 3 books
        print(f"\nProcessing book {i+1}/{min(3, len(book_pages))}: {book['url']}")
        
        # Read the content file
        content_file = os.path.join(book['dir'], "content.txt")
        if os.path.exists(content_file):
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract book information
                print("Extracting book information using LLM...")
                book_info = extract_product_info(
                    content, 
                    custom_prompt="Extract the book title, author, price, and category from"
                )
                
                # Calculate cost
                cost_info = calculate_cost(book_info["usage"], "meta-llama/llama-4-scout-17b-16e-instruct")
                
                # Save the extracted info
                extracted_file = os.path.join(book['dir'], "extracted_info.json")
                with open(extracted_file, 'w') as f:
                    json.dump({
                        "url": book["url"],
                        "info": book_info["content"],
                        "usage": book_info["usage"],
                        "cost": cost_info
                    }, f, indent=2)
                
                print(f"Saved extracted information to {extracted_file}")
                print(f"Book information: {book_info['content'][:200]}...")
                
            except Exception as e:
                print(f"Error processing book content: {e}")
    
    print("\nDone processing crawled data")

if __name__ == "__main__":
    main() 