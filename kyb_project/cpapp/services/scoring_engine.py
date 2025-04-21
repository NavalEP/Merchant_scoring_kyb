class DoctorScoringEngine:
    def __init__(self):
        # Initialize scoring rules
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
            "Medical Device": 4
        }
        
        self.geoiq_service = None
        try:
            from .GeoIQ import GeoIQService
            self.geoiq_service = GeoIQService()
        except Exception as e:
            print(f"GeoIQ service initialization failed: {e}")
    
    def normalize_rating(self, rating, source):
        """Normalize ratings from different sources to a 0-5 scale"""
        try:
            if source == "practo":
                # Convert percentage recommendation to 0-5 scale
                return float(rating.strip('%')) / 20 if '%' in str(rating) else float(rating)
            elif source == "justdial":
                # Justdial ratings are already on a 0-5 scale
                return float(rating)
            else:
                # Default case
                return float(rating) if rating else 0
        except (ValueError, TypeError):
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
            rating = float(rating)
            rating_count = int(rating_count)
            
            # Base rating score (0-5)
            category = self.get_rating_category(rating)
            base_score = self.rating_scores.get(category, 2)
            
            # Rating count score (1-5)
            count_category = self.get_rating_count_category(rating_count)
            count_score = self.rating_count_categories.get(count_category, 1)
            
            # Combined weighted score:
            # - High rating with many reviews gets the highest score
            # - Low rating with few reviews gets the lowest score
            # - High rating with few reviews or low rating with many reviews gets a middle score
            weighted_score = (base_score * 0.6) + (count_score * 0.4)
            
            # Bonus for extremely high review counts with good ratings
            if rating_count > 500 and rating >= 4.0:
                weighted_score += min((rating_count - 500) / 1000, 1.0)
                
            return min(weighted_score, 5)  # Cap at 5
        except (ValueError, TypeError):
            return 2  # Default middle value
    
    def evaluate_location(self, address):
        """Evaluate location quality using GeoIQ"""
        if not self.geoiq_service or not address:
            return "Medium"  # Default if GeoIQ service is not available
            
        try:
            location_data = self.geoiq_service.get_location_data_by_address(address)
            
            # Analysis based on specified variables
            avg_income = location_data.get('w_hh_income_10l_above_perc', 0)
            retail_density = location_data.get('p_retail_gc_np', 0)
            print(avg_income, retail_density)
            
            if avg_income > 30 and retail_density > 20:
                return "Prime"
            elif avg_income > 15 or retail_density > 10:
                return "Medium"
            else:
                return "Poor"
        except Exception as e:
            print(f"GeoIQ evaluation failed: {e}")
            return "Medium"
    
    def verify_medical_license(self, registration_no, doctor_data=None):
        """Verify if the doctor has a valid medical license"""
        if not registration_no:
            return False
            
        # Check if exists in NMC database
        from cpapp.models.nmc import NMCDoctor
        
        try:
            nmc_match = NMCDoctor.objects.filter(registrationNo=registration_no).exists()
            if nmc_match:
                return True
                
            # If we have full doctor data, we can do more checks
            if doctor_data and hasattr(doctor_data, 'registration'):
                justdial_reg = doctor_data.registration
                if justdial_reg and justdial_reg == registration_no:
                    return True
        except Exception as e:
            print(f"License verification error: {e}")
            
        return False
    
    def calculate_qualification_score(self, qualification_text):
        """Calculate score based on qualification"""
        qualification_level = self.extract_qualification_level(qualification_text)
        return self.qualification_scores.get(qualification_level, 3)
    
    def calculate_experience_score(self, experience_text):
        """Calculate score based on experience"""
        years = self.extract_experience_years(experience_text)
        category = self.get_experience_category(years)
        return self.experience_scores.get(category, 3)
    
    def calculate_rating_score(self, rating, source, rating_count=None):
        """Calculate score based on rating and rating count"""
        normalized_rating = self.normalize_rating(rating, source)
        
        if rating_count:
            # Use weighted calculation that considers count
            return self.calculate_weighted_rating(normalized_rating, rating_count)
        else:
            # Fall back to original method if count not available
            category = self.get_rating_category(normalized_rating)
            return self.rating_scores.get(category, 2)
    
    def calculate_location_score(self, address):
        """Calculate score based on location"""
        location_category = self.evaluate_location(address)
        return self.location_scores.get(location_category, 0)
    
    def calculate_specialization_score(self, specialization):
        """Calculate score based on specialization"""
        if not specialization:
            return 3  # Default middle value
        
        # Try to match the specialization with our known categories
        for category, score in self.specialization_scores.items():
            if category.lower() in specialization.lower():
                return score
        
        # Default score if no match found
        return 2
    
    def score_doctor(self, doctor_data, source="justdial"):
        """Score a doctor based on different factors"""
        scores = {}
        
        # Extract data based on source
        if source == "practo":
            qualification = doctor_data.detailed_qualifications
            experience = doctor_data.experience
            rating = doctor_data.recommendation_percent
            # Extract rating count (patient_stories for Practo)
            rating_count = getattr(doctor_data, 'patient_stories', 0)
            address = f"{doctor_data.doctor_address}, {doctor_data.location}"
            registration_no = None  # Practo doesn't provide registration number
            specialization = doctor_data.speciality
        elif source == "justdial":
            qualification = doctor_data.qualification
            experience = doctor_data.experience
            rating = doctor_data.rating
            # Extract rating count for JustDial
            rating_count = getattr(doctor_data, 'rating_count', 0)
            address = doctor_data.clinic_address
            registration_no = doctor_data.registration
            specialization = doctor_data.specialization
        elif source == "nmc":
            qualification = doctor_data.doctorDegree
            experience = None  # NMC doesn't provide experience
            rating = None  # NMC doesn't provide ratings
            rating_count = 0  # NMC doesn't provide rating count
            address = doctor_data.address
            registration_no = doctor_data.registrationNo
            specialization = doctor_data.doctorDegree  # Using degree as specialization
        else:
            # Generic data extraction
            qualification = getattr(doctor_data, 'qualification', '')
            experience = getattr(doctor_data, 'experience', '')
            rating = getattr(doctor_data, 'rating', '')
            rating_count = getattr(doctor_data, 'rating_count', 0)
            address = getattr(doctor_data, 'address', '')
            registration_no = getattr(doctor_data, 'registration_no', None)
            specialization = getattr(doctor_data, 'specialization', '')
            
        # Calculate individual scores
        scores['qualification_score'] = self.calculate_qualification_score(qualification)
        scores['experience_score'] = self.calculate_experience_score(experience) if experience else 5
        
        # Calculate both standard rating score and weighted rating score
        normalized_rating = self.normalize_rating(rating, source) if rating else 0
        if normalized_rating:
            category = self.get_rating_category(normalized_rating)
            scores['rating_score'] = self.rating_scores.get(category, 2)
            # Calculate weighted rating score if rating count is available
            scores['weighted_rating_score'] = self.calculate_weighted_rating(normalized_rating, rating_count) if rating_count else scores['rating_score']
        else:
            scores['rating_score'] = 5
            scores['weighted_rating_score'] = 5
            
        scores['location_score'] = self.calculate_location_score(address)
        scores['specialization_score'] = self.calculate_specialization_score(specialization)
        
        # Calculate license verification score
        scores['license_verified'] = self.verify_medical_license(registration_no, doctor_data)
        scores['license_score'] = 10 if scores['license_verified'] else 0
        
        # Add rating count as additional info
        scores['rating_count'] = rating_count
        
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
        
        total_score = (
            normalized_scores['qualification_score'] * weights['qualification'] +
            normalized_scores['experience_score'] * weights['experience'] +
            normalized_scores['rating_score'] * weights['rating'] +
            normalized_scores['weighted_rating_score'] * weights['weighted_rating'] +
            normalized_scores['location_score'] * weights['location'] +
            normalized_scores['specialization_score'] * weights['specialization'] +
            normalized_scores['license_score'] * weights['license']
        )
        
        # Risk category
        if total_score >= 80:
            risk_category = "Low Risk"
        elif total_score >= 60:
            risk_category = "Medium Risk"
        elif total_score >= 40:
            risk_category = "High Risk"
        else:
            risk_category = "Very High Risk"
        
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
        
        # Extract data based on source
        if source == "justdial":
            rating = clinic_data.rating
            rating_count = getattr(clinic_data, 'rating_count', 0)
            address = clinic_data.address
            associated_doctors = clinic_data.associated_doctors
        else:
            # Generic extraction
            rating = getattr(clinic_data, 'rating', '')
            rating_count = getattr(clinic_data, 'rating_count', 0)
            address = getattr(clinic_data, 'address', '')
            associated_doctors = getattr(clinic_data, 'associated_doctors', '')
        
        # Calculate individual scores
        normalized_rating = self.normalize_rating(rating, source) if rating else 0
        if normalized_rating:
            category = self.get_rating_category(normalized_rating)
            scores['rating_score'] = self.rating_scores.get(category, 2)
            # Calculate weighted rating score if rating count is available
            scores['weighted_rating_score'] = self.calculate_weighted_rating(normalized_rating, rating_count) if rating_count else scores['rating_score']
        else:
            scores['rating_score'] = 5
            scores['weighted_rating_score'] = 5
            
        scores['location_score'] = self.calculate_location_score(address)
        scores['rating_count'] = rating_count
        
        # Check if any associated doctors are verified
        has_verified_doctors = False
        doctor_score_sum = 0
        doctor_count = 0
        
        if associated_doctors:
            from cpapp.models.justdial import JustDialDoctor
            from cpapp.models.nmc import NMCDoctor
            
            # Parse list of associated doctors (comma-separated)
            doctor_names = [name.strip() for name in associated_doctors.split(',') if name.strip()]
            
            for doctor_name in doctor_names:
                try:
                    # Find matching doctor in database
                    doctors = JustDialDoctor.objects.filter(doctor_name__icontains=doctor_name)
                    
                    if doctors.exists():
                        doctor = doctors.first()
                        doctor_score = self.score_doctor(doctor, "justdial")
                        doctor_score_sum += doctor_score['total_score']
                        doctor_count += 1
                        
                        if doctor_score['license_verified']:
                            has_verified_doctors = True
                except Exception as e:
                    print(f"Error processing doctor {doctor_name}: {e}")
        
        # Average doctor score if available
        avg_doctor_score = doctor_score_sum / doctor_count if doctor_count > 0 else 0
        scores['doctors_score'] = avg_doctor_score * 0.5  # Half weight of full doctor score
        
        # Extra points for having verified doctors
        scores['verified_doctors_bonus'] = 10 if has_verified_doctors else 0
        
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
        
        total_score = (
            normalized_scores['rating_score'] * weights['rating'] +
            normalized_scores['weighted_rating_score'] * weights['weighted_rating'] +
            normalized_scores['location_score'] * weights['location'] +
            normalized_scores['doctors_score'] * weights['doctors'] +
            normalized_scores['verified_doctors_bonus'] * weights['verified_bonus']
        )
        
        # Risk category
        if total_score >= 80:
            risk_category = "Low Risk"
        elif total_score >= 60:
            risk_category = "Medium Risk"
        elif total_score >= 40:
            risk_category = "High Risk"
        else:
            risk_category = "Very High Risk"
        
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