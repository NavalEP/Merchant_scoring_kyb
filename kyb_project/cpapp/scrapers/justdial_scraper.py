import os
import pandas as pd
import time
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import random
import re
import os
def get_clinic_cards_count(page):
    """Get the current count of clinic cards on the page"""
    return page.evaluate("""() => {
        return document.querySelectorAll('div.jsx-ee3d18659dbf4034.resultbox_info').length;
    }""")

def scroll_page(page, max_attempts=8):
    """
    Enhanced scroll page function to load ALL clinics on the page
    """
    print("Starting slow scrolling to load all clinic entries...")
    
    # Initial count of clinic cards
    initial_count = get_clinic_cards_count(page)
    current_count = initial_count
    print(f"Initial clinic count: {initial_count}")
    
    # Get page height
    page_height = page.evaluate("document.body.scrollHeight")
    attempts = 0
    last_new_content = 0  # Track when we last found new content
    
    while attempts < max_attempts:
        # Scroll down incrementally with human-like behavior
        for _ in range(random.randint(2, 4)):
            # Calculate dynamic scroll amount
            scroll_amount = random.randint(200, 400)
            
            # Smooth scroll with dynamic timing
            page.evaluate(f"""
                window.scrollBy({{
                    top: {scroll_amount},
                    left: 0,
                    behavior: 'smooth'
                }});
            """)
            
            # Add random mouse movements
            viewport_size = page.viewport_size
            page.mouse.move(
                random.randint(0, viewport_size['width']),
                random.randint(0, viewport_size['height'])
            )
            
            # Variable delay between scroll steps
            time.sleep(random.uniform(1, 2))
        
        # Check for new content
        new_count = get_clinic_cards_count(page)
        if new_count > current_count:
            print(f"Found {new_count} clinics (added {new_count - current_count} new)")
            current_count = new_count
            last_new_content = 0  # Reset attempt counter when we find new content
        else:
            last_new_content += 1
        
        # Get updated page height
        new_height = page.evaluate("document.body.scrollHeight")
        
        # If we've reached the bottom and haven't found new content in several attempts
        if new_height <= page_height and last_new_content >= 3:
            attempts += 1
            # Try scrolling back up slightly to trigger any lazy loading
            if random.random() < 0.4:  # 40% chance
                page.evaluate(f"""
                    window.scrollBy({{
                        top: {random.randint(-300, -150)},
                        left: 0,
                        behavior: 'smooth'
                    }});
                """)
                time.sleep(random.uniform(1, 2))
        else:
            page_height = new_height
        
        # Add random pauses to seem more human-like
        if random.random() < 0.2:  # 20% chance
            time.sleep(random.uniform(2, 3))
    
    final_count = get_clinic_cards_count(page)
    print(f"Finished scrolling. Total clinics loaded: {final_count}")
    return final_count

def extract_doctor_links(page, soup):
    """Extract doctor links from clinic detail page"""
    doctor_links = []
    
    # Find all doctor carousel items
    doctor_elements = soup.select('div.carousel_item a[href*="/Dr-"]')
    
    for doctor_elem in doctor_elements:
        try:
            doctor_url = doctor_elem.get('href', '')
            if doctor_url:
                # Make sure URL is absolute
                if not doctor_url.startswith('http'):
                    doctor_url = 'https://www.justdial.com' + doctor_url
                
                # Get doctor name and specialization if available using the updated selectors
                doctor_name = doctor_elem.select_one('div.jddtl_slide_mtext.font18.fw500.color111.line_clamp_1')
                doctor_spec = doctor_elem.select_one('div.jddtl_slide_stext.font14.fw400.color555.line_clamp_3')
                doctor_rating = doctor_elem.select_one('div.moreoptions_rateavg.font18.fw700.color111.mr-8')
                
                # If the specific selectors don't work, try more general ones as fallback
                if not doctor_name:
                    doctor_name = doctor_elem.select_one('.jddtl_slide_mtext')
                if not doctor_spec:
                    doctor_spec = doctor_elem.select_one('.jddtl_slide_stext')
                if not doctor_rating:
                    doctor_rating = doctor_elem.select_one('.moreoptions_rateavg')
                
                doctor_info = {
                    'doctor_url': doctor_url,
                    'doctor_name': doctor_name.text.strip() if doctor_name else "Not available",
                    'specialization': doctor_spec.text.strip() if doctor_spec else "Not available",
                    'rating': doctor_rating.text.strip() if doctor_rating else "Not available"
                }
                
                doctor_links.append(doctor_info)
        except Exception as e:
            print(f"Error extracting doctor link: {str(e)}")
            continue
    
    return doctor_links

def generate_sql_inserts(df, table_name):
    """Generate SQL INSERT statements from DataFrame"""
    sql_statements = []
    
    for _, row in df.iterrows():
        columns = ', '.join(df.columns)
        values = ', '.join([f'"{str(val)}"' if val is not None else "NULL" for val in row])
        sql_statements.append(f"INSERT INTO {table_name} ({columns}) VALUES ({values});")
    
    return '\n'.join(sql_statements)

def save_to_database(df, session):
    """Save scraped data to database using SQLAlchemy session"""
    # Temporarily disable database saving
    print("Database saving is temporarily disabled")
    return False

def scroll_detail_page(page, max_scroll=5):
    """
    Scroll a detail page to load dynamic content without repeated calls to clinic counter
    """
    print("Scrolling clinic detail page to load content...")
    
    page_height = page.evaluate("document.body.scrollHeight")
    
    # Simple scrolling for detail pages
    for i in range(max_scroll):
        # Scroll down incrementally
        scroll_amount = random.randint(300, 600)
        
        page.evaluate(f"""
            window.scrollBy({{
                top: {scroll_amount},
                left: 0,
                behavior: 'smooth'
            }});
        """)
        
        # Add random mouse movements
        viewport_size = page.viewport_size
        page.mouse.move(
            random.randint(0, viewport_size['width']),
            random.randint(0, viewport_size['height'])
        )
        
        # Variable delay between scroll steps
        time.sleep(random.uniform(0.8, 1.5))
        
        # Check if we're at the bottom
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height <= page_height:
            break
        
        page_height = new_height
    
    # Scroll back up to trigger any lazy loading
    page.evaluate("""
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    """)
    time.sleep(1)

def scrape_justdial_clinics(location, category, num_pages=3, save_to_db=True, verbose=False):
    """
    Scrape ALL clinic information from Justdial for given pages
    
    Args:
        location (str): City name (e.g., 'Bangalore', 'Delhi')
        category (str): Category to search (e.g., 'Clinics', 'Hospitals')
        num_pages (int): Number of pages to scrape
        save_to_db (bool): Whether to save data to database
        verbose (bool): Whether to print detailed logs
    """
    # Generate URL with proper URL encoding for location
    location = location.replace(" ", "-").title()
    category = category.replace(" ", "-").title()
    
    # Use the base URL format with additional parameters to avoid access denial
    base_url = f"https://www.justdial.com/{location}/{category}/nct-10101647?trkid=2986-{location.lower()}-fcat&term={category}"
    
    # Create timestamp for file naming
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Store all scraped businesses
    all_businesses = []
    seen_urls = set()  # Track unique URLs to avoid duplicates
    
    # Prepare output file path
    output_file = f"output/justdial_{location}_{category}_{timestamp}.csv"
    
    with sync_playwright() as p:
        # Launch browser with additional configurations
        browser = p.chromium.launch(
            headless=False,  # Set to False to see what's happening
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized'
            ]
        )
        
        # Set up browser context with additional configurations
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            has_touch=True,
            is_mobile=False,
            locale='en-US',
        )
        
        # Add stealth mode script
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {},
                webstore: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        current_page = 1
        max_retries = 3  # Maximum number of retries per page
        
        while current_page <= num_pages:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    page = context.new_page()
                    
                    # Set longer timeouts
                    page.set_default_navigation_timeout(120000)  # 2 minutes
                    page.set_default_timeout(60000)  # 1 minute
                    
                    # Construct page URL with proper pagination
                    if current_page == 1:
                        page_url = f"{base_url}?trkid=2986-{location.lower()}-fcat&term={category}"
                    else:
                        page_url = f"{base_url}/page-{current_page}?trkid=2986-{location.lower()}-fcat&term={category}"
                    
                    # Add random delay before navigation (2-5 seconds)
                    time.sleep(2 + random.random() * 3)
                    
                    try:
                        # First navigate with domcontentloaded
                        response = page.goto(
                            page_url,
                            wait_until="domcontentloaded",
                            timeout=120000
                        )
                        
                        if response is None or not response.ok:
                            print(f"Failed to load page {current_page}. Retrying...")
                            retry_count += 1
                            time.sleep(5)
                            continue
                        
                        # Wait for the page to be relatively stable
                        time.sleep(5)
                        
                        # Check for access denied page
                        if "Access Denied" in page.content():
                            print("Access denied detected. Implementing bypass strategy...")
                            
                            # Rotate user agent
                            new_user_agent = random.choice([
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
                            ])
                            
                            # Close current page and create a new one with different user agent
                            page.close()
                            context = browser.new_context(user_agent=new_user_agent)
                            page = context.new_page()
                            
                            # Add longer delay before retry
                            time.sleep(10 + random.random() * 5)
                            retry_count += 1
                            continue
                        
                        # Try to find any of the possible content indicators
                        content_selectors = [
                            'div[class*="resultbox_info"]',
                            'div[class*="store-details"]',
                            'div[class*="jsx-"]',
                            'div[class*="jdlist"]',
                            'section[class*="jpag"]'
                        ]
                        
                        content_found = False
                        for selector in content_selectors:
                            try:
                                element = page.wait_for_selector(selector, timeout=30000)
                                if element:
                                    content_found = True
                                    break
                            except Exception:
                                continue
                        
                        if not content_found:
                            print("Content not found, retrying...")
                            retry_count += 1
                            time.sleep(5)
                            continue
                        
                        # Add some random mouse movements and scrolls
                        for _ in range(3):
                            page.mouse.move(
                                random.randint(100, 800),
                                random.randint(100, 600)
                            )
                            time.sleep(random.random())
                        
                        # Scroll to load ALL content with improved behavior
                        clinics_loaded = scroll_page(page)
                        if clinics_loaded == 0:
                            print(f"No clinics found on page {current_page}")
                            retry_count += 1
                            time.sleep(5)
                            continue

                        print(f"Successfully loaded {clinics_loaded} clinics on page {current_page}")
                        
                        # Get page content and parse with BeautifulSoup
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Replace the problematic selector:
                        containers = soup.select('section.rslwrp, div[class*="resultbox"], div[class*="listing-container"]')

                        # And update the listing detection code:
                        clinic_listings = []
                        for container in containers:
                            # Find all listings within each container
                            listings = container.find_all(['div'], class_=lambda x: x and (
                                'resultbox_info' in x or
                                'store-details' in x or
                                'listing-item' in x or
                                'jd_listingDetail' in x
                            ))
                            clinic_listings.extend(listings)

                        # If no listings found with the above method, try direct search
                        if not clinic_listings:
                            clinic_listings = soup.find_all(['div'], class_=lambda x: x and (
                                'resultbox_info' in x or
                                'store-details' in x or
                                'listing-item' in x or
                                'jd_listingDetail' in x
                            ))
                        
                        if not clinic_listings:
                            print("No listings found with current selectors")
                            print("Available classes:", [elem.get('class') for elem in soup.find_all(class_=True)])
                            retry_count += 1
                            time.sleep(5)
                            continue
                        
                        # Process ALL found clinics without any maximum limit
                        page_entries = 0
                        for listing in clinic_listings:
                            try:
                                # Extract URL first to check for duplicates
                                url = "N/A"
                                url_element = listing.find('div', class_=lambda x: x and 'resultbox_title_anchorbox' in x)
                                if not url_element:
                                    url_element = listing.find_parent('a', href=True)
                                if url_element:
                                    url = url_element['href']
                                
                                # Skip if we've seen this URL before
                                if url in seen_urls:
                                    continue
                                
                                # Extract name with multiple possible selectors
                                name = "N/A"
                                name_selectors = [
                                    ('div', 'resultbox_title_anchor'),
                                    ('span', 'store-name'),
                                    ('h2', 'jdlist-name'),
                                    ('a', 'store-name'),
                                    ('span', 'lng_cont_name')
                                ]
                                for tag, class_name in name_selectors:
                                    name_element = listing.find(tag, class_=class_name)
                                    if name_element:
                                        name = name_element.text.strip()
                                        break
                                
                                # Extract rating with multiple possible selectors
                                rating = "N/A"
                                rating_selectors = [
                                    ('div', 'resultbox_totalrate'),
                                    ('span', 'total-rate'),
                                    ('span', 'star_m')
                                ]
                                for tag, class_name in rating_selectors:
                                    rating_element = listing.find(tag, class_=class_name)
                                    if rating_element:
                                        rating_text = rating_element.text.strip()
                                        # Extract first number from rating text
                                        rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                                        if rating_match:
                                            rating = rating_match.group(1)
                                        break
                                
                                # Extract rating count with multiple possible selectors
                                rating_count = "0"
                                rating_count_selectors = [
                                    ('div', 'resultbox_countrate'),
                                    ('span', 'rate-count'),
                                    ('span', 'votes')
                                ]
                                for tag, class_name in rating_count_selectors:
                                    rating_count_element = listing.find(tag, class_=class_name)
                                    if rating_count_element:
                                        count_text = rating_count_element.text.strip()
                                        # Extract numbers from text
                                        count_match = re.search(r'(\d+)', count_text)
                                        if count_match:
                                            rating_count = count_match.group(1)
                                        break
                                
                                # Extract address with multiple possible selectors
                                address = "N/A"
                                address_selectors = [
                                    ('div', 'locatcity'),
                                    ('span', 'cont_fl_addr'),
                                    ('p', 'address-info'),
                                    ('span', 'address')
                                ]
                                for tag, class_name in address_selectors:
                                    address_element = listing.find(tag, class_=class_name)
                                    if address_element:
                                        address = address_element.text.strip()
                                        break
                                
                                # Extract phone number with multiple possible selectors
                                phone_number = "N/A"
                                phone_selectors = [
                                    ('span', 'callcontent'),
                                    ('span', 'contact-info'),
                                    ('p', 'contact-number'),
                                    ('span', 'mobilesv')
                                ]
                                for tag, class_name in phone_selectors:
                                    phone_element = listing.find(tag, class_=class_name)
                                    if phone_element:
                                        phone_number = phone_element.text.strip()
                                        break
                                
                                # Store the data
                                business_data = {
                                    'name': name,
                                    'rating': rating,
                                    'rating_count': rating_count,
                                    'address': address,
                                    'phone_number': phone_number,
                                    'category': category,
                                    'location': location,
                                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                # Get clinic detail URL
                                detail_url = None
                                url_element = listing.find('div', class_=lambda x: x and 'resultbox_title_anchorbox' in x)
                                if url_element and url_element.get('href'):
                                    detail_url = 'https://www.justdial.com' + url_element['href'] if not url_element['href'].startswith('http') else url_element['href']
                                
                                if detail_url:
                                    # Open clinic detail page in new tab
                                    detail_page = context.new_page()
                                    try:
                                        detail_page.goto(detail_url, wait_until="domcontentloaded")
                                        time.sleep(3)  # Wait for content to load
                                        
                                        # Use the detail-specific scroll function instead
                                        scroll_detail_page(detail_page)
                                        
                                        # Get detail page content
                                        detail_content = detail_page.content()
                                        detail_soup = BeautifulSoup(detail_content, 'html.parser')
                                        
                                        # Extract doctor links
                                        doctors = extract_doctor_links(detail_page, detail_soup)
                                        
                                        # Add doctors to business data
                                        business_data['associated_doctors'] = doctors
                                        
                                    except Exception as e:
                                        print(f"Error processing clinic detail page: {str(e)}")
                                        business_data['associated_doctors'] = []
                                    finally:
                                        detail_page.close()
                                else:
                                    business_data['associated_doctors'] = []
                                
                                # Only add if we have at least a name or address
                                if name != "N/A" or address != "N/A":
                                    all_businesses.append(business_data)
                                    seen_urls.add(url)  # Add URL to seen set
                                    page_entries += 1
                                    if verbose:
                                        print(f"Scraped: {name} | Rating: {rating} | Phone: {phone_number}")
                            
                            except Exception as e:
                                if verbose:
                                    print(f"Error scraping a listing: {str(e)}")
                                    traceback.print_exc()
                                continue
                        
                        if page_entries == 0:
                            print(f"No new entries found on page {current_page}. Moving to next page...")
                            break
                        
                        print(f"Successfully scraped {page_entries} new entries from page {current_page}")
                        break  # Break the retry loop on success
                    
                    except Exception as e:
                        print(f"Error during page processing: {str(e)}")
                        if verbose:
                            traceback.print_exc()
                        retry_count += 1
                        time.sleep(5)
                        continue
                    
                    finally:
                        page.close()
                
                except Exception as e:
                    print(f"Browser error: {str(e)}")
                    if verbose:
                        traceback.print_exc()
                    retry_count += 1
                    time.sleep(5)
                    continue
            
            if retry_count >= max_retries:
                print(f"Failed to scrape page {current_page} after {max_retries} attempts")
            
            current_page += 1
        
        browser.close()
    
    # Create DataFrame from collected data
    businesses_df = pd.DataFrame(all_businesses)
    
    if not businesses_df.empty:
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Save to CSV
        csv_filename = f'justdial_{location}_{category}_{timestamp}.csv'
        csv_filepath = os.path.join('output', csv_filename)
        businesses_df.to_csv(csv_filepath, index=False)
        print(f"Data saved to {csv_filepath}")
        
        if save_to_db:
            # Generate SQL statements
            sql_statements = generate_sql_inserts(businesses_df, 'justdial_healthcare_businesses')
            sql_filename = f'justdial_{location}_{category}_{timestamp}.sql'
            sql_filepath = os.path.join('output', sql_filename)
            
            with open(sql_filepath, 'w', encoding='utf-8') as sql_file:
                sql_file.write(sql_statements)
            
            print(f"SQL statements saved to {sql_filepath}")
    else:
        print("No data collected, nothing to save.")
    
    return businesses_df

def main():
    # Get location input from user
    print("\nAvailable locations examples: Delhi, Mumbai, Bangalore, Chennai, Kolkata, etc.")
    location = input("Enter location to scrape (e.g., Delhi): ").strip()
    
    # Validate location input
    while not location:
        print("Location cannot be empty!")
        location = input("Please enter a valid location: ").strip()
    
    # Get category input with default value
    category = input("Enter category to scrape (press Enter for default 'Clinics'): ").strip() or "Clinics"
    
    # Get number of pages with validation
    while True:
        try:
            num_pages = int(input("Enter number of pages to scrape (press Enter for default 3): ") or "3")
            if num_pages > 0:
                break
            print("Number of pages must be greater than 0")
        except ValueError:
            print("Please enter a valid number")
    
    # Configuration parameters
    params = {
        'location': location,
        'category': category,
        'num_pages': num_pages,
        'save_to_db': True,
        'verbose': False
    }

    print(f"\nStarting Justdial scraper with:")
    print(f"  Location: {params['location']}")
    print(f"  Category: {params['category']}")
    print(f"  Pages to scrape: {params['num_pages']}")
    print()
    
    # Run the scraper
    businesses_df = scrape_justdial_clinics(**params)
    
    if not businesses_df.empty:
        print(f"\nSuccessfully scraped {len(businesses_df)} businesses")
        print("\nSample data:")
        print(businesses_df[['name', 'rating', 'phone_number', 'address']].head(3))
    else:
        print("No businesses were scraped. Please check the logs for errors.")

if __name__ == "__main__":
    main()
