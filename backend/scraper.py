import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import random
import sys
import os
import concurrent.futures
import threading

def get_products(query):
    """
    Scrapes Google Shopping for products matching the query using Selenium.
    Returns a list of dictionaries containing product details.
    """
    options = uc.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    options.add_argument("--disable-gpu")
    driver = uc.Chrome(options=options, version_main=142)

    try:
        # Navigate to Google Shopping
        driver.get("https://shopping.google.com/")
        
        # Handle Cookie Consent (if present)
        try:
            # Look for "Reject all" or "Accept all" buttons
            # These are often in a dialog. We try a few common XPath patterns.
            # Added Romanian translations: Respinge, Acceptă
            consent_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Reject all') or contains(., 'Accept all') or contains(., 'I agree') or contains(., 'Respinge') or contains(., 'Acceptă') or contains(., 'Sunt de acord')]"))
            )
            consent_button.click()
            time.sleep(0.5) # Wait for dialog to close
        except:
            # If no consent button found, maybe we are already good or it's a different layout
            pass

        # Find search bar and input query
        # Google Shopping search input usually has name='q' or similar
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Human-like scrolling to trigger lazy loading and avoid detection
        # Scroll more to get more results
        for i in range(15): 
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.0, 4.0))
            
            # Try to click "More results" button if it exists
            try:
                # Common selectors for "More results" or "Load more" in Google Shopping
                # It might vary, but button often has text "More" or specific classes
                # Added "Mai multe" for RO locale if detected
                more_btns = driver.find_elements(By.XPATH, "//span[contains(text(), 'More') or contains(text(), 'Mai multe')]")
                for btn in more_btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(0.5)
            except:
                pass

        # Scroll back up a bit to ensure elements are in view
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)

        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        products = {} # Use dict for deduplication by key
        
        # Selectors found from debug_page.html
        # Container classes: rwVHAc, ropLT
        results = soup.select('.rwVHAc, .ropLT')
        
        for result in results:
            try:
                # Extract Name
                name_tag = result.select_one('.bXPcId')
                if not name_tag:
                    name_tag = result.select_one('h3')
                
                name = name_tag.get_text(strip=True) if name_tag else "N/A"
                
                if not name or name == "N/A":
                    continue

                # Extract Price
                price_tag = result.select_one('.M3sJBb')
                if not price_tag:
                    price_tag = result.select_one('span[aria-hidden="true"]') 

                price = price_tag.get_text(strip=True) if price_tag else "N/A"

                # Extract Link
                link_tag = None
                
                # Special handling for rwVHAc (Ads) - Link/Image is in grandparent
                if 'rwVHAc' in result.get('class', []):
                    grandparent = result.parent.parent if result.parent else None
                    if grandparent:
                        link_tag = grandparent.find('a')
                        # Also find image in grandparent
                        img_tag = grandparent.find('img')
                
                # Fallback / Standard handling for ropLT or if above failed
                if not link_tag:
                    if result.name == 'a':
                        link_tag = result
                    else:
                        link_tag = result.select_one('a')
                    
                    if not link_tag:
                        curr = result
                        for _ in range(5):
                            if curr.name == 'a':
                                link_tag = curr
                                break
                            curr = curr.parent
                            if not curr: break
                
                link = link_tag['href'] if link_tag else ""
                if link.startswith('/'):
                    link = "https://www.google.com" + link

                # Extract Image
                image = ""
                # If we didn't find img_tag in grandparent logic above
                if 'rwVHAc' not in result.get('class', []) or not img_tag:
                    img_tag = result.select_one('img')
                
                if img_tag:
                    # Prioritize data-src/lsrc as they are often higher res or the real image
                    image = img_tag.get('src')
                    if not image or image.startswith('data:image/gif'):
                        image = img_tag.get('data-src') or img_tag.get('data-lsrc') or ""
                
                # Extract Firm (Seller)
                firm_tag = result.select_one('.CsnLnf')
                firm = firm_tag.get_text(strip=True) if firm_tag else "N/A"
                
                # Extract Description
                description = name 

                # Deduplication and Merging
                product_key = (name, price, firm)
                
                new_product = {
                    "name": name,
                    "price": price,
                    "link": link,
                    "image": image,
                    "firm": firm,
                    "description": description
                }

                # STRICT FILTER: User requires BOTH image and link.
                if not link or not image:
                    continue

                if product_key in products:
                    existing = products[product_key]
                    if not existing['link'] and link:
                        products[product_key] = new_product
                    elif not existing['image'] and image and (link or not existing['link']):
                        products[product_key] = new_product
                else:
                    if name != "N/A":
                        products[product_key] = new_product

            except Exception as e:
                continue

        return list(products.values())

    except Exception as e:
        print(f"Error scraping Google Shopping: {e}")
        return []
    finally:
        driver.quit()

driver_lock = threading.Lock()

def fetch_details_for_chunk(chunk, html_dir):
    """
    Worker function to process a chunk of products with a dedicated Selenium driver.
    Optimized for speed: Single tab, eager loading, minimal waits.
    """
    detailed_chunk = []
    
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.page_load_strategy = 'eager' 
    
    driver = None
    try:
        with driver_lock:
            options.add_argument("--disable-gpu")
            driver = uc.Chrome(options=options, version_main=142)
    except Exception as e:
        print(f"Worker failed to start driver: {e}")
        return []

    try:
        for product in chunk:
            link = product.get("link")
            if not link:
                detailed_chunk.append({**product, "html_text": ""})
                continue
            
            try:
                driver.get(link)
                # Eager strategy returns early. Wait for interactive state.
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "interactive" or d.execute_script("return document.readyState") == "complete"
                    )
                except:
                    pass
                
                # Buffer to ensure content rendering
                time.sleep(1.5)
                
                final_url = driver.current_url

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                html_text = str(soup)
                
                detailed_chunk.append({
                    **product,
                    "link": final_url,
                    "google_link": link,
                    "html_text": html_text
                })
                
                safe_name = "".join([c if c.isalnum() else "_" for c in product['name']])[:50]
                file_name = f"{html_dir}/{safe_name}_{random.randint(1000,9999)}.html"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(html_text)

            except Exception as e:
                print(f"Failed to fetch {link}: {e}")
                detailed_chunk.append({
                    **product,
                    "html_text": ""
                })
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
    return detailed_chunk

def scrape_google_products(query: str, max_products: int = 50) -> list[dict]:
    """
    Orchestrates the scraping of Google Shopping for products matching the query.
    1. Gets initial list of products.
    2. Fetches detailed info (HTML, resolved links) in parallel.
    3. Saves results and HTML files.
    """
    print(f"Starting scraping for query: '{query}'")
    
    # 1. Get initial results (Single Threaded)
    results = get_products(query)
    
    # Limit to max products for the detailed scrape
    products = results[:max_products]
    
    print(f"\nFound {len(products)} products. Starting parallel detailed fetch...")
    
    # Create directory for HTML files
    safe_query = "".join([c if c.isalnum() else "_" for c in query])
    html_dir = f"html_{safe_query}"
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)

    # 2. Parallel Processing
    # Split products into chunks
    NUM_WORKERS = 4
    if len(products) < NUM_WORKERS:
        NUM_WORKERS = len(products)
    
    chunk_size = (len(products) + NUM_WORKERS - 1) // NUM_WORKERS if NUM_WORKERS > 0 else 1
    product_chunks = [products[i:i + chunk_size] for i in range(0, len(products), chunk_size)]
    
    detailed_products = []
    
    print(f"Spawning {len(product_chunks)} worker threads...")
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(fetch_details_for_chunk, chunk, html_dir): chunk for chunk in product_chunks}
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                try:
                    data = future.result()
                    detailed_products.extend(data)
                    print(f"Worker finished. Total collected so far: {len(detailed_products)}")
                except Exception as exc:
                    print(f"Worker generated an exception: {exc}")
                    
    except KeyboardInterrupt:
        print("\nStopping early... Saving partial results.")

    # Save to file
    filename = f"products_{safe_query}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(detailed_products, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to {filename}")
    print(f"HTML files saved to {html_dir}/")
    
    return detailed_products

if __name__ == "__main__":
    # Test the scraper
    query = "iphone 15 pro"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    scrape_google_products(query)
