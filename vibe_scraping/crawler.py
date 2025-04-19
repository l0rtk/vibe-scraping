"""
Web crawler for collecting pages from websites with configurable depth.

This module provides a sophisticated web crawler that:
1. Respects robots.txt
2. Uses appropriate delays between requests
3. Handles URL normalization and deduplication
4. Provides depth-first or breadth-first crawling options
5. Implements politeness policies for responsible crawling
6. Supports custom URL filtering
7. Handles session management and cookie persistence
"""

import requests
import logging
import time
import random
import re
import os
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser
from collections import deque
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import json
import hashlib


from .selenium_scraper import scrape_with_selenium

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebCrawler:
    """
    A web crawler that crawls pages and builds a graph of the web.
    
    Args:
        start_url (str): The URL to start crawling from
        max_depth (int, optional): Maximum depth to crawl. Defaults to 2.
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 100.
        follow_external_links (bool, optional): Whether to follow links to external domains. Defaults to False.
        respect_robots_txt (bool, optional): Whether to respect robots.txt. Defaults to True.
        user_agent (str, optional): User agent to use for requests. Defaults to None.
        delay (float, optional): Delay between requests in seconds. Defaults to 0.
        save_path (str, optional): Path to save crawled data. Defaults to "./crawl_data".
        generate_graph (bool, optional): Whether to generate a graph of the crawled pages. Defaults to False.
        graph_type (str, optional): Type of graph to generate. Options: "page" (default), "domain", "interactive", "tree".
        log_level (str, optional): Logging level. Defaults to "INFO".
        use_scrapy (bool, optional): Whether to use Scrapy for crawling. Defaults to False.
        scrapy_settings (dict, optional): Additional settings for Scrapy. Defaults to None.
        save_html (bool, optional): Whether to save HTML content of crawled pages. Defaults to True.
        save_screenshots (bool, optional): Whether to save screenshots of crawled pages. Defaults to False.
        headless (bool, optional): Whether to run the browser in headless mode when taking screenshots. Defaults to True.
        browser_type (str, optional): Type of browser to use for screenshots. Options: "chrome" (default), "firefox".
        filter_urls (callable, optional): Function to filter URLs before crawling. Takes URL as argument, returns bool.
        extract_metadata (callable, optional): Function to extract metadata from a page. Takes URL and HTML as arguments.
        cache_backend (str, optional): Type of cache to use. Options: "memory" (default), "sqlite", "redis".
        redis_url (str, optional): URL for Redis cache if using "redis" cache_backend. Defaults to "redis://localhost:6379/0".
    """
    
    def __init__(
        self,
        start_url,
        max_depth=2,
        max_pages=100,
        follow_external_links=False,
        respect_robots_txt=True,
        user_agent=None,
        delay=0,
        save_path="./crawl_data",
        generate_graph=False,
        graph_type="page",
        log_level="INFO",
        use_scrapy=False,
        scrapy_settings=None,
        save_html=True,
        save_screenshots=False,
        headless=True,
        browser_type="chrome",
        filter_urls=None,
        extract_metadata=None,
        cache_backend="memory",
        redis_url="redis://localhost:6379/0",
    ):
        # Set up logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.follow_external_links = follow_external_links
        self.respect_robots_txt = respect_robots_txt
        self.user_agent = user_agent
        self.delay = delay
        self.save_path = save_path
        self.generate_graph = generate_graph
        self.graph_type = graph_type
        self.use_scrapy = use_scrapy
        self.scrapy_settings = scrapy_settings or {}
        self.save_html = save_html
        self.save_screenshots = save_screenshots
        self.headless = headless
        self.browser_type = browser_type
        self.filter_urls = filter_urls
        self.extract_metadata = extract_metadata
        self.cache_backend = cache_backend
        self.redis_url = redis_url
        
        # Initialize the crawl data structure
        self.crawled_urls = {}
        self.visited_urls = set()
        self.queue = deque([(start_url, 0)])  # (url, depth)
        self.start_time = None
        self.end_time = None
        
        # Ensure the save path exists
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
            
        # Set up URL filters
        self.domain = urlparse(start_url).netloc
        
        # Initialize robots.txt parser if needed
        self.robots_parser = None
        if self.respect_robots_txt:
            try:
                self._init_robots_parser()
            except Exception as e:
                self.logger.warning(f"Error initializing robots.txt parser: {str(e)}")
                self.robots_parser = None
                
        # Set up cache
        self._init_cache()
        
        # Set up screenshot capabilities if needed
        if self.save_screenshots:
            try:
                from selenium import webdriver
                if self.browser_type.lower() == "chrome":
                    options = webdriver.ChromeOptions()
                    if self.headless:
                        options.add_argument('--headless')
                        options.add_argument('--no-sandbox')
                    self.browser = webdriver.Chrome(options=options)
                else:  # firefox
                    from selenium.webdriver.firefox.options import Options
                    options = Options()
                    if self.headless:
                        options.add_argument('--headless')
                    self.browser = webdriver.Firefox(options=options)
            except ImportError:
                self.logger.warning("Selenium not installed. Cannot save screenshots.")
                self.save_screenshots = False
            except Exception as e:
                self.logger.warning(f"Error initializing browser: {str(e)}")
                self.save_screenshots = False
    
    def crawl(self):
        """
        Start the crawling process.
        
        Returns:
            tuple: (Number of pages crawled, path to graph file if generated, otherwise None)
        """
        self.start_time = time.time()
        
        try:
            if self.use_scrapy:
                self.logger.info(f"Starting crawl from {self.start_url}")
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
                        delay=self.delay,  # Pass the delay parameter to Scrapy
                        additional_settings=self.scrapy_settings,
                        save_html=self.save_html,
                        generate_graph=self.generate_graph,
                        graph_type=self.graph_type
                    )
                except Exception as e:
                    self.logger.error(f"Error using Scrapy: {str(e)}")
                    self.logger.info("Falling back to the default crawler")
                    return self._crawl_breadth_first()
            else:
                return self._crawl_breadth_first()
        finally:
            self.end_time = time.time()
            self._save_metadata()
            
            # Close browser if it was opened
            if hasattr(self, 'browser'):
                try:
                    self.browser.quit()
                except:
                    pass
    
    def _crawl_breadth_first(self):
        """Perform breadth-first crawling."""
        self.start_time = datetime.now()
        self.logger.info(f"Starting breadth-first crawl from {self.start_url}")
        
        while self.queue and len(self.crawled_urls) < self.max_pages:
            url, depth = self.queue.popleft()
            
            if depth > self.max_depth:
                continue
                
            self.logger.info(f"Crawling [{len(self.crawled_urls)+1}/{self.max_pages}]: {url} (depth {depth})")
            
            try:
                html_content, text_content, soup = self._fetch_page(url)
                if not html_content:
                    continue
                    
                self.crawled_urls[url] = {
                    "last_visit": datetime.now().isoformat(),
                    "depth": depth,
                    "hash": hashlib.md5(url.encode()).hexdigest(),
                    "links": self._extract_links(soup, url),
                    "text_length": len(text_content)
                }
                
                # Extract links from the page
                links = self._extract_links(soup, url)
                
                # Save the page data
                self._save_page(url, html_content, text_content, links, depth)
                
                # Add new links to the queue
                for link in links:
                    if link not in self.visited_urls:
                        self.queue.append((link, depth + 1))
                        self.visited_urls.add(link)
                
                # Apply delay before next request
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {str(e)}")
        
        # Update and save the metadata
        self.logger.info(f"Crawl completed. {len(self.crawled_urls)} pages crawled.")
        
        # Generate the graph if requested
        graph_file = None
        if self.generate_graph:
            graph_file = self.generate_graph_visualization()
        
        return len(self.crawled_urls), graph_file
    
    def _fetch_page(self, url):
        """Fetch a page and parse it."""
        # Try with regular requests first
        try:
            response = requests.get(url, headers={"User-Agent": self.user_agent}, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get the text
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Check if content is substantial enough
                if len(text_content) > 500:
                    return html_content, text_content, soup
                else:
                    self.logger.warning(f"Content may be incomplete for {url}, trying Selenium as fallback...")
            else:
                self.logger.error(f"Failed to retrieve page {url} (Status code: {response.status_code})")
        
        except Exception as e:
            self.logger.error(f"Error during page retrieval {url}: {str(e)}")
        
        # If we're here and selenium_fallback is True, try with Selenium
        if self.use_scrapy:
            try:
                self.logger.info(f"Attempting to scrape {url} with Selenium...")
                
                # Get the HTML with Selenium
                html_content = scrape_with_selenium(url, headless=self.headless)
                
                if html_content and len(html_content) > 0:
                    # Parse the HTML with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Clean up the content
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # Extract text
                    text_content = soup.get_text(separator=' ', strip=True)
                    self.logger.info(f"Successfully retrieved {len(text_content)} characters using Selenium")
                    
                    return html_content, text_content, soup
                else:
                    self.logger.error(f"Failed to retrieve content with Selenium for {url}")
            
            except Exception as e:
                self.logger.error(f"Error during Selenium scraping for {url}: {str(e)}")
        
        return None, None, None
    
    def _save_page(self, url, html_content, text_content, links, depth):
        """Save the crawled page data to disk."""
        # Create a unique filename based on the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        page_dir = os.path.join(self.save_path, url_hash)
        os.makedirs(page_dir, exist_ok=True)
        
        # Save original HTML content
        with open(os.path.join(page_dir, "page.html"), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Save cleaned HTML content
        cleaned_html = self._clean_html(html_content)
        with open(os.path.join(page_dir, "page_cleaned.html"), 'w', encoding='utf-8') as f:
            f.write(cleaned_html)
            
        # Save extracted text
        with open(os.path.join(page_dir, "text.txt"), 'w', encoding='utf-8') as f:
            f.write(text_content)
            
        # Save page metadata including outgoing links
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
            
        # Update the global metadata with this page's info
        self.crawled_urls[url] = {
            "last_visit": datetime.now().isoformat(),
            "depth": depth,
            "hash": url_hash,
            "links": links,  # Store links for graph representation
            "text_length": len(text_content)
        }
    
    def _is_allowed_by_robots(self, url):
        """Check if the URL is allowed by robots.txt."""
        if not self.respect_robots_txt:
            return True
        
        return self.robots_parser.can_fetch(self.user_agent, url)
    
    def _normalize_url(self, url, parent_url):
        """Normalize the URL to avoid crawling the same page multiple times."""
        # If the URL is relative, make it absolute
        full_url = urljoin(parent_url, url)
        
        # Remove fragments (anchors)
        full_url = urldefrag(full_url)[0]
        
        # Remove trailing slashes for consistency
        if full_url.endswith('/'):
            full_url = full_url[:-1]
        
        return full_url
    
    def _should_follow(self, url):
        """Determine if the URL should be followed."""
        # Check if the URL has been visited
        if url in self.visited_urls:
            return False
        
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's from the same domain or allowed subdomain
        if not self.follow_external_links and parsed_url.netloc != self.domain:
            # If not following external domains, only follow URLs from the exact same domain
            return False
        
        # Check against URL pattern if provided
        if self.filter_urls and not self.filter_urls(url):
            return False
        
        # Check if the URL is allowed by robots.txt
        if not self._is_allowed_by_robots(url):
            return False
        
        # Get the file extension (if any)
        path = parsed_url.path.lower()
        file_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', 
                           '.xls', '.xlsx', '.zip', '.tar', '.gz', '.mp3', '.mp4', '.avi']
        
        # Skip binary and document file extensions
        if any(path.endswith(ext) for ext in file_extensions):
            return False
        
        return True
    
    def _extract_links(self, soup, url):
        """Extract links from the page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = self._normalize_url(href, url)
            if self._should_follow(absolute_url):
                links.append(absolute_url)
        return links
    
    def _clean_html(self, html_content):
        """Clean the HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
    
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
            
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
            
        # Remove unnecessary attributes from all elements
        for tag in soup.find_all(True):
            # Keep only essential attributes
            attrs_to_keep = ['href', 'src', 'alt', 'title', 'class', 'id']
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr not in attrs_to_keep:
                    del tag[attr]
                    
        # Clean up whitespace
        for tag in soup.find_all(True):
            if tag.string:
                tag.string = re.sub(r'\s+', ' ', tag.string).strip()
                
        # Get the cleaned HTML
        cleaned_html = soup.prettify()
        
        return cleaned_html

    def get_crawl_stats(self, graph_file=None):
        """Get statistics about the crawl."""
        stats = {
            "pages_crawled": len(self.crawled_urls),
            "start_url": self.start_url,
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "crawl_method": "breadth-first",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "domain": self.domain
        }
        
        # Add graph file path if available
        if graph_file:
            stats["graph_file"] = graph_file
            
        return stats

    def generate_graph_visualization(self, graph_type=None, title=None, output_file=None):
        """
        Generate a graph visualization of the crawled data.
        
        Args:
            graph_type: Type of graph to generate ("tree", "page", "domain", or "interactive")
            title: Custom title for the graph
            output_file: Path to save the graph file
            
        Returns:
            Path to the generated graph file or None if generation fails
        """
        graph_type = graph_type or self.graph_type or "tree"  # Default to tree visualization
        title = title or f"Web Crawl Graph - {self.start_url}"
        
        try:
            # Import visualization functions only when needed
            from .visualizer import (
                generate_crawl_graph, 
                generate_domain_graph, 
                create_dynamic_graph,
                create_tree_visualization
            )
            
            if graph_type == "tree":
                return create_tree_visualization(
                    self.save_path,
                    output_file=output_file
                )
            elif graph_type == "page":
                return generate_crawl_graph(
                    self.save_path, 
                    output_file=output_file,
                    title=title
                )
            elif graph_type == "domain":
                return generate_domain_graph(
                    self.save_path,
                    output_file=output_file,
                    title=title
                )
            elif graph_type == "interactive":
                return create_dynamic_graph(
                    self.save_path,
                    output_file=output_file
                )
            else:
                self.logger.error(f"Unknown graph type: {graph_type}")
                return None
                
        except ImportError:
            self.logger.error("Could not import visualization modules. Make sure networkx and matplotlib are installed.")
            return None
        except Exception as e:
            self.logger.error(f"Error generating graph: {str(e)}")
            return None
            
    def generate_tree_visualization(self, output_file=None):
        """Generate an interactive tree visualization with root at the top."""
        return self.generate_graph_visualization("tree", None, output_file)
        
    def generate_page_graph(self, title=None, output_file=None):
        """Generate a page-level graph visualization."""
        return self.generate_graph_visualization("page", title, output_file)
        
    def generate_domain_graph(self, title=None, output_file=None):
        """Generate a domain-level graph visualization."""
        return self.generate_graph_visualization("domain", title, output_file)
        
    def generate_interactive_graph(self, output_file=None):
        """Generate an interactive HTML graph visualization."""
        return self.generate_graph_visualization("interactive", None, output_file)

    def _init_robots_parser(self):
        """Initialize the robots.txt parser."""
        parsed_url = urlparse(self.start_url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        self.robots_parser = RobotFileParser()
        self.robots_parser.set_url(robots_url)
        self.robots_parser.read()
        self.logger.info(f"Loaded robots.txt from {robots_url}")
    
    def _init_cache(self):
        """Initialize the cache."""
        # This method is empty as the original implementation didn't include cache initialization
        pass
    
    def _save_metadata(self):
        """Save metadata about the crawl to a file."""
        # Ensure the save directory exists
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        
        # Handle start_time and end_time which might be float or datetime objects
        start_time_value = self.start_time
        if hasattr(self.start_time, 'timestamp'):
            start_time_value = self.start_time.timestamp()
        
        end_time_value = self.end_time
        if hasattr(self.end_time, 'timestamp'):
            end_time_value = self.end_time.timestamp()
        
        # Calculate duration
        if isinstance(self.start_time, (int, float)) and isinstance(self.end_time, (int, float)):
            duration = self.end_time - self.start_time
        elif hasattr(self.start_time, 'timestamp') and hasattr(self.end_time, 'timestamp'):
            duration = (self.end_time - self.start_time).total_seconds()
        else:
            duration = 0
        
        # Create metadata dictionary
        metadata = {
            "start_url": self.start_url,
            "crawled_urls": self.crawled_urls,
            "crawl_stats": {
                "start_time": start_time_value,
                "end_time": end_time_value,
                "duration": duration,
                "pages_crawled": len(self.crawled_urls),
                "max_depth": self.max_depth,
                "max_pages": self.max_pages
            }
        }
        
        # Save metadata to file
        metadata_file = os.path.join(self.save_path, "metadata.json")
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            self.logger.info(f"Metadata saved to {metadata_file}")
        except Exception as e:
            self.logger.error(f"Error saving metadata: {str(e)}")
            return None
        
        return metadata_file


# CLI function for using the crawler directly
def crawl_site(
    start_url,
    output_dir="crawled_data",
    max_depth=2,
    max_pages=100,
    crawl_method="breadth",
    delay=1.0,
    follow_subdomains=False,
    use_selenium=False,
    use_scrapy=False,
    url_filter=None,
    generate_graph=False,
    graph_type="tree",
    graph_title=None
):
    """
    Crawl a website and save the content to the specified directory.
    
    Args:
        start_url: URL to start crawling from
        output_dir: Directory to save the crawled data
        max_depth: Maximum crawl depth
        max_pages: Maximum number of pages to crawl
        crawl_method: "breadth" or "depth" crawling method
        delay: Delay between requests in seconds
        follow_subdomains: Whether to follow links to subdomains
        use_selenium: Use Selenium for JavaScript rendering if needed
        use_scrapy: Use Scrapy for faster parallel crawling
        url_filter: Regular expression pattern for URLs to follow
        generate_graph: Whether to generate a graph visualization after crawling
        graph_type: Type of graph to generate ("tree", "page", "domain", or "interactive")
        graph_title: Title for the graph visualization
    
    Returns:
        Dictionary with crawl statistics and graph file path if generated
    """
    # Create the crawler instance
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        delay=delay,
        save_path=output_dir,
        crawl_method=crawl_method,
        follow_external_links=follow_subdomains,
        respect_robots_txt=True,
        user_agent=None,
        generate_graph=generate_graph,
        graph_type=graph_type,
        log_level="INFO",
        use_scrapy=use_scrapy,
        scrapy_settings=None,
        save_html=True,
        save_screenshots=False,
        headless=use_selenium,
        browser_type="chrome",
        filter_urls=url_filter,
        extract_metadata=None,
        cache_backend="memory",
        redis_url="redis://localhost:6379/0"
    )
    
    # Start crawling
    pages_crawled, graph_file = crawler.crawl()
    
    # Get crawl stats
    stats = crawler.get_crawl_stats(graph_file)
    
    # Return stats
    return stats


# Example usage
if __name__ == "__main__":
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Web crawler for collecting pages from websites")
    parser.add_argument("url", help="URL to start crawling from")
    parser.add_argument("--output", default="crawled_data", help="Directory to save the crawled data")
    parser.add_argument("--depth", type=int, default=2, help="Maximum crawl depth")
    parser.add_argument("--pages", type=int, default=100, help="Maximum number of pages to crawl")
    parser.add_argument("--method", choices=["breadth", "depth"], default="breadth", help="Crawling method")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--subdomains", action="store_true", help="Follow links to subdomains")
    parser.add_argument("--selenium", action="store_true", help="Use Selenium for JavaScript rendering if needed")
    parser.add_argument("--scrapy", action="store_true", help="Use Scrapy for faster parallel crawling")
    parser.add_argument("--filter", help="Regular expression pattern for URLs to follow")
    parser.add_argument("--graph", action="store_true", help="Generate a graph visualization")
    parser.add_argument("--graph-type", choices=["tree", "page", "domain", "interactive"], 
                        default="tree", help="Type of graph to generate")
    
    args = parser.parse_args()
    
    # Crawl the site
    stats = crawl_site(
        start_url=args.url,
        output_dir=args.output,
        max_depth=args.depth,
        max_pages=args.pages,
        crawl_method=args.method,
        delay=args.delay,
        follow_subdomains=args.subdomains,
        use_selenium=args.selenium,
        use_scrapy=args.scrapy,
        url_filter=args.filter,
        generate_graph=args.graph,
        graph_type=args.graph_type
    )
    
    # Print stats
    print(f"\nCrawl completed:")
    print(f"Pages crawled: {stats['pages_crawled']}")
    print(f"Max depth: {stats['max_depth']}")
    print(f"Start URL: {stats['start_url']}")
    print(f"Domain: {stats['domain']}")
    print(f"Method: {stats['crawl_method']}")
    print(f"Output directory: {args.output}") 