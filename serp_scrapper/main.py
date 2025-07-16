import os
import random
from fastapi import FastAPI, Request
import time
from utils import GoogleShoppingData
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re


app = FastAPI()


def extract_price(price_str):
    """
    Extracts numeric price from a string and returns it as a float.
    If no valid price is found, returns None.
    """
    match = re.search(r'[\d,.]+', price_str)
    if match:
        # Remove commas and convert to float
        try:
            return float(match.group().replace(',', ''))
        except ValueError:
            return None
    return None

async def scrape_google_shopping(query):

    options = uc.ChromeOptions()
    # Normal flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Set a consistent but believable User-Agent
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

    # Mimic real screen size
    width = random.randint(1280, 1920)
    height = random.randint(720, 1080)
    options.add_argument(f"--window-size={width},{height}")

    # Download preferences
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)

    # Create driver (uc takes care of the stealth part automatically)
    driver = uc.Chrome(options=options, use_subprocess=True)
    
    # Patch webdriver-related JS variables
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            });
            Object.defineProperty(navigator, 'languages', {
              get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'platform', {
              get: () => 'Win32'
            });
            Object.defineProperty(navigator, 'vendor', {
              get: () => 'Google Inc.'
            });
            window.chrome = {
              runtime: {},
              // Add more spoofed properties if needed
            };
        """
    })

    wait = WebDriverWait(driver, 30)

    try:
        # 1. go to google shopping
        driver.get("https://www.google.com/shopping?udm=28")
        time.sleep(3)  # wait for the page to load

        # 2. upload via send_keys on the **second** input
        inputs = driver.find_element(By.ID, 'oDgap')
        inputs.send_keys(query)
        time.sleep(2)  # wait for the input to be processed


        driver.find_element(By.XPATH, '//*[@id="tsf"]/div[1]/div[1]/div[1]/button').click()
        time.sleep(3)  # wait for the search results to load
        print("Search completed.")
        
        # Optionally scroll down (in case lazy loading or carousels)
        driver.execute_script("window.scrollBy(0, 300);")

        try:
            container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.pla-unit-container')))

            if not container:
                print('⚠️ Timeout waiting for product container.')
                return "No products found."

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            results = []
            print("try case run")

            for card in soup.select('div.pla-unit-container'):
                name_tag = card.select_one('.pla-unit-title-link span')
                price_tag = card.select_one('.T4OwTb span')
                img_tag = card.select_one('.pla-unit-img-container img')
                merchant_tag = card.select_one('.LbUacb span')
                rating_tag = card.select_one('span[aria-label*="Rated"]')
                product_url = card.select_one('a.pla-unit-title-link')['href']

                pr_tag = price_tag.get_text(strip=True)
                price_float = extract_price(pr_tag)

                results.append({
                    "position": None,
                    "title": name_tag.get_text(strip=True) if name_tag else None,
                    "product_link": product_url if product_url else None,
                    "product_id": None,
                    "serpapi_product_api": None,
                    "immersive_product_page_token": None,
                    "serpapi_immersive_product_api": None,
                    "source": merchant_tag.get_text(strip=True) if merchant_tag else None,
                    "source_icon": None,
                    "price": price_tag.get_text(strip=True) if price_tag else None,
                    "extracted_price": price_float,
                    "rating": rating_tag['aria-label'] if rating_tag else None,
                    "reviews": None,
                    "thumbnail": img_tag['src'] if img_tag and img_tag.has_attr('src') else None,
                    "delivery": None
                    })

            driver.quit()
            dict = {"search_result": results}
            return dict

        except:
            try:
                container = driver.find_element(By.CLASS_NAME, "Z8PPnf")
                product_divs = container.find_elements(By.CSS_SELECTOR, "div.gXGikb")
                print("Exception case 1- Found product divs:", len(product_divs))

                product_results = []
                for div in product_divs:
                    soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")

                    # Extract product name
                    name_tag = soup.find("div", class_="gkQHve")
                    name = name_tag.get_text(strip=True) if name_tag else None

                    # Extract product ID
                    data_id = soup.find("div", class_="liKJmf wTrwWd")
                    product_id = data_id.get("data-cid") if data_id else None

                    # Extract price
                    price_tag = soup.find("span", class_="lmQWe")
                    price = price_tag.get_text(strip=True) if price_tag else None

                    try:
                        # Extract rating - Only if aria-label contains "Rated"
                        rating_tag = soup.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                        rating = rating_tag["aria-label"] if rating_tag else None

                    except:
                        rating = None

                    # Extract image
                    image_tag = soup.find("img", class_="VeBrne")
                    image_url = image_tag.get("src") if image_tag  else None

                    extract_price_value = extract_price(price)
                    product_results.append({
                        "position": None,
                        "title": name,
                        "product_link": None,
                        "product_id": product_id,
                        "serpapi_product_api": None,
                        "immersive_product_page_token": None,
                        "serpapi_immersive_product_api": None,
                        "source": None,
                        "source_icon": None,
                        "price": price,
                        "extracted_price": extract_price_value,
                        "rating": rating,
                        "reviews": None,
                        "thumbnail": image_url,
                        "delivery": None
                    })

                driver.quit()
                dict = {"search_result": product_results}
                return dict

            except:
                try:
                    html_content = driver.page_source
                    soup = BeautifulSoup(html_content, "html.parser")
                    results = []

                    # New DOM structure: UL > LI.I8iMf
                    product_list = soup.select("ul.lvS33d li.I8iMf")
                    print(f"Exception case 2- Found, {len(product_list)} product cards")

                    for card in product_list:
                        # Product Name
                        name_tag = card.select_one("div.gkQHve")
                        name = name_tag.get_text(strip=True) if name_tag else None

                        data_id = card.find("div", class_="MtXiu mZ9c3d wYFOId M919M W5CKGc wTrwWd")
                        product_id = data_id.get("data-cid") if data_id else None

                        # Price
                        price_tag = card.find("span", class_="lmQWe")
                        price = price_tag.get_text(strip=True) if price_tag else None

                        try:
                            # Rating
                            rating_tag = card.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                            rating = rating_tag["aria-label"] if rating_tag else None
                        except:
                            rating = None

                        # Image
                        image_tag = card.find("img", class_="VeBrne")
                        image_url = image_tag.get("src") if image_tag else None

                        # Product URL - optional, not always available
                        link_tag = card.find("a", href=True)
                        product_url = link_tag["href"] if link_tag else None

                        extract_price_value = extract_price(price)
                        results.append({
                            "position": None,
                            "title": name,
                            "product_link": product_url,
                            "product_id": product_id,
                            "serpapi_product_api": None,
                            "immersive_product_page_token": None,
                            "serpapi_immersive_product_api": None,
                            "source": None,
                            "source_icon": None,
                            "price": price,
                            "extracted_price": extract_price_value,
                            "rating": rating,
                            "reviews": None,
                            "thumbnail": image_url,
                            "delivery": None
                        })

                    driver.quit()
                    
                    dict = {"search_result": results}
                    return dict

                except:
                    # Wait for items to be visible
                    items = driver.find_elements(By.CSS_SELECTOR, "li.YBo8bb")
                    print("Fallback - Exception Case: 3", len(items), "products")

                    product_results = []

                    for no, item in enumerate(items):
                        soup = BeautifulSoup(item.get_attribute("innerHTML"), "html.parser")

                        # Extracting Name
                        name = None
                        name_tag = soup.select_one("div.gkQHve.SsM98d.RmEs5b.gGeaLc")
                        if name_tag:
                            name = name_tag.get_text(strip=True)

                        # Extracting Price
                        price = None
                        price_tag = soup.find("span", class_="lmQWe")
                        if price_tag:
                            price = price_tag.get_text(strip=True)

                        # Extracting Rating
                        rating = None
                        rating_tag = soup.find("span", class_="z3HNkc")
                        if rating_tag and rating_tag.has_attr("aria-label"):
                            rating = rating_tag["aria-label"]

                        # Extracting Image URL
                        image_url = None
                        image_tag = soup.find("img", class_="FsH7wb wtYWhc")
                        if not image_tag:
                            image_tag = soup.find("img", class_="uhHOwf ez24Df")
                        if image_tag and image_tag.has_attr("src"):
                            image_url = image_tag["src"]

                        extract_price_value = extract_price(price)
                        product_info ={
                            "position": None,
                            "title": name,
                            "product_link": None,
                            "product_id": None,
                            "serpapi_product_api": None,
                            "immersive_product_page_token": None,
                            "serpapi_immersive_product_api": None,
                            "source": None,
                            "source_icon": None,
                            "price": price,
                            "extracted_price": extract_price_value,
                            "rating": rating,
                            "reviews": None,
                            "thumbnail": image_url,
                            "delivery": None
                        }

                        product_results.append(product_info)

                    driver.quit()
                    dict = {"search_result": product_results}
                    return dict
                        
    finally:
        driver.quit()



@app.post("/get-products")
async def main_function(search_query:str, selected_country: str):

    user_query = search_query
    selected_country = selected_country
    data = await scrape_google_shopping(user_query)
    return data











# inside_url = driver.find_element(By.XPATH, '//*[@id="rSanR"]/div[4]/div/div/div/div[3]/div/div[7]/div/div/div/div/div[1]/div[1]/div[2]/div')
# soup = BeautifulSoup(inside_url, 'html.parser')

# offers = []

# for offer in soup.select('div[role="listitem"]'):
#     try:
#         retailer = offer.select_one('.hP4iBf.gUf0b.uWvFpd')
#         price = offer.select_one('.GBgquf, .Pgbknd, .wepMxd')
#         product = offer.select_one('.Rp8BL.CpcIhb.y1FcZd.rYkzq')
#         availability = offer.select_one('.gASiG.jvP2Jb.jIpmhc')
#         url = offer.select_one('a')['href']

#         offers.append({
#             'retailer': retailer.text.strip() if retailer else None,
#             'price': price.text.strip() if price else None,
#             'product': product.text.strip() if product else None,
#             'availability': availability.text.strip() if availability else None,
#             'url': url
#         })
#     except Exception as e:
#         print("Error parsing an offer:", e)

# # Output
# for offer in offers:
#     print(offer, "offer 1")
