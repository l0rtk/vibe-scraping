"""Vibe Scraping - A library for scraping product information and extracting structured data using LLMs.

This package provides tools for:
- Scraping web pages using both regular HTTP requests and Selenium
- Extracting structured product information using Groq API
- Tracking API usage and costs
- Crawling websites to collect pages with configurable depth
- Visualizing web crawl results as interactive graphs
"""

__version__ = "0.2.0"

from .main import (
    scrape_webpage, 
    extract_product_info, 
    calculate_cost, 
    print_results, 
    process_product_page,
    MODEL_PRICING
)

from .selenium_scraper import scrape_with_selenium
from .crawler import WebCrawler, crawl_site
from .visualizer import (
    generate_crawl_graph,
    generate_domain_graph,
    create_dynamic_graph
)

__all__ = [
    'scrape_webpage',
    'extract_product_info',
    'calculate_cost',
    'print_results',
    'process_product_page',
    'scrape_with_selenium',
    'WebCrawler',
    'crawl_site',
    'MODEL_PRICING',
    # Visualization functions
    'generate_crawl_graph',
    'generate_domain_graph',
    'create_dynamic_graph'
]
