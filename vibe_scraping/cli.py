#!/usr/bin/env python3
"""CLI for vibe-scraping."""

import argparse
import os
import sys
from vibe_scraping.crawler import WebCrawler
from vibe_scraping import SCRAPY_AVAILABLE, __version__

def main():
    parser = argparse.ArgumentParser(description="Vibe Scraping")
    parser.add_argument('--version', action='version', version=f'vibe-scraping {__version__}')
    
    # URL argument
    parser.add_argument('url', nargs='?', help='URL to crawl')
    
    # Options
    parser.add_argument('-o', '--output', default='./crawled_data', help='Output directory')
    parser.add_argument('-d', '--depth', type=int, default=5, help='Max depth')
    parser.add_argument('-p', '--pages', type=int, default=1000, help='Max pages')
    parser.add_argument('--delay', type=float, default=0.1, help='Request delay')
    parser.add_argument('-f', '--follow-external', action='store_true', help='Follow external links')
    parser.add_argument('-i', '--ignore-robots', action='store_true', help='Ignore robots.txt')
    
    args = parser.parse_args()
    
    # Check if Scrapy is available
    if not SCRAPY_AVAILABLE:
        print("Error: Scrapy is not installed. Install with: pip install scrapy")
        return 1
    
    # Show help if no URL provided
    if not args.url:
        parser.print_help()
        return 1
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Create crawler
    crawler = WebCrawler(
        start_url=args.url,
        max_depth=args.depth,
        max_pages=args.pages,
        follow_external_links=args.follow_external,
        respect_robots_txt=not args.ignore_robots,
        delay=args.delay,
        save_path=args.output
    )
    
    # Run crawler
    try:
        result = crawler.crawl()
        
        # Print results
        pages_crawled = result.get('pages_crawled', 0) if isinstance(result, dict) else result
        print(f"\nCrawl completed: {pages_crawled} pages")
        print(f"Data saved to: {args.output}")
        
        return 0
    except KeyboardInterrupt:
        print("\nCrawl interrupted")
        return 1
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 