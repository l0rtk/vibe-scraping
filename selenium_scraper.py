from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
import logging
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_selenium_driver(headless=True, undetected=True):
    """Set up a Selenium WebDriver with Chrome.
    
    Args:
        headless: Whether to run Chrome in headless mode
        undetected: Try to use undetected-chromedriver to bypass bot detection
        
    Returns:
        WebDriver instance
    """
    # First try undetected-chromedriver if requested and available
    if undetected:
        try:
            import undetected_chromedriver as uc
            logger.info("Using undetected-chromedriver to bypass bot detection")
            
            options = uc.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            
            # Set window size for consistent rendering
            options.add_argument("--window-size=1920,1080")
            
            # Add common browser arguments
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Create driver
            driver = uc.Chrome(options=options)
            return driver
        except ImportError:
            logger.warning("undetected-chromedriver not installed. Falling back to standard Selenium.")
            logger.warning("Install with: pip install undetected-chromedriver")
        except Exception as e:
            logger.warning(f"Error with undetected-chromedriver: {e}. Falling back to standard Selenium.")
    
    # Fallback to regular Selenium
    options = Options()
    if headless:
        options.add_argument("--headless=new")  # Use the new headless mode
    
    # Basic options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Add user agent to appear as a real browser
    system = platform.system()
    if system == "Windows":
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    elif system == "Darwin":  # macOS
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    else:  # Linux
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    
    options.add_argument(f"user-agent={user_agent}")
    
    # Disable automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Add language preference
    options.add_argument("--lang=en-US,en;q=0.9")
    
    # Add common browser preferences
    prefs = {
        "profile.default_content_setting_values.notifications": 2,  # Block notifications
        "credentials_enable_service": False,  # Disable password saving
        "profile.password_manager_enabled": False,
        "intl.accept_languages": "en-US,en",
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Execute CDP commands to bypass bot detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'es']
                });
            """
        })
        
        return driver
    except Exception as e:
        logger.error(f"Failed to set up Chrome driver: {e}")
        return None

def human_like_interaction(driver):
    """Perform human-like interactions on the page to bypass bot detection.
    
    Args:
        driver: WebDriver instance
    """
    try:
        # Random wait before interaction
        time.sleep(1 + random.random() * 2)
        
        # Get page dimensions
        width = driver.execute_script("return document.documentElement.scrollWidth")
        height = driver.execute_script("return document.documentElement.scrollHeight")
        
        # Move mouse randomly
        actions = ActionChains(driver)
        for _ in range(3):
            x, y = random.randint(10, width-10), random.randint(10, min(height, 800))
            actions.move_by_offset(x, y)
            actions.perform()
            time.sleep(0.5 + random.random())
        
        # Click on visible elements randomly (avoiding links)
        try:
            elements = driver.find_elements(By.TAG_NAME, "div")
            if elements:
                random_element = random.choice(elements[:10])  # Choose from first 10 to avoid clicking on hidden elements
                actions.move_to_element(random_element)
                actions.perform()
        except Exception as e:
            logger.debug(f"Error during random element interaction: {e}")
        
        # Press Page Down key a couple of times
        body = driver.find_element(By.TAG_NAME, "body")
        for _ in range(2):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1 + random.random())
    
    except Exception as e:
        logger.warning(f"Error during human-like interaction: {e}")

def scroll_page(driver, pause_time=1.0):
    """Scroll the page to load lazy-loaded elements.
    
    Args:
        driver: WebDriver instance
        pause_time: Time to pause between scrolls
    """
    try:
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll gradually with random pauses
        for i in range(min(5, max(2, last_height // 500))):  # Adjust number of scrolls based on page height
            # Scroll down in increments with some randomness
            scroll_amount = random.randint(480, 820)  # Randomize scroll amount
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            # Wait to load page with random delay
            time.sleep(pause_time + random.random() * 1.5)
            
            # Sometimes scroll back up a bit to mimic human behavior
            if random.random() < 0.3:  # 30% chance
                driver.execute_script(f"window.scrollBy(0, {-random.randint(50, 200)});")
                time.sleep(0.5 + random.random())
    except Exception as e:
        logger.warning(f"Error during page scrolling: {e}")

def clear_cookies_and_cache(driver):
    """Clear cookies and cache to avoid detection"""
    try:
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        logger.info("Cleared cookies and cache")
    except Exception as e:
        logger.warning(f"Error clearing cookies and cache: {e}")

def scrape_with_selenium(url, wait_time=10, scroll=True, headless=True, undetected=True):
    """Scrape a webpage using Selenium with Chrome.
    
    Args:
        url: The URL to scrape
        wait_time: Maximum time to wait for page to load
        scroll: Whether to scroll the page to load lazy content
        headless: Whether to run Chrome in headless mode
        undetected: Try to use undetected-chromedriver to bypass bot detection
        
    Returns:
        The extracted text content or None if failed
    """
    driver = None
    try:
        logger.info(f"Attempting to scrape {url} with Selenium...")
        
        # Try with undetected-chromedriver first
        driver = setup_selenium_driver(headless=headless, undetected=undetected)
        
        if not driver:
            logger.error("Failed to initialize Chrome driver")
            return None
        
        # Clear cookies and cache first
        clear_cookies_and_cache(driver)
        
        # Load the page with a referrer to look more natural
        driver.execute_script(f"""
            var meta = document.createElement('meta');
            meta.name = 'referrer';
            meta.content = 'origin';
            document.getElementsByTagName('head')[0].appendChild(meta);
        """)
        
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(3 + random.random() * 2)  # Random wait between 3-5 seconds
        
        # Perform human-like interactions
        human_like_interaction(driver)
        
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
        
        # Take a screenshot for debugging
        try:
            screenshot_path = "page_screenshot.png"
            driver.save_screenshot(screenshot_path)
            logger.info(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")
        
        # Extract page content
        page_source = driver.page_source
        
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
    content = scrape_with_selenium(url, headless=False)  # Set headless=False to see the browser
    if content:
        print(f"Successfully scraped {len(content)} characters")
        
        # Parse with BeautifulSoup to extract text
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Clean up the content
        for script in soup(["script", "style"]):
            script.extract()
        
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        print(f"Extracted {len(text)} characters of text")
        
        # Save to file for inspection
        with open("scraped_content.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("Saved text to scraped_content.txt")
    else:
        print("Failed to scrape the page") 