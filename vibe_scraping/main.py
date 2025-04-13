import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
import os
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Model pricing (per million tokens)
MODEL_PRICING = {
    # Meta models
    "meta-llama/llama-4-scout-17b-16e-instruct": {"input": 0.11, "output": 0.34},
    "meta-llama/llama-4-maverick-17b-128e-instruct": {"input": 0.20, "output": 0.60},
}

def scrape_webpage(url, max_retries=3, use_selenium_fallback=True):
    """Scrape content from a webpage, mimicking a real browser.
    
    Args:
        url: URL to scrape
        max_retries: Maximum number of retry attempts
        use_selenium_fallback: Whether to try Selenium if regular requests fail
    
    Returns:
        Extracted text content or None if failed
    """
    # Common user agents to mimic real browsers
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]
    
    # Common headers to appear like a real browser
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    # First, try with regular requests
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to retrieve {url} (attempt {attempt+1}/{max_retries})...")
            
            # Add a slight delay between retries to avoid triggering rate limits
            if attempt > 0:
                time.sleep(2 + random.random() * 3)  # Sleep 2-5 seconds between retries
            
            # Make the request with headers to appear more like a real browser
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check if we need to clean up the content (remove scripts, styles, etc.)
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get the text
                text = soup.get_text(separator=' ', strip=True)
                logger.info(f"Successfully retrieved {len(text)} characters of text")
                
                # If text content is too short, it might indicate a blocking mechanism
                if len(text) < 500:
                    logger.warning(f"Warning: Retrieved text is suspiciously short ({len(text)} chars)")
                    logger.warning("The site might be blocking scraping or requiring JavaScript")
                    
                    # Try again with a different approach - get the raw HTML
                    if len(text) < 100:
                        logger.info("Attempting to extract from raw HTML...")
                        # Use a more permissive approach to extract text
                        text = ' '.join(soup.stripped_strings)
                        logger.info(f"Extracted {len(text)} characters using alternative method")
                
                # Check if content is substantial enough or if we should try Selenium
                if len(text) > 500 or not use_selenium_fallback:
                    return text
                else:
                    logger.warning("Content may be incomplete, trying Selenium as fallback...")
                    break  # Move to Selenium fallback
            else:
                logger.error(f"Failed to retrieve page (Status code: {response.status_code})")
        
        except Exception as e:
            logger.error(f"Error during page retrieval: {str(e)}")
    
    # If we get here and use_selenium_fallback is True, try with Selenium
    if use_selenium_fallback:
        try:
            logger.info("Attempting to scrape with Selenium (headless Chrome)...")
            
            # Import the Selenium scraper (only when needed to avoid dependencies)
            from .selenium_scraper import scrape_with_selenium
            
            # Get the HTML with Selenium
            html_content = scrape_with_selenium(url)
            
            if html_content and len(html_content) > 0:
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Clean up the content
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                logger.info(f"Successfully retrieved {len(text)} characters using Selenium")
                
                return text
            else:
                logger.error("Failed to retrieve content with Selenium")
        
        except ImportError:
            logger.error("Selenium is not installed. To use the Selenium fallback, install selenium and webdriver-manager.")
        except Exception as e:
            logger.error(f"Error during Selenium scraping: {str(e)}")
    
    logger.error(f"Failed to retrieve the page after all attempts")
    return None

def extract_product_info(text, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, max_retries=3):
    """Extract product information using Groq API.
    
    Args:
        text: The text content to analyze
        model: The model to use
        custom_prompt: Custom prompt to use instead of the default
        max_retries: Maximum number of retries for API calls
    
    Returns:
        Dictionary containing the extracted content and token usage
    """
    import time
    
    # Prepare the prompt
    if custom_prompt:
        prompt = f"{custom_prompt}: {text}"
    else:
        prompt = f"Extract the product name, price, and description and the product attributes from the following text: {text}"
    
    # Initialize Groq client
    groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Add retry logic
    retry_count = 0
    backoff_time = 1.0  # Start with 1 second backoff
    
    while retry_count <= max_retries:
        try:
            logger.info(f"Sending request to Groq API (attempt {retry_count + 1}/{max_retries + 1})...")
            
            # Set timeout to avoid hanging
            response = groq.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=60.0  # 60 second timeout
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                logger.warning(f"API call failed: {str(e)}")
                logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                logger.error(f"All retry attempts failed: {str(e)}")
                raise Exception(f"Failed to get response from Groq API after {max_retries + 1} attempts: {str(e)}")

def calculate_cost(usage, model):
    """Calculate the cost based on token usage."""
    if model in MODEL_PRICING:
        input_cost = (usage["input_tokens"] / 1_000_000) * MODEL_PRICING[model]["input"]
        output_cost = (usage["output_tokens"] / 1_000_000) * MODEL_PRICING[model]["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "has_pricing": True
        }
    return {"has_pricing": False}

def print_results(product_info, cost_info, model):
    """Print the extracted information and usage statistics."""
    print(product_info["content"])
    
    if cost_info["has_pricing"]:
        usage = product_info["usage"]
        print(f"\nToken Usage and Cost:")
        print(f"Input tokens: {usage['input_tokens']} (${cost_info['input_cost']:.6f})")
        print(f"Output tokens: {usage['output_tokens']} (${cost_info['output_cost']:.6f})")
        print(f"Total tokens: {usage['total_tokens']}")
        print(f"Total cost: ${cost_info['total_cost']:.6f}\n")
        print(f"Estimated price for this operation: ${cost_info['total_cost']:.6f}")
    else:
        usage = product_info["usage"]
        print(f"\nToken Usage:")
        print(f"Input tokens: {usage['input_tokens']}")
        print(f"Output tokens: {usage['output_tokens']}")
        print(f"Total tokens: {usage['total_tokens']}")
        print(f"Cost calculation unavailable for model: {model}\n")
        print(f"Estimated price for this operation: Unknown (pricing data not available for {model})")

def process_product_page(url, model="meta-llama/llama-4-scout-17b-16e-instruct", custom_prompt=None, use_selenium_fallback=True):
    """Process a product page from start to finish.
    
    Args:
        url: The URL of the product page
        model: The model to use
        custom_prompt: Optional custom prompt to use
        use_selenium_fallback: Whether to use Selenium as a fallback if regular scraping fails
    """
    # Scrape the webpage
    text = scrape_webpage(url, use_selenium_fallback=use_selenium_fallback)
    if not text:
        print("Failed to retrieve the page")
        return None, None
    
    # Extract product information
    product_info = extract_product_info(text, model, custom_prompt)
    
    # Calculate cost
    cost_info = calculate_cost(product_info["usage"], model)
    
    # Print results
    print_results(product_info, cost_info, model)
    
    return product_info, cost_info

if __name__ == "__main__":
    # Example usage
    url = "https://gstore.ge/product/asus-zenbook-duo-14-ux8406ma-ql099w-black/"
    model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    process_product_page(url, model)








