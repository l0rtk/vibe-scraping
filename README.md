# Product Scraping Library

A lightweight library for scraping product information from websites and extracting structured data using Groq API.

## Installation

### From PyPI (not yet available)

```bash
pip install vibe-scraping
```

### From source

```bash
git clone https://github.com/yourusername/vibe-scraping.git
cd vibe-scraping
pip install -e .  # Install in development mode

# To install with all extras
pip install -e ".[advanced]"
```

## Setup

Create a `.env` file with your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```

## Directory Structure

```
├── vibe_scraping/           # Main package
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Core library functions
│   ├── selenium_scraper.py  # Selenium-based scraper
│   ├── crawler.py           # Web crawler
│   ├── visualizer.py        # Graph visualization
│   └── cli.py               # Command-line interface
├── setup.py                 # Package setup file
├── LICENSE                  # MIT License
├── MANIFEST.in              # Package manifest
├── README.md                # Documentation
└── requirements.txt         # Dependencies
```

## Usage

### Command Line

#### Product Information Extraction

```bash
# If installed via pip
vibe-scrape extract https://example.com/product/some-product

# Or running directly from source
python -m vibe_scraping.cli extract https://example.com/product/some-product

# With custom prompt
vibe-scrape extract https://example.com/product --prompt "Extract technical specs"

# For JavaScript-heavy sites (opens browser window)
vibe-scrape extract https://example.com/product --selenium

# Headless browser mode (faster but may be detected)
vibe-scrape extract https://example.com/product --selenium --headless

# Save content for later use
vibe-scrape extract https://example.com/product --save-content data.txt

# Use previously saved content
vibe-scrape extract https://example.com/product --use-saved data.txt
```

#### Web Crawler

```bash
# Crawl a website with default settings (depth 2, max 100 pages)
vibe-scrape crawl https://example.com

# Set crawl depth and max pages
vibe-scrape crawl https://example.com --depth 3 --pages 200

# Specify output directory
vibe-scrape crawl https://example.com --output crawled_data

# Use depth-first crawling instead of breadth-first (default)
vibe-scrape crawl https://example.com --method depth

# Follow links to subdomains
vibe-scrape crawl https://example.com --subdomains

# Use Selenium for JavaScript rendering
vibe-scrape crawl https://example.com --selenium

# Filter URLs by pattern
vibe-scrape crawl https://example.com --filter "product/.*"

# Generate a graph visualization after crawling
vibe-scrape crawl https://example.com --graph

# Generate a specific type of graph
vibe-scrape crawl https://example.com --graph --graph-type domain

# Create an interactive HTML visualization
vibe-scrape crawl https://example.com --graph --graph-type interactive

# Add a custom title to the graph
vibe-scrape crawl https://example.com --graph --graph-title "My Website Crawl"
```

#### Graph Visualization

```bash
# Visualize previously crawled data
vibe-scrape visualize crawled_data

# Generate a domain-level graph
vibe-scrape visualize crawled_data --type domain

# Create an interactive visualization
vibe-scrape visualize crawled_data --type interactive

# Customize the output file path
vibe-scrape visualize crawled_data --output my_graph.png

# Set a custom title
vibe-scrape visualize crawled_data --title "Website Structure"

# Limit the number of nodes in the graph
vibe-scrape visualize crawled_data --max-nodes 50

# Hide labels on nodes
vibe-scrape visualize crawled_data --no-labels
```

### Python Code

#### Product Information Extraction

```python
from vibe_scraping import process_product_page

# Simple usage
result = process_product_page("https://example.com/product")

# With custom prompt
result = process_product_page(
    "https://example.com/product",
    custom_prompt="Extract technical specifications from"
)

# For JavaScript sites
result = process_product_page(
    "https://example.com/product",
    use_selenium_fallback=True
)
```

#### Web Crawler

```python
from vibe_scraping import WebCrawler, crawl_site

# Quick crawl with helper function
stats = crawl_site(
    start_url="https://example.com",
    output_dir="crawled_data",
    max_depth=2,
    max_pages=100
)
print(f"Crawled {stats['pages_crawled']} pages")

# More control with WebCrawler class
crawler = WebCrawler(
    start_url="https://example.com",
    max_depth=3,
    max_pages=200,
    delay=1.5,  # 1.5 seconds delay between requests
    crawl_method="breadth",  # "breadth" or "depth"
    save_path="crawled_data",
    url_pattern=r"example.com/products/.*",  # Only follow product URLs
    selenium_fallback=True,  # Use Selenium if needed
    follow_subdomains=False,  # Stay on the same domain
    respect_robots_txt=True  # Respect robots.txt rules
)
crawler.crawl()

# Crawl and generate a graph in one step
stats = crawl_site(
    start_url="https://example.com",
    output_dir="crawled_data",
    max_depth=2,
    max_pages=100,
    generate_graph=True,  # Create a graph visualization
    graph_type="page"     # "page", "domain", or "interactive"
)
print(f"Graph saved to: {stats.get('graph_file')}")
```

#### Graph Visualization

```python
from vibe_scraping import generate_crawl_graph, generate_domain_graph, create_dynamic_graph

# Generate a page-level graph
graph_file = generate_crawl_graph(
    crawl_data_path="crawled_data",
    output_file="crawl_graph.png",  # Optional, defaults to crawl_graph.png in crawl_data_path
    max_nodes=100,                  # Limit the number of nodes
    title="My Web Crawl Graph",     # Custom title
    with_labels=True                # Show labels on nodes
)

# Generate a domain-level graph
domain_graph = generate_domain_graph(
    crawl_data_path="crawled_data",
    output_file="domain_graph.png",
    title="Domain Connections",
    node_size_factor=100            # Node size based on page count
)

# Create an interactive HTML visualization
# Requires pyvis: pip install pyvis
interactive_graph = create_dynamic_graph(
    crawl_data_path="crawled_data",
    output_file="interactive_graph.html"
)
```

## Key Features

- **Regular Scraping**: Fast HTTP requests with BeautifulSoup parsing
- **JavaScript Support**: Selenium-based scraping for dynamic content
- **Anti-Bot Protection**: Bypass Cloudflare and other protections with undetected-chromedriver
- **Flexible Extraction**: Custom prompts for targeted information extraction
- **Cost Tracking**: Monitor API usage and costs
- **Offline Mode**: Save and reuse content to reduce API calls
- **Error Handling**: Automatic retries and fallbacks
- **Web Crawler**: Collect pages from websites with configurable depth
- **Polite Crawling**: Respects robots.txt and implements politeness policies
- **Crawl Methods**: Breadth-first and depth-first search strategies
- **URL Filtering**: Regular expression-based URL filtering
- **Graph Visualization**: Create visual representations of crawled websites
- **Domain Analysis**: Visualize connections between domains
- **Interactive Graphs**: Generate interactive HTML visualizations

## Web Crawler Features

The web crawler provides advanced features for collecting pages from websites:

- **Configurable Depth**: Set maximum crawl depth to control how deep the crawler goes
- **Politeness Policies**: Adjustable delays between requests and randomization
- **Robots.txt Support**: Respects website crawling rules
- **URL Normalization**: Avoids crawling the same page multiple times
- **URL Filtering**: Regular expression-based filtering for targeted crawling
- **Session Management**: Handles cookies and headers
- **Metadata Tracking**: Records crawl statistics and page information
- **Breadth-First & Depth-First**: Choose the crawling strategy that fits your needs
- **Subdomain Support**: Option to follow links to subdomains
- **Selenium Integration**: Handle JavaScript-heavy sites with Selenium

## Graph Visualization Features

The library provides multiple ways to visualize crawled websites:

- **Page-Level Graphs**: Visualize connections between individual pages
- **Domain-Level Graphs**: See how different domains are interconnected
- **Interactive Visualizations**: Create dynamic HTML graphs for exploration
- **Customization Options**: Control node size, colors, labels, and layout
- **Size-Based Nodes**: Node sizes reflect the number of pages in domains
- **Color Coding**: Different colors for different domains
- **Path Visualization**: See the crawl path and link relationships

## Handling Protected Sites

Sites with Cloudflare or similar protections require special handling:

```bash
# Use visible browser window (recommended for protected sites)
vibe-scrape extract https://protected-site.com/product --selenium

# If blocked, try undetected mode (opens browser window)
# This simulates human-like behavior to bypass detection
vibe-scrape extract https://protected-site.com/product --selenium
```

## Supported Models

- meta-llama/llama-4-scout-17b-16e-instruct
- meta-llama/llama-4-maverick-17b-128e-instruct
