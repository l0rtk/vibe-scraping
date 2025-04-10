# Product Scraping Library

A tiny library for scraping product information from websites and using Groq API to extract structured data.

## Setup

1. Clone this repository
2. Install dependencies:

```
pip install requests beautifulsoup4 groq python-dotenv
```

3. Create a `.env` file with your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```

4. (Optional) For JavaScript-heavy websites, install Selenium dependencies:

```
pip install selenium webdriver-manager
```

5. (Optional) For websites with advanced anti-bot protections:

```
pip install undetected-chromedriver
```

## Usage

### As a Library

```python
from main import process_product_page

# Process a product page with default model
result = process_product_page("https://example.com/product/some-product")

# Process with specific model
result = process_product_page(
    "https://example.com/product/some-product",
    model="meta-llama/llama-4-maverick-17b-128e-instruct"
)

# Process with a custom prompt
result = process_product_page(
    "https://example.com/product/some-product",
    custom_prompt="Extract only the pricing information and available colors from"
)

# Process JavaScript-heavy site with Selenium
result = process_product_page(
    "https://site-with-javascript.com/product",
    custom_prompt="Extract technical specifications from",
    use_selenium_fallback=True  # Will try regular requests first, then use Selenium
)

# Access the extracted information and cost details
product_info, cost_info = result
print(product_info["content"])  # The extracted product details
print(cost_info["total_cost"])  # The cost of the API call
```

### Command Line Interface

The library also comes with a simple command-line interface:

```bash
# Basic usage
python cli.py https://example.com/product/some-product

# Specify a different model
python cli.py https://example.com/product/some-product --model meta-llama/llama-4-maverick-17b-128e-instruct

# Use a custom prompt
python cli.py https://example.com/product/some-product --prompt "Extract only the technical specifications and warranty information from"

# Force using Selenium for JavaScript-heavy sites
python cli.py https://example.com/product/some-product --selenium

# Disable Selenium fallback (use only regular requests)
python cli.py https://example.com/product/some-product --no-selenium

# Save scraped content to a file (useful when API is down)
python cli.py https://example.com/product/some-product --save-content scraped_data.txt

# Use previously saved content instead of scraping again
python cli.py https://example.com/product/some-product --use-saved scraped_data.txt

# Increase API retries for unstable connections
python cli.py https://example.com/product/some-product --max-retries 5

# Only output the extracted information (no token usage or cost details)
python cli.py https://example.com/product/some-product --quiet
```

Make the CLI executable:

```bash
chmod +x cli.py
./cli.py https://example.com/product/some-product
```

### Example Script

Check out `example.py` for more advanced usage examples:

```bash
# Run with default settings (standard requests)
python example.py

# Use Selenium for JavaScript-heavy sites
python example.py --selenium

# Specify a custom URL to process
python example.py --url https://some-site.com/product
```

This script demonstrates:

- Processing a product page and saving the information to a JSON file
- Comparing results with different prompts
- Comparing regular requests vs. Selenium-based scraping

## Handling JavaScript-Heavy Websites

Some websites rely heavily on JavaScript to load content, which makes them difficult to scrape with regular HTTP requests. This library provides two approaches:

1. **Automatic Fallback**: By default, the library will first try regular requests and automatically fall back to Selenium if it detects insufficient content.

2. **Forced Selenium**: You can force the use of Selenium for known JavaScript-heavy sites.

### Prerequisites for Selenium:

- Install Selenium: `pip install selenium webdriver-manager`
- Chrome browser installed (the library uses ChromeDriver)

### How it works:

1. The library first attempts to scrape with regular requests
2. If content is missing or suspiciously short, it falls back to Selenium
3. Selenium launches a headless Chrome browser to render the page with JavaScript
4. The rendered HTML is then processed to extract text

## Handling Websites with Anti-Bot Protections

Some websites use sophisticated anti-bot protections that can block even Selenium. For these cases, the library includes advanced features:

1. **Undetected ChromeDriver**: Uses a specialized version of ChromeDriver that bypasses common detection methods
2. **Human-like Behavior**: Mimics human browsing patterns with random scrolling, pauses, and interactions
3. **Browser Fingerprinting Protection**: Modifies browser properties to avoid detection

### Prerequisites:

```bash
pip install undetected-chromedriver
```

### Usage:

```bash
# Using the CLI
python cli.py https://protected-site.com/product --selenium

# In code
from selenium_scraper import scrape_with_selenium
html = scrape_with_selenium(url, headless=False, undetected=True)
```

## Handling API Failures

The library includes robust error handling for API calls:

1. **Automatic Retries**: Will retry failed API calls with exponential backoff
2. **Content Saving**: Can save scraped content to a file for later processing
3. **Offline Mode**: Can use previously saved content when the API is down

Example workflow for unstable connections:

```bash
# First scrape and save content (even if API call fails)
python cli.py https://example.com/product --save-content product_data.txt

# Later process the saved content
python cli.py https://example.com/product --use-saved product_data.txt
```

## Functions

- `scrape_webpage(url, use_selenium_fallback=True)`: Scrapes content from a URL
- `extract_product_info(text, model, custom_prompt, max_retries=3)`: Uses Groq API to extract product information
- `calculate_cost(usage, model)`: Calculates the cost of the API call
- `print_results(product_info, cost_info, model)`: Prints the results in a formatted way
- `process_product_page(url, model, custom_prompt, use_selenium_fallback)`: Main function that combines all steps

## Supported Models

Currently supports:

- meta-llama/llama-4-scout-17b-16e-instruct
- meta-llama/llama-4-maverick-17b-128e-instruct

Add more models to the `MODEL_PRICING` dictionary to extend support.
