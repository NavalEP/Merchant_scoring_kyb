import json
import requests
import logging
from django.conf import settings
from typing import List, Dict, Union, Optional
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

class GeoIQService:
    """Service to interact with GeoIQ API for location-based insights"""
    
    def __init__(self):
        self.api_key = os.getenv('VITE_GEOIQ_API_KEY')
        print(f"GeoIQ API Key: {'*****' + self.api_key[-4:] if self.api_key and len(self.api_key) > 4 else 'NOT FOUND'}")
        
        if not self.api_key:
            logger.error("VITE_GEOIQ_API_KEY not found in environment variables")
            raise ValueError("VITE_GEOIQ_API_KEY is required")
            
        self.base_url = os.getenv('VITE_GEOIQ_BASE_URL')
        print(f"GeoIQ Base URL: {self.base_url}")
        
        if not self.base_url:
            logger.error("VITE_GEOIQ_BASE_URL not found in environment variables")
            raise ValueError("VITE_GEOIQ_BASE_URL is required")
            
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Test API connection
        try:
            # Simple ping to check connectivity - we'll just check the status without fetching data
            test_url = f"{self.base_url}/ping"
            response = requests.get(test_url, headers=self.headers)
            if response.status_code == 200:
                print(f"✅ GeoIQ API Connection Successful")
            else:
                error_message = f"⚠️ GeoIQ API Connection Test Failed (Status Code: {response.status_code})"
                if response.status_code == 401:
                    error_message += f" - Authorization Failed, check your API key"
                elif response.status_code == 403:
                    error_message += f" - Access Forbidden, your account may not have access to this endpoint"
                print(error_message)
                try:
                    error_data = response.json()
                    print(f"Error Details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response Text: {response.text}")
        except Exception as e:
            print(f"⚠️ GeoIQ API Connection Error: {str(e)}")
        
    def get_location_data_by_coordinates(
        self, 
        latitude: float, 
        longitude: float, 
        radius: int = 1000,
        variables: Optional[List[str]] = None
    ) -> Dict:
        """
        Get location data by latitude and longitude
        
        Args:
            latitude (float): Location latitude between -90 to 90
            longitude (float): Location longitude between -180 to 180
            radius (int): Radius in meters (100 to 2000)
            variables (List[str], optional): List of variables to fetch
            
        Returns:
            Dict: Location data for the specified variables
        """
        if variables is None:
            # Default variables for the requirements mentioned
            variables = [
                # Property and rent data
                "p_retail_rppsfa", 
                "residence_arpsf", 
                "retail_rppsfa", 
                "d_residence_rppsfa", 
                "d_comm_rppsfa",
                
                # Neighborhood income data
                "w_pop_tt", 
                "w_hh_income_5l_above_perc", 
                "w_hh_income_10l_above_perc", 
                "w_hh_income_20l_above_perc",
                
                # Household assets data
                "avail_assets_car_jeep_van",
                
                # Retail and commercial data
                "p_retail_gc_np", 
                "p_restaurant_rt_np", 
                "p_dist_sm", 
                "br_v2shoppingmart_ct",
                
                # Office buildings data
                "o_land_bl", 
                "p_work_of_np_pincode",
                
                # Income tax data
                "secc_p_hh_pay_it_pt_r",
                
                # High-end restaurants
                "br_restaurant_ch_nt",
                
                # Healthcare Facilities
                "br_apollohospitals_ct", 
                "br_maxhealthcare_ct", 
                "br_fortishealthcare_ct", 
                "br_medantathemedicity_ct", 
                "br_clovedental_ct",
                
                # Retail & Lifestyle
                "br_lifestyle_ct", 
                "br_shoppersstop_ct", 
                "br_pantaloons_ct", 
                "br_westside_ct", 
                "br_central_ct", 
                "br_maxfashion_ct",
                
                # Luxury Brands
                "br_zara_ct", 
                "br_miniso_ct", 
                "br_calvinklein_ct", 
                "br_tommyhilfiger_ct",
                
                # Jewelry
                "br_tanishq_ct", 
                "br_kalyanjewellers_ct",
                
                # Fitness
                "br_cult_ct", 
                "br_goldsgym_ct", 
                "br_anytimefitness_ct", 
                "br_gym_ch_nt",
                
                # Entertainment
                "br_pvrcinemas_ct", 
                "br_inoxleisurelimited_ct",
                
                # Sports
                "br_nike_ct", 
                "br_adidas_ct", 
                "br_puma_ct", 
                "br_decathlon_ct"
            ]
            
        # Ensure we don't exceed the 50 variable limit
        if len(variables) > 50:
            logger.warning("More than 50 variables requested, truncating to 50")
            variables = variables[:50]
            
        variables_str = ",".join(variables)
        
        endpoint = f"{self.base_url}/getvariables"
        payload = {
            "lat": latitude,
            "lng": longitude,
            "radius": radius,
            "variables": variables_str
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            
            # Check for auth errors specifically
            if response.status_code == 401 or response.status_code == 403:
                auth_error = f"GeoIQ API Authorization Error ({response.status_code}): "
                try:
                    error_data = response.json()
                    if isinstance(error_data.get('body'), str):
                        try:
                            body_data = json.loads(error_data['body'])
                            auth_error += body_data.get('message', 'No error message provided')
                        except:
                            auth_error += error_data.get('body', 'Unknown error')
                    else:
                        auth_error += json.dumps(error_data)
                except:
                    auth_error += response.text or "Unknown error"
                    
                logger.error(auth_error)
                print(f"\n❌ AUTHORIZATION ERROR: {auth_error}")
                print("To fix this issue:")
                print("1. Check your .env file has the correct VITE_GEOIQ_API_KEY")
                print("2. Verify your API key is valid and has not expired")
                print("3. Make sure your account has access to the requested variables")
                print("4. Check if your plan has exceeded its quota or limits\n")
                
                # Return empty data to prevent breaking the application
                return {}
            
            response.raise_for_status()
            result = response.json()
            
            # Print API response for debugging
            print(f"\n===== GeoIQ API Response =====")
            print(f"Coordinates: {latitude}, {longitude} (radius: {radius}m)")
            print(f"Status: {result.get('status')}")
            print(f"Response Type: {type(result)}")
            print(f"Response Size: {len(json.dumps(result))} bytes")
            try:
                print(f"Number of variables returned: {len(result.get('data', {}))}")
            except:
                print("Could not determine number of variables")
            
            if result.get("status") != 200:
                print(f"ERROR: {json.dumps(result, indent=2)}")
            else:
                print(f"SUCCESS: Contains data for {len(variables)} requested variables")
            print(f"===============================\n")
            
            if isinstance(result.get('body'), str):
                # Parse the nested JSON string in body
                body_data = json.loads(result['body'])
                if body_data.get('status') == 200:
                    return body_data['data']
            
            if result.get("status") == 200:
                if "body" in result:
                    return result["body"]["data"]
                return result["data"]
            
            logger.error(f"GeoIQ API error: {result}")
            raise Exception(f"GeoIQ API returned status {result.get('status')}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    def get_location_data_by_address(
        self, 
        address: str, 
        pincode: Optional[str] = None,
        radius: int = 1000,
        variables: Optional[List[str]] = None
    ) -> Dict:
        """
        Get location data by address
        
        Args:
            address (str): Complete address of the location
            pincode (str, optional): Pincode to improve geocoding accuracy
            radius (int): Radius in meters (100 to 2000)
            variables (List[str], optional): List of variables to fetch
            
        Returns:
            Dict: Location data for the specified variables
        """
        if variables is None:
            # Default variables for the requirements mentioned
            variables = [
                # Property and rent data
                "p_retail_rppsfa", 
                "residence_arpsf", 
                "retail_rppsfa", 
                "d_residence_rppsfa", 
                "d_comm_rppsfa",
                
                # Neighborhood income data
                "w_pop_tt", 
                "w_hh_income_5l_above_perc", 
                "w_hh_income_10l_above_perc", 
                "w_hh_income_20l_above_perc",
                
                # Household assets data
                "avail_assets_car_jeep_van",
                
                # Retail and commercial data
                "p_retail_gc_np", 
                "p_restaurant_rt_np", 
                "p_dist_sm", 
                "br_v2shoppingmart_ct",
                
                # Office buildings data
                "o_land_bl", 
                "p_work_of_np_pincode",
                
                # Income tax data
                "secc_p_hh_pay_it_pt_r",
                
                # High-end restaurants
                "br_restaurant_ch_nt",
                
                # Healthcare Facilities
                "br_apollohospitals_ct", 
                "br_maxhealthcare_ct", 
                "br_fortishealthcare_ct", 
                "br_medantathemedicity_ct", 
                "br_clovedental_ct",
                
                # Retail & Lifestyle
                "br_lifestyle_ct", 
                "br_shoppersstop_ct", 
                "br_pantaloons_ct", 
                "br_westside_ct", 
                "br_central_ct", 
                "br_maxfashion_ct",
                
                # Luxury Brands
                "br_zara_ct", 
                "br_miniso_ct", 
                "br_calvinklein_ct", 
                "br_tommyhilfiger_ct",
                
                # Jewelry
                "br_tanishq_ct", 
                "br_kalyanjewellers_ct",
                
                # Fitness
                "br_cult_ct", 
                "br_goldsgym_ct", 
                "br_anytimefitness_ct", 
                "br_gym_ch_nt",
                
                # Entertainment
                "br_pvrcinemas_ct", 
                "br_inoxleisurelimited_ct",
                
                # Sports
                "br_nike_ct", 
                "br_adidas_ct", 
                "br_puma_ct", 
                "br_decathlon_ct"
            ]
            
        # Ensure we don't exceed the 50 variable limit
        if len(variables) > 50:
            logger.warning("More than 50 variables requested, truncating to 50")
            variables = variables[:50]
            
        variables_str = ",".join(variables)
        
        endpoint = f"{self.base_url}/getvariables"
        
        payload = {
            "address": address,
            "radius": radius,
            "variables": variables_str
        }
        
        if pincode:
            payload["pincode"] = pincode
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            
            # Check for auth errors specifically
            if response.status_code == 401 or response.status_code == 403:
                auth_error = f"GeoIQ API Authorization Error ({response.status_code}): "
                try:
                    error_data = response.json()
                    if isinstance(error_data.get('body'), str):
                        try:
                            body_data = json.loads(error_data['body'])
                            auth_error += body_data.get('message', 'No error message provided')
                        except:
                            auth_error += error_data.get('body', 'Unknown error')
                    else:
                        auth_error += json.dumps(error_data)
                except:
                    auth_error += response.text or "Unknown error"
                    
                logger.error(auth_error)
                print(f"\n❌ AUTHORIZATION ERROR: {auth_error}")
                print("To fix this issue:")
                print("1. Check your .env file has the correct VITE_GEOIQ_API_KEY")
                print("2. Verify your API key is valid and has not expired")
                print("3. Make sure your account has access to the requested variables")
                print("4. Check if your plan has exceeded its quota or limits\n")
                
                # Return empty data to prevent breaking the application
                return {}
            
            response.raise_for_status()
            result = response.json()
            
            # Print API response for debugging
            print(f"\n===== GeoIQ API Response =====")
            print(f"Address: {address}")
            print(f"Status: {result.get('status')}")
            print(f"Response Type: {type(result)}")
            print(f"Response Size: {len(json.dumps(result))} bytes")
            try:
                print(f"Number of variables returned: {len(result.get('data', {}))}")
            except:
                print("Could not determine number of variables")
            
            if result.get("status") != 200:
                print(f"ERROR: {json.dumps(result, indent=2)}")
            else:
                print(f"SUCCESS: Contains data for {len(variables)} requested variables")
            print(f"===============================\n")
            
            if isinstance(result.get('body'), str):
                # Parse the nested JSON string in body
                body_data = json.loads(result['body'])
                if body_data.get('status') == 200:
                    return body_data['data']
            
            if result.get("status") == 200:
                if "body" in result:
                    return result["body"]["data"]
                return result["data"]
            
            logger.error(f"GeoIQ API error: {result}")
            raise Exception(f"GeoIQ API returned status {result.get('status')}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise

    def analyze_location(
        self, 
        latitude: Optional[float] = None, 
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        pincode: Optional[str] = None,
        radius: int = 1000
    ) -> Dict:
        """
        Comprehensive location analysis with all required metrics
        
        Args:
            latitude (float, optional): Location latitude
            longitude (float, optional): Location longitude
            address (str, optional): Address if coordinates not provided
            pincode (str, optional): Pincode for address
            radius (int): Radius in meters (100 to 2000)
            
        Returns:
            Dict: Comprehensive location analysis
        """
        # Top 50 variables that are most valuable for location analysis
        variables = [
            # Property and rent data
            "p_retail_rppsfa", 
            "residence_arpsf", 
            "retail_rppsfa", 
            "d_residence_rppsfa", 
            "d_comm_rppsfa",
            
            # Neighborhood income data
            "w_pop_tt", 
            "w_hh_income_5l_above_perc", 
            "w_hh_income_10l_above_perc", 
            "w_hh_income_20l_above_perc",
            
            # Household assets data
            "avail_assets_car_jeep_van",
            
            # Retail and commercial data
            "p_retail_gc_np", 
            "p_restaurant_rt_np", 
            "p_dist_sm", 
            "br_v2shoppingmart_ct",
            
            # Office buildings data
            "o_land_bl", 
            "p_work_of_np_pincode",
            
            # Income tax data
            "secc_p_hh_pay_it_pt_r",
            
            # High-end restaurants
            "br_restaurant_ch_nt",
            
            # Healthcare Facilities
            "br_apollohospitals_ct", 
            "br_maxhealthcare_ct", 
            "br_fortishealthcare_ct", 
            "br_medantathemedicity_ct", 
            "br_clovedental_ct",
            
            # Retail & Lifestyle
            "br_lifestyle_ct", 
            "br_shoppersstop_ct", 
            "br_pantaloons_ct", 
            "br_westside_ct", 
            "br_central_ct", 
            "br_maxfashion_ct",
            
            # Luxury Brands
            "br_zara_ct", 
            "br_miniso_ct", 
            "br_calvinklein_ct", 
            "br_tommyhilfiger_ct",
            
            # Jewelry
            "br_tanishq_ct", 
            "br_kalyanjewellers_ct",
            
            # Fitness
            "br_cult_ct", 
            "br_goldsgym_ct", 
            "br_anytimefitness_ct", 
            "br_gym_ch_nt",
            
            # Entertainment
            "br_pvrcinemas_ct", 
            "br_inoxleisurelimited_ct",
            
            # Sports
            "br_nike_ct", 
            "br_adidas_ct", 
            "br_puma_ct", 
            "br_decathlon_ct"
        ]
        
        # Get raw data from GeoIQ
        if latitude is not None and longitude is not None:
            raw_data = self.get_location_data_by_coordinates(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                variables=variables
            )
        elif address:
            raw_data = self.get_location_data_by_address(
                address=address,
                pincode=pincode,
                radius=radius,
                variables=variables
            )
        else:
            raise ValueError("Either coordinates or address must be provided")
            
        # Organize data into required categories
        analysis = {
            "rental_rates": {
                "commercial_per_sqft": raw_data.get("p_retail_rppsfa", 0),
                "residential_per_sqft": raw_data.get("residence_arpsf", 0),
                "retail_per_sqft": raw_data.get("retail_rppsfa", 0),
                "predicted_residential_rent_per_sqft": raw_data.get("d_residence_rppsfa", 0),
                "predicted_commercial_rent_per_sqft": raw_data.get("d_comm_rppsfa", 0)
            },
            "household_assets": {
                "households_with_vehicles": raw_data.get("avail_assets_car_jeep_van", 0)
            },
            "neighborhood_income": {
                "total_population": raw_data.get("w_pop_tt", 0),
                "percentage_households_that_have_income_above_5_LPA": raw_data.get("w_hh_income_5l_above_perc", 0),
                "percentage_households_that_have_income_above_10_LPA": raw_data.get("w_hh_income_10l_above_perc", 0),
                "percentage_households_that_have_income_above_20_LPA": raw_data.get("w_hh_income_20l_above_perc", 0)
            },
            "similar_brands": {
                # Retail density
                "retail_density": raw_data.get("p_retail_gc_np", 0),
                "restaurant_density": raw_data.get("p_restaurant_rt_np", 0),
                
                # High-end restaurants data
                "high_end_restaurants_proportion": raw_data.get("br_restaurant_ch_nt", 0),
                
                # Fitness centers counts
                "anytime_fitness_count": raw_data.get("br_anytimefitness_ct", 0),
                "cult_count": raw_data.get("br_cult_ct", 0),
                "golds_gym_count": raw_data.get("br_goldsgym_ct", 0),
                "high_end_gyms_proportion": raw_data.get("br_gym_ch_nt", 0),
                
                # Cinema/theater counts
                "inox_leisure_count": raw_data.get("br_inoxleisurelimited_ct", 0),
                "pvr_cinemas_count": raw_data.get("br_pvrcinemas_ct", 0),
                
                # Income tax data
                "percentage_rural_households_paying_income_tax": raw_data.get("secc_p_hh_pay_it_pt_r", 0),
                
                # Healthcare facilities counts
                "apollo_hospitals_count": raw_data.get("br_apollohospitals_ct", 0),
                "clove_dental_count": raw_data.get("br_clovedental_ct", 0),
                "max_healthcare_count": raw_data.get("br_maxhealthcare_ct", 0),
                "medanta_the_medicity_count": raw_data.get("br_medantathemedicity_ct", 0),
                "fortis_healthcare_count": raw_data.get("br_fortishealthcare_ct", 0),
                
                # Sports stores counts
                "adidas_store_count": raw_data.get("br_adidas_ct", 0),
                "puma_store_count": raw_data.get("br_puma_ct", 0),
                "nike_store_count": raw_data.get("br_nike_ct", 0),
                "decathlon_store_count": raw_data.get("br_decathlon_ct", 0),

                # Jewelry stores counts
                "kalyan_jewellers_count": raw_data.get("br_kalyanjewellers_ct", 0),
                "tanishq_count": raw_data.get("br_tanishq_ct", 0),
                
                # Fashion and retail stores counts
                "biba_store_count": raw_data.get("br_biba_ct", 0),
                "calvin_klein_store_count": raw_data.get("br_calvinklein_ct", 0),
                "central_store_count": raw_data.get("br_central_ct", 0),
                "fabindia_store_count": raw_data.get("br_fabindia_ct", 0),
                "lifestyle_store_count": raw_data.get("br_lifestyle_ct", 0),
                "max_fashion_store_count": raw_data.get("br_maxfashion_ct", 0),
                "miniso_store_count": raw_data.get("br_miniso_ct", 0),
                "pantaloons_store_count": raw_data.get("br_pantaloons_ct", 0),
                "shoppers_stop_store_count": raw_data.get("br_shoppersstop_ct", 0),
                "tommy_hilfiger_store_count": raw_data.get("br_tommyhilfiger_ct", 0),
                "westside_store_count": raw_data.get("br_westside_ct", 0),
                "zara_store_count": raw_data.get("br_zara_ct", 0)
            },
            "shopping_malls": {
                "nearest_shopping_mall": raw_data.get("p_dist_sm", 0),
                "v2_shopping_mart_count": raw_data.get("br_v2shoppingmart_ct", 0)
            },
            "office_buildings": {
                "building_land": raw_data.get("o_land_bl", 0),
                "office_proportion_in_subdistrict": raw_data.get("p_work_of_np_pincode", 0)
            },
            "raw_data": raw_data  # Include raw data for reference if needed
        }
        
        # Calculate location score using the enhanced algorithm (matching the scoring engine)
        # Income indicators
        avg_income_5l = raw_data.get('w_hh_income_5l_above_perc', 0)
        avg_income_10l = raw_data.get('w_hh_income_10l_above_perc', 0)
        avg_income_20l = raw_data.get('w_hh_income_20l_above_perc', 0)
        income_tax_payers = raw_data.get('secc_p_hh_pay_it_pt_r', 0)

        # Commercial indicators
        retail_density = raw_data.get('p_retail_gc_np', 0)
        restaurant_density = raw_data.get('p_restaurant_rt_np', 0)
        retail_rent = raw_data.get('p_retail_rppsfa', 0)

        # Lifestyle indicators
        high_end_restaurants = raw_data.get('br_restaurant_ch_nt', 0)
        fitness_centers = (
            raw_data.get('br_anytimefitness_ct', 0) + 
            raw_data.get('br_cult_ct', 0) + 
            raw_data.get('br_goldsgym_ct', 0)
        )
        entertainment = (
            raw_data.get('br_pvrcinemas_ct', 0) + 
            raw_data.get('br_inoxleisurelimited_ct', 0)
        )

        # Premium retail presence
        premium_retail = (
            raw_data.get('br_lifestyle_ct', 0) + 
            raw_data.get('br_shoppersstop_ct', 0) + 
            raw_data.get('br_zara_ct', 0) + 
            raw_data.get('br_miniso_ct', 0) + 
            raw_data.get('br_tanishq_ct', 0) + 
            raw_data.get('br_calvinklein_ct', 0) + 
            raw_data.get('br_tommyhilfiger_ct', 0)
        )

        # Healthcare indicators
        healthcare_facilities = (
            raw_data.get('br_apollohospitals_ct', 0) + 
            raw_data.get('br_maxhealthcare_ct', 0) + 
            raw_data.get('br_fortishealthcare_ct', 0) + 
            raw_data.get('br_medantathemedicity_ct', 0)
        )

        # Calculate location score points (max 30 points)
        location_points = 0

        # Income indicators (0-10 points)
        if avg_income_10l > 25 or avg_income_20l > 10:
            location_points += 10
        elif avg_income_10l > 15 or avg_income_5l > 30:
            location_points += 7
        elif avg_income_5l > 20 or income_tax_payers > 15:
            location_points += 4

        # Commercial viability (0-7 points)
        if retail_density > 20 or retail_rent > 150:
            location_points += 7
        elif retail_density > 10 or retail_rent > 100:
            location_points += 4
        elif retail_density > 5 or restaurant_density > 10:
            location_points += 2

        # Premium establishments (0-8 points)
        if premium_retail >= 5 or high_end_restaurants > 0.5:
            location_points += 8
        elif premium_retail >= 3 or fitness_centers >= 3:
            location_points += 5
        elif premium_retail >= 1 or fitness_centers >= 1:
            location_points += 2

        # Healthcare ecosystem (0-5 points)
        if healthcare_facilities >= 3:
            location_points += 5
        elif healthcare_facilities >= 1:
            location_points += 3

        # Determine location category based on points
        if location_points >= 20:
            location_category = "Prime"
        elif location_points >= 12:
            location_category = "Medium"
        else:
            location_category = "Poor"

        # Add location score to analysis
        analysis["location_score"] = {
            "points": location_points,
            "max_points": 30,
            "category": location_category,
            "factors": {
                "income_indicators": {
                    "avg_income_5l_percent": avg_income_5l,
                    "avg_income_10l_percent": avg_income_10l,
                    "avg_income_20l_percent": avg_income_20l,
                    "income_tax_payers_percent": income_tax_payers
                },
                "commercial_indicators": {
                    "retail_density": retail_density,
                    "restaurant_density": restaurant_density,
                    "retail_rent": retail_rent
                },
                "premium_indicators": {
                    "premium_retail_count": premium_retail,
                    "high_end_restaurants": high_end_restaurants,
                    "fitness_centers": fitness_centers,
                    "entertainment_venues": entertainment
                },
                "healthcare_facilities": healthcare_facilities
            }
        }

        # Print full response for debugging
        logger.info(f"GeoIQ Analysis - Location Category: {location_category} (Score: {location_points}/30)")
        logger.debug(f"GeoIQ Raw Response: {json.dumps(raw_data, indent=2)}")
        logger.debug(f"GeoIQ Processed Analysis: {json.dumps(analysis, indent=2, default=str)}")

        return analysis