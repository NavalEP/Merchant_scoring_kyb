import pandas as pd
import re
import json
import urllib.parse
import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import random
import traceback
import time
import csv

def get_doctor_cards_count(page):
    """Get the current count of doctor cards on the page"""
    return page.evaluate("""() => {
        return document.querySelectorAll('div[data-qa-id="doctor_card"]').length;
    }""")

def scroll_page(page, min_doctors=30, max_attempts=5, max_doctors=30):
    """
    Slowly scroll page to load all dynamic content on search results page
    
    Args:
        page: Playwright page object
        min_doctors: Minimum number of doctors to try to load
        max_attempts: Maximum scrolling attempts
        max_doctors: Maximum number of doctors to load before stopping
    """
    print("Starting slow scrolling to load all doctor entries...")
    
    # Initial count of doctor cards
    initial_count = get_doctor_cards_count(page)
    current_count = initial_count
    
    print(f"Initial doctor count: {initial_count}")
    attempts = 0
    
    # Get page height
    page_height = page.evaluate("document.body.scrollHeight")
    
    # Do incremental scrolling
    scroll_step = 300  # Pixels to scroll each time
    current_position = 0
    
    while attempts < max_attempts:
        # Stop scrolling if we've found enough doctors
        if current_count >= max_doctors:
            print(f"Found {current_count} doctors which meets or exceeds target of {max_doctors}. Stopping scroll.")
            break
            
        # Scroll down incrementally
        current_position += scroll_step
        page.evaluate(f"window.scrollTo(0, {current_position})")
        
        # Wait a moment for content to load
        page.wait_for_timeout(1500)
        
        # Check if we're at the bottom of the page
        if current_position >= page_height:
            # Reached the bottom, wait a bit longer for any final loading
            page.wait_for_timeout(2000)
            
            # Get updated page height
            new_height = page.evaluate("document.body.scrollHeight")
            
            if new_height > page_height:
                # Page height increased, continue scrolling
                page_height = new_height
            else:
                # Check if we have enough doctors
                new_count = get_doctor_cards_count(page)
                print(f"Scroll attempt {attempts+1}: Found {new_count} doctors")
                
                if new_count > current_count:
                    print(f"Loaded {new_count - current_count} more doctors")
                    current_count = new_count
                    attempts = 0  # Reset attempts
                    
                    # Stop if we have enough doctors
                    if current_count >= max_doctors:
                        print(f"Found {current_count} doctors which meets or exceeds target of {max_doctors}. Stopping scroll.")
                        break
                    
                    # Reset to start scrolling from current position
                    current_position = 0
                    page.evaluate("window.scrollTo(0, 0)")
                    page.wait_for_timeout(1000)
                else:
                    attempts += 1
                
                # Break if we have enough doctors or hit several consecutive attempts with no change
                if (current_count >= min_doctors and attempts >= 2) or current_count >= max_doctors:
                    print(f"Loaded enough doctors ({current_count}) and no changes for {attempts} attempts")
                    break
        
        # Check for new doctors after each scroll step
        new_count = get_doctor_cards_count(page)
        if new_count > current_count:
            print(f"Found {new_count} doctors (added {new_count - current_count})")
            current_count = new_count
            
            # Stop if we have enough doctors
            if current_count >= max_doctors:
                print(f"Found {current_count} doctors which meets or exceeds target of {max_doctors}. Stopping scroll.")
                break
    
    print(f"Finished scrolling. Total doctors loaded: {current_count}")
    
    return current_count

def scroll_profile_page(page, max_attempts=5):
    """
    Scroll a doctor's profile page to load all dynamic content
    
    Args:
        page: Playwright page object
        max_attempts: Maximum scrolling attempts
    """
    # Simple quiet scrolling with minimal logging
    print("Loading profile page content...")
    
    # Get initial page height
    last_height = page.evaluate("document.body.scrollHeight")
    
    for attempt in range(max_attempts):
        # Scroll down to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        
        # Get new height
        new_height = page.evaluate("document.body.scrollHeight")
        
        # If no change in height, we've reached the bottom
        if new_height == last_height:
            break
            
        last_height = new_height
    
    # Scroll back to top and then halfway (to make contact buttons visible)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    page.wait_for_timeout(1000)

def extract_contact_number(page):
    """Extract contact number by clicking on the contact button with better error handling"""
    try:
        # Try multiple selectors for the contact button
        selectors = [
            'button[data-qa-id="call_button"]', 
            'button:has-text("Contact Clinic")',
            '.u-t-capitalize.u-bold.u-round-corner--large',
            'button.u-t-capitalize'
        ]
        
        for selector in selectors:
            contact_buttons = page.query_selector_all(selector)
            if contact_buttons and len(contact_buttons) > 0:
                # Click the first button (quietly)
                button = contact_buttons[0]
                page.wait_for_timeout(1000)
                button.click()
                page.wait_for_timeout(2000)  # Increased wait time
                
                # Try multiple selectors for the phone number
                phone_selectors = [
                    'div[data-qa-id="phone_number"]', 
                    '.u-large-font',
                    '.c-profile--clinic-contact-card .u-large-font'
                ]
                for phone_selector in phone_selectors:
                    phone_element = page.query_selector(phone_selector)
                    if phone_element:
                        return phone_element.inner_text()
                break
        
        return "Not available"
    except Exception as e:
        print(f"Error extracting contact number: {str(e)}")
        return "Not available"

def generate_sql_inserts(df, table_name='practo_doctors'):
    """
    Generate SQL INSERT statements from the DataFrame
    
    Args:
        df: pandas DataFrame with doctor information
        table_name: name of the target database table
        
    Returns:
        str: SQL INSERT statements for the data
    """
    if df.empty:
        return ""
    
    # Clean column names (replace spaces with underscores and remove special characters)
    df.columns = [re.sub(r'[^\w]', '_', col.lower()) for col in df.columns]
    
    # Escape single quotes in string values
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: str(x).replace("'", "''") if pd.notnull(x) else "NULL")
    
    # Create column definition for CREATE TABLE
    column_defs = []
    for col in df.columns:
        # Determine appropriate SQL data type
        if col in ['name', 'speciality', 'location', 'clinic_name', 'doctor_address', 
                   'doctor_url', 'contact_number', 'detailed_qualifications']:
            column_defs.append(f"{col} VARCHAR(500)")
        elif col in ['experience', 'consultation_fee', 'recommendation_percent', 'patient_stories']:
            column_defs.append(f"{col} INT")
        else:
            column_defs.append(f"{col} TEXT")
    
    # Construct column definitions string separately
    column_def_str = ',\n  '.join(column_defs)
    
    # Generate CREATE TABLE statement without problematic backslash in f-string
    create_table = f"""
-- Table structure for table `{table_name}`
CREATE TABLE IF NOT EXISTS `{table_name}` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  {column_def_str},
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
    
    # Generate INSERT statements
    inserts = []
    for _, row in df.iterrows():
        columns = ', '.join(f"`{col}`" for col in df.columns)
        values = []
        
        for col in df.columns:
            val = row[col]
            # Handle different data types
            if pd.isnull(val) or val == "NULL" or val == "Not available":
                values.append("NULL")
            elif col in ['experience', 'consultation_fee', 'recommendation_percent', 'patient_stories']:
                # Try to extract numeric values, use NULL if not a number
                try:
                    if isinstance(val, str) and val.isdigit():
                        values.append(val)
                    else:
                        values.append("NULL")
                except:
                    values.append("NULL")
            else:
                values.append(f"'{val}'")
        
        values_str = ', '.join(values)
        inserts.append(f"INSERT INTO `{table_name}` ({columns}) VALUES ({values_str});")
    
    # Combine all statements
    all_sql = create_table + "\n" + "\n".join(inserts)
    
    return all_sql

def scrape_practo_doctors(location, specialty, num_pages=2, save_to_db=False, debug=True, min_doctors_per_page=30, verbose=False, max_doctors=3000, table_name='practo_doctors'):
    """
    Enhanced scraper for Practo.com with doctor profile and clinic details
    
    Args:
        location (str): Search location (e.g. 'Bangalore', 'Delhi')
        specialty (str): Medical specialty to search (e.g. 'Dentist', 'Cardiologist')
        num_pages (int): Number of pages to scrape
        save_to_db (bool): Whether to save results to database (if False, save to CSV)
        debug (bool): Whether to run in debug mode (non-headless mode)
        min_doctors_per_page (int): Minimum number of doctors to try to load per page
        verbose (bool): Whether to print detailed progress messages
        max_doctors (int): Maximum number of doctors to scrape before stopping
        table_name (str): Table name for SQL output (if save_to_db is True)
        
    Returns:
        DataFrame: Collected doctor information with enhanced clinic details
    """
    all_doctors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Starting scraper for {specialty} in {location}")
    print(f"Will stop after collecting {max_doctors} doctors")
        
    # Create output directory for debug screenshots
    if debug:
        os.makedirs('debug_screenshots', exist_ok=True)
    
    with sync_playwright() as p:
        # Try using non-headless mode for debugging
        browser = p.chromium.launch(headless=False if debug else True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            viewport={"width": 1366, "height": 768},
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/'
            }
        )
        
        current_page = 1
        while current_page <= num_pages:
            try:
                # Use the exact URL format with encoded query parameters for better compatibility
                encoded_specialty = urllib.parse.quote(f'[{{"word":"{specialty}","autocompleted":true,"category":"subspeciality"}}]')
                
                if current_page == 1:
                    page_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={encoded_specialty}&city={location}"
                else:
                    page_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={encoded_specialty}&city={location}&page={current_page}"
                
                print(f"Scraping page {current_page} with URL: {page_url}")
                page = context.new_page()
                page.goto(page_url, timeout=60000)
                
                # Add random delays between actions to mimic human behavior
                page.wait_for_timeout(random.randint(2000, 5000))
                
                if debug:
                    page.screenshot(path=f'debug_screenshots/page_{current_page}_before_scroll.png')
                
                # Scroll to load dynamic content
                doctors_loaded = scroll_page(page, min_doctors=min_doctors_per_page, max_doctors=max_doctors)
                
                if debug:
                    page.screenshot(path=f'debug_screenshots/page_{current_page}_after_scroll.png')
                
                # Get page content after scrolling
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract search parameters
                search_location = soup.select_one('input[data-qa-id="omni-searchbox-locality"]')['value'] if soup.select_one('input[data-qa-id="omni-searchbox-locality"]') else location
                search_specialty = soup.select_one('input[data-qa-id="omni-searchbox-keyword"]')['value'] if soup.select_one('input[data-qa-id="omni-searchbox-keyword"]') else specialty
                
                # Extract doctor cards
                doctor_cards = soup.select('div[data-qa-id="doctor_card"]')
                print(f"Found {len(doctor_cards)} doctors on page {current_page}")
                
                if not doctor_cards:
                    print("No doctors found on this page, breaking")
                    break
                
                # Limit the number of cards to process based on max_doctors
                remaining_doctors = max_doctors - len(all_doctors)
                if remaining_doctors <= 0:
                    print(f"Already collected {len(all_doctors)} doctors, which meets or exceeds the target of {max_doctors}.")
                    break
                    
                # Determine how many doctors to process from this page
                doctors_to_process = min(len(doctor_cards), remaining_doctors)
                print(f"Processing {doctors_to_process} doctors from this page")
                
                # Process only the limited number of doctor cards
                for i, card in enumerate(doctor_cards[:doctors_to_process]):
                    if verbose or (i+1) % 5 == 0:
                        print(f"Processing doctor {i+1}/{doctors_to_process} on page {current_page} (Total: {len(all_doctors) + i + 1}/{max_doctors})")
                    
                    doctor_data = {
                        'speciality': search_specialty,
                        'location': search_location
                    }
                    
                    # Basic field extraction logic
                    fields = {
                        'name': ('h2[data-qa-id="doctor_name"]', 'text'),
                        'experience': ('[data-qa-id="doctor_experience"]', 'regex', r'(\d+).*?years experience'),
                        'clinic_name': ('a span[data-qa-id="doctor_clinic_name"]', 'text'),
                        'doctor_address': ('span[data-qa-id="practice_locality"]', 'text'),
                        'consultation_fee': ('[data-qa-id="consultation_fee"]', 'digits'),
                        'recommendation_percent': ('[data-qa-id="doctor_recommendation"]', 'text'),
                        'patient_stories': ('[data-qa-id="total_feedback"]', 'digits')
                    }
                    
                    for field, (selector, *extract_type) in fields.items():
                        try:
                            elem = card.select_one(selector)
                            if not elem:
                                doctor_data[field] = "Not available"
                                continue
                                
                            if extract_type[0] == 'text':
                                doctor_data[field] = elem.text.strip()
                            elif extract_type[0] == 'digits':
                                doctor_data[field] = re.sub(r'\D', '', elem.text) or "Not available"
                            elif extract_type[0] == 'regex':
                                match = re.search(extract_type[1], elem.text)
                                doctor_data[field] = match.group(1) if match else "Not available"
                        except Exception as e:
                            doctor_data[field] = "Not available"
                            if verbose:
                                print(f"Error extracting {field}: {str(e)}")
                    
                    # Extract profile URL and visit doctor profile page
                    doctor_url = card.select_one('a[href*="/doctor/"]')
                    if doctor_url:
                        doctor_profile_url = "https://www.practo.com" + doctor_url['href']
                        doctor_data['doctor_url'] = doctor_profile_url
                        
                        try:
                            # Visit doctor profile page to get detailed information
                            if verbose:
                                print(f"Visiting doctor profile: {doctor_profile_url}")
                            profile_page = context.new_page()
                            
                            # Use navigation timeout and retry logic
                            max_retries = 3
                            retry_count = 0
                            
                            while retry_count < max_retries:
                                try:
                                    profile_page.goto(doctor_profile_url, timeout=30000)
                                    break
                                except Exception as e:
                                    retry_count += 1
                                    if verbose:
                                        print(f"Navigation error (attempt {retry_count}/{max_retries}): {str(e)}")
                                    if retry_count >= max_retries:
                                        raise
                                    # Wait before retry
                                    time.sleep(2)
                            
                            # Use the specific profile page scrolling function
                            scroll_profile_page(profile_page)

                            # Extract detailed qualifications from profile page
                            detailed_qualifications_elem = profile_page.query_selector('p.c-profile__details[data-qa-id="doctor-qualifications"]')
                            if detailed_qualifications_elem:
                                doctor_data['detailed_qualifications'] = detailed_qualifications_elem.inner_text().strip()
                            else:
                                doctor_data['detailed_qualifications'] = "Not available"
                            
                            # Extract contact number
                            doctor_data['contact_number'] = extract_contact_number(profile_page)
                            
                            profile_page.close()
                        except Exception as e:
                            print(f"Error processing doctor profile: {str(e)}")
                            if verbose:
                                traceback.print_exc()  # Print full traceback only in verbose mode
                            
                            # Still add what we've gotten so far
                            all_doctors.append(doctor_data)
                            continue
                    else:
                        doctor_data['doctor_url'] = "Not available"
                        doctor_data['contact_number'] = "Not available"
                        doctor_data['detailed_qualifications'] = "Not available"
                    
                    all_doctors.append(doctor_data)
                    
                    # Save intermediate results every 30 doctors
                    if len(all_doctors) % 30 == 0:
                        temp_df = pd.DataFrame(all_doctors)
                        os.makedirs('output', exist_ok=True)
                        temp_csv = f'practo_{location}_{specialty}_interim_{timestamp}.csv'
                        temp_csv_path = os.path.join('output', temp_csv)
                        temp_df.to_csv(temp_csv_path, index=False)
                        print(f"Saved interim results for {len(all_doctors)} doctors")
                    
                    # Stop if we've reached the maximum number of doctors
                    if len(all_doctors) >= max_doctors:
                        print(f"Reached target of {max_doctors} doctors. Stopping scraper.")
                        break
                
                # Stop if we've reached the maximum number of doctors
                if len(all_doctors) >= max_doctors:
                    break
                
                current_page += 1
                page.close()
                
            except Exception as e:
                print(f"Error scraping page {current_page}: {str(e)}")
                if verbose:
                    traceback.print_exc()
                current_page += 1  # Try next page if current fails
                continue
        
        browser.close()
    
    # Create DataFrame from collected data
    doctors_df = pd.DataFrame(all_doctors)
    
    if not doctors_df.empty:
        # Get the absolute base path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Sanitize the specialty name for file system use
        safe_specialty = specialty.replace('/', '_').replace('\\', '_')
        
        # Create output directory path
        output_dir = os.path.join(base_dir, 'output', f'practo_{location}_{safe_specialty}')
        os.makedirs(output_dir, exist_ok=True)
        
        if save_to_db:
            # Generate SQL statements and save to file
            sql_statements = generate_sql_inserts(doctors_df, table_name)
            sql_filepath = os.path.join(output_dir, f'{table_name}_{timestamp}.sql')
            
            with open(sql_filepath, 'w', encoding='utf-8') as sql_file:
                sql_file.write(sql_statements)
            
            print(f"SQL INSERT statements saved to {sql_filepath}")
        
        # Always save to CSV as well
        csv_filename = f'practo_{location}_{safe_specialty}_{timestamp}.csv'
        csv_filepath = os.path.join(output_dir, csv_filename)
        doctors_df.to_csv(csv_filepath, index=False)
        print(f"Data saved to {csv_filepath}")
    else:
        print("No data collected, nothing to save.")
    
    return doctors_df

def main():
    # Define parameters for scraping
    params = {
        'location': "Delhi",
        'specialty': "Dermatologist",  # Updated to match the example from the website
        'num_pages': 1,
        'debug': True,
        'min_doctors_per_page': 30,
        'verbose': False,
        'max_doctors': 3000,
        'save_to_db': True,
        'table_name': 'practo_doctors'
    }

    print(f"Starting Practo scraper with:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()
    
    # Run the scraper
    doctors_df = scrape_practo_doctors(**params)
    
    if not doctors_df.empty:
        print(f"\nSuccessfully scraped {len(doctors_df)} doctors")
        print("\nSample data:")
        print(doctors_df[['name', 'contact_number', 'clinic_name', 'detailed_qualifications']].head(3))
    else:
        print("No doctors were scraped. Please check the logs for errors.")

if __name__ == "__main__":
    main() 