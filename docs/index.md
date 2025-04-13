# Vibe Scraping Documentation

Welcome to the Vibe Scraping documentation. This package provides tools for scraping product information from websites and extracting structured data using Groq API.

## Installation

```bash
# From PyPI (not yet available)
pip install vibe-scraping

# From source
git clone https://github.com/yourusername/vibe-scraping.git
cd vibe-scraping
pip install -e .

# With advanced features
pip install -e ".[advanced]"
```

## Basic Usage

### Command Line

#### Product Information Extraction

```bash
# Basic usage
vibe-scrape extract https://example.com/product/some-product

# With custom prompt
vibe-scrape extract https://example.com/product --prompt "Extract technical specs"

# For JavaScript-heavy sites
vibe-scrape extract https://example.com/product --selenium
```

#### Web Crawler

```bash
# Basic usage with default settings
vibe-scrape crawl https://example.com

# With custom depth and max pages
vibe-scrape crawl https://example.com --depth 3 --pages 200

# With output directory specified
vibe-scrape crawl https://example.com --output crawled_data

# Using depth-first search instead of breadth-first
vibe-scrape crawl https://example.com --method depth
```

### Python API

#### Product Information Extraction

```python
from vibe_scraping import process_product_page

# Basic usage
product_info, cost_info = process_product_page("https://example.com/product")

# With custom prompt
product_info, cost_info = process_product_page(
    "https://example.com/product",
    custom_prompt="Extract technical specifications from"
)

# Print the extracted information
print(product_info["content"])

# Print cost information
if cost_info["has_pricing"]:
    print(f"Total cost: ${cost_info['total_cost']:.6f}")
```

#### Web Crawler Usage

```python
from vibe_scraping import WebCrawler, crawl_site

# Quick usage with helper function
stats = crawl_site(
    start_url="https://example.com",
    output_dir="crawled_data",
    max_depth=2,
    max_pages=100,
    crawl_method="breadth",
    delay=1.0
)
print(f"Crawled {stats['pages_crawled']} pages")

# Advanced usage with WebCrawler class
crawler = WebCrawler(
    start_url="https://example.com",
    max_depth=3,
    max_pages=200,
    delay=1.5,
    delay_randomize=True,
    respect_robots_txt=True,
    crawl_method="breadth",
    save_path="crawled_data",
    url_pattern=r"example.com/products/.*",  # Only follow product URLs
    selenium_fallback=True,
    follow_subdomains=False
)

# Start crawling
crawler.crawl()

# Get stats
stats = crawler.get_crawl_stats()
print(f"Crawled {stats['pages_crawled']} pages")
```

## API Reference

### Main Functions

- `scrape_webpage(url, max_retries=3, use_selenium_fallback=True)`: Scrape content from a webpage
- `extract_product_info(text, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, max_retries=3)`: Extract product information using Groq API
- `calculate_cost(usage, model)`: Calculate the cost based on token usage
- `process_product_page(url, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, use_selenium_fallback=True)`: Process a product page from start to finish

### Selenium Functions

- `scrape_with_selenium(url, wait_time=10, scroll=True, headless=False, undetected=True)`: Scrape a page using Selenium with various options

### Web Crawler Functions and Classes

- `WebCrawler`: The main web crawler class with numerous configuration options
- `crawl_site(start_url, output_dir="crawled_data", max_depth=2, max_pages=100, crawl_method="breadth", delay=1.0, follow_subdomains=False, use_selenium=False, url_filter=None)`: Helper function for quick crawling

## Web Crawler Features

The web crawler provides several advanced features:

### Crawling Strategies

- Breadth-first search: Explores all links at the current depth before going deeper
- Depth-first search: Follows each path to its maximum depth before backtracking

### Politeness Policies

- Configurable delays between requests
- Randomization of delays to appear more human-like
- Respect for robots.txt directives

### URL Handling

- URL normalization to avoid duplicate content
- URL filtering using regular expressions
- Option to follow or ignore subdomains

### Content Processing

- Saves both HTML and extracted text content
- Maintains metadata about each crawled page
- Supports revisit policies (never, daily, always)

### Advanced Options

- Selenium integration for JavaScript-heavy sites
- Session management for maintaining cookies
- Custom headers and user agent configuration

## Configuration

Create a `.env` file with your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```
