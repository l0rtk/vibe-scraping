#!/usr/bin/env python3
"""Example usage of the deep web crawler."""

from vibe_scraping.crawler import WebCrawler
from vibe_scraping import SCRAPY_AVAILABLE

def main():
    if not SCRAPY_AVAILABLE:
        print("Scrapy is not installed. Install with: pip install scrapy")
        return
        
    # Create crawler    
    crawler = WebCrawler(
        start_url="https://newshub.ge",
        max_depth=3,
        max_pages=100,
        save_path="./crawl_example"
    )
    
    # Run crawl
    result = crawler.crawl()
    
    # Print results
    pages = result.get('pages_crawled', 0) if isinstance(result, dict) else result
    print(f"Crawled {pages} pages to ./crawl_example")

if __name__ == "__main__":
    main() 