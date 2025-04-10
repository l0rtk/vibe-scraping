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
python example.py
```

This script demonstrates:

- Processing a product page and saving the information to a JSON file
- Comparing multiple products in a single run
- Using individual components of the library

## Functions

- `scrape_webpage(url)`: Scrapes text content from a given URL
- `extract_product_info(text, model, custom_prompt)`: Uses Groq API to extract product information
- `calculate_cost(usage, model)`: Calculates the cost of the API call
- `print_results(product_info, cost_info, model)`: Prints the results in a formatted way
- `process_product_page(url, model, custom_prompt)`: Main function that combines all steps

## Supported Models

Currently supports:

- meta-llama/llama-4-scout-17b-16e-instruct
- meta-llama/llama-4-maverick-17b-128e-instruct

Add more models to the `MODEL_PRICING` dictionary to extend support.
