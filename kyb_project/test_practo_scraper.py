#!/usr/bin/env python
"""
Test script for Practo scraper
"""
import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kyb_project.settings')
django.setup()

from cpapp.scrapers.enhanced_practo_scrape import scrape_practo_doctors


def test_practo_scraper():
    """Test function for Practo scraper"""
    print("Testing Practo scraper...")
    
    # Parameters for the scraper
    location = input("Enter location (e.g., Delhi): ") or "Delhi"
    specialty = input("Enter specialty (e.g., Dentist, ENT Specialist): ") or "Dentist"
    num_pages = int(input("Enter number of pages to scrape (default 1): ") or "1")
    max_doctors = int(input("Enter maximum number of doctors to scrape (default 300): ") or "300")
    generate_sql = input("Generate SQL statements? (y/n, default y): ").lower() != 'n'
    table_name = input("Enter SQL table name (default 'practo_doctors'): ") or "practo_doctors"
    
    print(f"\nStarting scrape for {specialty} in {location} ({num_pages} pages, max {max_doctors} doctors)...")
    if generate_sql:
        print(f"Will generate SQL for table: {table_name}")
    
    try:
        # Call the scraper
        doctors_df = scrape_practo_doctors(
            location=location,
            specialty=specialty,
            num_pages=num_pages,
            max_doctors=max_doctors,
            save_to_db=generate_sql,
            table_name=table_name
        )
        
        print(f"\nScraping completed successfully!")
        print(f"Found {len(doctors_df)} doctors")
        
        # Print first few rows
        if not doctors_df.empty:
            print("\nSample data:")
            print(doctors_df[['name', 'contact_number', 'clinic_name']].head())
            
            # Show output file locations
            print("\nOutput files:")
            print(f"CSV: output/practo_{location}_{specialty}_*.csv")
            if generate_sql:
                print(f"SQL: output/practo_{location}_{specialty}_*.sql")
        
        return True
    except Exception as e:
        print(f"\nError testing scraper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_practo_scraper()
    sys.exit(0 if success else 1) 