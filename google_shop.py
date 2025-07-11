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


app = FastAPI()


async def scrape_google_shopping(query):

    options = uc.ChromeOptions()

    # # Configure Edge options
    # # options = Options()

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

    # Setup Edge WebDriver
    # driver = webdriver.Edge(options=options)

    try:
        # 1. go to google shopping
        driver.get("https://www.google.com/shopping?udm=28")
        time.sleep(6)  # wait for the page to load

        # 2. upload via send_keys on the **second** input
        inputs = driver.find_element(By.ID, 'oDgap')
        inputs.send_keys(query)
        time.sleep(5)  # wait for the input to be processed


        driver.find_element(By.XPATH, '//*[@id="tsf"]/div[1]/div[1]/div[1]/button').click()
        time.sleep(5)  # wait for the search results to load
        # time.sleep(110)  # wait for the search results to load
        print("Search completed.")
        
        # Optionally scroll down (in case lazy loading or carousels)
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(1) 

        # html_content = driver.page_source
        # with open("captcha_page.html", "w", encoding="utf-8") as file:
        #     file.write(html_content)

        try:
            # driver.save_screenshot("SS1.png")
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

                results.append({
                    'name': name_tag.get_text(strip=True) if name_tag else None,
                    'price': price_tag.get_text(strip=True) if price_tag else None,
                    'image': img_tag['src'] if img_tag and img_tag.has_attr('src') else None,
                    'rating': rating_tag['aria-label'] if rating_tag else None,
                    'product_url': product_url if product_url else None
                    # 'merchant': merchant_tag.get_text(strip=True) if merchant_tag else None,
                })

            driver.quit()
            return results

        except:
            try:
                # driver.save_screenshot("SS2.png")
                container = driver.find_element(By.CLASS_NAME, "Z8PPnf")
                product_divs = container.find_elements(By.CSS_SELECTOR, "div.gXGikb")
                print("Exception case 1- Found product divs:", len(product_divs))

                product_results = []
                for div in product_divs:
                    soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")

                    # Extract product name
                    name_tag = soup.find("div", class_="gkQHve")
                    name = name_tag.get_text(strip=True) if name_tag else None

                    # Extract price
                    price_tag = soup.find("span", class_="lmQWe")
                    price = price_tag.get_text(strip=True) if price_tag else None

                    # Extract rating - Only if aria-label contains "Rated"
                    rating_tag = soup.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                    rating = rating_tag["aria-label"] if rating_tag else None

                    # Extract image
                    image_tag = soup.find("img", class_="VeBrne")
                    image_url = image_tag.get("src") if image_tag  else None

                    product_results.append({
                        "name": name,
                        "price": price,
                        "rating": rating,
                        "image": image_url,
                        "product_url": None
                    })

                driver.quit()
                return product_results
            
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

                        # Price
                        price_tag = card.find("span", class_="lmQWe")
                        price = price_tag.get_text(strip=True) if price_tag else None

                        # Rating
                        rating_tag = card.find("span", attrs={"aria-label": lambda x: x and "Rated" in x})
                        rating = rating_tag["aria-label"] if rating_tag else None

                        # Image
                        image_tag = card.find("img", class_="VeBrne")
                        image_url = image_tag.get("src") if image_tag else None

                        # Product URL - optional, not always available
                        link_tag = card.find("a", href=True)
                        product_url = link_tag["href"] if link_tag else None

                        results.append({
                            "name": name,
                            "price": price,
                            "rating": rating,
                            "image": image_url,
                            "product_url": product_url
                        })

                    driver.quit()
                    return results if results else "❌ No products extracted."

                except:
                    # driver.save_screenshot("SS3.png")
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

                        product_info = {
                            "name": name,
                            "price": price,
                            "rating": rating,
                            "image": image_url,
                            "product_url": None
                        }

                        product_results.append(product_info)

                    driver.quit()
                    return product_results
                        
    finally:
        driver.quit()




@app.post("/api/google_shopping")
async def main_function(data: GoogleShoppingData):

    user_query = data.query
    data = await scrape_google_shopping(user_query)
    return data














        



















# Optionally scroll down (in case lazy loading or carousels)
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # time.sleep(3)  # give JS time to render


        # # Wait for container to be visible
        # container = WebDriverWait(driver, 15).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='list']"))
        # )
        # print("Container found.")

        # # Now get all list items inside it
        # items = container.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
        # print(items, f"Found {len(items)} items.")

        # for i, item in enumerate(items, 1):
        #     try:
        #         product_name = item.find_element(By.CSS_SELECTOR, "div[role='gkQHve SsM98d RmEs5b']").text
        #     except:
        #         product_name = "N/A"
            
        #     try:
        #         price = item.find_element(By.CSS_SELECTOR, "div[role='lmQWe']").text
        #     except:
        #         price = "N/A"

        #     try:
        #         description = item.find_element(By.CSS_SELECTOR, "div[role='n7emVc QgzbTc RmEs5b']").text
        #     except:
        #         description = "N/A"

        #     # try:
        #     #     link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
        #     # except:
        #     #     link = "N/A"

        #     print(f"--- Item #{i} ---")
        #     print(f"Name       : {product_name}")
        #     print(f"Price      : {price}")
        #     print(f"Description: {description}")
        #     print(f"Link       : {link}")



        # for item in get_all_divs:
        #     try:
        #         title = item.find_element(By.CLASS_NAME, 'sh-no__title').text
        #         price = item.find_element(By.CLASS_NAME, 'a8Pemb').text
        #         link = item.find_element(By.CLASS_NAME, 'sh-no__link').get_attribute('href')
        #         print(f"Title: {title}")
        #         print(f"Price: {price}")
        #         print(f"Link: {link}")
        #         print("-" * 50)
        #     except Exception as e:
        #         print(f"Error processing item: {e}")