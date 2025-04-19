#!/usr/bin/env python3
"""
Command line interface for vibe-scraping deep crawling functionality.
"""

import argparse
import os
import sys
from vibe_scraping.crawler import WebCrawler, crawl_site
from vibe_scraping import SCRAPY_AVAILABLE, __version__

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Vibe Scraping - Deep web crawler using Scrapy")
    
    # Add version info
    parser.add_argument('--version', action='version', version=f'vibe-scraping {__version__}')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Crawl command
    crawl_parser = subparsers.add_parser('crawl', help='Crawl a website deeply')
    crawl_parser.add_argument('url', help='URL to start crawling from')
    crawl_parser.add_argument('--output', '-o', default='./crawled_data', 
                              help='Directory to save crawled data (default: ./crawled_data)')
    crawl_parser.add_argument('--depth', '-d', type=int, default=5, 
                              help='Maximum crawl depth (default: 5)')
    crawl_parser.add_argument('--pages', '-p', type=int, default=1000, 
                              help='Maximum pages to crawl (default: 1000)')
    crawl_parser.add_argument('--delay', type=float, default=0.1, 
                              help='Delay between requests in seconds (default: 0.1)')
    crawl_parser.add_argument('--follow-external', action='store_true',
                              help='Follow links to external domains (default: False)')
    crawl_parser.add_argument('--ignore-robots', action='store_true',
                              help='Ignore robots.txt (default: False)')
    crawl_parser.add_argument('--user-agent', 
                              default='vibe-scraper (+https://github.com/yourusername/vibe-scraping)',
                              help='User agent to use for requests')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if Scrapy is installed')
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # Handle commands
    if args.command == 'crawl':
        if not SCRAPY_AVAILABLE:
            print("Error: Scrapy is not installed. Please install with: pip install scrapy")
            sys.exit(1)
            
        handle_crawl_command(args)
    elif args.command == 'check':
        handle_check_command()
    else:
        parser.print_help()

def handle_crawl_command(args):
    """Handle the crawl command."""
    print(f"Starting deep crawl of {args.url}")
    print(f"Max depth: {args.depth}, Max pages: {args.pages}")
    print(f"Output directory: {args.output}")
    print(f"Follow external links: {args.follow_external}")
    print(f"Respect robots.txt: {not args.ignore_robots}")
    print(f"Delay between requests: {args.delay}s")
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Create crawler instance
    crawler = WebCrawler(
        start_url=args.url,
        max_depth=args.depth,
        max_pages=args.pages,
        follow_external_links=args.follow_external,
        respect_robots_txt=not args.ignore_robots,
        user_agent=args.user_agent,
        delay=args.delay,
        save_path=args.output
    )
    
    # Start crawling
    print("\nStarting crawler...\n")
    try:
        result = crawler.crawl()
        
        # Print results
        if isinstance(result, dict):
            pages_crawled = result.get('pages_crawled', 0)
        else:
            pages_crawled = result
            
        print(f"\nCrawl completed!")
        print(f"Pages crawled: {pages_crawled}")
        print(f"Data saved to: {args.output}")
        
        # Print detailed information if available
        if isinstance(result, dict):
            print("\nCrawl details:")
            for key, value in result.items():
                if key != 'pages_crawled':  # Already printed above
                    print(f"{key}: {value}")
    
    except KeyboardInterrupt:
        print("\nCrawl interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during crawl: {str(e)}")
        sys.exit(1)

def handle_check_command():
    """Check if Scrapy is installed."""
    if SCRAPY_AVAILABLE:
        import scrapy
        print(f"Scrapy is installed (version {scrapy.__version__})")
        print("You're ready to run deep crawls!")
    else:
        print("Scrapy is NOT installed")
        print("Please install it with: pip install scrapy")

if __name__ == '__main__':
    main() 