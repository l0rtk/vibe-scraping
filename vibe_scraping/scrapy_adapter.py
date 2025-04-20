"""
Scrapy integration for vibe-scraping.

This module provides a Scrapy-based crawler implementation focused on deep web crawling.
"""

import os
import json
import logging
import time
from datetime import datetime
import hashlib
from urllib.parse import urlparse, urldefrag

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Scrapy-related modules
try:
    import scrapy
    from scrapy.crawler import CrawlerProcess
    from scrapy.spiders import CrawlSpider, Rule
    from scrapy.linkextractors import LinkExtractor
    from scrapy.exceptions import NotConfigured
    SCRAPY_AVAILABLE = True
except ImportError:
    SCRAPY_AVAILABLE = False
    logger.warning("Scrapy is not installed. Install with: pip install scrapy")

# Only define the spider class if Scrapy is available
if SCRAPY_AVAILABLE:
    class VibeCrawlSpider(CrawlSpider):
        """Scrapy spider for deep web crawling."""
        
        name = "vibe_scraper"
        
        def __init__(self, *args, **kwargs):
            """Initialize the spider with custom parameters."""
            # Extract parameters from kwargs
            self.start_url = kwargs.pop('start_url', None)
            self.max_depth = kwargs.pop('max_depth', 5)
            self.follow_subdomains = kwargs.pop('follow_subdomains', False)
            self.respect_robots = kwargs.pop('respect_robots', True)
            self.save_path = kwargs.pop('save_path', 'crawled_data')
            
            # Create a save directory if it doesn't exist
            os.makedirs(self.save_path, exist_ok=True)
            
            # Initialize metadata
            self.metadata_file = os.path.join(self.save_path, "metadata.json")
            self.metadata = self._load_metadata()
            
            # Setup the start URLs
            self.start_urls = [self.start_url] if self.start_url else []
            
            # Extract domain from start URL
            if self.start_url:
                parsed_url = urlparse(self.start_url)
                self.base_domain = parsed_url.netloc
                self.base_scheme = parsed_url.scheme
            
            # Define crawl rules
            allowed_domains = [self.base_domain] if not self.follow_subdomains else None
            
            # Create rules based on the parameters
            rules = [
                Rule(
                    LinkExtractor(allow=[], deny_extensions=[], unique=True),
                    callback='parse_item',
                    follow=True,
                    process_links='process_links',
                    cb_kwargs={'depth': 1}
                )
            ]
            
            # Set allowed domains
            if allowed_domains:
                self.allowed_domains = allowed_domains
            
            # Set rules
            self.rules = rules
            
            # Initialize statistics
            self.stats = {
                'pages_crawled': 0,
                'start_time': datetime.now().isoformat(),
                'start_url': self.start_url,
                'max_depth': self.max_depth
            }
            
            # Make sure crawled_urls exists in metadata
            if "crawled_urls" not in self.metadata:
                self.metadata["crawled_urls"] = {}
                
            # Initialize CrawlSpider
            super(VibeCrawlSpider, self).__init__(*args, **kwargs)
        
        def _load_metadata(self):
            """Load metadata from previous crawls if available."""
            try:
                if os.path.exists(self.metadata_file):
                    with open(self.metadata_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {str(e)}")
            
            # Initial metadata structure
            return {
                "last_crawl": None,
                "crawled_urls": {},
                "pages_crawled": 0,
                "start_url": self.start_url
            }
        
        def _update_metadata(self):
            """Update and save metadata after crawling."""
            self.metadata["last_crawl"] = datetime.now().isoformat()
            self.metadata["pages_crawled"] = len(self.metadata["crawled_urls"])
            self.metadata["start_url"] = self.start_url
            
            # Make sure crawl_stats exists in metadata
            if "crawl_stats" not in self.metadata:
                self.metadata["crawl_stats"] = {}
                
            # Update crawl stats
            self.metadata["crawl_stats"]["pages_crawled"] = self.stats['pages_crawled']
            self.metadata["crawl_stats"]["start_time"] = time.time() - (self.stats.get('elapsed_time_seconds', 0))
            self.metadata["crawl_stats"]["end_time"] = time.time()
            self.metadata["crawl_stats"]["duration"] = self.stats.get('elapsed_time_seconds', 0)
            self.metadata["crawl_stats"]["max_depth"] = self.max_depth
            self.metadata["crawl_stats"]["max_pages"] = self.crawler.settings.getint('CLOSESPIDER_PAGECOUNT')
            
            # Save to file
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        
        def parse_start_url(self, response):
            """Process the start URL."""
            return self.parse_item(response, depth=0)
        
        def process_links(self, links):
            """Process links to normalize URLs and apply depth limiting."""
            processed_links = []
            
            for link in links:
                # Skip non-HTTP links and problematic URLs
                if link.url.startswith(('mailto:', 'tel:', 'fax:', 'javascript:')) or \
                   (':' in link.url and not link.url.startswith(('http://', 'https://'))):
                    continue
                
                try:
                    # Normalize the URL
                    url = urldefrag(link.url)[0]  # Remove fragments
                    
                    # Remove trailing slashes for consistency
                    if url.endswith('/'):
                        url = url[:-1]
                    
                    # Update the link
                    link.url = url
                    processed_links.append(link)
                except Exception as e:
                    logger.warning(f"Error processing link {link.url}: {str(e)}")
            
            return processed_links
        
        def parse_item(self, response, depth=1):
            """Parse a crawled page and save its data."""
            # Check depth
            if depth > self.max_depth:
                return
            
            url = response.url
            logger.info(f"Crawling [{self.stats['pages_crawled'] + 1}]: {url} (depth {depth})")
            
            # Extract content
            html_content = response.body.decode('utf-8', errors='replace')
            
            # Create a hash of the URL for the file path
            url_hash = hashlib.md5(url.encode()).hexdigest()
            page_dir = os.path.join(self.save_path, url_hash)
            os.makedirs(page_dir, exist_ok=True)
            
            # Save the HTML content
            with open(os.path.join(page_dir, "page.html"), 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Extract links
            links = [link for link in response.css('a::attr(href)').getall()]
            
            # Save page metadata
            page_metadata = {
                "url": url,
                "crawl_time": datetime.now().isoformat(),
                "depth": depth,
                "links": links,
                "html_length": len(html_content)
            }
            
            with open(os.path.join(page_dir, "metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(page_metadata, f, indent=2)
            
            # Update global metadata
            self.metadata["crawled_urls"][url] = {
                "last_visit": datetime.now().isoformat(),
                "depth": depth,
                "hash": url_hash,
                "links": links,
                "html_length": len(html_content)
            }
            
            # Save metadata after each page
            try:
                self._update_metadata()
            except Exception as e:
                logger.warning(f"Error updating metadata: {str(e)}")
            
            # Update the statistics
            self.stats['pages_crawled'] += 1
            
            # Check if we need to follow links at this depth
            if depth < self.max_depth:
                # The CrawlSpider will handle following links based on the rules
                pass
            
            # Return item for the pipeline
            return {
                "url": url,
                "depth": depth,
                "links": links,
                "html_length": len(html_content)
            }
            
        def closed(self, reason):
            """Called when the crawler is closed."""
            # Update and save the metadata one last time
            try:
                self._update_metadata()
                logger.info(f"Crawl finished, processed {self.stats['pages_crawled']} pages")
            except Exception as e:
                logger.error(f"Error saving final metadata: {str(e)}")


def crawl_with_scrapy(
    start_url, 
    save_path, 
    max_depth=5, 
    max_pages=1000, 
    follow_external_links=False,
    respect_robots_txt=True,
    user_agent=None,
    delay=0.1,
    additional_settings=None,
    save_html=True,
    generate_graph=False,
    graph_type=None
):
    """
    Crawl a website using Scrapy.
    
    Args:
        start_url: URL to start crawling from
        save_path: Directory to save the crawled data
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
        follow_external_links: Whether to follow links to external domains
        respect_robots_txt: Whether to respect robots.txt
        user_agent: User agent to use for requests
        delay: Delay between requests in seconds
        additional_settings: Additional Scrapy settings
        save_html: Whether to save HTML content (always True in this version)
        generate_graph: Not used in this version
        graph_type: Not used in this version
        
    Returns:
        Dictionary with crawl statistics or int with pages crawled count
    """
    # Check if Scrapy is available
    if not SCRAPY_AVAILABLE:
        logger.error("Scrapy is not installed. Please install with: pip install scrapy")
        raise ImportError("Scrapy is not installed")
    
    # Create a directory for saving crawled data
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    # Set up a Scrapy project
    settings = {
        'USER_AGENT': user_agent or 'vibe-scraper (+https://github.com/l0rtk/vibe-scraping)',
        'ROBOTSTXT_OBEY': respect_robots_txt,
        'DOWNLOAD_DELAY': delay,
        'CLOSESPIDER_PAGECOUNT': max_pages,
        'DEPTH_LIMIT': max_depth,
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        'COOKIES_ENABLED': True,
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 43200,  # 12 hours
        'HTTPCACHE_DIR': 'httpcache',
        'HTTPCACHE_IGNORE_HTTP_CODES': [503, 504, 505, 500, 400, 401, 402, 403, 404],
        'HTTPCACHE_STORAGE': 'scrapy.extensions.httpcache.FilesystemCacheStorage',
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS': 16,  # Higher concurrency for faster crawling
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408]
    }
    
    # Update with additional settings if provided
    if additional_settings:
        settings.update(additional_settings)
    
    # Create a crawler process
    process = CrawlerProcess(settings)
    
    # Start the crawler
    process.crawl(
        VibeCrawlSpider,
        start_url=start_url,
        max_depth=max_depth,
        follow_subdomains=follow_external_links,
        respect_robots=respect_robots_txt,
        save_path=save_path
    )
    
    # Run the crawler and wait until it finishes
    process.start()
    
    # Load the metadata file to get statistics
    metadata_file = os.path.join(save_path, "metadata.json")
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Return a dictionary with crawl statistics
        return {
            'pages_crawled': metadata.get('pages_crawled', 0),
            'start_url': start_url,
            'max_depth': max_depth,
            'max_pages': max_pages,
            'save_path': save_path
        }
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        # Fallback to returning just the count or 0 if it couldn't be determined
        return metadata.get('pages_crawled', 0) if 'metadata' in locals() else 0 