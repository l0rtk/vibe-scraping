from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_selenium_driver(headless=True):
    """Set up a Selenium WebDriver with Chrome.
    
    Args:
        headless: Whether to run Chrome in headless mode
        
    Returns:
        WebDriver instance
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Add user agent to appear as a real browser
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to set up Chrome driver: {e}")
        return None

def scroll_page(driver, pause_time=1.0):
    """Scroll the page to load lazy-loaded elements.
    
    Args:
        driver: WebDriver instance
        pause_time: Time to pause between scrolls
    """
    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll down in increments
    for i in range(5):  # Limit to 5 scrolls for performance
        # Scroll down to bottom
        driver.execute_script(f"window.scrollTo(0, {last_height // 5 * (i+1)});")
        
        # Wait to load page
        time.sleep(pause_time + random.random())

def scrape_with_selenium(url, wait_time=10, scroll=True):
    """Scrape a webpage using Selenium with Chrome.
    
    Args:
        url: The URL to scrape
        wait_time: Maximum time to wait for page to load
        scroll: Whether to scroll the page to load lazy content
        
    Returns:
        The extracted text content or None if failed
    """
    driver = None
    try:
        logger.info(f"Attempting to scrape {url} with Selenium...")
        driver = setup_selenium_driver()
        
        if not driver:
            logger.error("Failed to initialize Chrome driver")
            return None
        
        # Load the page
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(3 + random.random() * 2)  # Random wait between 3-5 seconds
        
        # Scroll the page if needed
        if scroll:
            scroll_page(driver)
        
        # Wait for the content to be present
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            logger.warning(f"Timeout waiting for page content: {e}")
        
        # Extract page content
        page_source = driver.page_source
        
        # Take a screenshot for debugging (optional)
        # driver.save_screenshot("page_screenshot.png")
        
        logger.info(f"Successfully scraped page with Selenium (length: {len(page_source)})")
        return page_source
        
    except Exception as e:
        logger.error(f"Error during Selenium scraping: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Test the scraper
    url = "https://alta.ge/home-appliance/kitchen-appliances/microwaves/toshiba-mm-eg24p-bm-black.html"
    content = scrape_with_selenium(url)
    if content:
        print(f"Successfully scraped {len(content)} characters")
    else:
        print("Failed to scrape the page") 