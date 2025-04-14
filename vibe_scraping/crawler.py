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
    """Advanced web crawler with configurable depth and politeness policies."""
    
    def __init__(
        self,
        start_url,
        max_depth=2,
        max_pages=100,
        delay=1.0,
        delay_randomize=True,
        user_agent=None,
        respect_robots_txt=True,
        crawl_method="breadth",  # "breadth" or "depth"
        save_path="crawled_data",
        url_pattern=None,
        selenium_fallback=False,
        headless=True,
        follow_subdomains=False,
        handle_ajax=False,
        revisit_policy="never",  # "never", "daily", "always"
        cookies=None,
        custom_headers=None
    ):
        """Initialize the web crawler with the specified parameters.
        
        Args:
            start_url: The starting URL for crawling
            max_depth: Maximum depth for crawling (default: 2)
            max_pages: Maximum number of pages to crawl (default: 100)
            delay: Delay between requests in seconds (default: 1.0)
            delay_randomize: Whether to randomize the delay (default: True)
            user_agent: Custom user agent (default: None, uses a common browser UA)
            respect_robots_txt: Whether to respect robots.txt (default: True)
            crawl_method: "breadth" for BFS or "depth" for DFS (default: "breadth")
            save_path: Path to save crawled data (default: "crawled_data")
            url_pattern: Regex pattern for URLs to follow (default: None = all)
            selenium_fallback: Use Selenium if regular requests fail (default: False)
            headless: Run Selenium in headless mode (default: True)
            follow_subdomains: Whether to follow links to subdomains (default: False)
            handle_ajax: Whether to handle AJAX-loaded content (default: False)
            revisit_policy: Policy for revisiting pages (default: "never")
            cookies: Custom cookies to use for requests (default: None)
            custom_headers: Custom headers to use for requests (default: None)
        """
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.base_delay = delay
        self.delay_randomize = delay_randomize
        self.respect_robots_txt = respect_robots_txt
        self.crawl_method = crawl_method
        self.save_path = save_path
        self.selenium_fallback = selenium_fallback
        self.headless = headless
        self.follow_subdomains = follow_subdomains
        self.handle_ajax = handle_ajax
        self.revisit_policy = revisit_policy
        
        # Set up parsing components
        parsed_url = urlparse(start_url)
        self.base_domain = parsed_url.netloc
        self.base_scheme = parsed_url.scheme
        
        # Set up the URL pattern
        self.url_pattern = re.compile(url_pattern) if url_pattern else None
        
        # Set up the user agent
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        
        # Set up the robots.txt parser
        self.robots_parser = RobotFileParser()
        if self.respect_robots_txt:
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            try:
                self.robots_parser.set_url(robots_url)
                self.robots_parser.read()
                logger.info(f"Loaded robots.txt from {robots_url}")
            except Exception as e:
                logger.warning(f"Error loading robots.txt: {str(e)}")
        
        # Configure headers
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"  # Do Not Track request
        }
        
        # Add any custom headers
        if custom_headers:
            self.headers.update(custom_headers)
        
        # Set up cookies and session management
        self.session = requests.Session()
        if cookies:
            self.session.cookies.update(cookies)
            
        # Set up state
        self.visited = set()  # Set of visited URLs
        self.page_count = 0
        self.crawl_start_time = None
        
        # Create the save directory
        os.makedirs(self.save_path, exist_ok=True)
        self.metadata_file = os.path.join(self.save_path, "metadata.json")
        
        # Load existing metadata if available
        self.metadata = self._load_metadata()
    
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
            "pages_crawled": 0
        }
    
    def _update_metadata(self):
        """Update and save metadata after crawling."""
        self.metadata["last_crawl"] = datetime.now().isoformat()
        self.metadata["pages_crawled"] = len(self.metadata["crawled_urls"])
        
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _should_revisit(self, url):
        """Determine if a URL should be revisited based on the revisit policy."""
        if url not in self.metadata["crawled_urls"]:
            return True
            
        if self.revisit_policy == "never":
            return False
        elif self.revisit_policy == "always":
            return True
        elif self.revisit_policy == "daily":
            # Check if last visit was more than a day ago
            last_visit = datetime.fromisoformat(self.metadata["crawled_urls"][url]["last_visit"])
            time_diff = datetime.now() - last_visit
            return time_diff.days >= 1
        
        return False
    
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
        with open(os.path.join(page_dir, "cleaned.html"), 'w', encoding='utf-8') as f:
            f.write(cleaned_html)
        
        # Save text content
        with open(os.path.join(page_dir, "content.txt"), 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        # Save metadata about the page
        page_meta = {
            "url": url,
            "crawl_time": datetime.now().isoformat(),
            "depth": depth,
            "links_found": len(links),
            "links": links
        }
        
        with open(os.path.join(page_dir, "metadata.json"), 'w') as f:
            json.dump(page_meta, f, indent=2)
        
        # Update global metadata
        self.metadata["crawled_urls"][url] = {
            "hash": url_hash,
            "last_visit": datetime.now().isoformat(),
            "depth": depth
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
        if url in self.visited:
            return False
        
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Check if it's from the same domain or allowed subdomain
        if not self.follow_subdomains and parsed_url.netloc != self.base_domain:
            # If not following subdomains, only follow URLs from the exact same domain
            return False
        elif self.follow_subdomains and not self._is_subdomain(parsed_url.netloc):
            # If following subdomains, check if it's a subdomain of the base domain
            return False
        
        # Check against URL pattern if provided
        if self.url_pattern and not self.url_pattern.search(url):
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
    
    def _is_subdomain(self, domain):
        """Check if the domain is a subdomain of the base domain."""
        if domain == self.base_domain:
            return True
        
        # Check if it's a subdomain
        return domain.endswith(f".{self.base_domain}")
    
    def _get_delay(self):
        """Get the appropriate delay between requests."""
        if self.delay_randomize:
            # Add a random amount between 0 and 100% of base delay
            return self.base_delay * (1 + random.random())
        return self.base_delay
    
    def _extract_links(self, soup, url):
        """Extract links from the page."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = self._normalize_url(href, url)
            if self._should_follow(absolute_url):
                links.append(absolute_url)
        return links
    
    def crawl(self):
        """Start the crawling process."""
        if self.crawl_method == "breadth":
            self._breadth_first_crawl()
        else:
            self._depth_first_crawl()
            
        # Update and save metadata after crawling
        self._update_metadata()
        
        logger.info(f"Crawl completed. Visited {self.page_count} pages.")
        return self.page_count
    
    def _breadth_first_crawl(self):
        """Perform breadth-first crawling."""
        self.crawl_start_time = datetime.now()
        logger.info(f"Starting breadth-first crawl from {self.start_url}")
        
        # Initialize the queue with the starting URL and depth 0
        queue = deque([(self.start_url, 0)])
        self.visited.add(self.start_url)
        
        while queue and self.page_count < self.max_pages:
            url, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
                
            logger.info(f"Crawling [{self.page_count+1}/{self.max_pages}]: {url} (depth {depth})")
            
            try:
                html_content, text_content, soup = self._fetch_page(url)
                if not html_content:
                    continue
                    
                self.page_count += 1
                
                # Extract links from the page
                links = self._extract_links(soup, url)
                
                # Save the page data
                self._save_page(url, html_content, text_content, links, depth)
                
                # Add new links to the queue
                for link in links:
                    if link not in self.visited:
                        queue.append((link, depth + 1))
                        self.visited.add(link)
                
                # Apply delay before next request
                time.sleep(self._get_delay())
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
    
    def _depth_first_crawl(self):
        """Perform depth-first crawling."""
        self.crawl_start_time = datetime.now()
        logger.info(f"Starting depth-first crawl from {self.start_url}")
        
        # Initialize the stack with the starting URL and depth 0
        stack = [(self.start_url, 0)]
        self.visited.add(self.start_url)
        
        while stack and self.page_count < self.max_pages:
            url, depth = stack.pop()
            
            if depth > self.max_depth:
                continue
                
            logger.info(f"Crawling [{self.page_count+1}/{self.max_pages}]: {url} (depth {depth})")
            
            try:
                html_content, text_content, soup = self._fetch_page(url)
                if not html_content:
                    continue
                    
                self.page_count += 1
                
                # Extract links from the page
                links = self._extract_links(soup, url)
                
                # Save the page data
                self._save_page(url, html_content, text_content, links, depth)
                
                # Add new links to the stack (in reverse order to maintain priority)
                for link in reversed(links):
                    if link not in self.visited:
                        stack.append((link, depth + 1))
                        self.visited.add(link)
                
                # Apply delay before next request
                time.sleep(self._get_delay())
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
    
    def _fetch_page(self, url):
        """Fetch a page and parse it."""
        # Try with regular requests first
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get the text
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Check if content is substantial enough
                if len(text_content) > 500 or not self.selenium_fallback:
                    return html_content, text_content, soup
                else:
                    logger.warning(f"Content may be incomplete for {url}, trying Selenium as fallback...")
            else:
                logger.error(f"Failed to retrieve page {url} (Status code: {response.status_code})")
        
        except Exception as e:
            logger.error(f"Error during page retrieval {url}: {str(e)}")
        
        # If we're here and selenium_fallback is True, try with Selenium
        if self.selenium_fallback:
            try:
                logger.info(f"Attempting to scrape {url} with Selenium...")
                
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
                    logger.info(f"Successfully retrieved {len(text_content)} characters using Selenium")
                    
                    return html_content, text_content, soup
                else:
                    logger.error(f"Failed to retrieve content with Selenium for {url}")
            
            except Exception as e:
                logger.error(f"Error during Selenium scraping for {url}: {str(e)}")
        
        return None, None, None
    
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


    def get_crawl_stats(self):
        """Get statistics about the crawl."""
        return {
            "pages_crawled": self.page_count,
            "start_url": self.start_url,
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "crawl_method": self.crawl_method,
            "start_time": self.crawl_start_time.isoformat() if self.crawl_start_time else None,
            "end_time": datetime.now().isoformat() if self.crawl_start_time else None,
            "domain": self.base_domain
        }


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
    url_filter=None
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
        url_filter: Regular expression pattern for URLs to follow
    
    Returns:
        Dictionary with crawl statistics
    """
    # Create the crawler instance
    crawler = WebCrawler(
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        delay=delay,
        save_path=output_dir,
        crawl_method=crawl_method,
        follow_subdomains=follow_subdomains,
        selenium_fallback=use_selenium,
        url_pattern=url_filter
    )
    
    # Start crawling
    crawler.crawl()
    
    # Return stats
    return crawler.get_crawl_stats()


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
    parser.add_argument("--filter", help="Regular expression pattern for URLs to follow")
    
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
        url_filter=args.filter
    )
    
    # Print stats
    print(f"\nCrawl completed:")
    print(f"Pages crawled: {stats['pages_crawled']}")
    print(f"Max depth: {stats['max_depth']}")
    print(f"Start URL: {stats['start_url']}")
    print(f"Domain: {stats['domain']}")
    print(f"Method: {stats['crawl_method']}")
    print(f"Output directory: {args.output}") 