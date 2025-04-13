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

```bash
# Basic usage
vibe-scrape https://example.com/product/some-product

# With custom prompt
vibe-scrape https://example.com/product --prompt "Extract technical specs"

# For JavaScript-heavy sites
vibe-scrape https://example.com/product --selenium
```

### Python API

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

## API Reference

### Main Functions

- `scrape_webpage(url, max_retries=3, use_selenium_fallback=True)`: Scrape content from a webpage
- `extract_product_info(text, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, max_retries=3)`: Extract product information using Groq API
- `calculate_cost(usage, model)`: Calculate the cost based on token usage
- `process_product_page(url, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, use_selenium_fallback=True)`: Process a product page from start to finish

### Selenium Functions

- `scrape_with_selenium(url, wait_time=10, scroll=True, headless=False, undetected=True)`: Scrape a page using Selenium with various options

## Configuration

Create a `.env` file with your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```
