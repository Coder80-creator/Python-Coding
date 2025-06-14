# scraper.py
import requests
from bs4 import BeautifulSoup
import re  # Import regex for cleaning price strings

# Define a fixed USD to INR conversion rate.
USD_TO_INR_RATE = 83.50


def clean_and_convert_price(price_str):
    """
    Cleans a price string, extracts the numeric value, converts it to a float,
    and then converts it to INR.
    """
    if not isinstance(price_str, str):
        return 0.0
    numeric_parts_found = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', price_str)
    if not numeric_parts_found:
        return 0.0
    try:
        numeric_price_usd = float(numeric_parts_found[0].replace(',', ''))
        return numeric_price_usd * USD_TO_INR_RATE
    except (ValueError, IndexError):
        return 0.0


def scrape_amazon(product_name):
    """
    Scrapes Amazon for a given product name, focusing on customer ratings.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    search_query = product_name.replace(' ', '+')
    search_url = f"https://www.amazon.com/s?k={search_query}"

    print(f"\n--- Scraping Amazon for: {product_name} ---")
    print(f"URL: {search_url}")

    try:
        response = requests.get(search_url, headers=headers, timeout=25)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve Amazon page: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []

    # FIXED: Using a more reliable selector for product items.
    # We look for divs with a 'data-asin' attribute, which is a unique product identifier.
    items = soup.find_all('div', {'data-asin': re.compile(r'.')})

    if not items:
        print("Debug: No items found with 'data-asin'. Trying older selectors.")
        items = soup.find_all('div', {'data-component-type': 's-search-result'})

    print(f"Found {len(items)} potential items on Amazon.")

    for item in items:
        # Ensure the item is a valid product entry and not an empty div
        if not item.find('h2'):
            continue

        title_element = item.find('h2', class_='a-size-mini') or item.find('span', class_='a-text-normal')
        price_element = item.find('span', class_='a-offscreen')
        link_element = item.find('a', class_='a-link-normal', href=True)
        image_element = item.find('img', class_='s-image')

        # FIXED: Selector for customer rating
        rating_element = item.find('span', class_='a-icon-alt')

        if title_element and price_element and link_element:
            title = title_element.get_text(strip=True)
            price_str = price_element.get_text(strip=True)
            link = "https://www.amazon.com" + link_element['href']
            image_url = image_element[
                'src'] if image_element else "https://placehold.co/100x100/E0E0E0/6C757D?text=No+Image"
            customer_rating = rating_element.get_text(strip=True) if rating_element else "Not Rated"

            numeric_inr_price = clean_and_convert_price(price_str)
            if numeric_inr_price > 0:
                display_inr_price = f"₹ {numeric_inr_price:,.2f}"
                results.append({
                    'title': title,
                    'price': display_inr_price,
                    'numeric_price': numeric_inr_price,
                    'link': link,
                    'image_url': image_url,
                    'customer_rating': customer_rating  # Changed key for clarity
                })

    print(f"Successfully processed {len(results)} Amazon results.")
    return results


def scrape_ebay(product_name):
    """
    Scrapes eBay for a given product name, focusing on seller ratings.
    """
    search_url = f"https://www.ebay.com/sch/i.html?_nkw={product_name.replace(' ', '+')}"
    print(f"\n--- Scraping eBay for: {product_name} ---")
    print(f"URL: {search_url}")

    try:
        response = requests.get(search_url, timeout=25)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve eBay page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    results = []

    for item in soup.select('.s-item'):
        title_element = item.select_one('.s-item__title')
        price_element = item.select_one('.s-item__price')
        link_element = item.select_one('.s-item__link')
        image_element = item.select_one('.s-item__image-img')

        # FIXED: Selector for seller information
        seller_info_element = item.select_one('.s-item__seller-info-text')

        if title_element and price_element and link_element:
            title = title_element.get_text(strip=True)
            if "shop with confidence" in title.lower() or "new listing" in title.lower():
                continue

            price_str = price_element.get_text(strip=True)
            link = link_element['href']
            image_url = image_element['src'] if image_element and image_element.get(
                'src') else "https://placehold.co/100x100/E0E0E0/6C757D?text=No+Image"
            seller_info = seller_info_element.get_text(
                strip=True) if seller_info_element else "Seller info not available"

            numeric_inr_price = clean_and_convert_price(price_str)
            if numeric_inr_price > 0:
                display_inr_price = f"₹ {numeric_inr_price:,.2f}"
                results.append({
                    'title': title,
                    'price': display_inr_price,
                    'numeric_price': numeric_inr_price,
                    'link': link,
                    'image_url': image_url,
                    'seller_info': seller_info  # Changed key for clarity
                })

    print(f"Successfully processed {len(results)} eBay results.")
    return results


def scrape_all_sites(product_name):
    """
    Scrapes both Amazon and eBay, sorts the results, and returns them.
    """
    amazon_results = scrape_amazon(product_name)
    ebay_results = scrape_ebay(product_name)

    amazon_results_sorted = sorted(amazon_results, key=lambda x: x['numeric_price'])
    ebay_results_sorted = sorted(ebay_results, key=lambda x: x['numeric_price'])

    # The dictionary keys ('customer_rating', 'seller_info') now reflect the source of the rating.
    return {
        'amazon': amazon_results_sorted,
        'ebay': ebay_results_sorted
    }
