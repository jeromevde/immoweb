#%%
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import yaml
import random
import time

# List of realistic User-Agent strings to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

def fetch_listings(url):
    # Set up Selenium with headless Chrome
    options = Options()
    options.headless = True  # Run in headless mode (no visible browser window)
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")  # Random User-Agent
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
    options.add_argument("--no-sandbox")  # Required for some environments
    options.add_argument("--disable-dev-shm-usage")  # Avoid memory issues
    options.add_argument("--disable-gpu")  # Disable GPU for headless mode
    options.add_argument("accept-language=en-US,en;q=0.9")
    options.add_argument("referer=https://www.immoweb.be/")

    # Specify ChromeDriver path if not in PATH (uncomment and adjust if needed)
    # service = Service('/path/to/chromedriver')
    # driver = webdriver.Chrome(service=service, options=options)
    driver = webdriver.Chrome(options=options)  # Assumes chromedriver is in PATH

    try:
        # Navigate to the URL
        print(f"Fetching URL with Selenium: {url}")
        driver.get(url)
        
        # Wait for JavaScript to load (adjust time as needed)
        time.sleep(3)  # Increase if content loads slowly
        
        # Optional: Scroll to trigger lazy-loaded content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Wait for additional content to load
        
        # Get the rendered page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Debugging: Save or print page source to verify content
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved page source to 'page_source.html' for debugging.")

        listings = []
        for li in soup.find_all('li', class_='search-results__item'):
            article = li.find('article')
            if not article:
                continue
            # Extract link
            title_tag = article.find('a', class_='card__title-link')
            link = title_tag['href'] if title_tag else None
            # Extract price
            price_tag = article.find('p', class_='card--result__price')
            price = price_tag.get_text(strip=True) if price_tag else None
            # Extract bedrooms and square meters with robust parsing
            info_tag = article.find('p', class_='card__information--property')
            bedrooms = None
            sqm = None
            if info_tag:
                info_text = info_tag.get_text(' ', strip=True).lower()
                # Flexible bedroom parsing
                if 'bdr.' in info_text or 'bedroom' in info_text:
                    parts = info_text.split('bdr.' if 'bdr.' in info_text else 'bedroom')
                    bedrooms = parts[0].strip().split()[-1] if parts[0].strip() else None
                # Flexible square meter parsing
                if 'm²' in info_text or 'm2' in info_text:
                    parts = info_text.split('m²' if 'm²' in info_text else 'm2')
                    sqm = parts[0].strip().split()[-1] if parts[0].strip() else None
            # Extract address
            address_tag = article.find('p', class_='card--results__information--locality')
            address = address_tag.get_text(strip=True) if address_tag else None
            # Extract picture
            img_tag = article.find('img', class_='card__media-picture')
            picture = img_tag['src'] if img_tag else None
            listings.append({
                'link': link,
                'price': price,
                'bedrooms': bedrooms,
                'sqm': sqm,
                'address': address,
                'picture': picture
            })
        if not listings:
            print("No listings found. Check 'page_source.html' to verify content.")
        return listings
    except Exception as e:
        print(f"Selenium Error: {e}")
        return []
    finally:
        driver.quit()

def build_url_from_config(config_path):
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml file not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        return None
    
    # Base URL
    base_url = f"https://www.immoweb.be/{config.get('language', 'en')}/search-{config.get('rooms', 3)}-rooms/{config.get('propertyType', 'house')}/for-sale"
    
    # Postal codes formatting
    postal_codes = [str(pc) for pc in config.get('postalCodes', [])]
    postal_codes_str = ','.join(postal_codes)
    
    # Parameters in the correct order
    params = [
        f"countries={config.get('countries', 'BE')}",
        f"maxBedroomCount={config.get('maxBedroomCount', 3)}",
        f"minBedroomCount={config.get('minBedroomCount', 3)}",
        f"postalCodes={postal_codes_str}",
        f"maxPrice={config.get('maxPrice', 700000)}",
        f"page={config.get('page', 1)}",
        f"orderBy={config.get('orderBy', 'newest')}"
    ]
    
    # Join parameters with '&' to form the query string
    query_string = '&'.join(params)
    
    return f"{base_url}?{query_string}"

def main():
    url = build_url_from_config('config.yaml')
    if not url:
        return
    print("Generated URL:", url)
    listings = fetch_listings(url)
    if listings:
        for l in listings:
            print(l)
    else:
        print("No listings found or request failed.")

if __name__ == "__main__":
    main()
#%%