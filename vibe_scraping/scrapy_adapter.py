"""
Scrapy integration for vibe-scraping.

This module provides a Scrapy-based crawler implementation for faster and more efficient web scraping,
while maintaining compatibility with the existing vibe-scraping API.
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
    logger.warning("Scrapy is not installed. Fast crawling will not be available. Install with: pip install scrapy")

# Only define the spider class if Scrapy is available
if SCRAPY_AVAILABLE:
    class VibeCrawlSpider(CrawlSpider):
        """Scrapy spider implementing the vibe-scraping crawler logic."""
        
        name = "vibe_scraper"
        
        def __init__(self, *args, **kwargs):
            """Initialize the spider with custom parameters."""
            # Extract parameters from kwargs
            self.start_url = kwargs.pop('start_url', None)
            self.max_depth = kwargs.pop('max_depth', 2)
            self.follow_subdomains = kwargs.pop('follow_subdomains', False)
            self.respect_robots = kwargs.pop('respect_robots', True)
            self.url_pattern = kwargs.pop('url_pattern', None)
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
            rules = []
            
            if self.url_pattern:
                # If URL pattern is specified, only follow links that match it
                rules.append(
                    Rule(
                        LinkExtractor(
                            allow=[self.url_pattern], 
                            deny_extensions=[],
                            unique=True
                        ),
                        callback='parse_item',
                        follow=True,
                        process_links='process_links',
                        cb_kwargs={'depth': 1}
                    )
                )
            else:
                # Otherwise, follow all links within the allowed domains
                rules.append(
                    Rule(
                        LinkExtractor(
                            allow=[], 
                            deny_extensions=[],
                            unique=True
                        ),
                        callback='parse_item',
                        follow=True,
                        process_links='process_links',
                        cb_kwargs={'depth': 1}
                    )
                )
            
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
                "url_frontier": [],
                "pages_crawled": 0,
                "start_url": self.start_url
            }
        
        def _update_metadata(self):
            """Update and save metadata after crawling."""
            self.metadata["last_crawl"] = datetime.now().isoformat()
            self.metadata["pages_crawled"] = len(self.metadata["crawled_urls"])
            self.metadata["start_url"] = self.start_url
            
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        
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
                    url = link.url
                    url = urldefrag(url)[0]  # Remove fragments
                    
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
            
            # Extract text content (simplified)
            text_content = ' '.join(response.xpath('//body//text()').getall())
            
            # Save text content
            with open(os.path.join(page_dir, "text.txt"), 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Extract links
            links = [link for link in response.css('a::attr(href)').getall()]
            
            # Save page metadata
            page_metadata = {
                "url": url,
                "crawl_time": datetime.now().isoformat(),
                "depth": depth,
                "links": links,
                "text_length": len(text_content),
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
                "text_length": len(text_content)
            }
            
            # Update statistics
            self.stats['pages_crawled'] += 1
            
            # Follow links recursively if within depth limit
            if depth < self.max_depth:
                for link in links:
                    # Skip mailto: links and other non-HTTP schemes
                    if link.startswith(('mailto:', 'tel:', 'fax:', 'javascript:')) or ':' in link and not link.startswith(('http://', 'https://')):
                        continue
                    
                    try:
                        full_url = response.urljoin(link)
                        yield scrapy.Request(
                            full_url, 
                            callback=self.parse_item,
                            cb_kwargs={'depth': depth + 1}
                        )
                    except ValueError as e:
                        logger.warning(f"Skipping invalid URL: {link} - {str(e)}")
                        continue
        
        def closed(self, reason):
            """Called when the spider closes."""
            # Update metadata
            self._update_metadata()
            
            # Update stats
            self.stats['end_time'] = datetime.now().isoformat()
            self.stats['start_url'] = self.start_url  # Ensure start_url is in stats
            
            # Save stats to a file
            stats_file = os.path.join(self.save_path, "crawl_stats.json")
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
            logger.info(f"Crawl completed. Visited {self.stats['pages_crawled']} pages.")


def crawl_with_scrapy(
    start_url,
    output_dir="crawled_data",
    max_depth=2,
    max_pages=100,
    delay=1.0,  # For politeness
    follow_subdomains=False,
    url_filter=None,
    respect_robots=True,
    generate_graph=False,
    graph_type="page",
    graph_title=None,
    concurrent_requests=8  # Added parameter for concurrent requests
):
    """
    Crawl a website using Scrapy for faster performance.
    
    Args:
        start_url: URL to start crawling from
        output_dir: Directory to save the crawled data
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        follow_subdomains: Whether to follow links to subdomains
        url_filter: Regular expression pattern for URLs to follow
        respect_robots: Whether to respect robots.txt
        generate_graph: Whether to generate a graph visualization
        graph_type: Type of graph to generate
        graph_title: Custom title for the graph
        concurrent_requests: Number of concurrent requests
        
    Returns:
        Dictionary with crawl statistics
    """
    if not SCRAPY_AVAILABLE:
        logger.error("Scrapy is not installed. Please install it with: pip install scrapy")
        return {"error": "Scrapy not installed", "pages_crawled": 0}
    
    # Create a crawler process
    process = CrawlerProcess(settings={
        'USER_AGENT': 'vibe-scraping (+https://github.com/yourusername/vibe-scraping)',
        'ROBOTSTXT_OBEY': respect_robots,
        'DOWNLOAD_DELAY': delay,
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS': concurrent_requests,
        'CONCURRENT_REQUESTS_PER_DOMAIN': max(2, concurrent_requests // 2),  # Balance per domain
        'DEPTH_LIMIT': max_depth,
        'CLOSESPIDER_PAGECOUNT': max_pages,
        'LOG_LEVEL': 'INFO',
        # URL handling settings
        'URLLENGTH_LIMIT': 2000,  # Limit URL length to avoid problems
        'AJAXCRAWL_ENABLED': True,  # Handle AJAX crawling
        # Skip non-http schemes in LinkExtractor
        'LINK_EXTRACTOR_RESTRICT_SCHEMES': ['http', 'https']
    })
    
    # Start the crawl
    process.crawl(
        VibeCrawlSpider,
        start_url=start_url,
        max_depth=max_depth,
        follow_subdomains=follow_subdomains,
        respect_robots=respect_robots,
        url_pattern=url_filter,
        save_path=output_dir
    )
    
    # Run the crawler
    process.start()  # This will block until the crawling is finished
    
    # Load the stats
    try:
        with open(os.path.join(output_dir, "crawl_stats.json"), 'r') as f:
            stats = json.load(f)
    except Exception as e:
        logger.error(f"Error loading stats: {str(e)}")
        stats = {
            "pages_crawled": 0,
            "error": str(e)
        }
    
    # Generate graph if requested
    if generate_graph and stats.get("pages_crawled", 0) > 0:
        try:
            from .visualizer import (
                generate_crawl_graph, 
                generate_domain_graph, 
                create_dynamic_graph
            )
            
            graph_path = None
            if graph_type == "page":
                graph_path = generate_crawl_graph(
                    output_dir, 
                    title=graph_title or f"Web Crawl Graph - {start_url}"
                )
            elif graph_type == "domain":
                graph_path = generate_domain_graph(
                    output_dir,
                    title=graph_title or f"Domain Graph - {start_url}"
                )
            elif graph_type == "interactive":
                graph_path = create_dynamic_graph(output_dir)
            
            if graph_path:
                stats["graph_file"] = graph_path
        except ImportError:
            logger.warning("Could not import visualization modules. Make sure networkx and matplotlib are installed.")
        except Exception as e:
            logger.error(f"Error generating graph: {str(e)}")
    
    return stats 