"""
Streamlined web crawler focusing exclusively on deep Scrapy-based crawling.

This module provides a simplified web crawler that:
1. Uses Scrapy for efficient and fast crawling
2. Focuses on deep crawling functionality without extra features
3. Respects robots.txt and implements polite crawling
"""

import os
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebCrawler:
    """
    A streamlined web crawler focusing exclusively on deep Scrapy-based crawling.
    
    Args:
        start_url (str): The URL to start crawling from
        max_depth (int, optional): Maximum depth to crawl. Defaults to 5.
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 1000.
        follow_external_links (bool, optional): Whether to follow links to external domains. Defaults to False.
        respect_robots_txt (bool, optional): Whether to respect robots.txt. Defaults to True.
        user_agent (str, optional): User agent to use for requests. Defaults to None.
        delay (float, optional): Delay between requests in seconds. Defaults to 0.1.
        save_path (str, optional): Path to save crawled data. Defaults to "./crawl_data".
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
        save_path="./crawl_data",
    ):
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.follow_external_links = follow_external_links
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent
        self.delay = delay
        self.save_path = save_path
        
        # Ensure the save path exists
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
            
        # Set up URL filters
        self.domain = urlparse(start_url).netloc
    
    def crawl(self):
        """
        Start the crawling process using Scrapy.
        
        Returns:
            dict or int: Information about the crawl, including pages crawled
        """
        logger.info(f"Starting Scrapy crawl from {self.start_url}")
        try:
            from vibe_scraping.scrapy_adapter import crawl_with_scrapy
            
            return crawl_with_scrapy(
                start_url=self.start_url,
                save_path=self.save_path,
                max_depth=self.max_depth,
                max_pages=self.max_pages,
                follow_external_links=self.follow_external_links,
                respect_robots_txt=self.respect_robots_txt,
                user_agent=self.user_agent,
                delay=self.delay,
                save_html=True,
                generate_graph=False,
                graph_type=None
            )
        except ImportError as e:
            logger.error("Scrapy is not installed. Please install with: pip install scrapy")
            raise e
        except Exception as e:
            logger.error(f"Error using Scrapy: {str(e)}")
            raise e

def crawl_site(
    start_url,
    output_dir="crawled_data",
    max_depth=5,
    max_pages=1000,
    delay=0.1,
    follow_external_links=False,
    respect_robots_txt=True,
    user_agent=None
):
    """
    Simplified helper function to crawl a website using Scrapy.
    
    Args:
        start_url (str): URL to start crawling from
        output_dir (str): Directory to save crawled data
        max_depth (int): Maximum depth to crawl
        max_pages (int): Maximum number of pages to crawl
        delay (float): Delay between requests in seconds
        follow_external_links (bool): Whether to follow external links
        respect_robots_txt (bool): Whether to respect robots.txt
        user_agent (str): User agent string to use
        
    Returns:
        dict or int: Crawl results including pages crawled
    """
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        follow_external_links=follow_external_links,
        respect_robots_txt=respect_robots_txt,
        user_agent=user_agent,
        delay=delay,
        save_path=output_dir
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
        user_agent=None
    )
    
    # Print stats
    print(f"\nCrawl completed:")
    print(f"Pages crawled: {stats['pages_crawled']}")
    print(f"Max depth: {stats['max_depth']}")
    print(f"Start URL: {stats['start_url']}")
    print(f"Output directory: {args.output}") 