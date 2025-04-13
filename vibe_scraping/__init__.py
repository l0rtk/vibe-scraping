"""Vibe Scraping - A library for scraping product information and extracting structured data using LLMs.

This package provides tools for:
- Scraping web pages using both regular HTTP requests and Selenium
- Extracting structured product information using Groq API
- Tracking API usage and costs
"""

__version__ = "0.1.0"

from .main import (
    scrape_webpage, 
    extract_product_info, 
    calculate_cost, 
    print_results, 
    process_product_page,
    MODEL_PRICING
)

from .selenium_scraper import scrape_with_selenium

__all__ = [
    'scrape_webpage',
    'extract_product_info',
    'calculate_cost',
    'print_results',
    'process_product_page',
    'scrape_with_selenium',
    'MODEL_PRICING'
]
