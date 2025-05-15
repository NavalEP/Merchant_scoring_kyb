import logging

class DoctorScoringEngine:
    def __init__(self):
        # Initialize scoring rules
        self.logger = logging.getLogger(__name__)
        self.location_scores = {
            "Prime": 10,
            "Medium": 5,
            "Poor": 0
        }
        
        self.experience_scores = {
            "under 5 years": 3,
            "5-10 years": 4,
            "10+ years": 5,
            "Not the owner": 0
        }
        
        self.rating_scores = {
            "4.9 or more": 1,
            "4.4-4.8": 5,
            "4.1-4.3": 3,
            "less than 4.1": 1
        }
        
        # NEW: Rating count categories and scores
        self.rating_count_categories = {
            "1000+": 5,
            "500-999": 4, 
            "200-499": 3,
            "50-199": 2,
            "Less than 50": 1
        }
        
        self.qualification_scores = {
            "DM": 10,
            "MCh": 10,
            "DNB (Super Specialties)": 9.5,
            "Post-Doctoral Fellowships": 9,
            "PhD in Medical Sciences": 9,
            "MD": 8.5,
            "MS": 8.5,
            "MDS": 8,
            "DNB (Broad Specialties)": 8,
            "Medical PG Diplomas": 6.5,
            "MBBS": 6,
            "MBBS (Foreign)": 5.5,
            "BDS": 5,
            "BAMS": 5,
            "BHMS": 5,
            "BUMS": 4.5,
            "Other": 2
        }
        
        self.specialization_scores = {
            "Aesthetics": 1,
            "Ayush": 2,
            "Cardiology": 2,
            "Cosmetology": 2,
            "Dentistry": 3,
            "Dermatology": 2,
            "Dermatologist": 2,
            "ENT": 4,
            "General Surgery": 3,
            "Gynecology and obstetrics": 4,
            "Hair": 1,
            "Home Care Facility": 3,
            "IVF": 5,
            "Multispeciality Hospital": 3,
            "Neurology": 4,
            "Ophthalmology": 5,
            "Orthopedics": 5,
            "Pain Management": 3,
            "Physiotherapy": 2,
            "Plastic surgery": 4,
            "Prosthetics": 5,
            "Speech and Hearing": 4,
            "Super Speciality Hospital": 5,
            "Urology": 4,
            "Medical Device": 4,
            "Pediatrics": 3,
            "Internal Medicine": 3,
            "Psychiatry": 3,
            "Radiology": 3,
            "Anesthesiology": 3,
            "Oncology": 4,
            "Endocrinology": 3,
            "Gastroenterology": 3,
            "Nephrology": 3,
            "Pulmonology": 3,
            "Rheumatology": 3,
            "Hematology": 3
        }
        
        # Initialize GeoIQ service
        self.geoiq_service = None
        try:
            from .GeoIQ import GeoIQService
            self.geoiq_service = GeoIQService()
            self.logger.info("GeoIQ service initialized successfully")
        except Exception as e:
            self.logger.error(f"GeoIQ service initialization failed: {str(e)}")
            # Service will be None, and location scoring will use default values
    
    def normalize_rating(self, rating, source):
        """Normalize ratings from different sources to a 0-5 scale"""
        try:
            if not rating:
                return 0
            
            # Convert to string to handle both string and numeric inputs
            rating_str = str(rating).strip()
            
            if source == "practo":
                # Convert percentage recommendation to 0-5 scale
                if '%' in rating_str:
                    return float(rating_str.strip('%')) / 20
                else:
                    return float(rating_str)
            elif source == "justdial":
                # Justdial ratings are already on a 0-5 scale
                return float(rating_str)
            elif source == "bajaj":
                # Bajaj may provide ratings as percentages
                if '%' in rating_str:
                    return float(rating_str.strip('%')) / 20
                else:
                    return float(rating_str)
            elif source == "googlemap":
                # Google Maps ratings are on a 0-5 scale
                return float(rating_str)
            else:
                # Default case
                # If it has a % sign, assume it's a percentage
                if '%' in rating_str:
                    return float(rating_str.strip('%')) / 20
                else:
                    return float(rating_str)
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error normalizing rating '{rating}' from {source}: {str(e)}")
            return 0
    
    def extract_qualification_level(self, qualification_text):
        """Extract highest qualification level from qualification text"""
        if not qualification_text:
            return "Other"
            
        qualification_text = qualification_text.upper()
        
        # Check for super-specialties first
        if "DM" in qualification_text and not "DMRE" in qualification_text:
            return "DM"
        elif "MCH" in qualification_text:
            return "MCh"
        elif "DNB" in qualification_text and any(super_spec in qualification_text for super_spec in ["CARDIO", "NEURO", "GASTRO", "ONCO", "ENDOCRIN"]):
            return "DNB (Super Specialties)"
        elif any(fellowship in qualification_text for fellowship in ["FELLOWSHIP", "POST-DOCTORAL"]):
            return "Post-Doctoral Fellowships"
        elif "PHD" in qualification_text:
            return "PhD in Medical Sciences"
        elif "MD" in qualification_text and not "MBBS" in qualification_text:
            return "MD"
        elif "MS" in qualification_text and not ("MBBS" in qualification_text or "MDS" in qualification_text):
            return "MS"
        elif "MDS" in qualification_text:
            return "MDS"
        elif "DNB" in qualification_text:
            return "DNB (Broad Specialties)"
        elif any(diploma in qualification_text for diploma in ["DGO", "DCH", "DMRE", "DIPLOMA"]):
            return "Medical PG Diplomas"
        elif "MBBS" in qualification_text and any(foreign in qualification_text for foreign in ["FOREIGN", "ABROAD", "INTERNATIONAL"]):
            return "MBBS (Foreign)"
        elif "MBBS" in qualification_text:
            return "MBBS"
        elif "BDS" in qualification_text:
            return "BDS"
        elif "BAMS" in qualification_text:
            return "BAMS"
        elif "BHMS" in qualification_text:
            return "BHMS"
        elif "BUMS" in qualification_text:
            return "BUMS"
        else:
            return "Other"
    
    def extract_experience_years(self, experience_text):
        """Extract years of experience from text"""
        import re
        
        if not experience_text:
            return 0
            
        # Look for patterns like "10 years", "10+ years", etc.
        match = re.search(r'(\d+)(?:\+)?\s*(?:years|yrs)', experience_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
            
        # Look for numeric values
        match = re.search(r'(\d+)', experience_text)
        if match:
            return int(match.group(1))
            
        return 0
    
    def get_experience_category(self, years):
        """Categorize experience based on years"""
        if years >= 10:
            return "10+ years"
        elif years >= 5:
            return "5-10 years"
        else:
            return "under 5 years"
    
    def get_rating_category(self, rating):
        """Categorize rating based on normalized 0-5 scale"""
        if rating >= 4.9:
            return "4.9 or more"
        elif rating >= 4.4:
            return "4.4-4.8"
        elif rating >= 4.1:
            return "4.1-4.3"
        else:
            return "less than 4.1"
    
    def get_rating_count_category(self, count):
        """Categorize rating count"""
        if count >= 1000:
            return "1000+"
        elif count >= 500:
            return "500-999"
        elif count >= 200:
            return "200-499"
        elif count >= 50:
            return "50-199"
        else:
            return "Less than 50"
    
    def calculate_weighted_rating(self, rating, rating_count):
        """Calculate a weighted rating score based on both rating value and count"""
        if not rating or not rating_count:
            return 0
            
        try:
            # Ensure we have numeric values
            try:
                rating = float(rating)
                
                # Clean rating count if it's a string with non-numeric characters
                if isinstance(rating_count, str) and not rating_count.isdigit():
                    rating_count = self.clean_rating_count(rating_count)
                else:
                    rating_count = int(float(rating_count))  # Convert to float first in case it's a decimal string
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid rating or count values: {rating}, {rating_count}. Error: {str(e)}")
                return 0
            
            # Validate ranges
            if rating < 0 or rating > 5:
                self.logger.warning(f"Rating {rating} out of expected range (0-5)")
                rating = max(0, min(rating, 5))  # Clamp to 0-5
                
            if rating_count < 0:
                self.logger.warning(f"Negative rating count: {rating_count}")
                rating_count = 0
            
            # Get base rating category score
            category = self.get_rating_category(rating)
            base_score = self.rating_scores.get(category, 0)
            
            # Get rating count category score
            count_category = self.get_rating_count_category(rating_count)
            count_score = self.rating_count_categories.get(count_category, 0)
            
            # Log for debugging
            self.logger.debug(f"Weighted rating calculation: rating={rating} (category={category}, score={base_score}), " 
                         f"count={rating_count} (category={count_category}, score={count_score})")
            
            # Combined weighted score:
            # - High rating with many reviews gets the highest score
            # - Low rating with few reviews gets the lowest score
            # - High rating with few reviews or low rating with many reviews gets a middle score
            weighted_score = (base_score * 0.6) + (count_score * 0.4)
            
            # Bonus for extremely high review counts with good ratings
            if rating_count > 500 and rating >= 4.0:
                bonus = min((rating_count - 500) / 1000, 1.0)
                self.logger.debug(f"Applied bonus of {bonus} for high review count")
                weighted_score += bonus
                
            final_score = min(weighted_score, 5)  # Cap at 5
            self.logger.debug(f"Final weighted rating score: {final_score}")
            return final_score
            
        except Exception as e:
            self.logger.error(f"Error calculating weighted rating: {str(e)}")
            return 0  # Return 0 instead of default middle value
    
    def evaluate_location(self, address):
        """Evaluate location quality using GeoIQ"""
        if not self.geoiq_service or not address:
            self.logger.warning("GeoIQ service not available or address is empty")
            return "Poor"
            
        try:
            # Get location data using analyze_location instead of get_location_data_by_address
            # This provides us with the pre-calculated location_score
            location_analysis = self.geoiq_service.analyze_location(address=address)
            
            # Use the pre-calculated location category if available
            if location_analysis and "location_score" in location_analysis:
                location_category = location_analysis["location_score"]["category"]
                location_points = location_analysis["location_score"]["points"]
                
                self.logger.info(f"Using pre-calculated location score for {address}: {location_category} ({location_points}/30)")
                return location_category
            
            # Fall back to previous calculation method if location_score is not available
            location_data = location_analysis.get("raw_data", {})
            
            # Comprehensive location analysis using multiple factors
            # 1. Income indicators
            avg_income_5l = location_data.get('w_hh_income_5l_above_perc', 0)
            avg_income_10l = location_data.get('w_hh_income_10l_above_perc', 0)
            avg_income_20l = location_data.get('w_hh_income_20l_above_perc', 0)
            income_tax_payers = location_data.get('secc_p_hh_pay_it_pt_r', 0)
            
            # 2. Commercial indicators
            retail_density = location_data.get('p_retail_gc_np', 0)
            restaurant_density = location_data.get('p_restaurant_rt_np', 0)
            retail_rent = location_data.get('p_retail_rppsfa', 0)
            
            # 3. Lifestyle indicators
            high_end_restaurants = location_data.get('br_restaurant_ch_nt', 0)
            fitness_centers = (
                location_data.get('br_anytimefitness_ct', 0) + 
                location_data.get('br_cult_ct', 0) + 
                location_data.get('br_goldsgym_ct', 0)
            )
            entertainment = (
                location_data.get('br_pvrcinemas_ct', 0) + 
                location_data.get('br_inoxleisurelimited_ct', 0)
            )
            
            # 4. Premium retail presence
            premium_retail = (
                location_data.get('br_lifestyle_ct', 0) + 
                location_data.get('br_shoppersstop_ct', 0) + 
                location_data.get('br_zara_ct', 0) + 
                location_data.get('br_miniso_ct', 0) + 
                location_data.get('br_tanishq_ct', 0) + 
                location_data.get('br_calvinklein_ct', 0) + 
                location_data.get('br_tommyhilfiger_ct', 0)
            )
            
            # 5. Healthcare indicators
            healthcare_facilities = (
                location_data.get('br_apollohospitals_ct', 0) + 
                location_data.get('br_maxhealthcare_ct', 0) + 
                location_data.get('br_fortishealthcare_ct', 0) + 
                location_data.get('br_medantathemedicity_ct', 0)
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
            
            self.logger.debug(f"Location analysis for {address}: income indicators={avg_income_10l}/{avg_income_20l}, " 
                         f"commercial={retail_density}/{retail_rent}, premium retail={premium_retail}, "
                         f"location_points={location_points}")
            
            # Determine location category based on points
            if location_points >= 20:
                return "Prime"
            elif location_points >= 12:
                return "Medium"
            else:
                return "Poor"
        except Exception as e:
            self.logger.error(f"GeoIQ evaluation failed: {str(e)}")
            return "Poor"
    
    def verify_medical_license(self, registration_no, doctor_data=None):
        """Verify if the doctor has a valid medical license"""
        if not registration_no:
            self.logger.debug("No registration number provided for verification")
            return False
            
        self.logger.debug(f"Verifying medical license: {registration_no}")
            
        # Check if exists in NMC database
        from cpapp.models.nmc import NMCDoctor
        from cpapp.models.nmc_dental import NMCDentalDoctor
        
        try:
            # Check in regular NMC database
            nmc_match = NMCDoctor.objects.filter(registrationNo=registration_no).exists()
            if nmc_match:
                self.logger.debug(f"License {registration_no} verified in NMC database")
                return True
            
            # Check in NMC dental database
            nmc_dental_match = NMCDentalDoctor.objects.filter(registration_number=registration_no).exists()
            if nmc_dental_match:
                self.logger.debug(f"License {registration_no} verified in NMC dental database")
                return True
                
            # If we have full doctor data, we can do more checks
            if doctor_data:
                # Check if registration number matches what's in doctor_data
                if hasattr(doctor_data, 'registration') and doctor_data.registration:
                    justdial_reg = doctor_data.registration
                    if justdial_reg and justdial_reg == registration_no:
                        self.logger.debug(f"License {registration_no} verified via doctor data match")
                        return True
                
                # For NMC data, check against registrationNo
                elif hasattr(doctor_data, 'registrationNo') and doctor_data.registrationNo:
                    if doctor_data.registrationNo == registration_no:
                        self.logger.debug(f"License {registration_no} verified via NMC registrationNo match")
                        return True
                
            self.logger.debug(f"License {registration_no} could not be verified in any database")
            return False
            
        except Exception as e:
            self.logger.error(f"License verification error for {registration_no}: {str(e)}")
            return False
    
    def calculate_qualification_score(self, qualification_text):
        """Calculate score based on qualification"""
        qualification_level = self.extract_qualification_level(qualification_text)
        return self.qualification_scores.get(qualification_level)
    
    def calculate_experience_score(self, experience_text):
        """Calculate score based on experience"""
        years = self.extract_experience_years(experience_text)
        category = self.get_experience_category(years)
        return self.experience_scores.get(category)
    
    def calculate_rating_score(self, rating, source, rating_count=None):
        """Calculate score based on rating and rating count"""
        normalized_rating = self.normalize_rating(rating, source)
        
        if rating_count:
            # Use weighted calculation that considers count
            return self.calculate_weighted_rating(normalized_rating, rating_count)
        else:
            # Fall back to original method if count not available
            category = self.get_rating_category(normalized_rating)
            return self.rating_scores.get(category)
    
    def calculate_location_score(self, address):
        """Calculate score based on location"""
        location_category = self.evaluate_location(address)
        return self.location_scores.get(location_category)
    
    def calculate_specialization_score(self, specialization):
        """Calculate score based on specialization"""
        if not specialization:
            self.logger.debug("No specialization provided")
            return 0
            
        # Convert to lowercase for case-insensitive matching
        specialization_lower = specialization.lower()
        
        # Try exact match first (case-insensitive)
        for category, score in self.specialization_scores.items():
            if category.lower() == specialization_lower:
                self.logger.debug(f"Exact match for specialization '{specialization}': {score}")
                return score
        
        # Try to find partial matches if no exact match
        best_match = None
        best_score = 0
        
        for category, score in self.specialization_scores.items():
            category_lower = category.lower()
            # Check if category is in specialization or vice versa
            if category_lower in specialization_lower or specialization_lower in category_lower:
                if score > best_score:
                    best_match = category
                    best_score = score
        
        if best_match:
            self.logger.debug(f"Partial match for specialization '{specialization}': {best_match} with score {best_score}")
            return best_score
            
        # Check for common keywords that might indicate certain specialties
        keywords = {
            "surgery": 3,
            "hospital": 3,
            "clinic": 2,
            "dental": 3,
            "eye": 5,
            "ortho": 5,
            "cardio": 2,
            "neuro": 4,
            "gynec": 4,
            "skin": 2,
            "derma": 2,  # Added for dermatology
            "hair": 1,
            "physio": 2,
            "ayurvedic": 2,
            "homeopathic": 2,
            "pediatric": 3,
            "child": 3,
            "cancer": 4,
            "onco": 4,
            "radio": 3,
            "gastro": 3,
            "kidney": 3,
            "nephro": 3,
            "lung": 3,
            "pulmo": 3,
            "endo": 3,
            "diabetes": 3,
            "plastic": 4,
            "dentist": 3,
            "dental": 3
        }
        
        for keyword, score in keywords.items():
            if keyword in specialization_lower:
                self.logger.debug(f"Keyword match for specialization '{specialization}': {keyword} with score {score}")
                return score
        
        # Return 0 if no match found
        self.logger.debug(f"No match found for specialization '{specialization}'")
        return 0
    
    def clean_rating_count(self, raw_rating_count):
        """Clean up rating count - handle formats like '1,108 Rating'"""
        import re
        
        if not raw_rating_count:
            return 0
            
        # Convert to string if it's not already
        if not isinstance(raw_rating_count, str):
            raw_rating_count = str(raw_rating_count)
        
        # Remove commas and text, leaving just the numeric part
        cleaned_count = re.sub(r'[^\d]', '', raw_rating_count)
        
        # Convert to integer
        try:
            return int(cleaned_count) if cleaned_count else 0
        except (ValueError, TypeError):
            self.logger.warning(f"Could not convert rating count: {raw_rating_count}")
            return 0
    
    def score_doctor(self, doctor_data, source):
        """Score a doctor based on various factors"""
        # Initialize scores dictionary
        scores = {}
        
        # Extract basic information
        doctor_name = ""
        specialization = ""
        qualification = ""
        experience = ""
        rating = 0
        rating_count = 0
        address = ""
        location = ""
        registration_no = None
        
        try:
            if source == "justdial":
                doctor_name = getattr(doctor_data, 'doctor_name', "")
                specialization = getattr(doctor_data, 'category', "")
                qualification = getattr(doctor_data, 'qualification', "")
                experience = getattr(doctor_data, 'experience', "")
                rating = self.normalize_rating(getattr(doctor_data, 'rating', 0), source)
                
                # Clean up rating count - handle formats like "1,108 Rating"
                raw_rating_count = getattr(doctor_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                
                address = getattr(doctor_data, 'clinic_address', "")
                location = getattr(doctor_data, 'location', "")
                registration_no = getattr(doctor_data, 'registration', None)
                
            elif source == "practo":
                doctor_name = getattr(doctor_data, 'name', "")
                specialization = getattr(doctor_data, 'speciality', "")
                qualification = getattr(doctor_data, 'detailed_qualifications', "")
                experience = getattr(doctor_data, 'experience', "")
                rating = self.normalize_rating(getattr(doctor_data, 'recommendation_percent', 0), source)
                # Practo doesn't always provide rating count
                raw_rating_count = getattr(doctor_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(doctor_data, 'doctor_address', "")
                location = getattr(doctor_data, 'location', "")
                registration_no = getattr(doctor_data, 'registration_no', None)
                
            elif source == "new_practo":
                doctor_name = getattr(doctor_data, 'doctor_name', "")
                specialization = getattr(doctor_data, 'specialization', "")
                qualification = getattr(doctor_data, 'qualification', "")
                experience = getattr(doctor_data, 'experience', "")
                rating = self.normalize_rating(getattr(doctor_data, 'rating', 0), "justdial")
                raw_rating_count = getattr(doctor_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                
                # Extract address from clinic_data
                address = ""
                if hasattr(doctor_data, 'clinic_data'):
                    clinic_data = doctor_data.clinic_data
                    if isinstance(clinic_data, dict):
                        address = clinic_data.get('address', '')
                    elif isinstance(clinic_data, str):
                        # Try to parse JSON if it's a string
                        try:
                            import json
                            clinic_json = json.loads(clinic_data)
                            address = clinic_json.get('address', '')
                        except:
                            pass
                
                location = getattr(doctor_data, 'location', "")
                registration_no = getattr(doctor_data, 'registration', None)
                
            elif source == "nmc":
                doctor_name = f"{getattr(doctor_data, 'firstName', '')} {getattr(doctor_data, 'lastName', '')}".strip()
                specialization = ""  # NMC data doesn't have specialization
                qualification = getattr(doctor_data, 'doctorDegree', "")
                experience = ""  # NMC data doesn't have experience
                rating = 0  # NMC data doesn't have ratings
                rating_count = 0
                address = getattr(doctor_data, 'address', "")
                location = address
                registration_no = getattr(doctor_data, 'registrationNo', None)
                
            elif source == "bajaj":
                doctor_name = getattr(doctor_data, 'name', "")
                specialization = getattr(doctor_data, 'specialities', "")
                qualification = getattr(doctor_data, 'qualifications', "")
                experience = getattr(doctor_data, 'experience', "")
                rating = self.normalize_rating(getattr(doctor_data, 'rating_percent', 0), "practo")
                raw_rating_count = getattr(doctor_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(doctor_data, 'clinic_address', "")
                location = getattr(doctor_data, 'clinic_location', "")
                registration_no = getattr(doctor_data, 'hpr_id', None)
                
            elif source == "savein":
                doctor_name = getattr(doctor_data, 'doctor_name', "")
                if not doctor_name:
                    doctor_name = getattr(doctor_data, 'name', "")
                specialization = getattr(doctor_data, 'specialization', "")
                qualification = getattr(doctor_data, 'qualification', "")
                experience = getattr(doctor_data, 'experience', "")
                rating = self.normalize_rating(getattr(doctor_data, 'rating', 0), "justdial")
                raw_rating_count = getattr(doctor_data, 'reviews_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(doctor_data, 'address', "")
                location = getattr(doctor_data, 'location', "")
                registration_no = None
            
            # Log the extracted data
            self.logger.debug(f"Extracted data for {doctor_name}: specialization={specialization}, qualification={qualification}, "
                       f"experience={experience}, rating={rating}, rating_count={rating_count}, registration={registration_no}")
                       
            # Calculate individual scores
            scores['qualification_score'] = self.calculate_qualification_score(qualification)
            scores['experience_score'] = self.calculate_experience_score(experience)
            scores['rating_score'] = self.calculate_rating_score(rating, source, rating_count)
            
            # Calculate weighted rating score
            scores['weighted_rating_score'] = self.calculate_weighted_rating(rating, rating_count) if rating_count else scores['rating_score']
            
            scores['location_score'] = self.calculate_location_score(address)
            scores['specialization_score'] = self.calculate_specialization_score(specialization)
            
            # Calculate license verification score
            scores['license_verified'] = self.verify_medical_license(registration_no, doctor_data)
            scores['license_score'] = 10 if scores['license_verified'] else 0
            
            # Add rating count as additional info
            scores['rating_count'] = rating_count
            
        except Exception as e:
            # Log the error and continue with default scores
            self.logger.error(f"Error processing doctor data: {str(e)}")
            # Set default scores for any missing values
            scores.setdefault('qualification_score', 0)
            scores.setdefault('experience_score', 0)
            scores.setdefault('rating_score', 0)
            scores.setdefault('weighted_rating_score', 0)
            scores.setdefault('location_score', 0)
            scores.setdefault('specialization_score', 0)
            scores.setdefault('license_verified', False)
            scores.setdefault('license_score', 0)
            scores.setdefault('rating_count', 0)
        
        # Normalize all scores to percentage (0-100)
        max_qualification_score = 10
        max_experience_score = 5
        max_rating_score = 5 
        max_weighted_rating_score = 5
        max_location_score = 10
        max_specialization_score = 5
        max_license_score = 10
        
        normalized_scores = {
            'qualification_score': (scores['qualification_score'] / max_qualification_score) * 100,
            'experience_score': (scores['experience_score'] / max_experience_score) * 100,
            'rating_score': (scores['rating_score'] / max_rating_score) * 100,
            'weighted_rating_score': (scores['weighted_rating_score'] / max_weighted_rating_score) * 100,
            'location_score': (scores['location_score'] / max_location_score) * 100,
            'specialization_score': (scores['specialization_score'] / max_specialization_score) * 100,
            'license_score': (scores['license_score'] / max_license_score) * 100
        }
        
        # Weighted total score (out of 100)
        weights = {
            'qualification': 0.15,
            'experience': 0.15,
            'rating': 0.05,  # Reduced to add weighted rating
            'weighted_rating': 0.05,  # Added new weight for weighted rating
            'location': 0.10,
            'specialization': 0.10,
            'license': 0.40  # High weight for license verification
        }
        
        # Calculate contribution of each component to total score
        score_components = {
            'qualification': normalized_scores['qualification_score'] * weights['qualification'],
            'experience': normalized_scores['experience_score'] * weights['experience'],
            'rating': normalized_scores['rating_score'] * weights['rating'],
            'weighted_rating': normalized_scores['weighted_rating_score'] * weights['weighted_rating'],
            'location': normalized_scores['location_score'] * weights['location'],
            'specialization': normalized_scores['specialization_score'] * weights['specialization'],
            'license': normalized_scores['license_score'] * weights['license']
        }
        
        # Sum up the weighted scores
        total_score = sum(score_components.values())
        
        # Log the score breakdown
        self.logger.info(f"Doctor scoring breakdown for {doctor_name}:")
        for component, score in score_components.items():
            self.logger.info(f"  {component}: {score:.2f} (normalized: {normalized_scores.get(f'{component}_score', 0):.2f}%, weight: {weights.get(component, 0)})")
        self.logger.info(f"  Total score: {total_score:.2f}")
        
        # Risk category
        if total_score >= 80:
            risk_category = "Low Risk"
        elif total_score >= 60:
            risk_category = "Medium Risk"
        elif total_score >= 40:
            risk_category = "High Risk"
        else:
            risk_category = "Very High Risk"
            
        self.logger.info(f"  Risk category: {risk_category}")
        
        return {
            'qualification_score': scores['qualification_score'],
            'experience_score': scores['experience_score'],
            'rating_score': scores['rating_score'],
            'weighted_rating_score': scores['weighted_rating_score'],
            'location_score': scores['location_score'],
            'specialization_score': scores['specialization_score'],
            'license_score': scores['license_score'],
            'license_verified': scores['license_verified'],
            'normalized_qualification_score': normalized_scores['qualification_score'],
            'normalized_experience_score': normalized_scores['experience_score'],
            'normalized_rating_score': normalized_scores['rating_score'],
            'normalized_weighted_rating_score': normalized_scores['weighted_rating_score'],
            'normalized_location_score': normalized_scores['location_score'],
            'normalized_specialization_score': normalized_scores['specialization_score'],
            'normalized_license_score': normalized_scores['license_score'],
            'total_score': total_score,
            'risk_category': risk_category,
            'rating_count': scores['rating_count']
        }
    
    def score_clinic(self, clinic_data, source="justdial"):
        """Score a clinic based on various factors"""
        scores = {}
        
        try:
            # Extract data based on source
            if source == "justdial":
                name = getattr(clinic_data, 'name', '')
                rating = getattr(clinic_data, 'rating', '')
                raw_rating_count = getattr(clinic_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(clinic_data, 'address', '')
                associated_doctors = getattr(clinic_data, 'associated_doctors', '')
                category = getattr(clinic_data, 'category', '')
            elif source == "googlemap":
                name = getattr(clinic_data, 'name', '')
                rating = getattr(clinic_data, 'rating', '')
                raw_rating_count = getattr(clinic_data, 'reviews', 0)  # Google Maps uses 'reviews' for count
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(clinic_data, 'full_address', '')
                associated_doctors = ''  # Google Maps doesn't directly list associated doctors
                category = getattr(clinic_data, 'category', '')
            else:
                # Generic extraction for other sources
                name = getattr(clinic_data, 'name', '')
                rating = getattr(clinic_data, 'rating', '')
                raw_rating_count = getattr(clinic_data, 'rating_count', 0)
                rating_count = self.clean_rating_count(raw_rating_count)
                address = getattr(clinic_data, 'address', '')
                associated_doctors = getattr(clinic_data, 'associated_doctors', '')
                category = getattr(clinic_data, 'category', '')
            
            # Log the extracted data
            self.logger.debug(f"Extracted clinic data for {name}: category={category}, rating={rating}, "
                         f"rating_count={rating_count}, address={address}")
            
            # Calculate individual scores
            normalized_rating = self.normalize_rating(rating, source) if rating else 0
            if normalized_rating:
                category = self.get_rating_category(normalized_rating)
                scores['rating_score'] = self.rating_scores.get(category, 0)
                # Calculate weighted rating score if rating count is available
                scores['weighted_rating_score'] = self.calculate_weighted_rating(normalized_rating, rating_count) if rating_count else scores['rating_score']
            else:
                scores['rating_score'] = 0
                scores['weighted_rating_score'] = 0
                
            scores['location_score'] = self.calculate_location_score(address)
            scores['rating_count'] = rating_count
            
            # Check if any associated doctors are verified
            has_verified_doctors = False
            doctor_score_sum = 0
            doctor_count = 0
            
            if associated_doctors:
                from cpapp.models.justdial import JustDialDoctor
                from cpapp.models.nmc import NMCDoctor
                from cpapp.models.nmc_dental import NMCDentalDoctor
                from cpapp.models.practo import PractoDoctor
                from cpapp.models.practor_new import NewPractoDoctor
                from cpapp.models.bajaj_doctor import BajajDoctor
                from cpapp.models.savein_doctor import SaveinDoctor
                
                # Parse list of associated doctors (comma-separated)
                doctor_names = [name.strip() for name in associated_doctors.split(',') if name.strip()]
                
                for doctor_name in doctor_names:
                    try:
                        self.logger.debug(f"Looking up associated doctor: {doctor_name}")
                        
                        # Try to find matching doctor in different databases
                        found_doctor = False
                        
                        # Search in JustDial
                        doctors = JustDialDoctor.objects.filter(doctor_name__icontains=doctor_name)
                        if doctors.exists():
                            doctor = doctors.first()
                            doctor.refresh_from_db()
                            doctor_score = self.score_doctor(doctor, "justdial")
                            doctor_score_sum += doctor_score['total_score']
                            doctor_count += 1
                            found_doctor = True
                            
                            if doctor_score['license_verified']:
                                has_verified_doctors = True
                                
                            self.logger.debug(f"Found doctor '{doctor_name}' in JustDial database. Score: {doctor_score['total_score']}")
                                
                        # If not found in JustDial, try Practo
                        if not found_doctor:
                            doctors = PractoDoctor.objects.filter(name__icontains=doctor_name)
                            if doctors.exists():
                                doctor = doctors.first()
                                doctor.refresh_from_db()
                                doctor_score = self.score_doctor(doctor, "practo")
                                doctor_score_sum += doctor_score['total_score']
                                doctor_count += 1
                                found_doctor = True
                                
                                if doctor_score['license_verified']:
                                    has_verified_doctors = True
                                    
                                self.logger.debug(f"Found doctor '{doctor_name}' in Practo database. Score: {doctor_score['total_score']}")
                                
                        # If not found in Practo, try NewPracto
                        if not found_doctor:
                            doctors = NewPractoDoctor.objects.filter(doctor_name__icontains=doctor_name)
                            if doctors.exists():
                                doctor = doctors.first()
                                doctor.refresh_from_db()
                                doctor_score = self.score_doctor(doctor, "new_practo")
                                doctor_score_sum += doctor_score['total_score']
                                doctor_count += 1
                                found_doctor = True
                                
                                if doctor_score['license_verified']:
                                    has_verified_doctors = True
                                    
                                self.logger.debug(f"Found doctor '{doctor_name}' in New Practo database. Score: {doctor_score['total_score']}")
                                
                        # If not found elsewhere, try NMC
                        # For NMC we need to split the doctor name into first/last name
                        if not found_doctor and ' ' in doctor_name:
                            name_parts = doctor_name.split(' ', 1)
                            first_name = name_parts[0]
                            last_name = name_parts[1] if len(name_parts) > 1 else ''
                            
                            # Try searching by first name + last name
                            doctors = NMCDoctor.objects.filter(
                                firstName__icontains=first_name, 
                                lastName__icontains=last_name
                            )
                            
                            if doctors.exists():
                                doctor = doctors.first()
                                doctor.refresh_from_db()
                                doctor_score = self.score_doctor(doctor, "nmc")
                                doctor_score_sum += doctor_score['total_score']
                                doctor_count += 1
                                found_doctor = True
                                
                                # NMC doctors are always license verified
                                has_verified_doctors = True
                                
                                self.logger.debug(f"Found doctor '{doctor_name}' in NMC database. Score: {doctor_score['total_score']}")
                        
                        if not found_doctor:
                            self.logger.debug(f"Could not find doctor '{doctor_name}' in any database")
                            
                    except Exception as e:
                        self.logger.error(f"Error processing doctor {doctor_name}: {str(e)}")
            
            # Average doctor score if available
            avg_doctor_score = doctor_score_sum / doctor_count if doctor_count > 0 else 0
            scores['doctors_score'] = avg_doctor_score * 0.5  # Half weight of full doctor score
            
            # Extra points for having verified doctors
            scores['verified_doctors_bonus'] = 10 if has_verified_doctors else 0
            
            # Log associated doctors info
            self.logger.info(f"Associated doctors for clinic: {doctor_count} doctors found, {avg_doctor_score:.2f} avg score, verified: {has_verified_doctors}")
            
        except Exception as e:
            # Log the error and continue with default scores
            self.logger.error(f"Error processing clinic data: {str(e)}")
            # Set default scores for any missing values
            scores.setdefault('rating_score', 0)
            scores.setdefault('weighted_rating_score', 0)
            scores.setdefault('location_score', 0)
            scores.setdefault('doctors_score', 0)
            scores.setdefault('verified_doctors_bonus', 0)
            scores.setdefault('rating_count', 0)
        
        # Normalize all scores to percentage (0-100)
        max_rating_score = 5
        max_weighted_rating_score = 5
        max_location_score = 10
        max_verified_bonus = 10
        
        normalized_scores = {
            'rating_score': (scores['rating_score'] / max_rating_score) * 100,
            'weighted_rating_score': (scores['weighted_rating_score'] / max_weighted_rating_score) * 100,
            'location_score': (scores['location_score'] / max_location_score) * 100,
            'doctors_score': scores['doctors_score'],  # Already normalized
            'verified_doctors_bonus': (scores['verified_doctors_bonus'] / max_verified_bonus) * 100
        }
        
        # Weighted total score (out of 100)
        weights = {
            'rating': 0.10,
            'weighted_rating': 0.10,
            'location': 0.20,
            'doctors': 0.40,
            'verified_bonus': 0.20
        }
        
        # Calculate contribution of each component to total score
        score_components = {
            'rating': normalized_scores['rating_score'] * weights['rating'],
            'weighted_rating': normalized_scores['weighted_rating_score'] * weights['weighted_rating'],
            'location': normalized_scores['location_score'] * weights['location'],
            'doctors': normalized_scores['doctors_score'] * weights['doctors'],
            'verified_bonus': normalized_scores['verified_doctors_bonus'] * weights['verified_bonus']
        }
        
        # Sum up the weighted scores
        total_score = sum(score_components.values())
        
        # Log the score breakdown
        self.logger.info(f"Clinic scoring breakdown for {name}:")
        for component, score in score_components.items():
            self.logger.info(f"  {component}: {score:.2f} (normalized: {normalized_scores.get(f'{component}_score', 0):.2f}%, weight: {weights.get(component, 0)})")
        self.logger.info(f"  Total score: {total_score:.2f}")
        
        # Risk category
        if total_score >= 80:
            risk_category = "Low Risk"
        elif total_score >= 60:
            risk_category = "Medium Risk"
        elif total_score >= 40:
            risk_category = "High Risk"
        else:
            risk_category = "Very High Risk"
            
        self.logger.info(f"  Risk category: {risk_category}")
        
        return {
            'rating_score': scores['rating_score'],
            'weighted_rating_score': scores['weighted_rating_score'],
            'location_score': scores['location_score'],
            'doctors_score': scores['doctors_score'],
            'verified_doctors_bonus': scores['verified_doctors_bonus'],
            'normalized_rating_score': normalized_scores['rating_score'],
            'normalized_weighted_rating_score': normalized_scores['weighted_rating_score'],
            'normalized_location_score': normalized_scores['location_score'],
            'normalized_doctors_score': normalized_scores['doctors_score'],
            'normalized_verified_doctors_bonus': normalized_scores['verified_doctors_bonus'],
            'total_score': total_score,
            'risk_category': risk_category,
            'rating_count': scores['rating_count']
        }