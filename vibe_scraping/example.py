#!/usr/bin/env python3
"""
Example usage of the deep web crawling functionality.
This script demonstrates how to use the library for deep crawling with Scrapy.
"""

import argparse
import os
from vibe_scraping.crawler import WebCrawler, crawl_site
from vibe_scraping import SCRAPY_AVAILABLE

def crawl_website(url, output_dir="crawled_data", max_depth=5, max_pages=1000, delay=0.1):
    """
    Crawl a website deeply using Scrapy and save the results.
    
    Args:
        url: The website URL to start crawling from
        output_dir: Directory to save the crawled data
        max_depth: Maximum depth to crawl
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        
    Returns:
        Dict with crawl statistics
    """
    if not SCRAPY_AVAILABLE:
        print("Scrapy is not installed. Please install with: pip install scrapy")
        return None
        
    print(f"Starting deep crawl of {url}")
    print(f"Max depth: {max_depth}, Max pages: {max_pages}")
    print(f"Output directory: {output_dir}")
    
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a crawler instance
    crawler = WebCrawler(
        start_url=url,
        max_depth=max_depth,
        max_pages=max_pages,
        follow_external_links=False,  # Stay on the same domain
        respect_robots_txt=True,      # Respect robots.txt
        delay=delay,                  # Reasonable delay between requests
        save_path=output_dir
    )
    
    # Start the crawl
    result = crawler.crawl()
    
    # Print results
    if isinstance(result, dict):
        pages_crawled = result.get('pages_crawled', 0)
    else:
        pages_crawled = result
        
    print(f"\nCrawl completed!")
    print(f"Pages crawled: {pages_crawled}")
    print(f"Data saved to: {output_dir}")
    
    return result


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Deep web crawling with Scrapy")
    parser.add_argument("--url", default="https://newshub.ge", 
                       help="URL to start crawling from (default: newshub.ge)")
    parser.add_argument("--output", default="./crawled_data",
                       help="Directory to save crawled data (default: ./crawled_data)")
    parser.add_argument("--depth", type=int, default=5,
                       help="Maximum crawl depth (default: 5)")
    parser.add_argument("--pages", type=int, default=1000,
                       help="Maximum pages to crawl (default: 1000)")
    parser.add_argument("--delay", type=float, default=0.1,
                       help="Delay between requests in seconds (default: 0.1)")
    args = parser.parse_args()
    
    # Run the crawler
    result = crawl_website(
        url=args.url,
        output_dir=args.output,
        max_depth=args.depth,
        max_pages=args.pages,
        delay=args.delay
    )
    
    # Check if successful
    if not result:
        print("\nCrawl failed - please make sure Scrapy is installed.")
        print("Install with: pip install scrapy")
    else:
        print("\nCrawl details:")
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(f"Pages crawled: {result}") 