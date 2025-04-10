import requests
from bs4 import BeautifulSoup
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Model pricing (per million tokens)
MODEL_PRICING = {
    # Meta models
    "meta-llama/llama-4-scout-17b-16e-instruct": {"input": 0.11, "output": 0.34},
    "meta-llama/llama-4-maverick-17b-128e-instruct": {"input": 0.20, "output": 0.60},
}

def scrape_webpage(url):
    """Scrape content from a webpage."""
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    return None

def extract_product_info(text, model="meta-llama/llama-4-scout-17b-16e-instruct"):
    """Extract product information using Groq API."""
    groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    prompt = f"Extract the product name, price, and description and the product attributes from the following text: {text}"
    
    response = groq.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    
    return {
        "content": response.choices[0].message.content,
        "usage": {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
    }

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

def process_product_page(url, model="meta-llama/llama-4-scout-17b-16e-instruct"):
    """Process a product page from start to finish."""
    # Scrape the webpage
    text = scrape_webpage(url)
    if not text:
        print("Failed to retrieve the page")
        return
    
    # Extract product information
    product_info = extract_product_info(text, model)
    
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








