import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
import time
import random

# Lock to prevent race conditions during driver initialization if strict thread safety is needed for uc
driver_lock = threading.Lock()

def search_google_snippet(query: str, driver=None) -> str:
    """
    Performs a Google search and extracts the snippets from the first page.
    If driver is provided, uses it. Otherwise creates a one-off driver (slower).
    """
    should_quit = False
    if not driver:
        should_quit = True
        options = uc.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        with driver_lock:
             driver = uc.Chrome(options=options, version_main=142)

    try:
        driver.get("https://www.google.com/search?q=" + query)
        
        # Simple consent handling (reused logic)
        try:
            consent = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Reject all') or contains(., 'Accept all') or contains(., 'Respinge') or contains(., 'Acceptă')]"))
            )
            consent.click()
        except:
            pass

        # Wait for results - generic body wait
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Try to find the main result container
        text = ""
        try:
            content_element = driver.find_element(By.ID, "search")
            text = content_element.text
        except:
            # Fallback to body
            text = driver.find_element(By.TAG_NAME, "body").text

        # Cleanup: simpler whitespace
        text = " ".join(text.split())
        
        return text[:3000] # Limit context size

    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return ""
    finally:
        if should_quit and driver:
            driver.quit()

def get_firm_context(firm_name: str) -> str:
    """
    Orchestrates gathering context for a firm.
    Runs 2 searches: one for business info (Listafirme), one for trust/reviews.
    Returns a combined string.
    """
    if not firm_name or firm_name == "N/A":
        return "No firm name provided."

    # We use a single driver for both searches to save startup time
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    context = f"Context for firm '{firm_name}':\n\n"
    
    driver = None
    try:
        with driver_lock:
             driver = uc.Chrome(options=options, version_main=142)
        
        # Search 1: Business Info
        # Using "cifra de afaceri" (turnover) to find size
        biz_query = f"{firm_name} cifra de afaceri listafirme"
        biz_text = search_google_snippet(biz_query, driver)
        context += f"--- Business Data (Source: Google/Listafirme) ---\n{biz_text}\n\n"
        
        time.sleep(random.uniform(1, 2))
        
        # Search 2: Trust/Reviews
        trust_query = f"{firm_name} pareri reddit trustpilot teapa"
        trust_text = search_google_snippet(trust_query, driver)
        context += f"--- Reputation Data (Source: Google/Reddit/Trustpilot) ---\n{trust_text}\n"
        
    except Exception as e:
        context += f"\nError gathering context: {str(e)}"
    finally:
        if driver:
            driver.quit()
            
    return context

if __name__ == "__main__":
    # Test
    print(get_firm_context("evomag"))
