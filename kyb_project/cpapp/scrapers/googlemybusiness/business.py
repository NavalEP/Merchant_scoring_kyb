import os
import pickle
import time
import random
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import language_v1


# If modifying scopes, delete the token.pickle file
SCOPES = ['https://www.googleapis.com/auth/business.manage']

def get_credentials():
    """
    Gets valid user credentials from storage or initiates the OAuth flow.
    Returns credentials object.
    """
    creds = None
    
    # Check if token.pickle exists with saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If no valid credentials available, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client secrets from client_secrets.json
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    return creds

def make_api_request_with_backoff(request_func, max_retries=5):
    """
    Execute an API request with exponential backoff for rate limiting.
    """
    retries = 0
    while retries < max_retries:
        try:
            return request_func()
        except HttpError as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                wait_time = (2 ** retries) + random.random()
                print(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise
    raise Exception("Max retries exceeded")

def get_all_accounts():
    """
    Retrieve all Google Business Profile accounts for the authenticated user.
    """
    credentials = get_credentials()
    service = build('mybusinessaccountmanagement', 'v1', credentials=credentials)
    
    try:
        accounts = make_api_request_with_backoff(
            lambda: service.accounts().list().execute()
        )
        return accounts.get('accounts', [])
    except Exception as e:
        print(f"Error retrieving accounts: {str(e)}")
        return []

def get_all_locations(account_name):
    """
    Retrieve all locations for a specific account with pagination.
    """
    credentials = get_credentials()
    service = build('mybusinessbusinessinformation', 'v1', credentials=credentials)
    
    all_locations = []
    page_token = None
    
    while True:
        try:
            response = make_api_request_with_backoff(
                lambda: service.accounts().locations().list(
                    parent=account_name,
                    pageSize=100,
                    pageToken=page_token if page_token else ''
                ).execute()
            )
            
            locations = response.get('locations', [])
            all_locations.extend(locations)
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        except Exception as e:
            print(f"Error retrieving locations: {str(e)}")
            break
            
    return all_locations

def filter_healthcare_locations(locations):
    """
    Filter locations to include only healthcare-related businesses.
    """
    healthcare_categories = [
        "doctor", 
        "medical_clinic", 
        "dentist", 
        "hospital",
        "physician",
        "healthcare"
    ]

    filtered_locations = []
    for location in locations:
        primary_category = location.get('primaryCategory', {}).get('displayName', '').lower()
        if any(category in primary_category for category in healthcare_categories):
            filtered_locations.append(location)
            
    return filtered_locations

def get_location_reviews(location_name):
    """
    Retrieve reviews for a specific location.
    """
    credentials = get_credentials()
    service = build('mybusinessplaceactions', 'v1', credentials=credentials)
    
    all_reviews = []
    page_token = None
    
    while True:
        try:
            response = make_api_request_with_backoff(
                lambda: service.locations().reviews().list(
                    parent=location_name,
                    pageSize=50,
                    pageToken=page_token if page_token else ''
                ).execute()
            )
            
            reviews = response.get('reviews', [])
            all_reviews.extend(reviews)
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        except Exception as e:
            print(f"Error retrieving reviews: {str(e)}")
            break
            
    return all_reviews

def analyze_review_sentiment(review_text):
    """
    Analyze sentiment of review text using Google Cloud Natural Language API.
    """
    client = language_v1.LanguageServiceClient()
    
    document = language_v1.Document(
        content=review_text,
        type_=language_v1.Document.Type.PLAIN_TEXT
    )
    
    try:
        sentiment = client.analyze_sentiment(document=document).document_sentiment
        return {
            'score': sentiment.score,  # Range from -1.0 (negative) to 1.0 (positive)
            'magnitude': sentiment.magnitude  # Intensity of emotion
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {str(e)}")
        return {'score': 0, 'magnitude': 0}

def extract_business_data(location):
    """
    Extract structured business data from location object.
    """
    try:
        address_data = location.get('address', {})
        address_lines = address_data.get('addressLines', [''])
        
        return {
            'name': location.get('title', ''),
            'address': {
                'street': address_lines[0] if address_lines else '',
                'city': address_data.get('locality', ''),
                'state': address_data.get('administrativeArea', ''),
                'zip': address_data.get('postalCode', ''),
                'country': address_data.get('regionCode', '')
            },
            'phone': location.get('phoneNumbers', {}).get('primaryPhone', ''),
            'website': location.get('websiteUri', ''),
            'categories': [
                location.get('primaryCategory', {}).get('displayName', ''),
                *[cat.get('displayName', '') for cat in location.get('additionalCategories', [])]
            ],
            'location_id': location.get('name', '').split('/')[-1]
        }
    except Exception as e:
        print(f"Error extracting business data: {str(e)}")
        return {}

def process_location(location):
    """
    Process a single location to extract all relevant data.
    """
    try:
        location_name = location.get('name')
        
        # Get basic business data
        business_data = extract_business_data(location)
        
        # Get reviews
        reviews = get_location_reviews(location_name)
        
        # Process reviews
        processed_reviews = []
        total_sentiment_score = 0
        
        for review in reviews:
            review_text = review.get('comment', '')
            if review_text:
                sentiment = analyze_review_sentiment(review_text)
                total_sentiment_score += sentiment['score']
                
                processed_reviews.append({
                    'rating': review.get('starRating', {}).get('starRating', 0),
                    'text': review_text,
                    'time': review.get('createTime', ''),
                    'sentiment': sentiment
                })
        
        # Calculate average rating and sentiment
        avg_rating = sum(r.get('rating', 0) for r in processed_reviews) / len(processed_reviews) if processed_reviews else 0
        avg_sentiment = total_sentiment_score / len(processed_reviews) if processed_reviews else 0
        
        # Compile results
        result = {
            'business_data': business_data,
            'reviews': {
                'count': len(processed_reviews),
                'average_rating': avg_rating,
                'average_sentiment': avg_sentiment,
                'reviews': processed_reviews
            }
        }
        
        return result
    except Exception as e:
        print(f"Error processing location: {str(e)}")
        return None

def save_data_to_file(data, filename):
    """
    Save processed data to a JSON file.
    """
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data: {str(e)}")

def main():
    """
    Main function to orchestrate the entire process.
    """
    print("Starting Google Business Profile data collection...")
    
    # Get all accounts
    accounts = get_all_accounts()
    if not accounts:
        print("No accounts found. Please ensure you have access to Google Business Profile.")
        return
    
    print(f"Found {len(accounts)} account(s)")
    
    all_processed_locations = []
    
    # Process each account
    for account in accounts:
        account_name = account.get('name')
        print(f"Processing account: {account.get('accountName')}")
        
        # Get all locations for the account
        locations = get_all_locations(account_name)
        print(f"Found {len(locations)} location(s)")
        
        # Filter for healthcare locations
        healthcare_locations = filter_healthcare_locations(locations)
        print(f"Found {len(healthcare_locations)} healthcare location(s)")
        
        # Process each healthcare location
        for location in healthcare_locations:
            print(f"Processing location: {location.get('title')}")
            processed_location = process_location(location)
            if processed_location:
                all_processed_locations.append(processed_location)
    
    # Save all data
    if all_processed_locations:
        save_data_to_file(all_processed_locations, 'healthcare_locations_data.json')
        print(f"Successfully processed {len(all_processed_locations)} healthcare locations")
    else:
        print("No healthcare locations were processed")

if __name__ == "__main__":
    main()