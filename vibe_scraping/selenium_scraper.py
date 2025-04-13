from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
import logging
import platform
import shutil

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
            import sys
            logger.info(f"Python path: {sys.path}")
            logger.info(f"Trying to import undetected_chromedriver...")
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
            
            # Get Chrome version from the system
            import subprocess
            try:
                chrome_version_output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
                chrome_version = chrome_version_output.strip().split(' ')[2]  # Get the version number
                major_version = chrome_version.split('.')[0]  # Just the major version number
                logger.info(f"Detected Chrome version: {chrome_version} (major: {major_version})")
                
                # Create driver with specific version
                driver = uc.Chrome(options=options, version_main=int(major_version))
            except Exception as chrome_version_error:
                logger.warning(f"Error detecting Chrome version: {chrome_version_error}")
                # Fallback to default
                driver = uc.Chrome(options=options)
                
            return driver
        except ImportError as e:
            logger.warning(f"undetected-chromedriver import error: {e}")
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
        # Check if chrome is available in PATH
        chrome_path = shutil.which("google-chrome")
        if not chrome_path:
            chrome_path = shutil.which("chrome")
            
        if chrome_path:
            logger.info(f"Using Chrome browser from: {chrome_path}")
            
        driver = webdriver.Chrome(options=options)
        
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
        
        # Get viewport dimensions (visible area)
        viewport_width = driver.execute_script("return window.innerWidth")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Move mouse using relative movements within viewport boundaries
        actions = ActionChains(driver)
        
        # Reset mouse position by moving to a known location first
        actions.move_to_element(driver.find_element(By.TAG_NAME, "body"))
        actions.perform()
        
        # Make a few small, random relative movements
        for _ in range(3):
            # Use smaller relative movements (-100 to +100 pixels)
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            
            # Perform the movement with proper error handling
            try:
                actions = ActionChains(driver)
                actions.move_by_offset(x_offset, y_offset)
                actions.perform()
                time.sleep(0.5 + random.random())
            except Exception as e:
                logger.debug(f"Mouse movement error: {e}")
                # Reset mouse position if movement fails
                actions = ActionChains(driver)
                actions.move_to_element(driver.find_element(By.TAG_NAME, "body"))
                actions.perform()
        
        # Try to interact with visible elements safely
        try:
            # Find visible, interactive elements
            elements = driver.find_elements(By.CSS_SELECTOR, "div:not([style*='display:none']):not([style*='visibility:hidden'])")
            if elements:
                # Filter to elements that are in viewport
                visible_elements = []
                for elem in elements[:20]:  # Check first 20 to avoid too much processing
                    try:
                        if driver.execute_script("""
                            var elem = arguments[0];
                            var rect = elem.getBoundingClientRect();
                            return (
                                rect.top >= 0 &&
                                rect.left >= 0 &&
                                rect.bottom <= window.innerHeight &&
                                rect.right <= window.innerWidth
                            );
                        """, elem):
                            visible_elements.append(elem)
                    except:
                        continue
                
                # Move to a random visible element if any were found
                if visible_elements:
                    random_element = random.choice(visible_elements)
                    actions = ActionChains(driver)
                    actions.move_to_element(random_element)
                    actions.perform()
                    time.sleep(0.5 + random.random())
        except Exception as e:
            logger.debug(f"Error during element interaction: {e}")
        
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
        
        # Only try to clear storage if we're on a valid page (not data: URL)
        current_url = driver.current_url
        if current_url and not current_url.startswith("data:"):
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            logger.info("Cleared cookies and cache")
        else:
            logger.info("Cleared cookies only (storage clearing skipped - not on a valid page)")
    except Exception as e:
        logger.warning(f"Error clearing cookies and cache: {e}")

def scrape_with_selenium(url, wait_time=10, scroll=True, headless=False, undetected=True):
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
        
        # Try with undetected-chromedriver first - NOTE: Setting headless=False to bypass Cloudflare
        driver = setup_selenium_driver(headless=False, undetected=undetected)
        
        if not driver:
            logger.error("Failed to initialize Chrome driver")
            return None
        
        # Load the page with a referrer to look more natural
        logger.info(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait longer for Cloudflare to process
        logger.info("Waiting for page to load and possible Cloudflare check to pass...")
        time.sleep(10 + random.random() * 5)  # Random wait between 10-15 seconds
        
        # Check if we hit a Cloudflare challenge or captcha
        page_source = driver.page_source.lower()
        if "cloudflare" in page_source and ("challenge" in page_source or "security check" in page_source):
            logger.warning("Cloudflare protection detected, waiting longer...")
            # Wait much longer for a human to potentially solve the challenge
            time.sleep(30)  # Wait 30 seconds in case there's a timeout challenge
        
        # Clear cookies and cache after loading the page
        clear_cookies_and_cache(driver)
        
        driver.execute_script(f"""
            var meta = document.createElement('meta');
            meta.name = 'referrer';
            meta.content = 'origin';
            document.getElementsByTagName('head')[0].appendChild(meta);
        """)
        
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
        
        # Check if we still have cloudflare protection
        if "cloudflare" in page_source.lower() and len(page_source) < 5000:
            logger.warning("Still detecting Cloudflare protection after waiting. Content may be limited.")
        
        # Parse with BeautifulSoup to extract text content
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Clean up the content
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get the text
        text = soup.get_text(separator=' ', strip=True)
        
        logger.info(f"Successfully scraped page with Selenium (length: {len(page_source)})")
        if len(text) < 1000:
            logger.warning(f"Warning: Extracted text is suspiciously short ({len(text)} chars)")
            logger.warning("This may indicate the site is blocking scraping")
        
        return page_source
        
    except Exception as e:
        logger.error(f"Error during Selenium scraping: {e}")
        return None
        
    finally:
        if driver:
            logger.info("ensuring close")
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