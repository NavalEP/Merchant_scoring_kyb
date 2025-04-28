import unittest
import os
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from cpapp.services.scoring_engine import MerchantScoringEngine

class TestMerchantScoringEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MerchantScoringEngine()
        
    def test_business_risk_score(self):
        # Test case 1: High-risk business
        merchant_data = {
            'entity_type': 'Proprietorship',
            'address_vintage': 'Under 1 year',
            'rent_owned': 'rented'
        }
        score = self.engine.calculate_business_risk_score(merchant_data)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)
        
        # Test case 2: Low-risk business
        merchant_data = {
            'entity_type': 'Ltd or Pvt Ltd',
            'address_vintage': '3+ years',
            'rent_owned': 'owned'
        }
        score = self.engine.calculate_business_risk_score(merchant_data)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)
    
    def test_legal_risk_score(self):
        # Test case 1: Valid medical license
        verification_checks = [
            {'check_type': 'Medical license validity', 'status': 'passed'}
        ]
        score = self.engine.calculate_legal_risk_score({}, verification_checks)
        self.assertEqual(score, 25.0)  # 15/60 * 100
        
        # Test case 2: No verification checks
        score = self.engine.calculate_legal_risk_score({}, [])
        self.assertEqual(score, 0.0)
    
    def test_service_quality_score(self):
        # Test case 1: High-quality service
        merchant_data = {
            'experience_years': 15,
            'owner_education': 'MD',
            'location_analysis': {'commercial_rent_per_sqft': 150}
        }
        social_media_data = {
            'google': {'rating': 4.8},
            'practo': {'rating': 4.7}
        }
        score = self.engine.calculate_service_quality_score(merchant_data, social_media_data)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        
        # Test case 2: Medium-quality service
        merchant_data = {
            'experience_years': 7,
            'owner_education': 'MBBS',
            'location_analysis': {'commercial_rent_per_sqft': 75}
        }
        social_media_data = {
            'google': {'rating': 4.2},
            'practo': {'rating': 4.1}
        }
        score = self.engine.calculate_service_quality_score(merchant_data, social_media_data)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_ethical_risk_score(self):
        # Test case 1: High ethical score
        merchant_data = {
            'owner_education': 'MD'
        }
        social_media_data = {
            'sentiment_score': 0.8
        }
        score = self.engine.calculate_ethical_risk_score(merchant_data, social_media_data)
        self.assertGreater(score, 0)
        self.assertLess(score, 100)
    
    def test_complete_scoring(self):
        # Test complete merchant scoring
        merchant_data = {
            'entity_type': 'Ltd or Pvt Ltd',
            'address_vintage': '3+ years',
            'rent_owned': 'owned',
            'experience_years': 15,
            'owner_education': 'MD',
            'location_analysis': {'commercial_rent_per_sqft': 150}
        }
        
        verification_checks = [
            {'check_type': 'Medical license validity', 'status': 'passed'}
        ]
        
        social_media_data = {
            'google': {'rating': 4.8},
            'practo': {'rating': 4.7},
            'sentiment_score': 0.8
        }
        
        result = self.engine.score_merchant(merchant_data, verification_checks, social_media_data)
        
        # Check all required fields are present
        self.assertIn('business_risk_score', result)
        self.assertIn('legal_risk_score', result)
        self.assertIn('service_quality_score', result)
        self.assertIn('ethical_risk_score', result)
        self.assertIn('total_score', result)
        self.assertIn('risk_category', result)
        
        # Check score ranges
        self.assertGreater(result['total_score'], 0)
        self.assertLessEqual(result['total_score'], 100)
        
        # Check risk category
        self.assertIn(result['risk_category'], ['Low Risk', 'Medium Risk', 'High Risk', 'Very High Risk'])

if __name__ == '__main__':
    unittest.main() 