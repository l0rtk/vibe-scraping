# Product Scraping Library

A lightweight library for scraping product information from websites and extracting structured data using Groq API.

## Setup

```bash
# Install basic dependencies
pip install requests beautifulsoup4 groq python-dotenv

# For JavaScript-heavy sites
pip install selenium

# For sites with anti-bot protection
pip install undetected-chromedriver
```

Create a `.env` file with your Groq API key:

```
GROQ_API_KEY=your_api_key_here
```

## Usage

### Command Line

```bash
# Basic usage
python cli.py https://example.com/product/some-product

# With custom prompt
python cli.py https://example.com/product --prompt "Extract technical specs"

# For JavaScript-heavy sites (opens browser window)
python cli.py https://example.com/product --selenium

# Headless browser mode (faster but may be detected)
python cli.py https://example.com/product --selenium --headless

# Save content for later use
python cli.py https://example.com/product --save-content data.txt

# Use previously saved content
python cli.py https://example.com/product --use-saved data.txt
```

### Python Code

```python
from main import process_product_page

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

## Key Features

- **Regular Scraping**: Fast HTTP requests with BeautifulSoup parsing
- **JavaScript Support**: Selenium-based scraping for dynamic content
- **Anti-Bot Protection**: Bypass Cloudflare and other protections with undetected-chromedriver
- **Flexible Extraction**: Custom prompts for targeted information extraction
- **Cost Tracking**: Monitor API usage and costs
- **Offline Mode**: Save and reuse content to reduce API calls
- **Error Handling**: Automatic retries and fallbacks

## Handling Protected Sites

Sites with Cloudflare or similar protections require special handling:

```bash
# Use visible browser window (recommended for protected sites)
python cli.py https://protected-site.com/product --selenium

# If blocked, try undetected mode (opens browser window)
# This simulates human-like behavior to bypass detection
python cli.py https://protected-site.com/product --selenium
```

## Supported Models

- meta-llama/llama-4-scout-17b-16e-instruct
- meta-llama/llama-4-maverick-17b-128e-instruct
