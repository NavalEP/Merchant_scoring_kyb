import os
import pandas as pd
import time
import re
import json
import random
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def get_doctor_cards_count(page):
    """Get the current count of doctor cards on the page"""
    return await page.evaluate("""() => {
        return document.querySelectorAll('div.jsx-ee3d18659dbf4034.resultbox_info').length;
    }""")

async def add_random_mouse_movement(page):
    """Simulate random mouse movements - DISABLED for better performance"""
    # Function intentionally left empty to maintain code structure
    pass

def human_like_delay():
    """Add minimal delays to avoid being blocked"""
    time.sleep(random.uniform(0.5, 1.0))  # Reduced from 1.5-3.5

async def scroll_page(page, scroll_attempts=5):
    """Optimized scroll page with better error handling and timeouts"""
    print("Scrolling to load all doctor entries...")
    
    try:
        # Initial wait with longer timeout and more flexible load state
        await page.wait_for_load_state("domcontentloaded", timeout=30000)
        
        # Add additional wait for network to stabilize
        try:
            await page.wait_for_load_state("networkidle", timeout=20000)
        except:
            print("Network didn't reach idle state, continuing anyway...")
        
        # Initial count of doctor cards
        initial_count = await get_doctor_cards_count(page)
        current_count = initial_count
        print(f"Initial doctor count: {initial_count}")
        
        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_attempt = 0
        
        while scroll_attempt < scroll_attempts:
            # Scroll in larger chunks for faster loading
            await page.evaluate("""
                window.scrollBy({
                    top: 800,  // Increased from 500
                    left: 0,
                    behavior: 'auto'  // Changed from 'smooth' for faster scrolling
                });
            """)
            
            # Shorter wait time with dynamic adjustment
            if scroll_attempt == 0:
                await asyncio.sleep(1.5)  # Longer initial wait
            else:
                await asyncio.sleep(0.5)  # Faster subsequent scrolls
            
            # Check for new doctors with optimized counting
            new_count = await get_doctor_cards_count(page)
            if new_count > current_count:
                print(f"Found {new_count} doctors (added {new_count - current_count})")
                current_count = new_count
                scroll_attempt = 0  # Reset attempts when we find new doctors
                
                # If we found significant number of doctors, we can reduce wait time
                if new_count > 20:
                    await asyncio.sleep(0.3)  # Reduced wait time when we have enough doctors
            
            # Check if we've reached the bottom
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempt += 1
                if scroll_attempt >= scroll_attempts:
                    # Quick final check
                    await asyncio.sleep(0.5)  # Reduced from 1.5
                    final_count = await get_doctor_cards_count(page)
                    print(f"Finished scrolling. Total doctors loaded: {final_count}")
                    return final_count > 0
            else:
                scroll_attempt = 0
                last_height = new_height
    except Exception as e:
        print(f"Error in scroll_page: {str(e)}")
        return False

async def scroll_profile_page(page, max_attempts=2):
    """Optimized profile page scrolling with faster loading"""
    print("Loading doctor profile content...")
    
    # Wait for initial content load
    await page.wait_for_load_state("domcontentloaded", timeout=5000)
    
    # Get initial page height
    last_height = await page.evaluate("document.body.scrollHeight")
    
    for attempt in range(max_attempts):
        # Fast scroll to bottom
        await page.evaluate("""
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'auto'
            });
        """)
        
        # Minimal wait time
        await asyncio.sleep(0.5)  # Reduced from 1.0
        
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
            
        last_height = new_height
    
    # Quick scroll to middle for optimal content visibility
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    await asyncio.sleep(0.3)  # Reduced from 0.5

def extract_detail_page_info(page, soup):
    """Extract detailed doctor information from individual doctor pages"""
    # Add a longer delay to ensure all data is properly loaded
    time.sleep(3)  # Ensure page is fully loaded before extraction
    
    doctor_details = {
        'doctor_name': "Not available",
        'rating': "Not available", 
        'rating_count': "Not available",
        'experience': "Not available",
        'consultation_fee': "Not available",
        'clinic_address': "Not available",
        'specialization': "Not available",
        'registration': "Not available",
        'qualification': "Not available",
        'phone_number': "Not available"
    }

    # Extract doctor name
    for selector in [
        'h1.jsx-6cd7a16dc8a9fe0c.compney.font23.fw500.color111',
        'div.vendbox_title h1'
    ]:
        if name_elem := soup.select_one(selector):
            doctor_details['doctor_name'] = name_elem.text.strip()
            break

    # Extract rating
    for selector in [
        'div[role="button"][tabindex="0"][class*="vendbox_rateavg"][style*="background:"]',
        'div.vendbox_rateavg'
    ]:
        if rating_elem := soup.select_one(selector):
            if rating_match := re.search(r'(\d+\.?\d*)', rating_elem.text.strip()):
                doctor_details['rating'] = rating_match.group(1)
                break

    # Extract rating count
    for selector in [
        'div[role="button"][aria-label="Ratings"][tabindex="0"].jsx-6cd7a16dc8a9fe0c.vendbox_ratecount.font15.fw400.color555.pointer.mr-10',
        'div.vendbox_ratecount'
    ]:
        if count_elem := soup.select_one(selector):
            doctor_details['rating_count'] = count_elem.text.replace('Ratings', '').strip()
            break

    # Extract experience using multiple selectors
    experience_selectors = [
        'div[role="presentation"][tabindex="0"].adress.font14.fw100.color111',
        'li.jsx-5a5f5a91676d6d2d.dtl_infolist_item div.jsx-5a5f5a91676d6d2d.dtl_infotext'
    ]

    # Try each selector
    for selector in experience_selectors:
        if exp_elem := soup.select_one(selector):
            exp_text = exp_elem.text.strip()
            # Extract years from text like "29 Years in Healthcare"
            if years_match := re.search(r'(\d+)\s*Years?', exp_text):
                doctor_details['experience'] = f"{years_match.group(1)} Years"
                break
            else:
                doctor_details['experience'] = exp_text
            break
    
    # If still not found, check in list items
    if doctor_details['experience'] == "Not available":
        for item in soup.select('li.jsx-5a5f5a91676d6d2d.dtl_infolist_item'):
            if label := item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_labeltext'):
                if any(exp_word in label.text.lower() for exp_word in ['experience', 'exp', 'years']):
                    if value := item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_infotext'):
                        doctor_details['experience'] = value.text.strip()
                        break

    # Extract consultation fee
    for selector in [
       
        'div[role="presentation"][tabindex="-1"].font15.fw400.color111.rupicon'
        
    ]:
        if fee_elem := soup.select_one(selector):
            if "Consultation Fee:" in fee_elem.text:
                if fee_match := re.search(r'₹\s*([0-9,]+)', fee_elem.text):
                    doctor_details['consultation_fee'] = fee_match.group(1).replace(',', '')
                    break

    # Extract clinic address
    for selector in [
        'div.jsx-53afd63b02888f33.parentvendor_address.font14.fw400.color111.mt-6',
        'address.jsx-53afd63b02888f33.vendorinfo_address.font16.fw400.color111.mb-10.pl-20.pr-20'
    ]:
        if addr_elem := soup.select_one(selector):
            doctor_details['clinic_address'] = addr_elem.text.strip()
            break
    
    # Try to get clinic name and address from parentvendor_details if available
    if clinic_details := soup.select_one('div.jsx-53afd63b02888f33.parentvendor_details'):
        if clinic_name := clinic_details.select_one('div.jsx-53afd63b02888f33.parentvendor_title span.jsx-53afd63b02888f33.color111.pointer'):
            doctor_details['clinic_name'] = clinic_name.text.strip()
        
        if clinic_addr := clinic_details.select_one('div.jsx-53afd63b02888f33.parentvendor_address'):
            doctor_details['clinic_address'] = clinic_addr.text.strip()

    # Add additional delay to ensure all dynamic content is loaded
    time.sleep(2)
    
    # Extract specialization, registration and qualification
    for item in soup.select('li.jsx-5a5f5a91676d6d2d.dtl_infolist_item'):
        # Look for label div
        if label := item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_labeltext.dblock.font15.fw400.color777.mb-4'):
            if value := item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_infotext.font16.fw500.color111'):
                label_text = label.text.strip()
                value_text = value.text.strip()
                
                if "Specialization" in label_text:
                    doctor_details['specialization'] = value_text
                elif "Registration" in label_text:
                    doctor_details['registration'] = value_text
                elif "Qualification" in label_text or "Main Qualification" in label_text:
                    doctor_details['qualification'] = value_text
                elif "Additional Qualification" in label_text:
                    if doctor_details.get('qualification', "Not available") != "Not available":
                        doctor_details['qualification'] += f"; {value_text}"
                    else:
                        doctor_details['qualification'] = value_text

    # Extract phone number - add extra delay to ensure phone numbers are loaded
    time.sleep(1.5)
    
    if phone_elem := soup.select_one('div.jsx-53afd63b02888f33.rightaside_number .font16.fw500.color007.pointer'):
        doctor_details['phone_number'] = phone_elem.text.strip()
    # Try alternative selector if first one fails
    elif phone_elem := soup.select_one('div.jsx-53afd63b02888f33.mt-5.pl-10.pr-10 div.jsx-53afd63b02888f33.rightaside_number span.jsx-53afd63b02888f33.font16.fw500.color007.pointer'):
        doctor_details['phone_number'] = phone_elem.text.strip()
    else:
        doctor_details['phone_number'] = "Not available"

    return doctor_details

def retry_with_backoff(func, max_attempts=3):
    """Implement retry mechanism with exponential backoff"""
    async def wrapper(*args, **kwargs):
        attempt = 0
        while attempt < max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    raise e
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt} failed. Retrying in {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
    return wrapper

async def setup_browser_context(playwright):
    """Setup browser and context with improved settings"""
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        viewport={"width": 1366, "height": 768},
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
    )
    return browser, context

@retry_with_backoff
async def scrape_justdial_doctors(location, category, num_pages=3):
    """
    Scrape doctor information from JustDial by directly extracting doctor detail page links.
    
    Args:
        location (str): Location to search for doctors (e.g., 'Delhi', 'Mumbai')
        category (str): Category of professionals to search for (e.g., 'Doctors', 'Dentists')
        num_pages (int): Maximum number of pages to scrape
        
    Returns:
        DataFrame: Collected doctor information
    """
    all_doctors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Use the updated URL format with proper filters
    # Construct URL based on category and location
    if category.lower() in ["ivf doctors", "ivf", "ivf doctor"]:
        url = f"https://www.justdial.com/{location}/IVF-Doctors/nct-10265455?trkid=559316-{location.lower()}&term=IVF&filters=%5B%7B%22e%22%3A%224%22%2C%22v%22%3A%5B%22ii01%22%5D%7D%5D&filtersApplied=%5B%7B%22mv%22%3A%221182%22%2C%22v%22%3A%5B%22ii01%22%5D%7D%5D&checkin=1745712000&checkout=1745798400"
        print(f"Using specialized IVF doctors URL: {url}")
    else:
        # Default URL format for other doctor categories
        url = f"https://www.justdial.com/{location}/{category}-in-{location}/nct-10989817?trkid=865483-{location.lower()}-fcat&term=&filters=%5B%7B%22e%22%3A%224%22%2C%22v%22%3A%5B%22ii01%22%5D%7D%5D&filtersApplied=%5B%7B%22mv%22%3A%221182%22%2C%22v%22%3A%5B%22ii01%22%5D%7D%5D&checkin=1744934400&checkout=1745020800"
    
    async with async_playwright() as p:
        browser, context = await setup_browser_context(p)
        page = await context.new_page()
        
        # Navigate to the initial URL and ensure page load
        print(f"Navigating to initial URL: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(8)  # Longer initial wait
            try:
                await page.wait_for_selector('div.resultbox_info', timeout=20000)
            except:
                print(f"Warning: {category} cards not immediately visible, continuing...")
        except Exception as e:
            print(f"Error navigating to initial URL: {str(e)}")
            await browser.close()
            return pd.DataFrame()
        
        current_page = 1
        
        while current_page <= num_pages:
            print(f"\nProcessing page {current_page}...")
            
            if not await scroll_page(page):
                print(f"No {category} found after scrolling, stopping loop...")
                break

            # Get the current HTML content and use BeautifulSoup for extraction.
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Fix the selector to match the actual HTML structure
            doctor_link_elements = soup.select("a.resultbox[aria-label*='contract info']")
            
            # Add fallback selectors if the first one doesn't work
            if not doctor_link_elements:
                print("Primary selector failed, trying alternative selectors...")
                doctor_link_elements = soup.select("a.resultbox")
                
            if not doctor_link_elements:
                print("Alternative selector failed, trying generic link selector in result boxes...")
                doctor_link_elements = soup.select("div.resultbox_info > a")
            
            # Debug information to understand what we're finding
            print(f"Found {len(doctor_link_elements)} {category} link elements")
            
            if not doctor_link_elements:
                print(f"No {category} links found on page {current_page}")
                # Debug the page structure to help identify the correct selector
                print("Dumping sample HTML for debugging:")
                result_boxes = soup.select("div.jsx-ee3d18659dbf4034.resultbox_info")
                if result_boxes:
                    print(f"Found {len(result_boxes)} result boxes")
                    if len(result_boxes) > 0:
                        print("Sample result box HTML:")
                        print(result_boxes[0].parent.prettify()[:500])  # Print first 500 chars of parent element
                break
            
            doctor_links = []
            for elem in doctor_link_elements:
                href = elem.get('href')
                if href:
                    # Ensure the URL is complete
                    if not href.startswith("http"):
                        href = 'https://www.justdial.com' + href
                    if href not in doctor_links:
                        doctor_links.append(href)
            
            total_doctors_found = len(doctor_links)
            print(f"Found {total_doctors_found} {category} links on page {current_page}")
            
            # Create tasks for processing doctor pages concurrently
            async def process_doctor_page(link):
                try:
                    detail_page = await context.new_page()
                    await detail_page.goto(link, wait_until="domcontentloaded")
                    await asyncio.sleep(3)  # Wait for initial load
                    
                    await scroll_profile_page(detail_page)
                    
                    detail_content = await detail_page.content()
                    detail_soup = BeautifulSoup(detail_content, 'html.parser')
                    doctor_details = extract_detail_page_info(detail_page, detail_soup)
                    doctor_details['detail_url'] = link
                    doctor_details['location'] = location
                    doctor_details['category'] = category
                    
                    await detail_page.close()
                    return doctor_details
                except Exception as e:
                    print(f"Error processing {category} detail page: {str(e)}")
                    return None

            # Process doctor pages concurrently with a semaphore to limit concurrent requests
            sem = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
            async def bounded_process(link):
                async with sem:
                    return await process_doctor_page(link)

            tasks = [bounded_process(link) for link in doctor_links]
            results = await asyncio.gather(*tasks)
            
            # Add successful results to all_doctors
            all_doctors.extend([r for r in results if r is not None])
            print(f"Processed {len(all_doctors)} {category} so far")
            
            # Check for next page navigation
            next_page_selector = 'a[aria-label="Go to next page"]'
            if await page.query_selector(next_page_selector) is not None:
                current_page += 1
                print(f"Navigating to page {current_page}...")
                try:
                    await page.click(next_page_selector)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(5)  # Wait for the next page to load
                except Exception as e:
                    print(f"Error navigating to next page: {str(e)}")
                    break
            else:
                print("No next page button found.")
                break
        
        await browser.close()
    
    # Create DataFrame from collected data and save to CSV
    if all_doctors:
        os.makedirs('output', exist_ok=True)
        df = pd.DataFrame(all_doctors)
        df = df.fillna("Not available")
        
        # Reorder columns to make location and category first and detail_url last
        cols = ['location', 'category']
        other_cols = [col for col in df.columns if col not in ['location', 'category', 'detail_url']]
        if 'detail_url' in df.columns:
            cols = cols + other_cols + ['detail_url']
        else:
            cols = cols + other_cols
        
        df = df[cols]
        
        # Save intermediate results every 30 doctors
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i in range(0, len(all_doctors), 30):
            temp_df = pd.DataFrame(all_doctors[:i+30])
            temp_csv = f'justdial_{location}_{category}_interim_{timestamp}.csv'
            temp_csv_path = os.path.join('output', temp_csv)
            temp_df.to_csv(temp_csv_path, index=False)
            print(f"Saved interim results for {min(i+30, len(all_doctors))} {category}")
        
        # Save final results
        csv_filename = f'justdial_{category}_data_{location}_{timestamp}.csv'
        csv_filepath = os.path.join('output', csv_filename)
        df.to_csv(csv_filepath, index=False)
        
        print(f"Scraped {len(all_doctors)} {category}. Data saved to {csv_filepath}")
        return df
    else:
        print(f"No {category} data collected.")
        return pd.DataFrame()

async def main():
    """
    Main function to run the JustDial scraper with user-provided parameters
    """
    # Get input parameters from user
    location = input("Enter location (e.g., Delhi, Mumbai): ")
    category = input("Enter category (e.g., Doctors, Dentists, Physiotherapists): ") or "Doctors"
    
    try:
        num_pages = int(input("Enter number of pages to scrape (default 3): ") or 3)
    except ValueError:
        num_pages = 3
        print("Invalid input. Using default value of 3 pages.")
    
    # Run the scraper with user-provided parameters
    print(f"\nStarting scraper for location: {location}")
    print(f"Category: {category}")
    print(f"Will scrape up to {num_pages} pages.")
    print("Will extract all entries found on each page.")
    print(f"Using URL with specific filters for qualified {category}.\n")
    
    scraped_data = await scrape_justdial_doctors(
        location=location,
        category=category,
        num_pages=num_pages
    )
    
    print(f"\nFinal Results:")
    print(f"Total pages processed: {num_pages}")
    print(f"Total {category} collected: {len(scraped_data)}")

if __name__ == "__main__":
    asyncio.run(main())
