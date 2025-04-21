import os
import json
from unittest.mock import patch, MagicMock
import business  # Import the main script

def test_credentials():
    """Test that credentials can be obtained"""
    if os.path.exists('token.pickle'):
        print("Found existing token.pickle file")
    else:
        print("No token.pickle found, will need to authenticate")
    
    try:
        credentials = business.get_credentials()
        print("✅ Successfully obtained credentials")
        return True
    except Exception as e:
        print(f"❌ Error getting credentials: {str(e)}")
        return False

def test_api_connection():
    """Test basic API connection"""
    try:
        accounts = business.get_all_accounts()
        print(f"✅ Successfully connected to API and found {len(accounts)} accounts")
        return True
    except Exception as e:
        print(f"❌ Error connecting to API: {str(e)}")
        return False

def mock_test_without_api():
    """Run tests with mocked API responses"""
    # Mock account data
    mock_accounts = [{'name': 'accounts/123', 'accountName': 'Test Medical Practice'}]
    
    # Mock location data
    mock_locations = [
        {
            'name': 'accounts/123/locations/456',
            'title': 'Test Medical Clinic',
            'primaryCategory': {'displayName': 'Medical Clinic'},
            'address': {
                'addressLines': ['123 Medical St'],
                'locality': 'Medical City',
                'administrativeArea': 'MC',
                'postalCode': '12345',
                'regionCode': 'US'
            },
            'phoneNumbers': {'primaryPhone': '123-456-7890'},
            'websiteUri': 'https://testclinic.com'
        }
    ]
    
    # Mock reviews
    mock_reviews = [
        {
            'name': 'accounts/123/locations/456/reviews/789',
            'comment': 'Great service, very professional staff.',
            'starRating': {'starRating': 5},
            'createTime': '2023-01-01T12:00:00Z'
        }
    ]
    
    # Mock sentiment analysis
    mock_sentiment = {'score': 0.8, 'magnitude': 0.9}
    
    # Patch the API functions
    with patch('business.get_all_accounts', return_value=mock_accounts):
        with patch('business.get_all_locations', return_value=mock_locations):
            with patch('business.get_location_reviews', return_value=mock_reviews):
                with patch('business.analyze_review_sentiment', return_value=mock_sentiment):
                    # Run the main function
                    business.main()
    
    # Check if the output file was created
    if os.path.exists('healthcare_locations_data.json'):
        with open('healthcare_locations_data.json', 'r') as f:
            data = json.load(f)
            print(f"✅ Successfully created output file with {len(data)} locations")
        return True
    else:
        print("❌ Failed to create output file")
        return False

def test_specific_function(function_name, *args):
    """Test a specific function from the business module"""
    try:
        function = getattr(business, function_name)
        result = function(*args)
        print(f"✅ Successfully tested {function_name}")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ Error testing {function_name}: {str(e)}")
        return False

if __name__ == "__main__":
    print("Google Business Profile Scraper Test Menu")
    print("----------------------------------------")
    print("1. Test credentials")
    print("2. Test API connection")
    print("3. Run mock test without API")
    print("4. Test specific function")
    print("5. Run full script")
    
    choice = input("Enter your choice (1-5): ")
    
    if choice == '1':
        test_credentials()
    elif choice == '2':
        test_api_connection()
    elif choice == '3':
        mock_test_without_api()
    elif choice == '4':
        available_functions = [
            'get_credentials', 'get_all_accounts', 'get_all_locations',
            'filter_healthcare_locations', 'get_location_reviews',
            'analyze_review_sentiment', 'extract_business_data',
            'process_location', 'save_data_to_file'
        ]
        print("Available functions:")
        for i, func in enumerate(available_functions, 1):
            print(f"{i}. {func}")
        
        func_choice = int(input("Select function to test (1-9): ")) - 1
        if 0 <= func_choice < len(available_functions):
            function_name = available_functions[func_choice]
            
            if function_name == 'get_all_locations':
                account_name = input("Enter account name (e.g., accounts/123456): ")
                test_specific_function(function_name, account_name)
            elif function_name == 'filter_healthcare_locations':
                # Use a simple mock location list
                mock_locs = [
                    {'primaryCategory': {'displayName': 'Medical Clinic'}},
                    {'primaryCategory': {'displayName': 'Restaurant'}}
                ]
                test_specific_function(function_name, mock_locs)
            else:
                test_specific_function(function_name)
        else:
            print("Invalid function choice")
    elif choice == '5':
        business.main()
    else:
        print("Invalid choice") 