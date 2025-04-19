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
                "url_frontier": [],
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
            
            # Update global metadata - always include in crawled_urls
            self.metadata["crawled_urls"][url] = {
                "last_visit": datetime.now().isoformat(),
                "depth": depth,
                "hash": url_hash,
                "links": links,
                "text_length": len(text_content)
            }
            
            # Save metadata after each page
            try:
                # Use a temporary file to avoid corruption if interrupted
                temp_metadata_file = f"{self.metadata_file}.tmp"
                with open(temp_metadata_file, 'w') as f:
                    json.dump(self.metadata, f, indent=2)
                # Then rename to the actual file
                os.replace(temp_metadata_file, self.metadata_file)
            except Exception as e:
                logger.error(f"Error saving metadata: {e}")
            
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
    save_path, 
    max_depth=2, 
    max_pages=100, 
    follow_external_links=False,
    respect_robots_txt=True,
    user_agent=None,
    delay=0.0,
    additional_settings=None,
    save_html=True,
    generate_graph=False,
    graph_type="page"
):
    """
    Perform a web crawl using Scrapy for efficient parallel processing.
    
    Args:
        start_url: URL to start crawling from
        save_path: Directory to save crawled data
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
        follow_external_links: Whether to follow links to external domains
        respect_robots_txt: Whether to respect robots.txt
        user_agent: User agent string for crawler
        delay: Delay between requests in seconds
        additional_settings: Dictionary of additional Scrapy settings
        save_html: Whether to save HTML content
        generate_graph: Whether to generate a graph visualization
        graph_type: Type of graph to generate (page, domain, interactive, or tree)
        
    Returns:
        dict: Statistics about the crawl including pages_crawled and graph_file path
    """
    if not SCRAPY_AVAILABLE:
        logger.error("Scrapy is not installed. Please install it with: pip install scrapy")
        return {"error": "Scrapy not installed", "pages_crawled": 0}
    
    # Record the start time
    start_time = time.time()
    
    # Create a crawler process
    process = CrawlerProcess(settings={
        'USER_AGENT': user_agent or 'vibe-scraping (+https://github.com/yourusername/vibe-scraping)',
        'ROBOTSTXT_OBEY': respect_robots_txt,
        'DOWNLOAD_DELAY': delay,
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': max(2, 8 // 2),  # Balance per domain
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
        follow_subdomains=follow_external_links,
        respect_robots=respect_robots_txt,
        url_pattern=None,
        save_path=save_path
    )
    
    # Run the crawler
    process.start()  # This will block until the crawling is finished
    
    # Record end time and calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    # Load the stats
    try:
        with open(os.path.join(save_path, "crawl_stats.json"), 'r') as f:
            stats = json.load(f)
    except Exception as e:
        logger.error(f"Error loading stats: {str(e)}")
        stats = {
            "pages_crawled": 0,
            "error": str(e)
        }
    
    # Load metadata
    metadata_file = os.path.join(save_path, "metadata.json")
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {str(e)}")
        metadata = {
            "crawled_urls": {},
            "start_url": start_url
        }
    
    # Find all URL files in the save directory to recover any missed URLs
    url_hashes = {}
    for entry in os.listdir(save_path):
        entry_path = os.path.join(save_path, entry)
        if os.path.isdir(entry_path):
            # This might be a URL directory
            meta_file = os.path.join(entry_path, "metadata.json")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, 'r') as f:
                        page_meta = json.load(f)
                        url = page_meta.get("url")
                        if url:
                            url_hashes[url] = entry  # Map URL to hash directory
                except Exception as e:
                    logger.warning(f"Error loading page metadata: {str(e)}")
    
    # Add missing URLs to metadata
    pages_crawled = stats.get("pages_crawled", 0)
    existing_urls = set(metadata.get("crawled_urls", {}).keys())
    missing_urls = set(url_hashes.keys()) - existing_urls
    
    # Ensure crawled_urls exists in metadata
    if "crawled_urls" not in metadata:
        metadata["crawled_urls"] = {}
    
    # Add any missing URLs to metadata
    for url in missing_urls:
        url_hash = url_hashes[url]
        meta_file = os.path.join(save_path, url_hash, "metadata.json")
        try:
            with open(meta_file, 'r') as f:
                page_meta = json.load(f)
                metadata["crawled_urls"][url] = {
                    "last_visit": page_meta.get("crawl_time", datetime.now().isoformat()),
                    "depth": page_meta.get("depth", 0),
                    "hash": url_hash,
                    "links": page_meta.get("links", []),
                    "text_length": page_meta.get("text_length", 0)
                }
        except Exception as e:
            logger.warning(f"Error adding URL to metadata: {str(e)}")
            # Add a minimal entry
            metadata["crawled_urls"][url] = {
                "last_visit": datetime.now().isoformat(),
                "depth": 0,
                "hash": url_hash,
                "links": [],
                "text_length": 0
            }
    
    # Update crawl_stats in metadata
    if "crawl_stats" not in metadata:
        metadata["crawl_stats"] = {}
    
    # Determine the actual number of pages crawled
    urls_in_metadata = len(metadata.get("crawled_urls", {}))
    
    # Use the higher count between stats and metadata
    final_count = max(pages_crawled, urls_in_metadata)
    
    # If there's a significant discrepancy, log it
    if abs(pages_crawled - urls_in_metadata) > 1:
        logger.warning(f"Scrapy counted {pages_crawled} pages but metadata has {urls_in_metadata} URLs")
    
    # Update the crawl_stats in metadata
    metadata["crawl_stats"].update({
        "start_url": start_url,
        "max_depth": max_depth,
        "max_pages": max_pages,
        "pages_crawled": final_count,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "use_scrapy": True,
        "respect_robots_txt": respect_robots_txt
    })
    
    # Count unique domains
    domains = set()
    for url in metadata.get("crawled_urls", {}).keys():
        parsed = urlparse(url)
        domains.add(parsed.netloc)
    metadata["crawl_stats"]["domains_count"] = len(domains)
    metadata["crawl_stats"]["domains"] = list(domains)
    
    # Calculate max depth actually reached
    max_depth_reached = 0
    for url, data in metadata.get("crawled_urls", {}).items():
        depth = data.get("depth", 0)
        if isinstance(depth, (int, float)):
            max_depth_reached = max(max_depth_reached, depth)
    metadata["crawl_stats"]["max_depth_reached"] = max_depth_reached
    
    # Save the updated metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Generate graph if requested
    if generate_graph and stats.get("pages_crawled", 0) > 0:
        try:
            from .visualizer import (
                generate_crawl_graph, 
                generate_domain_graph, 
                create_dynamic_graph,
                create_tree_visualization
            )
            
            graph_path = None
            if graph_type == "tree":
                # Create a special case for tree visualization to ensure start_url is properly included
                try:
                    # First load the metadata
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Make sure the start URL is properly recorded in the metadata
                    if "crawled_urls" in metadata:
                        # Ensure start_url is present in the crawled_urls
                        if start_url not in metadata["crawled_urls"]:
                            # Add start URL to crawled_urls if missing
                            metadata["crawled_urls"][start_url] = {
                                "last_visit": datetime.now().isoformat(),
                                "depth": 0,
                                "hash": hashlib.md5(start_url.encode()).hexdigest(),
                                "links": list(metadata["crawled_urls"].keys())[:10],  # Link to first 10 pages
                                "text_length": 0
                            }
                            
                            # Save updated metadata
                            with open(metadata_file, 'w') as f:
                                json.dump(metadata, f, indent=2)
                    
                    # Now create the tree visualization
                    graph_path = create_tree_visualization(save_path)
                except Exception as e:
                    logger.error(f"Error in tree visualization: {str(e)}")
                    graph_path = None
            elif graph_type == "page":
                graph_path = generate_crawl_graph(
                    save_path, 
                    title=f"Web Crawl Graph - {start_url}"
                )
            elif graph_type == "domain":
                graph_path = generate_domain_graph(
                    save_path,
                    title=f"Domain Graph - {start_url}"
                )
            elif graph_type == "interactive":
                graph_path = create_dynamic_graph(save_path)
            
            if graph_path:
                stats["graph_file"] = graph_path
        except ImportError:
            logger.warning("Could not import visualization modules. Make sure networkx and matplotlib are installed.")
        except Exception as e:
            logger.error(f"Error generating graph: {str(e)}")
    
    return stats 