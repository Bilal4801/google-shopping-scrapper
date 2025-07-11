import os
import time
import random
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
import urllib.parse as urlparse



API_KEY = "9f45229e2e8317c07c3f0eace3eeeab2"

# === Setup undetected Chrome driver with anti-detection options ===
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-extensions')
options.add_argument('--disable-popup-blocking')
options.add_argument('--lang=en-US,en;q=0.9')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.7204.97 Safari/537.36')
# if os.name != 'nt':
# options.add_argument('--headless=new')

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 15)


# === CAPTCHA Helpers ===
def is_captcha_page():
    try:
        driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
        return True
    except:
        return False

def extract_sitekey():
    try:
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
        src = iframe.get_attribute('src')
        parsed = urlparse.urlparse(src)
        params = urlparse.parse_qs(parsed.query)
        return params.get('k', [None])[0]
    except:
        return None

def solve_captcha(sitekey, page_url):
    print(f"[+] Submitting CAPTCHA to 2Captcha: sitekey={sitekey}")
    resp = requests.post('http://2captcha.com/in.php', data={
        'key': API_KEY,
        'method': 'userrecaptcha',
        'googlekey': sitekey,
        'pageurl': page_url,
        'json': 1
    }).json()
    if resp.get('status') != 1:
        print('❌ 2Captcha error:', resp.get('request'))
        return None
    task_id = resp['request']
    print(f"[✔] CAPTCHA submitted. Task ID: {task_id}")

    for i in range(60):
        time.sleep(5)
        result = requests.get('http://2captcha.com/res.php', params={
            'key': API_KEY,
            'action': 'get',
            'id': task_id,
            'json': 1
        }).json()
        if result.get('status') == 1:
            print('[✅] CAPTCHA token received.')
            return result['request']
        print(f'...waiting ({i+1}/60)')
    print('❌ Timeout solving CAPTCHA')
    return None


def inject_token(token):
    driver.execute_script('''
        document.getElementById('g-recaptcha-response').style.display='block';
        document.getElementById('g-recaptcha-response').value=arguments[0];
        if(typeof submitCallback==='function') submitCallback(arguments[0]);
        else document.getElementById('captcha-form')?.submit();
    ''', token)
    time.sleep(3)

# === Helper to wait for one of many product containers ===
def wait_for_product_container():
    try:
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.pla-unit-container')))
    except TimeoutException:
        return None


# === Scrape Google Shopping ===
def scrape_google_shopping(query):
    try:
        print(f"\n🔍 Navigating to Google Shopping")
        driver.get('https://www.google.com/shopping?hl=en&gl=us&psb=1')
        time.sleep(5)

        if is_captcha_page():
            print("🧩 CAPTCHA detected")
            key = extract_sitekey()
            if key:
                token = solve_captcha(key, driver.current_url)
                if token:
                    inject_token(token)

        print(f"🔎 Typing query: {query}")
        search_input = wait.until(EC.presence_of_element_located((By.NAME, 'q')))
        search_input.clear()
        search_input.send_keys(query)
        search_input.submit()
        time.sleep(5)

        if is_captcha_page():
            print("🧩 CAPTCHA reappeared after search")
            key = extract_sitekey()
            if key:
                token = solve_captcha(key, driver.current_url)
                if token:
                    inject_token(token)

        container = wait_for_product_container()
        if not container:
            print('⚠️ Timeout waiting for product container.')
            driver.save_screenshot('no_results.png')
            return []

        # Scroll to load all products
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = []

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
                'merchant': merchant_tag.get_text(strip=True) if merchant_tag else None,
                'rating': rating_tag['aria-label'] if rating_tag else None,
                'url': product_url if product_url else None
            })

        print(f"✅ Found {len(results)} products.")
        return results

    except Exception as e:
        print("❌ Unhandled error:", e)
        driver.save_screenshot('error_debug.png')
        return []
    finally:
        driver.quit()


# === Main ===
if __name__ == '__main__':
    search_term = 'shirts'
    products = scrape_google_shopping(search_term)
    for p in products:
        print(p)
    input("📦 Done. Press ENTER to exit...")