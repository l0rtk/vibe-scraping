"""
Streamlined web crawler using Scrapy for deep crawling.
"""

import os
from urllib.parse import urlparse

from vibe_scraping.scrapy_adapter import crawl_with_scrapy, SCRAPY_AVAILABLE

class WebCrawler:
    """
    A streamlined web crawler using Scrapy.
    """
    
    def __init__(
        self,
        start_url,
        max_depth=5,
        max_pages=1000,
        follow_external_links=False,
        respect_robots_txt=True,
        user_agent=None,
        delay=0.1,
        save_path="./data/crawl_data",
        additional_settings=None,
        force_fresh_crawl=True
    ):
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.follow_external_links = follow_external_links
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent
        self.delay = delay
        self.save_path = save_path
        self.additional_settings = additional_settings or {}
        self.force_fresh_crawl = force_fresh_crawl
        
        os.makedirs(self.save_path, exist_ok=True)
        self.domain = urlparse(start_url).netloc
    
    def crawl(self):
        """Start crawling using Scrapy."""
        if not SCRAPY_AVAILABLE:
            raise ImportError("Scrapy is not installed. Install with: pip install scrapy")
            
        return crawl_with_scrapy(
            start_url=self.start_url,
            save_path=self.save_path,
            max_depth=self.max_depth,
            max_pages=self.max_pages,
            follow_external_links=self.follow_external_links,
            respect_robots_txt=self.respect_robots_txt,
            user_agent=self.user_agent,
            delay=self.delay,
            additional_settings=self.additional_settings,
            enable_caching=False,  # Disable caching by default
            force_recrawl=self.force_fresh_crawl
        )

def crawl_site(start_url, output_dir="crawled_data", max_depth=5, max_pages=1000, 
               delay=0.1, follow_external_links=False, respect_robots_txt=True, user_agent=None,
               force_fresh_crawl=True):
    """Convenience function to crawl a website."""
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        follow_external_links=follow_external_links,
        respect_robots_txt=respect_robots_txt,
        user_agent=user_agent,
        delay=delay,
        save_path=output_dir,
        force_fresh_crawl=force_fresh_crawl
    )
    
    return crawler.crawl()


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Web crawler for collecting pages from websites")
    parser.add_argument("url", help="URL to start crawling from")
    parser.add_argument("--output", default="crawled_data", help="Directory to save the crawled data")
    parser.add_argument("--depth", type=int, default=5, help="Maximum crawl depth")
    parser.add_argument("--pages", type=int, default=1000, help="Maximum number of pages to crawl")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests in seconds")
    parser.add_argument("--subdomains", action="store_true", help="Follow links to subdomains")
    parser.add_argument("--fresh", action="store_true", help="Force a fresh crawl ignoring cache")
    
    args = parser.parse_args()
    
    # Crawl the site
    stats = crawl_site(
        start_url=args.url,
        output_dir=args.output,
        max_depth=args.depth,
        max_pages=args.pages,
        delay=args.delay,
        follow_external_links=args.subdomains,
        respect_robots_txt=True,
        user_agent=None,
        force_fresh_crawl=args.fresh
    )
    
    # Print stats
    print(f"\nCrawl completed:")
    print(f"Pages crawled: {stats['pages_crawled']}")
    print(f"Max depth: {stats['max_depth']}")
    print(f"Start URL: {stats['start_url']}")
    print(f"Output directory: {args.output}") 