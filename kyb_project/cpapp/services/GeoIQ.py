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
        print(self.api_key)
        if not self.api_key:
            logger.error("GEOIQ_API_KEY not found in environment variables")
            raise ValueError("GEOIQ_API_KEY is required")
            
        self.base_url = os.getenv('VITE_GEOIQ_BASE_URL')
        print(self.base_url)
        if not self.base_url:
            logger.error("GEOIQ_BASE_URL not found in environment variables")
            raise ValueError("GEOIQ_BASE_URL is required")
            
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
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
                # Commercial/residential rent data
                "p_retail_rppsfa", "residence_arpsf", "retail_rppsfa", "d_residence_rppsfa", "d_comm_rppsfa",
                # Neighborhood income data
                "w_pop_tt", "w_hh_income_5l_above", "w_hh_income_5l_above_temp", "w_hh_income_5l_above_perc",
                "w_hh_income_10l_above", "w_hh_income_10l_above_temp", "w_hh_income_10l_above_perc",
                "w_hh_income_20l_above", "w_hh_income_20l_above_temp", "w_hh_income_20l_above_perc",
                # Household assets data
                "avail_assets_car_jeep_van",
                # Similar brands data
                "p_retail_gc_np", "p_restaurant_rt_np", "br_brandfactory_ct",
                # Shopping malls data
                "p_dist_sm", "br_v2shoppingmart_ct",
                # Office buildings data
                "o_land_bl",
                # Additional variables
                "distance_to_nearest_grocery_store",
                "average_restaurant_meal_price_for_two",
                "number_of_v2_shopping_mart_stores",
                "office_proportion_in_subdistrict",
                "p_work_of_np_pincode",
                # Sports stores
                "br_adidas_ct", "br_asics_ct", "br_fila_ct", "br_puma_ct", "br_reebok_ct", 
                "br_skechers_ct", "br_thenorthface_ct", "br_nike_ct",
                # Jewelry stores
                "br_amrapalijewellers_ct", "br_atlasjewellery_ct", "br_bhimajewellers_ct",
                "br_caratlane_ct", "br_geetanjali_ct", "br_gitanjali_ct", "br_grtjewellers_ct",
                "br_joscogroup_ct", "br_joyalukkas_ct", "br_joyalukkasjewellery_ct",
                "br_kalyanjewellers_ct", "br_malabar_ct", "br_malabargoldanddiamonds_ct",
                "br_orrajewellery_ct", "br_pcchandrajewellers_ct", "br_pcjeweller_ct",
                "br_saravana_ct", "br_senco_ct", "br_shubhjewellers_ct", "br_tanishq_ct",
                "br_tribhovandasbhimjizaveri_ct",
                # High-end restaurants
                "br_restaurant_ch_nt",
                # Fitness centers
                "br_anytimefitness_ct", "br_cult_ct", "br_fitnessfirst_ct", "br_goldsgym_ct", "br_gym_ch_nt",
                # Cinema/theater
                "br_cinemax_ct", "br_cinepolis_ct", "br_inoxleisurelimited_ct", "br_pvrcinemas_ct", "br_goldcinemas_ct",
                # Income tax data
                "secc_p_hh_pay_it_pt_r",
                # Healthcare facilities
                "br_apollohospitals_ct", "br_clovedental_ct", "br_maxhealthcare_ct", "br_drbatras_ct", "br_apollodentalclinic_ct",
                "br_gleneaglesglobalhospitals_ct", "br_medantathemedicity_ct", "br_wockhardthospitals_ct",
                "br_columbiaasia_ct", "br_fortishealthcare_ct",
                # Fashion and retail stores
                "br_accessorize_ct", "br_aeropostale_ct", "br_aldo_ct", "br_allensolly_ct",
                "br_and_ct", "br_anitadongre_ct", "br_arrow_ct", "br_aurelia_ct", "br_bata_ct",
                "br_beinghuman_ct", "br_biba_ct", "br_blackberrys_ct", "br_calvinklein_ct",
                "br_catwalk_ct", "br_celio_ct", "br_central_ct", "r_centro_ct", "br_chumbak_ct",
                "br_classicpolo_ct", "br_coach_ct", "br_ddmas_ct", "br_decathlon_ct", "br_dior_ct",
                "br_emporioarmani_ct", "br_fabindia_ct", "br_fastrack_ct", "br_fbb_ct",
                "br_flyingmachine_ct", "br_forever21_ct", "br_ginijony_ct", "br_hm_ct",
                "br_indianterrain_ct", "br_jackjones_ct", "br_jockey_ct", "br_khadims_ct",
                "br_lee_ct", "br_leecooper_ct", "br_levis_ct", "br_lifestyle_ct", "br_lotto_ct",
                "br_louisphilippe_ct", "br_madame_ct", "br_manyavar_ct", "br_marksspencer_ct",
                "br_maxfashion_ct", "br_meenabazar_ct", "br_michaelkors_ct", "br_miniso_ct",
                "br_montecarlo_ct", "br_more_ct", "br_mufti_ct", "br_nalli_ct", "br_namdharisfresh_ct",
                "br_nautica_ct", "br_neerus_ct", "br_next_ct", "br_numerouno_ct", "br_oxemberg_ct",
                "br_pantaloons_ct", "br_parkavenue_ct", "br_paulshark_ct", "br_pepejeans_ct",
                "br_peterengland_ct", "br_planetfashion_ct", "br_provogue_ct", "br_raymond_ct",
                "br_reliancefootprints_ct", "br_reliancetrendz_ct", "br_sabyasachi_ct", "br_saks_ct",
                "br_shoppersstop_ct", "br_siyaram_ct", "br_splash_ct", "br_spykar_ct",
                "br_stevemadden_ct", "br_swarovski_ct", "br_tommyhilfiger_ct",
                "br_unitedcolorsofbenetton_ct", "br_uspolo_ct", "br_vanheusen_ct", "br_veromoda_ct",
                "br_versace_ct", "r_wforwoman_ct", "br_westside_ct", "br_wills_ct", "br_woodland_ct",
                "br_worldoftitan_ct", "br_wrangler_ct", "br_zara_ct", "br_zodiac_ct", "br_hidesign_ct",
                "br_menmoms_ct", "br_duke_ct", "br_timex_ct", "br_firstcry_ct", "br_sonata_ct",
                "br_sunglasshut_ct", "br_superdry_ct", "br_helios_ct", "br_cantabil_ct", "br_rado_ct",
                "br_rayban_ct", "br_converse_ct", "br_addons_ct", "br_justwatches_ct", "br_mothercare_ct",
                "br_only_ct", "br_kapoor_ct", "br_casio_ct", "br_twillsretail_ct", "br_toonzstore_ct",
                "br_fossil_ct", "br_oakley_ct", "br_ethoswatches_ct", "br_hamleys_ct",
                "br_forevernewapparels_ct"
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
            response.raise_for_status()
            result = response.json()
            
            # Add this check for partial success
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
                # Commercial/residential rent data
                "p_retail_rppsfa", "residence_arpsf", "retail_rppsfa", "d_residence_rppsfa", "d_comm_rppsfa",
                # Neighborhood income data
                "w_pop_tt", "w_hh_income_5l_above", "w_hh_income_5l_above_temp", "w_hh_income_5l_above_perc",
                "w_hh_income_10l_above", "w_hh_income_10l_above_temp", "w_hh_income_10l_above_perc",
                "w_hh_income_20l_above", "w_hh_income_20l_above_temp", "w_hh_income_20l_above_perc",
                # Household assets data
                "avail_assets_car_jeep_van",
                # Similar brands data
                "p_retail_gc_np", "p_restaurant_rt_np", "br_brandfactory_ct",
                # Shopping malls data
                "p_dist_sm", "br_v2shoppingmart_ct",
                # Office buildings data
                "o_land_bl",
                # Additional variables
                "distance_to_nearest_grocery_store",
                "average_restaurant_meal_price_for_two",
                "number_of_v2_shopping_mart_stores",
                "office_proportion_in_subdistrict",
                "p_work_of_np_pincode",
                # Sports stores
                "br_adidas_ct", "br_asics_ct", "br_fila_ct", "br_puma_ct", "br_reebok_ct", 
                "br_skechers_ct", "br_thenorthface_ct", "br_nike_ct",
                # Jewelry stores
                "br_amrapalijewellers_ct", "br_atlasjewellery_ct", "br_bhimajewellers_ct",
                "br_caratlane_ct", "br_geetanjali_ct", "br_gitanjali_ct", "br_grtjewellers_ct",
                "br_joscogroup_ct", "br_joyalukkas_ct", "br_joyalukkasjewellery_ct",
                "br_kalyanjewellers_ct", "br_malabar_ct", "br_malabargoldanddiamonds_ct",
                "br_orrajewellery_ct", "br_pcchandrajewellers_ct", "br_pcjeweller_ct",
                "br_saravana_ct", "br_senco_ct", "br_shubhjewellers_ct", "br_tanishq_ct",
                "br_tribhovandasbhimjizaveri_ct",
                # High-end restaurants
                "br_restaurant_ch_nt",
                # Fitness centers
                "br_anytimefitness_ct", "br_cult_ct", "br_fitnessfirst_ct", "br_goldsgym_ct", "br_gym_ch_nt",
                # Cinema/theater
                "br_cinemax_ct", "br_cinepolis_ct", "br_inoxleisurelimited_ct", "br_pvrcinemas_ct", "br_goldcinemas_ct",
                # Income tax data
                "secc_p_hh_pay_it_pt_r",
                # Healthcare facilities
                "br_apollohospitals_ct", "br_clovedental_ct", "br_maxhealthcare_ct", "br_drbatras_ct", "br_apollodentalclinic_ct",
                "br_gleneaglesglobalhospitals_ct", "br_medantathemedicity_ct", "br_wockhardthospitals_ct",
                "br_columbiaasia_ct", "br_fortishealthcare_ct",
                # Fashion and retail stores
                "br_accessorize_ct", "br_aeropostale_ct", "br_aldo_ct", "br_allensolly_ct",
                "br_and_ct", "br_anitadongre_ct", "br_arrow_ct", "br_aurelia_ct", "br_bata_ct",
                "br_beinghuman_ct", "br_biba_ct", "br_blackberrys_ct", "br_calvinklein_ct",
                "br_catwalk_ct", "br_celio_ct", "br_central_ct", "r_centro_ct", "br_chumbak_ct",
                "br_classicpolo_ct", "br_coach_ct", "br_ddmas_ct", "br_decathlon_ct", "br_dior_ct",
                "br_emporioarmani_ct", "br_fabindia_ct", "br_fastrack_ct", "br_fbb_ct",
                "br_flyingmachine_ct", "br_forever21_ct", "br_ginijony_ct", "br_hm_ct",
                "br_indianterrain_ct", "br_jackjones_ct", "br_jockey_ct", "br_khadims_ct",
                "br_lee_ct", "br_leecooper_ct", "br_levis_ct", "br_lifestyle_ct", "br_lotto_ct",
                "br_louisphilippe_ct", "br_madame_ct", "br_manyavar_ct", "br_marksspencer_ct",
                "br_maxfashion_ct", "br_meenabazar_ct", "br_michaelkors_ct", "br_miniso_ct",
                "br_montecarlo_ct", "br_more_ct", "br_mufti_ct", "br_nalli_ct", "br_namdharisfresh_ct",
                "br_nautica_ct", "br_neerus_ct", "br_next_ct", "br_numerouno_ct", "br_oxemberg_ct",
                "br_pantaloons_ct", "br_parkavenue_ct", "br_paulshark_ct", "br_pepejeans_ct",
                "br_peterengland_ct", "br_planetfashion_ct", "br_provogue_ct", "br_raymond_ct",
                "br_reliancefootprints_ct", "br_reliancetrendz_ct", "br_sabyasachi_ct", "br_saks_ct",
                "br_shoppersstop_ct", "br_siyaram_ct", "br_splash_ct", "br_spykar_ct",
                "br_stevemadden_ct", "br_swarovski_ct", "br_tommyhilfiger_ct",
                "br_unitedcolorsofbenetton_ct", "br_uspolo_ct", "br_vanheusen_ct", "br_veromoda_ct",
                "br_versace_ct", "r_wforwoman_ct", "br_westside_ct", "br_wills_ct", "br_woodland_ct",
                "br_worldoftitan_ct", "br_wrangler_ct", "br_zara_ct", "br_zodiac_ct", "br_hidesign_ct",
                "br_menmoms_ct", "br_duke_ct", "br_timex_ct", "br_firstcry_ct", "br_sonata_ct",
                "br_sunglasshut_ct", "br_superdry_ct", "br_helios_ct", "br_cantabil_ct", "br_rado_ct",
                "br_rayban_ct", "br_converse_ct", "br_addons_ct", "br_justwatches_ct", "br_mothercare_ct",
                "br_only_ct", "br_kapoor_ct", "br_casio_ct", "br_twillsretail_ct", "br_toonzstore_ct",
                "br_fossil_ct", "br_oakley_ct", "br_ethoswatches_ct", "br_hamleys_ct",
                "br_forevernewapparels_ct"
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
            response.raise_for_status()
            result = response.json()
            
            # Add this check for partial success
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
        # Variables corresponding to each required category
        variables = [
            # Commercial/residential rent data
            "p_retail_rppsfa", "residence_arpsf", "retail_rppsfa", "d_residence_rppsfa", "d_comm_rppsfa",
            # Neighborhood income data
            "w_pop_tt", "w_hh_income_5l_above", "w_hh_income_5l_above_temp", "w_hh_income_5l_above_perc",
            "w_hh_income_10l_above", "w_hh_income_10l_above_temp", "w_hh_income_10l_above_perc",
            "w_hh_income_20l_above", "w_hh_income_20l_above_temp", "w_hh_income_20l_above_perc",
            # Household assets data
            "avail_assets_car_jeep_van",
            # Similar brands data
            "p_retail_gc_np", "p_restaurant_rt_np", "br_brandfactory_ct",
            # Shopping malls data
            "p_dist_sm", "br_v2shoppingmart_ct",
            # Office buildings data
            "o_land_bl", "p_work_of_np_pincode",
            # Fitness centers
            "br_anytimefitness_ct", "br_cult_ct", "br_fitnessfirst_ct", "br_goldsgym_ct", "br_gym_ch_nt",
            # Cinema/theater
            "br_cinemax_ct", "br_cinepolis_ct", "br_inoxleisurelimited_ct", "br_pvrcinemas_ct", "br_goldcinemas_ct",
            # Income tax data
            "secc_p_hh_pay_it_pt_r",
            # Healthcare facilities
            "br_apollohospitals_ct", "br_clovedental_ct", "br_maxhealthcare_ct", "br_drbatras_ct", "br_apollodentalclinic_ct",
            "br_gleneaglesglobalhospitals_ct", "br_medantathemedicity_ct", "br_wockhardthospitals_ct",
            "br_columbiaasia_ct", "br_fortishealthcare_ct",
            # Sports stores
            "br_adidas_ct", "br_asics_ct", "br_fila_ct", "br_puma_ct", "br_reebok_ct", 
            "br_skechers_ct", "br_thenorthface_ct", "br_nike_ct",
            # Jewelry stores
            "br_amrapalijewellers_ct", "br_atlasjewellery_ct", "br_bhimajewellers_ct",
            "br_caratlane_ct", "br_geetanjali_ct", "br_gitanjali_ct", "br_grtjewellers_ct",
            "br_joscogroup_ct", "br_joyalukkas_ct", "br_joyalukkasjewellery_ct",
            "br_kalyanjewellers_ct", "br_malabar_ct", "br_malabargoldanddiamonds_ct",
            "br_orrajewellery_ct", "br_pcchandrajewellers_ct", "br_pcjeweller_ct",
            "br_saravana_ct", "br_senco_ct", "br_shubhjewellers_ct", "br_tanishq_ct",
            "br_tribhovandasbhimjizaveri_ct",
            # High-end restaurants
            "br_restaurant_ch_nt",
            # Fashion and retail stores
            "br_accessorize_ct", "br_aeropostale_ct", "br_aldo_ct", "br_allensolly_ct",
            "br_and_ct", "br_anitadongre_ct", "br_arrow_ct", "br_aurelia_ct", "br_bata_ct",
            "br_beinghuman_ct", "br_biba_ct", "br_blackberrys_ct", "br_calvinklein_ct",
            "br_catwalk_ct", "br_celio_ct", "br_central_ct", "r_centro_ct", "br_chumbak_ct",
            "br_classicpolo_ct", "br_coach_ct", "br_ddmas_ct", "br_decathlon_ct", "br_dior_ct",
            "br_emporioarmani_ct", "br_fabindia_ct", "br_fastrack_ct", "br_fbb_ct",
            "br_flyingmachine_ct", "br_forever21_ct", "br_ginijony_ct", "br_hm_ct",
            "br_indianterrain_ct", "br_jackjones_ct", "br_jockey_ct", "br_khadims_ct",
            "br_lee_ct", "br_leecooper_ct", "br_levis_ct", "br_lifestyle_ct", "br_lotto_ct",
            "br_louisphilippe_ct", "br_madame_ct", "br_manyavar_ct", "br_marksspencer_ct",
            "br_maxfashion_ct", "br_meenabazar_ct", "br_michaelkors_ct", "br_miniso_ct",
            "br_montecarlo_ct", "br_more_ct", "br_mufti_ct", "br_nalli_ct", "br_namdharisfresh_ct",
            "br_nautica_ct", "br_neerus_ct", "br_next_ct", "br_numerouno_ct", "br_oxemberg_ct",
            "br_pantaloons_ct", "br_parkavenue_ct", "br_paulshark_ct", "br_pepejeans_ct",
            "br_peterengland_ct", "br_planetfashion_ct", "br_provogue_ct", "br_raymond_ct",
            "br_reliancefootprints_ct", "br_reliancetrendz_ct", "br_sabyasachi_ct", "br_saks_ct",
            "br_shoppersstop_ct", "br_siyaram_ct", "br_splash_ct", "br_spykar_ct",
            "br_stevemadden_ct", "br_swarovski_ct", "br_tommyhilfiger_ct",
            "br_unitedcolorsofbenetton_ct", "br_uspolo_ct", "br_vanheusen_ct", "br_veromoda_ct",
            "br_versace_ct", "r_wforwoman_ct", "br_westside_ct", "br_wills_ct", "br_woodland_ct",
            "br_worldoftitan_ct", "br_wrangler_ct", "br_zara_ct", "br_zodiac_ct", "br_hidesign_ct",
            "br_menmoms_ct", "br_duke_ct", "br_timex_ct", "br_firstcry_ct", "br_sonata_ct",
            "br_sunglasshut_ct", "br_superdry_ct", "br_helios_ct", "br_cantabil_ct", "br_rado_ct",
            "br_rayban_ct", "br_converse_ct", "br_addons_ct", "br_justwatches_ct", "br_mothercare_ct",
            "br_only_ct", "br_kapoor_ct", "br_casio_ct", "br_twillsretail_ct", "br_toonzstore_ct",
            "br_fossil_ct", "br_oakley_ct", "br_ethoswatches_ct", "br_hamleys_ct",
            "br_forevernewapparels_ct"
        ]
        
        # Ensure we don't exceed the 50 variable limit
        if len(variables) > 50:
            logger.warning("More than 50 variables requested, truncating to 50")
            variables = variables[:50]
        
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
                "commercial_per_sqft": raw_data.get("p_retail_rppsfa", 0),  # Average rent price per sq feet of commercial retail spaces
                "residential_per_sqft": raw_data.get("residence_arpsf", 0),  # Average rent price per square feet of residential space
                "retail_per_sqft": raw_data.get("retail_rppsfa", 0),  # Average rent price per sq feet of commercial retail spaces
                "predicted_residential_rent_per_sqft": raw_data.get("d_residence_rppsfa", 0),  # Predicted average rent per sq feet - Residential Spaces
                "predicted_commercial_rent_per_sqft": raw_data.get("d_comm_rppsfa", 0)  # Predicted average rent price per sq feet - Commercial Retail
            },
            "household_assets": {
                "households_with_vehicles": raw_data.get("avail_assets_car_jeep_van", 0)  # Number of households that have access to Car/Jeep/Van
            },
            "neighborhood_income": {
                "total_population": raw_data.get("w_pop_tt", 0),
                "number_of_households_with_income_above_5_lpa": raw_data.get("w_hh_income_5l_above", 0),
                "number_of_households_that_have_income_above_5_LPA_2024": raw_data.get("w_hh_income_5l_above_temp", 0),
                "percentage_households_that_have_income_above_5_LPA": raw_data.get("w_hh_income_5l_above_perc", 0),

                "number_of_households_with_income_above_10_lpa": raw_data.get("w_hh_income_10l_above", 0),
                "number_of_households_that_have_income_above_10_LPA_2024": raw_data.get("w_hh_income_10l_above_temp", 0),
                "percentage_households_that_have_income_above_10_LPA": raw_data.get("w_hh_income_10l_above_perc", 0),

                "number_of_households_with_income_above_20_lpa": raw_data.get("w_hh_income_20l_above", 0),
                "number_of_households_that_have_income_above_20_LPA_2024": raw_data.get("w_hh_income_20l_above_temp", 0),
                "percentage_households_that_have_income_above_20_LPA": raw_data.get("w_hh_income_20l_above_perc", 0)
            },
            "similar_brands": {
               
                 # Distance to the nearest grocery store in meters
                "restaurant_count": raw_data.get("p_restaurant_rt_np", 0),
                # Fitness centers counts
                "anytime_fitness_count": raw_data.get("br_anytimefitness_ct", 0),
                "cult_count": raw_data.get("br_cult_ct", 0),
                "fitness_first_count": raw_data.get("br_fitnessfirst_ct", 0),
                "golds_gym_count": raw_data.get("br_goldsgym_ct", 0),
                "high_end_gyms_proportion": raw_data.get("br_gym_ch_nt", 0),  # Proportion of high-end gyms in the selected catchment relative to total high-end gyms in the sub-district
                
                # Cinema/theater counts
                "cinemax_count": raw_data.get("br_cinemax_ct", 0),
                "cinepolis_count": raw_data.get("br_cinepolis_ct", 0),
                "inox_leisure_count": raw_data.get("br_inoxleisurelimited_ct", 0),
                "pvr_cinemas_count": raw_data.get("br_pvrcinemas_ct", 0),
                "gold_cinemas_count": raw_data.get("br_goldcinemas_ct", 0),
                
                # Income tax data
                "percentage_rural_households_paying_income_tax": raw_data.get("secc_p_hh_pay_it_pt_r", 0),
                
                # Healthcare facilities counts
                "apollo_hospitals_count": raw_data.get("br_apollohospitals_ct", 0),
                "clove_dental_count": raw_data.get("br_clovedental_ct", 0),
                "max_healthcare_count": raw_data.get("br_maxhealthcare_ct", 0),
                "dr_batras_count": raw_data.get("br_drbatras_ct", 0),
                "apollo_dental_clinic_count": raw_data.get("br_apollodentalclinic_ct", 0),
                "gleneagles_global_hospitals_count": raw_data.get("br_gleneaglesglobalhospitals_ct", 0),
                "medanta_the_medicity_count": raw_data.get("br_medantathemedicity_ct", 0),
                "wockhardt_hospitals_count": raw_data.get("br_wockhardthospitals_ct", 0),
                "columbia_asia_count": raw_data.get("br_columbiaasia_ct", 0),
                "fortis_healthcare_count": raw_data.get("br_fortishealthcare_ct", 0),
                
                #sports stores counts
                # Sports stores counts
                "adidas_store_count": raw_data.get("br_adidas_ct", 0),
                "asics_store_count": raw_data.get("br_asics_ct", 0), 
                "fila_store_count": raw_data.get("br_fila_ct", 0),
                "puma_store_count": raw_data.get("br_puma_ct", 0),
                "reebok_store_count": raw_data.get("br_reebok_ct", 0),
                "skechers_store_count": raw_data.get("br_skechers_ct", 0),
                "north_face_store_count": raw_data.get("br_thenorthface_ct", 0),
                "nike_store_count": raw_data.get("br_nike_ct", 0),

                # Jewelry stores counts
                "amrapali_jewellers_count": raw_data.get("br_amrapalijewellers_ct", 0),
                "atlas_jewellery_count": raw_data.get("br_atlasjewellery_ct", 0),
                "bhima_jewellers_count": raw_data.get("br_bhimajewellers_ct", 0),
                "caratlane_count": raw_data.get("br_caratlane_ct", 0),
                "geetanjali_count": raw_data.get("br_geetanjali_ct", 0),
                "gitanjali_count": raw_data.get("br_gitanjali_ct", 0),
                "grt_jewellers_count": raw_data.get("br_grtjewellers_ct", 0),
                "josco_group_count": raw_data.get("br_joscogroup_ct", 0),
                "joyalukkas_count": raw_data.get("br_joyalukkas_ct", 0),
                "joyalukkas_jewellery_count": raw_data.get("br_joyalukkasjewellery_ct", 0),
                "kalyan_jewellers_count": raw_data.get("br_kalyanjewellers_ct", 0),
                "malabar_count": raw_data.get("br_malabar_ct", 0),
                "malabar_gold_and_diamonds_count": raw_data.get("br_malabargoldanddiamonds_ct", 0),
                "orra_jewellery_count": raw_data.get("br_orrajewellery_ct", 0),
                "pc_chandra_jewellers_count": raw_data.get("br_pcchandrajewellers_ct", 0),
                "pc_jeweller_count": raw_data.get("br_pcjeweller_ct", 0),
                "saravana_count": raw_data.get("br_saravana_ct", 0),
                "senco_count": raw_data.get("br_senco_ct", 0),
                "shubh_jewellers_count": raw_data.get("br_shubhjewellers_ct", 0),
                "tanishq_count": raw_data.get("br_tanishq_ct", 0),
                "tribhovandas_bhimji_zaveri_count": raw_data.get("br_tribhovandasbhimjizaveri_ct", 0),

                # High-end restaurants data
                "high_end_restaurants_proportion": raw_data.get("br_restaurant_ch_nt", 0),  # Proportion of high-end restaurants in the selected catchment relative to total high-end restaurants in the sub-district
                # Fashion and retail stores counts
                "accessorize_store_count": raw_data.get("br_accessorize_ct", 0),
                "aeropostale_store_count": raw_data.get("br_aeropostale_ct", 0),
                "aldo_store_count": raw_data.get("br_aldo_ct", 0),
                "allen_solly_store_count": raw_data.get("br_allensolly_ct", 0),
                "and_store_count": raw_data.get("br_and_ct", 0),
                "anita_dongre_store_count": raw_data.get("br_anitadongre_ct", 0),
                "arrow_store_count": raw_data.get("br_arrow_ct", 0),
                "aurelia_store_count": raw_data.get("br_aurelia_ct", 0),
                "bata_store_count": raw_data.get("br_bata_ct", 0),
                "being_human_store_count": raw_data.get("br_beinghuman_ct", 0),
                "biba_store_count": raw_data.get("br_biba_ct", 0),
                "blackberrys_store_count": raw_data.get("br_blackberrys_ct", 0),
                "brand_factory_store_count": raw_data.get("br_brandfactory_ct", 0),
                "calvin_klein_store_count": raw_data.get("br_calvinklein_ct", 0),
                "catwalk_store_count": raw_data.get("br_catwalk_ct", 0),
                "celio_store_count": raw_data.get("br_celio_ct", 0),
                "central_store_count": raw_data.get("br_central_ct", 0),
                "centro_store_count": raw_data.get("r_centro_ct", 0),
                "chumbak_store_count": raw_data.get("br_chumbak_ct", 0),
                
                "coach_store_count": raw_data.get("br_coach_ct", 0),
                "ddmas_store_count": raw_data.get("br_ddmas_ct", 0),
                "decathlon_store_count": raw_data.get("br_decathlon_ct", 0),
                "dior_store_count": raw_data.get("br_dior_ct", 0),
                "emporio_armani_store_count": raw_data.get("br_emporioarmani_ct", 0),
                "fabindia_store_count": raw_data.get("br_fabindia_ct", 0),
                "fastrack_store_count": raw_data.get("br_fastrack_ct", 0),
                "fbb_store_count": raw_data.get("br_fbb_ct", 0),
                "flying_machine_store_count": raw_data.get("br_flyingmachine_ct", 0),
                "forever21_store_count": raw_data.get("br_forever21_ct", 0),
                "gini_jony_store_count": raw_data.get("br_ginijony_ct", 0),
                "hm_store_count": raw_data.get("br_hm_ct", 0),
                "indian_terrain_store_count": raw_data.get("br_indianterrain_ct", 0),
                "jack_jones_store_count": raw_data.get("br_jackjones_ct", 0),
                "jockey_store_count": raw_data.get("br_jockey_ct", 0),
                "khadims_store_count": raw_data.get("br_khadims_ct", 0),
                
                "levis_store_count": raw_data.get("br_levis_ct", 0),
                "lifestyle_store_count": raw_data.get("br_lifestyle_ct", 0),
                "lotto_store_count": raw_data.get("br_lotto_ct", 0),
                "louis_philippe_store_count": raw_data.get("br_louisphilippe_ct", 0),
                "madame_store_count": raw_data.get("br_madame_ct", 0),
                "manyavar_store_count": raw_data.get("br_manyavar_ct", 0),
                "marks_spencer_store_count": raw_data.get("br_marksspencer_ct", 0),
                
                "meena_bazar_store_count": raw_data.get("br_meenabazar_ct", 0),
                "michael_kors_store_count": raw_data.get("br_michaelkors_ct", 0),
                "miniso_store_count": raw_data.get("br_miniso_ct", 0),
                "monte_carlo_store_count": raw_data.get("br_montecarlo_ct", 0),
                "more_store_count": raw_data.get("br_more_ct", 0),
                "mufti_store_count": raw_data.get("br_mufti_ct", 0),
                "nalli_store_count": raw_data.get("br_nalli_ct", 0),
                "namdharis_fresh_store_count": raw_data.get("br_namdharisfresh_ct", 0),
                "nautica_store_count": raw_data.get("br_nautica_ct", 0),
                "neerus_store_count": raw_data.get("br_neerus_ct", 0),
                "next_store_count": raw_data.get("br_next_ct", 0),
                "numero_uno_store_count": raw_data.get("br_numerouno_ct", 0),
                "oxemberg_store_count": raw_data.get("br_oxemberg_ct", 0),
                "pantaloons_store_count": raw_data.get("br_pantaloons_ct", 0),
                "park_avenue_store_count": raw_data.get("br_parkavenue_ct", 0),
                "paul_shark_store_count": raw_data.get("br_paulshark_ct", 0),
                "pepe_jeans_store_count": raw_data.get("br_pepejeans_ct", 0),
                "peter_england_store_count": raw_data.get("br_peterengland_ct", 0),
                "planet_fashion_store_count": raw_data.get("br_planetfashion_ct", 0),
                "provogue_store_count": raw_data.get("br_provogue_ct", 0),
                "raymond_store_count": raw_data.get("br_raymond_ct", 0),
                "reliance_footprints_store_count": raw_data.get("br_reliancefootprints_ct", 0),
                "reliance_trendz_store_count": raw_data.get("br_reliancetrendz_ct", 0),
                "sabyasachi_store_count": raw_data.get("br_sabyasachi_ct", 0),
                "saks_store_count": raw_data.get("br_saks_ct", 0),
                "shoppers_stop_store_count": raw_data.get("br_shoppersstop_ct", 0),
                "siyaram_store_count": raw_data.get("br_siyaram_ct", 0),
                "splash_store_count": raw_data.get("br_splash_ct", 0),
                "spykar_store_count": raw_data.get("br_spykar_ct", 0),
                "steve_madden_store_count": raw_data.get("br_stevemadden_ct", 0),
                "swarovski_store_count": raw_data.get("br_swarovski_ct", 0),
                "tommy_hilfiger_store_count": raw_data.get("br_tommyhilfiger_ct", 0),
                "united_colors_of_benetton_store_count": raw_data.get("br_unitedcolorsofbenetton_ct", 0),
                "us_polo_store_count": raw_data.get("br_uspolo_ct", 0),
                "van_heusen_store_count": raw_data.get("br_vanheusen_ct", 0),
                "vero_moda_store_count": raw_data.get("br_veromoda_ct", 0),
                "versace_store_count": raw_data.get("br_versace_ct", 0),
                "w_for_woman_store_count": raw_data.get("r_wforwoman_ct", 0),
                "westside_store_count": raw_data.get("br_westside_ct", 0),
                "wills_store_count": raw_data.get("br_wills_ct", 0),
                "woodland_store_count": raw_data.get("br_woodland_ct", 0),
                "world_of_titan_store_count": raw_data.get("br_worldoftitan_ct", 0),
                "wrangler_store_count": raw_data.get("br_wrangler_ct", 0),
                "zara_store_count": raw_data.get("br_zara_ct", 0),
                "zodiac_store_count": raw_data.get("br_zodiac_ct", 0),
                "hidesign_store_count": raw_data.get("br_hidesign_ct", 0),
                "men_moms_store_count": raw_data.get("br_menmoms_ct", 0),
                "duke_store_count": raw_data.get("br_duke_ct", 0),
                "timex_store_count": raw_data.get("br_timex_ct", 0),
                "firstcry_store_count": raw_data.get("br_firstcry_ct", 0),
                "sonata_store_count": raw_data.get("br_sonata_ct", 0),
                "sunglass_hut_store_count": raw_data.get("br_sunglasshut_ct", 0),
                "superdry_store_count": raw_data.get("br_superdry_ct", 0),
                "helios_store_count": raw_data.get("br_helios_ct", 0),
                "cantabil_store_count": raw_data.get("br_cantabil_ct", 0),
                "rado_store_count": raw_data.get("br_rado_ct", 0),
                "rayban_store_count": raw_data.get("br_rayban_ct", 0),
                "converse_store_count": raw_data.get("br_converse_ct", 0),
                "addons_store_count": raw_data.get("br_addons_ct", 0),
                "justwatches_store_count": raw_data.get("br_justwatches_ct", 0),
                "mothercare_store_count": raw_data.get("br_mothercare_ct", 0),
                "only_store_count": raw_data.get("br_only_ct", 0),
                "kapoor_store_count": raw_data.get("br_kapoor_ct", 0),
                "casio_store_count": raw_data.get("br_casio_ct", 0),
                "twills_retail_store_count": raw_data.get("br_twillsretail_ct", 0),
                "toonz_store_count": raw_data.get("br_toonzstore_ct", 0),
                "fossil_store_count": raw_data.get("br_fossil_ct", 0),
                "oakley_store_count": raw_data.get("br_oakley_ct", 0),
                "ethoswatches_store_count": raw_data.get("br_ethoswatches_ct", 0),
                "hamleys_store_count": raw_data.get("br_hamleys_ct", 0),
                "forever_new_apparels_store_count": raw_data.get("br_forevernewapparels_ct", 0)
                
            },
            "shopping_malls": {
                "nearest_shopping_mall": raw_data.get("p_dist_sm", 0),
            },
            "office_buildings": {
                "building_land": raw_data.get("o_land_bl", 0),
                "office_proportion_in_subdistrict": raw_data.get("p_work_of_np_pincode", 0)  # Proportion of offices in the selected catchment relative to total offices in the sub-district
            },
            "raw_data": raw_data  # Include raw data for reference if needed
        }
        
        return analysis