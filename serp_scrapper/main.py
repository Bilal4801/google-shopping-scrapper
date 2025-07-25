# import os
# import random
# from fastapi import FastAPI, Request
# import time
# from typing import Optional
# from utils import GoogleShoppingData
# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# from fake_useragent import UserAgent
# import re


# app = FastAPI()


# def extract_price(price_str):
#     """
#     Extracts numeric price from a string and returns it as a float.
#     If no valid price is found, returns None.
#     """
#     match = re.search(r'[\d,.]+', price_str)
#     if match:
#         # Remove commas and convert to float
#         try:
#             return float(match.group().replace(',', ''))
#         except ValueError:
#             return None
#     return None

# async def scrape_google_shopping(query):

#     options = uc.ChromeOptions()
#     # Normal flags
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-extensions")
#     options.add_argument("--disable-blink-features=AutomationControlled")

#     # Set a consistent but believable User-Agent
#     options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

#     # Mimic real screen size
#     width = random.randint(1280, 1920)
#     height = random.randint(720, 1080)
#     options.add_argument(f"--window-size={width},{height}")

#     # Download preferences
#     prefs = {
#         "download.default_directory": os.getcwd(),
#         "download.prompt_for_download": False,
#     }
#     options.add_experimental_option("prefs", prefs)

#     # Create driver (uc takes care of the stealth part automatically)
#     driver = uc.Chrome(options=options, use_subprocess=True)
    
#     # Patch webdriver-related JS variables
#     driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#         "source": """
#             Object.defineProperty(navigator, 'webdriver', {
#               get: () => undefined
#             });
#             Object.defineProperty(navigator, 'languages', {
#               get: () => ['en-US', 'en']
#             });
#             Object.defineProperty(navigator, 'platform', {
#               get: () => 'Win32'
#             });
#             Object.defineProperty(navigator, 'vendor', {
#               get: () => 'Google Inc.'
#             });
#             window.chrome = {
#               runtime: {},
#               // Add more spoofed properties if needed
#             };
#         """
#     })

#     wait = WebDriverWait(driver, 30)

#     try:
#         # 1. go to google shopping
#         driver.get("https://www.google.com/shopping?udm=28")
#         time.sleep(3)  # wait for the page to load

#         # 2. upload via send_keys on the **second** input
#         inputs = driver.find_element(By.ID, 'oDgap')
#         inputs.send_keys(query)
#         time.sleep(2)  # wait for the input to be processed


#         driver.find_element(By.XPATH, '//*[@id="tsf"]/div[1]/div[1]/div[1]/button').click()
#         time.sleep(3)  # wait for the search results to load
#         print("Search completed.")
        
#         # Optionally scroll down (in case lazy loading or carousels)
#         driver.execute_script("window.scrollBy(0, 300);")

#         try:
#             container = driver.find_element(By.CLASS_NAME, "Z8PPnf")
#             product_divs = container.find_elements(By.CSS_SELECTOR, "div.gXGikb")
#             print("Exception case 1- Found product divs:", len(product_divs))

#             product_results = []
#             for div in product_divs:
#                 soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")

#                 # Extract product name
#                 name_tag = soup.find("div", class_="gkQHve")
#                 name = name_tag.get_text(strip=True) if name_tag else None

#                 # Extract product ID
#                 data_id = soup.find("div", class_="liKJmf wTrwWd")
#                 product_id = data_id.get("data-cid") if data_id else None

#                 # Extract price
#                 price_tag = soup.find("span", class_="lmQWe")
#                 price = price_tag.get_text(strip=True) if price_tag else None

#                 try:
#                     # Extract rating - Only if aria-label contains "Rated"
#                     rating_tag = soup.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
#                     rating = rating_tag["aria-label"] if rating_tag else None

#                 except:
#                     rating = None

#                 # Extract image
#                 image_tag = soup.find("img", class_="VeBrne")
#                 image_url = image_tag.get("src") if image_tag  else None

#                 extract_price_value = extract_price(price)
#                 product_results.append({
#                     "position": None,
#                     "title": name,
#                     "product_link": None,
#                     "product_id": product_id,
#                     "serpapi_product_api": None,
#                     "immersive_product_page_token": None,
#                     "serpapi_immersive_product_api": None,
#                     "source": None,
#                     "source_icon": None,
#                     "price": price,
#                     "extracted_price": extract_price_value,
#                     "rating": rating,
#                     "reviews": None,
#                     "thumbnail": image_url,
#                     "delivery": None
#                 })

#             driver.quit()
#             dict = {"search_result": product_results}
#             return dict

#         except:
#             try:
#                 html_content = driver.page_source
#                 soup = BeautifulSoup(html_content, "html.parser")
#                 results = []

#                 # New DOM structure: UL > LI.I8iMf
#                 product_list = soup.select("ul.lvS33d li.I8iMf")
#                 print(f"Exception case 2- Found, {len(product_list)} product cards")

#                 for card in product_list:
#                     # Product Name
#                     name_tag = card.select_one("div.gkQHve")
#                     name = name_tag.get_text(strip=True) if name_tag else None

#                     data_id = card.find("div", class_="MtXiu mZ9c3d wYFOId M919M W5CKGc wTrwWd")
#                     product_id = data_id.get("data-cid") if data_id else None

#                     # Price
#                     price_tag = card.find("span", class_="lmQWe")
#                     price = price_tag.get_text(strip=True) if price_tag else None

#                     try:
#                         # Rating
#                         rating_tag = card.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
#                         rating = rating_tag["aria-label"] if rating_tag else None
#                     except:
#                         rating = None

#                     # Image
#                     image_tag = card.find("img", class_="VeBrne")
#                     image_url = image_tag.get("src") if image_tag else None

#                     # Product URL - optional, not always available
#                     link_tag = card.find("a", href=True)
#                     product_url = link_tag["href"] if link_tag else None

#                     extract_price_value = extract_price(price)
#                     results.append({
#                         "position": None,
#                         "title": name,
#                         "product_link": product_url,
#                         "product_id": product_id,
#                         "serpapi_product_api": None,
#                         "immersive_product_page_token": None,
#                         "serpapi_immersive_product_api": None,
#                         "source": None,
#                         "source_icon": None,
#                         "price": price,
#                         "extracted_price": extract_price_value,
#                         "rating": rating,
#                         "reviews": None,
#                         "thumbnail": image_url,
#                         "delivery": None
#                     })

#                 driver.quit()
                
#                 dict = {"search_result": results}
#                 return dict

#             except:
#                 # Wait for items to be visible
#                 items = driver.find_elements(By.CSS_SELECTOR, "li.YBo8bb")
#                 print("Fallback - Exception Case: 3", len(items), "products")

#                 product_results = []

#                 for no, item in enumerate(items):
#                     soup = BeautifulSoup(item.get_attribute("innerHTML"), "html.parser")

#                     # Extracting Name
#                     name = None
#                     name_tag = soup.select_one("div.gkQHve.SsM98d.RmEs5b.gGeaLc")
#                     if name_tag:
#                         name = name_tag.get_text(strip=True)

#                     # Extracting Price
#                     price = None
#                     price_tag = soup.find("span", class_="lmQWe")
#                     if price_tag:
#                         price = price_tag.get_text(strip=True)

#                     # Extracting Rating
#                     rating = None
#                     rating_tag = soup.find("span", class_="z3HNkc")
#                     if rating_tag and rating_tag.has_attr("aria-label"):
#                         rating = rating_tag["aria-label"]

#                     # Extracting Image URL
#                     image_url = None
#                     image_tag = soup.find("img", class_="FsH7wb wtYWhc")
#                     if not image_tag:
#                         image_tag = soup.find("img", class_="uhHOwf ez24Df")
#                     if image_tag and image_tag.has_attr("src"):
#                         image_url = image_tag["src"]

#                     extract_price_value = extract_price(price)
#                     product_info ={
#                         "position": None,
#                         "title": name,
#                         "product_link": None,
#                         "product_id": None,
#                         "serpapi_product_api": None,
#                         "immersive_product_page_token": None,
#                         "serpapi_immersive_product_api": None,
#                         "source": None,
#                         "source_icon": None,
#                         "price": price,
#                         "extracted_price": extract_price_value,
#                         "rating": rating,
#                         "reviews": None,
#                         "thumbnail": image_url,
#                         "delivery": None
#                     }

#                     product_results.append(product_info)

#                 driver.quit()
#                 dict = {"search_result": product_results}
#                 return dict
                    
#     finally:
#         driver.quit()



# @app.post("/get-products")
# async def main_function(search_query:str, selected_country: Optional[str] = None):

#     user_query = search_query
#     selected_country = selected_country
#     data = await scrape_google_shopping(user_query)
#     return data








import os
import random
from fastapi import FastAPI, Request
import time
from typing import Optional
import asyncio
import threading
import uuid
from queue import Queue
from contextlib import asynccontextmanager
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import atexit


# Queue-based request processing
request_queue = Queue()
response_storage = {}  # Store responses by request_id
queue_worker_running = False
global_driver = None
processing_lock = threading.Lock()


def extract_price(price_str):
    """
    Extracts numeric price from a string and returns it as a float.
    If no valid price is found, returns None.
    """
    match = re.search(r'[\d,.]+', price_str)
    if match:
        try:
            return float(match.group().replace(',', ''))
        except ValueError:
            return None
    return None

def create_browser():
    """Create a new browser instance with stealth settings"""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    width = random.randint(1280, 1920)
    height = random.randint(720, 1080)
    options.add_argument(f"--window-size={width},{height}")
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
            Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
            window.chrome = { runtime: {} };
        """
    })
    return driver

def initialize_browser():
    """Initialize the single global browser"""
    global global_driver
    if global_driver is None:
        try:
            global_driver = create_browser()
            global_driver.get("https://www.google.com/shopping?udm=28")
            time.sleep(2)  # Allow initial page load
            print("Global browser initialized successfully")
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            raise e

def scrape_google_shopping_sync(query, request_id):
    """Synchronous version of scraping function - processes one request at a time"""
    global global_driver
    
    if global_driver is None:
        initialize_browser()
    
    try:
        print(f"[{request_id}] Starting to process query: {query}")
        wait = WebDriverWait(global_driver, 30)

        # Navigate to fresh Google Shopping page for each request
        global_driver.get("https://www.google.com/shopping?udm=28")
        time.sleep(random.uniform(1, 3))  # Random delay to mimic human behavior

        # Send query to search input
        inputs = wait.until(EC.presence_of_element_located((By.ID, 'oDgap')))
        inputs.clear()
        inputs.send_keys(query)
        time.sleep(1)

        global_driver.find_element(By.XPATH, '//*[@id="tsf"]/div[1]/div[1]/div[1]/button').click()
        time.sleep(3)
        print(f"[{request_id}] Search completed for query: {query}")

        # Scroll down
        global_driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(1)
        try:
            container = global_driver.find_element(By.CLASS_NAME, "Z8PPnf")
            product_divs = container.find_elements(By.CSS_SELECTOR, "div.gXGikb")
            print(f"[{request_id}] Found product divs: {len(product_divs)} for {query}")

            product_results = []
            for div in product_divs:
                soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")

                name_tag = soup.find("div", class_="gkQHve")
                name = name_tag.get_text(strip=True) if name_tag else None

                data_id = soup.find("div", class_="liKJmf wTrwWd")
                product_id = data_id.get("data-cid") if data_id else None
                print(product_id, "product id 1")

                if not product_id:
                    continue
                
                price_tag = soup.find("span", class_="lmQWe")
                price = price_tag.get_text(strip=True) if price_tag else None
                
                # ✅ NEW: Extract merchant name
                merchant_tag = soup.find("span", class_="WJMUdc rw5ecc")
                merchant_name = merchant_tag.get_text(strip=True) if merchant_tag else None

                try:
                    rating_tag = soup.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                    rating = rating_tag["aria-label"] if rating_tag else None
                except:
                    rating = None

                image_tag = soup.find("img", class_="VeBrne")
                image_url = image_tag.get("src") if image_tag else None

                extract_price_value = extract_price(price)
                product_results.append({
                    "position": None,
                    "title": name,
                    "product_link": None,
                    "product_id": product_id,
                    "serpapi_product_api": None,
                    "immersive_product_page_token": None,
                    "serpapi_immersive_product_api": None,
                    "source": merchant_name,
                    "source_icon": None,
                    "price": price,
                    "extracted_price": extract_price_value,
                    "rating": rating,
                    "reviews": None,
                    "thumbnail": image_url,
                    "delivery": None
                })

            result = {"search_result": product_results}
            print(f"[{request_id}] Successfully processed {len(product_results)} products")
            return result

        except Exception as e:
            print(f"[{request_id}] Exception case 1 for {query}: {e}")
            try:
                html_content = global_driver.page_source
                soup = BeautifulSoup(html_content, "html.parser")
                results = []

                product_list = soup.select("ul.lvS33d li.I8iMf")
                print(f"[{request_id}] Found {len(product_list)} product cards for {query}")

                for card in product_list:
                    name_tag = card.select_one("div.gkQHve")
                    name = name_tag.get_text(strip=True) if name_tag else None

                    data_id = card.find("div", class_="MtXiu mZ9c3d wYFOId M919M W5CKGc wTrwWd")
                    product_id = data_id.get("data-cid") if data_id else None
                    print(product_id, "product id 2")

                    if not product_id:
                        continue

                    price_tag = card.find("span", class_="lmQWe")
                    price = price_tag.get_text(strip=True) if price_tag else None
                    
                    merchant_tag = card.find("span", class_="WJMUdc rw5ecc")
                    merchant_name = merchant_tag.get_text(strip=True) if merchant_tag else None

                    try:
                        rating_tag = card.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                        rating = rating_tag["aria-label"] if rating_tag else None
                    except:
                        rating = None

                    image_tag = card.find("img", class_="VeBrne")
                    image_url = image_tag.get("src") if image_tag else None

                    product_url = None

                    extract_price_value = extract_price(price)
                    results.append({
                        "position": None,
                        "title": name,
                        "product_link": product_url,
                        "product_id": product_id,
                        "serpapi_product_api": None,
                        "immersive_product_page_token": None,
                        "serpapi_immersive_product_api": None,
                        "source": merchant_name,
                        "source_icon": None,
                        "price": price,
                        "extracted_price": extract_price_value,
                        "rating": rating,
                        "reviews": None,
                        "thumbnail": image_url,
                        "delivery": None
                    })

                result = {"search_result": results}
                print(f"[{request_id}] Successfully processed {len(results)} products (fallback 1)")
                return result

            except Exception as e:
                print(f"[{request_id}] Exception case 2 for {query}: {e}")
                items = global_driver.find_elements(By.CSS_SELECTOR, "li.YBo8bb")
                print(f"[{request_id}] Found {len(items)} products for {query}")

                product_results = []

                for no, item in enumerate(items):
                    soup = BeautifulSoup(item.get_attribute("innerHTML"), "html.parser")

                    name_tag = soup.select_one("div.gkQHve.SsM98d.RmEs5b.gGeaLc")
                    name = name_tag.get_text(strip=True) if name_tag else None

                    price_tag = soup.find("span", class_="lmQWe")
                    price = price_tag.get_text(strip=True) if price_tag else None

                    rating_tag = soup.find("span", class_="z3HNkc")
                    rating = rating_tag["aria-label"] if rating_tag and rating_tag.has_attr("aria-label") else None

                    merchant_tag = soup.find("span", class_="WJMUdc rw5ecc")
                    merchant_name = merchant_tag.get_text(strip=True) if merchant_tag else None

                    image_tag = soup.find("img", class_="FsH7wb wtYWhc")
                    if not image_tag:
                        image_tag = soup.find("img", class_="uhHOwf ez24Df")
                    image_url = image_tag["src"] if image_tag and image_tag.has_attr("src") else None

                    extract_price_value = extract_price(price)
                    product_info = {
                        "position": None,
                        "title": name,
                        "product_link": None,
                        "product_id": None,
                        "serpapi_product_api": None,
                        "immersive_product_page_token": None,
                        "serpapi_immersive_product_api": None,
                        "source": merchant_name,
                        "source_icon": None,
                        "price": price,
                        "extracted_price": extract_price_value,
                        "rating": rating,
                        "reviews": None,
                        "thumbnail": image_url,
                        "delivery": None
                    }

                    product_results.append(product_info)

                result = {"search_result": product_results}
                print(f"[{request_id}] Successfully processed {len(product_results)} products (fallback 2)")
                return result
                
    except Exception as e:
        print(f"[{request_id}] Error during scraping for {query}: {e}")
        return {"search_result": []}

def queue_worker():
    """Worker thread that processes requests from the queue sequentially"""
    global queue_worker_running, response_storage
    
    print("Queue worker started")
    queue_worker_running = True
    
    while queue_worker_running:
        try:
            # Get next request from queue (blocks until available)
            request_data = request_queue.get(timeout=1)
            
            if request_data is None:  # Shutdown signal
                break
                
            request_id = request_data['request_id']
            query = request_data['query']
            
            print(f"[{request_id}] Processing from queue: {query}")
            start_time = time.time()
            
            # Process the request sequentially (no concurrent access)
            with processing_lock:
                result = scrape_google_shopping_sync(query, request_id)
            
            end_time = time.time()
            print(f"[{request_id}] Completed in {end_time - start_time:.2f} seconds")
            
            # Store the result
            response_storage[request_id] = {
                'result': result,
                'completed': True,
                'timestamp': time.time()
            }
            
            # Mark task as done
            request_queue.task_done()
            
        except Exception as e:
            if not queue_worker_running:
                break
            print(f"Queue worker error: {e}")
            time.sleep(0.1)
    
    print("Queue worker stopped")

def cleanup_old_responses():
    """Clean up old responses to prevent memory leaks"""
    current_time = time.time()
    to_remove = []
    
    for request_id, data in response_storage.items():
        # Remove responses older than 10 minutes
        if current_time - data['timestamp'] > 600:
            to_remove.append(request_id)
    
    for request_id in to_remove:
        del response_storage[request_id]
    
    if to_remove:
        print(f"Cleaned up {len(to_remove)} old responses")

def cleanup_browser():
    """Clean up browser on application shutdown"""
    global global_driver, queue_worker_running
    
    # Stop queue worker
    queue_worker_running = False
    request_queue.put(None)  # Send shutdown signal
    
    if global_driver:
        try:
            global_driver.quit()
            print("Browser closed successfully")
        except Exception as e:
            print(f"Error closing browser: {e}")
        finally:
            global_driver = None

# Register cleanup function
atexit.register(cleanup_browser)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    print("Starting up FastAPI server...")
    print("Initializing single browser instance...")
    initialize_browser()
    print("Browser initialized successfully")
    
    # Start queue worker thread
    worker_thread = threading.Thread(target=queue_worker, daemon=True)
    worker_thread.start()
    print("Queue worker thread started")
    
    yield  # Server is running
    
    # Shutdown
    print("Shutting down FastAPI server...")
    cleanup_browser()
    print("Cleanup completed")

app = FastAPI(lifespan=lifespan)


@app.post("/get-products")
async def main_function(search_query: str, selected_country: Optional[str] = None):
    """Add request to queue and wait for completion"""
    user_query = search_query
    request_id = str(uuid.uuid4())
    
    print(f"[{request_id}] Received request for: {user_query}")
    
    # Add to queue
    request_queue.put({
        'request_id': request_id,
        'query': user_query,
        'country': selected_country
    })
    
    # Initialize response tracking
    response_storage[request_id] = {
        'result': None,
        'completed': False,
        'timestamp': time.time()
    }
    
    print(f"[{request_id}] Added to queue (queue size: {request_queue.qsize()})")
    
    # Wait for completion
    max_wait_time = 120  # 2 minutes timeout
    check_interval = 0.5
    waited_time = 0
    
    while waited_time < max_wait_time:
        if request_id in response_storage and response_storage[request_id]['completed']:
            result = response_storage[request_id]['result']
            print(f"[{request_id}] Request completed successfully")
            return result
        
        await asyncio.sleep(check_interval)
        waited_time += check_interval
    
    # Timeout
    print(f"[{request_id}] Request timed out")
    return {"search_result": [], "error": "Request timed out"}



@app.post("/restart-browser")
async def restart_browser():
    """Restart the browser (for testing purposes)"""
    cleanup_browser()
    time.sleep(2)
    initialize_browser()
    
    # Restart queue worker
    worker_thread = threading.Thread(target=queue_worker, daemon=True)
    worker_thread.start()
    
    return {"message": "Browser and queue worker restarted successfully"}

@app.get("/browser-status")
async def get_browser_status():
    """Get current browser and queue status"""
    global global_driver, queue_worker_running, response_storage
    
    browser_status = {
        "browser_active": False,
        "current_url": "N/A"
    }
    
    if global_driver:
        try:
            browser_status["browser_active"] = True
            browser_status["current_url"] = global_driver.current_url
        except Exception as e:
            browser_status["error"] = str(e)
    
    return {
        **browser_status,
        "queue_worker_running": queue_worker_running,
        "queue_size": request_queue.qsize(),
        "active_responses": len(response_storage),
        "pending_requests": [req_id for req_id, data in response_storage.items() if not data['completed']]
    }

@app.get("/queue-status")
async def get_queue_status():
    """Get detailed queue status"""
    cleanup_old_responses()  # Clean up old responses
    
    pending = [req_id for req_id, data in response_storage.items() if not data['completed']]
    completed = [req_id for req_id, data in response_storage.items() if data['completed']]
    
    return {
        "queue_size": request_queue.qsize(),
        "pending_requests": len(pending),
        "completed_requests": len(completed),
        "pending_request_ids": pending[:5],  # Show first 5
        "worker_running": queue_worker_running
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "queue_worker_running": queue_worker_running,
        "browser_active": global_driver is not None
    }
