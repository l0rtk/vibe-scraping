"""Vibe Scraping - Lightweight deep web crawler using Scrapy."""

__version__ = "0.3.0"

from .crawler import WebCrawler, crawl_site

# Import Scrapy adapter if available
try:
    from .scrapy_adapter import crawl_with_scrapy, SCRAPY_AVAILABLE
except ImportError:
    # Define a placeholder for SCRAPY_AVAILABLE if the module is not available
    SCRAPY_AVAILABLE = False

# Import analyzer functions
try:
    from .html_analyzer import HTMLAnalyzer, analyze_html_content
except ImportError:
    # If BeautifulSoup is not available
    HTMLAnalyzer = None
    analyze_html_content = None

__all__ = [
    'WebCrawler',
    'crawl_site',
    'SCRAPY_AVAILABLE',
    'crawl_with_scrapy',
    'HTMLAnalyzer',
    'analyze_html_content'
]
