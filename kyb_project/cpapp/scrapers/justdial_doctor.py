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

def human_like_delay():
    """Add minimal delays to avoid being blocked"""
    time.sleep(random.uniform(0.3, 0.7))  # Further reduced delay

async def scroll_page(page, scroll_attempts=3):
    """Optimized scroll page with better error handling and timeouts"""
    print("Scrolling to load all doctor entries...")
    
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=15000)
        
        initial_count = await get_doctor_cards_count(page)
        current_count = initial_count
        print(f"Initial doctor count: {initial_count}")
        
        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_attempt = 0
        
        while scroll_attempt < scroll_attempts:
            await page.evaluate("""
                window.scrollBy({
                    top: 1000,
                    left: 0,
                    behavior: 'auto'
                });
            """)
            
            await asyncio.sleep(0.3)
            
            new_count = await get_doctor_cards_count(page)
            if new_count > current_count:
                print(f"Found {new_count} doctors (added {new_count - current_count})")
                current_count = new_count
                scroll_attempt = 0
                
                if new_count > 20:
                    await asyncio.sleep(0.2)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempt += 1
                if scroll_attempt >= scroll_attempts:
                    await asyncio.sleep(0.3)
                    final_count = await get_doctor_cards_count(page)
                    print(f"Finished scrolling. Total doctors loaded: {final_count}")
                    return final_count > 0
            else:
                scroll_attempt = 0
                last_height = new_height
    except Exception as e:
        print(f"Error in scroll_page: {str(e)}")
        return False

async def scroll_profile_page(page):
    """Optimized profile page scrolling"""
    await page.wait_for_load_state("domcontentloaded", timeout=5000)
    
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(0.3)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")

async def extract_detail_page_info(page, soup):
    """Extract detailed doctor information from individual doctor pages"""
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
    doctor_name_elem = soup.select_one('h1.jsx-6cd7a16dc8a9fe0c.compney.font23.fw500.color111') or \
                      soup.select_one('div.vendbox_title h1')
    if doctor_name_elem:
        doctor_details['doctor_name'] = doctor_name_elem.text.strip()
    
    # Extract rating
    rating_elem = soup.select_one('div[role="button"][tabindex="0"][class*="vendbox_rateavg"][style*="background:"]') or \
                 soup.select_one('div.vendbox_rateavg')
    if rating_elem:
        rating_match = re.search(r'(\d+\.?\d*)', rating_elem.text.strip())
        if rating_match:
            doctor_details['rating'] = rating_match.group(1)
    
    # Extract rating count
    rating_count_elem = soup.select_one('div[role="button"][aria-label="Ratings"][tabindex="0"].jsx-6cd7a16dc8a9fe0c.vendbox_ratecount') or \
                       soup.select_one('div.vendbox_ratecount')
    if rating_count_elem:
        count_text = rating_count_elem.text.replace('Ratings', '').strip()
        doctor_details['rating_count'] = count_text
    
    # Extract experience
    operation_exp_elem = soup.select_one('div.operation div.adress.font14.fw100.color111')
    if operation_exp_elem and "Years in Healthcare" in operation_exp_elem.text:
        experience_match = re.search(r'(\d+)', operation_exp_elem.text)
        if experience_match:
            doctor_details['experience'] = f"{experience_match.group(1)} Years"
    
    # Extract consultation fee
    operation_fee_elem = soup.select_one('div.operation div.font15.fw400.color111.rupicon') or \
                        soup.select_one('div[role="presentation"][tabindex="-1"].font15.fw400.color111.rupicon')
    if operation_fee_elem and "Consultation Fee:" in operation_fee_elem.text:
        fee_match = re.search(r'₹\s*([0-9,]+)', operation_fee_elem.text)
        if fee_match:
            doctor_details['consultation_fee'] = fee_match.group(1).replace(',', '')
    
    # Extract clinic address
    clinic_address_elem = soup.select_one('div.jsx-e9bf6bc1cb6e9b5c.parentvendor_address') or \
                         soup.select_one('address.jsx-e9bf6bc1cb6e9b5c.vendorinfo_address')
    if clinic_address_elem:
        doctor_details['clinic_address'] = clinic_address_elem.text.strip()
    
    # Extract specialization, registration and qualification
    info_items = soup.select('li.jsx-5a5f5a91676d6d2d.dtl_infolist_item')
    for item in info_items:
        label_elem = item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_labeltext')
        value_elem = item.select_one('div.jsx-5a5f5a91676d6d2d.dtl_infotext')
        
        if label_elem and value_elem:
            label = label_elem.text.strip()
            value = value_elem.text.strip()
            
            if "Specialization" in label:
                doctor_details['specialization'] = value
            elif "Registration" in label:
                doctor_details['registration'] = value
            elif "Qualification" in label or "Main Qualification" in label:
                doctor_details['qualification'] = value
            elif "Additional Qualification" in label:
                if doctor_details['qualification'] != "Not available":
                    doctor_details['qualification'] += f"; {value}"
                else:
                    doctor_details['qualification'] = value
    
    # Extract phone number
    phone_elem = soup.select_one('div.jsx-e9bf6bc1cb6e9b5c.rightaside_number .font16.fw500.color007.pointer')
    if phone_elem:
        if "Show Number" in phone_elem.text:
            try:
                show_number_button = await page.query_selector('div.rightaside_number .font16.fw500.color007.pointer')
                if show_number_button:
                    await show_number_button.click()
                    await asyncio.sleep(0.5)
                    updated_soup = BeautifulSoup(await page.content(), 'html.parser')
                    phone_link = updated_soup.select_one('a[href^="tel:"]')
                    if phone_link:
                        doctor_details['phone_number'] = phone_link.text.strip()
            except Exception as e:
                print(f"Error extracting phone number: {str(e)}")
        else:
            doctor_details['phone_number'] = phone_elem.text.strip()
    
    return doctor_details

async def setup_browser_context(playwright):
    """Setup browser and context with improved settings"""
    browser = await playwright.chromium.launch(
        headless=True,
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

async def process_doctor_page(context, link, semaphore):
    """Process a single doctor page"""
    async with semaphore:
        try:
            detail_page = await context.new_page()
            await detail_page.goto(link, wait_until="domcontentloaded")
            await asyncio.sleep(1)
            
            await scroll_profile_page(detail_page)
            
            detail_content = await detail_page.content()
            detail_soup = BeautifulSoup(detail_content, 'html.parser')
            doctor_details = await extract_detail_page_info(detail_page, detail_soup)
            doctor_details['detail_url'] = link
            
            await detail_page.close()
            return doctor_details
            
        except Exception as e:
            print(f"Error processing doctor detail page: {str(e)}")
            return None

async def scrape_justdial_doctors(location, num_pages=3):
    """Asynchronous scraper for JustDial doctors"""
    all_doctors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    url = f"https://www.justdial.com/{location}/Doctors/nct-10892680"
    
    async with async_playwright() as p:
        browser, context = await setup_browser_context(p)
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
            
            current_page = 1
            semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
            
            while current_page <= num_pages:
                print(f"\nProcessing page {current_page}...")
                
                if not await scroll_page(page):
                    break
                
                html_content = await page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                doctor_link_elements = soup.select("a.resultbox[aria-label*='contract info']") or \
                                    soup.select("a.resultbox") or \
                                    soup.select("div.resultbox_info > a")
                
                doctor_links = [elem.get('href') for elem in doctor_link_elements if elem.get('href')]
                doctor_links = [f'https://www.justdial.com{link}' if not link.startswith('http') else link 
                              for link in dict.fromkeys(doctor_links)]
                
                print(f"Found {len(doctor_links)} doctor links on page {current_page}")
                
                # Process doctor pages concurrently
                tasks = [process_doctor_page(context, link, semaphore) for link in doctor_links]
                results = await asyncio.gather(*tasks)
                all_doctors.extend([r for r in results if r])
                
                next_page_selector = 'a[aria-label="Go to next page"]'
                if await page.query_selector(next_page_selector):
                    current_page += 1
                    await page.click(next_page_selector)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                else:
                    break
                
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        finally:
            await browser.close()
    
    if all_doctors:
        os.makedirs('output', exist_ok=True)
        df = pd.DataFrame(all_doctors)
        df = df.fillna("Not available")
        
        if 'detail_url' in df.columns:
            cols = [col for col in df.columns if col != 'detail_url'] + ['detail_url']
            df = df[cols]
        
        csv_filename = f'justdial_doctors_data_{timestamp}.csv'
        csv_filepath = os.path.join('output', csv_filename)
        df.to_csv(csv_filepath, index=False)
        
        print(f"Scraped {len(all_doctors)} doctors. Data saved to {csv_filepath}")
        return df
    else:
        print("No doctor data collected.")
        return pd.DataFrame()

async def main():
    """Async main function"""
    location = input("Enter location (e.g., Delhi, Mumbai): ")
    
    try:
        num_pages = int(input("Enter number of pages to scrape (default 3): ") or 3)
    except ValueError:
        num_pages = 3
        print("Invalid input. Using default value of 3 pages.")
    
    print(f"\nStarting scraper for location: {location}")
    print(f"Will scrape up to {num_pages} pages.")
    
    scraped_data = await scrape_justdial_doctors(
        location=location,
        num_pages=num_pages
    )
    
    print(f"\nFinal Results:")
    print(f"Total pages processed: {num_pages}")
    print(f"Total doctors collected: {len(scraped_data)}")

if __name__ == "__main__":
    asyncio.run(main())
