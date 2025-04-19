"""Vibe Scraping - A streamlined library for deep web crawling using Scrapy.

This package provides tools for:
- Efficient deep web crawling using Scrapy
- Configurable crawl depth and page limits  
- Politeness controls (robots.txt, delays)
"""

__version__ = "0.3.0"

from .crawler import WebCrawler, crawl_site

# Import Scrapy adapter if available
try:
    from .scrapy_adapter import crawl_with_scrapy, SCRAPY_AVAILABLE
except ImportError:
    # Define a placeholder for SCRAPY_AVAILABLE if the module is not available
    SCRAPY_AVAILABLE = False

__all__ = [
    'WebCrawler',
    'crawl_site',
    'SCRAPY_AVAILABLE',
    'crawl_with_scrapy'
]
