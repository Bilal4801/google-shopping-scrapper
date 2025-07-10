import os
import random
import time
from fastapi import FastAPI, Request
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent


# app = FastAPI()


def scrape_google_shopping(query):

    USER_AGENT = UserAgent()
    options = uc.ChromeOptions()
    # Configure Edge options
    # options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={USER_AGENT.random}")

    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    # Setup Edge WebDriver
    # driver = webdriver.Edge(options=options)

    try:
        # 1. go to google shopping
        driver.get("https://www.google.com/shopping?udm=28")
        time.sleep(10)  # wait for the page to load


        # 2. upload via send_keys on the **second** input
        inputs = driver.find_element(By.ID, 'APjFqb')
        inputs.send_keys(query)
        time.sleep(5)  # wait for the input to be processed


        driver.find_element(By.XPATH, '//*[@id="tsf"]/div[1]/div[1]/div[2]/button').click()
        time.sleep(6)  # wait for the search results to load
        # time.sleep(110)  # wait for the search results to load


        print("Search completed.")
        
        # sitekey = "6LfwuyUTAAAAAOAmoS0fdqijC2PbbdH4kjq62Y1b"
        # API_KEY = "9f45229e2e8317c07c3f0eace3eeeab2"


        # captcha_id = requests.post("http://2captcha.com/in.php",
        # data={
        #     "key": API_KEY,
        #     "method": "userrecaptcha",
        #     "googlekey": sitekey,
        #     "pageurl": "https://www.google.com/shopping?udm=28",
        #     "json": 1,
        # },
        # ).json()["request"]

        # print("Captcha ID:", captcha_id)

        # # === Step 5: Poll for solution ===
        # solution = None
        # for _ in range(30):
        #     res = requests.get(
        #         f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}&json=1"
        #     ).json()
            
        #     if res["status"] == 1:
        #         solution = res["request"]
        #         print("Captcha Solved:", solution)
        #         break
        #     time.sleep(10)

        # if not solution:
        #     raise Exception("Captcha could not be solved in time.")

        # # === Step 6: Inject the solution into the page ===
        # driver.execute_script(
        #     f'document.getElementById("g-recaptcha-response").innerHTML = "{solution}";'
        # )
        # driver.execute_script(
        #     'var element = document.getElementById("g-recaptcha-response");'
        #     'element.style.display = "block";'
        # )

        # time.sleep(2)

        # print("captcha solved successfully")



        # time.sleep(30)





        # Optionally scroll down (in case lazy loading or carousels)
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2) 

        try:
            wait = WebDriverWait(driver, 10)
            container = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.top-pla-group-inner")
            ))

            # Get inner HTML of the container
            inner_html = container.get_attribute("innerHTML")
            # print(inner_html, "inner html")


            soup = BeautifulSoup(inner_html, "html.parser")
            print(soup.prettify(), "soup")

            # Now extract all links inside it
            anchors = container.find_elements(By.TAG_NAME, "a")
            # for anchor in anchors:
            #     print(anchor, "anchor found in container")
            print(f"Found {len(anchors)} links")
            # for a in anchors:
            #     print(a.get_attribute("href"))

            # Use a set to store unique links
            unique_links = set()

            for a in anchors:
                href = a.get_attribute("href")
                if href and href not in unique_links:
                    unique_links.add(href)
                    print(href)
                else:
                    continue
            
            # print(unique_links, "unique links found")
            time.sleep(2)  # wait for the items to load

            return unique_links

        except:
            try:
                driver.save_screenshot("screenshot1.png")
                container = driver.find_element(By.CLASS_NAME, "Z8PPnf")
                print("Container found.", container)

                # Get all divs with class "gXGikb" (individual product cards)
                product_divs = driver.find_elements("css selector", "div.gXGikb")

                print("Exception case 1", "Number of product divs:", len(product_divs))
                # Now extract info from each div
                
                product_results = []
                for div in product_divs:
                    soup = BeautifulSoup(div.get_attribute("innerHTML"), "html.parser")

                    # Extract product name
                    name_tag = soup.find("div", class_="PZPZlf")
                    name = name_tag.get("data-entityname") if name_tag else None

                    # Extract price (Google uses multiple formats, check common class name)
                    price_tag = soup.find("span", string=lambda t: "$" in t if t else False)
                    price = price_tag.text.strip() if price_tag else None

                    # Extract rating (look for aria-label like "Rated 4.5 out of 5")
                    rating_tag = soup.find("span", attrs={"aria-label": True})
                    rating = rating_tag["aria-label"] if rating_tag else None

                    # Extract image src
                    image_tag = soup.find("img", class_="VeBrne")
                    image_url = image_tag.get("src") if image_tag else None

                    product_results.append({
                        "name": name,
                        "price": price,
                        "rating": rating,
                        "image": image_url
                    })

                return product_results
            
            except:
                driver.save_screenshot("screenshot2.png")
                # Find the main div with class 'qaQ0y'
                main_div = driver.find_element(By.XPATH, '//*[@id="rso"]/div[1]/div/div/g-card/div/div/div/div/div[2]/product-viewer-group/g-card/div/div[1]/div')

                # Find the <ul> inside it
                ul = main_div.find_element(By.TAG_NAME, "ul")

                # Get all <div class="Ez5pwe"> inside that <ul>
                items = ul.find_elements(By.CLASS_NAME, "Ez5pwe")
                print("Exception case 2", "Number of product divs:", len(items))

                product_results = []
                for no, item in enumerate(items):
                    soup = BeautifulSoup(item.get_attribute("innerHTML"), "html.parser")

                    # Extracting Name
                    name_tag = soup.select_one('div[aria-labelledby]')
                    name = name_tag['title'] if name_tag and name_tag.has_attr('title') else None

                    # Extracting Price (based on typical class or pattern, assuming it's inside span or div)
                    price = None
                    price_tag = soup.find('span', string=lambda text: text and '$' in text)
                    if price_tag:
                        price = price_tag.text.strip()

                    # Extracting Rating (search for numbers with decimal like 4.5/5 etc.)
                    rating = None
                    for span in soup.find_all('span'):
                        text = span.get_text(strip=True)
                        if '/' in text and any(char.isdigit() for char in text):
                            rating = text
                            break

                    # Extracting Image URL
                    img_tag = soup.find('img')
                    image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None

                    # Final Result
                    product_info = {
                        'name': name,
                        'price': price,
                        'rating': rating,
                        'image_url': image_url
                    }

                    product_results.append(product_info)
                
                return product_results
            
    finally:
        driver.quit()



# @app.post("/api/google_shopping")
# async def main_function():
#     data = scrape_google_shopping("LED spinner toys")
#     print(data)

data = scrape_google_shopping("LED Spinner")
print(data)  # This will print None since the function does not return anything
















        

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