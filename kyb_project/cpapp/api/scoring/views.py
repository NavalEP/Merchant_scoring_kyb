from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db.models import Q
import logging
import os
import json

from cpapp.models.practo import PractoDoctor
from cpapp.models.justdial import JustDialDoctor, JustDialClinic
from cpapp.models.nmc import NMCDoctor
from cpapp.models.bajaj_doctor import BajajDoctor
from cpapp.models.savein_doctor import SaveinDoctor
from cpapp.models.google_map_data import GoogleMapData
from cpapp.models.practor_new import NewPractoDoctor
from cpapp.services.scoring_engine import DoctorScoringEngine
from cpapp.services.review_scorer_integration import ReviewAnalysisService
from .serializers import (
    DoctorSearchSerializer, ClinicSearchSerializer,
    ScoreRequestSerializer, ScoreResponseSerializer,
    ReviewScoringRequestSerializer
)

# Define serializers inline for this view since they were removed from imports
class ReviewCheckStatusSerializer(serializers.Serializer):
    """Serializer for checking the status of a review scoring request"""
    request_id = serializers.CharField(help_text="ID of the asynchronous request to check")

# Set up logging
logger = logging.getLogger(__name__)


class SearchAPIView(APIView):
    """API endpoint for searching doctors and clinics"""
    
    def get(self, request):
        query = request.query_params.get('query', '')
        entity_type = request.query_params.get('entity_type', 'all')
        
        if not query:
            return Response(
                {"error": "Search query is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        
        # Search for doctors
        if entity_type in ['all', 'doctor']:
            # Search PractoDoctor
            practo_doctors = PractoDoctor.objects.filter(
                Q(name__icontains=query) | 
                Q(speciality__icontains=query)
            )[:10]
            
            for doctor in practo_doctors:
                results.append({
                    'id': doctor.id,
                    'name': doctor.name,
                    'source': 'practo',
                    'speciality': doctor.speciality,
                    'location': doctor.location,
                    'experience': doctor.experience,
                    'qualification': doctor.detailed_qualifications,
                    'rating': doctor.recommendation_percent,
                    'url': doctor.doctor_url,
                    'address': doctor.doctor_address,
                    'phone': doctor.contact_number
                })
            
            # Search JustDialDoctor
            jd_doctors = JustDialDoctor.objects.filter(
                Q(doctor_name__icontains=query) | 
                Q(category__icontains=query)
            )[:10]
            
            for doctor in jd_doctors:
                results.append({
                    'id': doctor.id,
                    'name': doctor.doctor_name,
                    'source': 'justdial',
                    'speciality': doctor.category,
                    'location': doctor.location,
                    'experience': doctor.experience,
                    'qualification': doctor.qualification,
                    'rating': doctor.rating,
                    'phone': doctor.phone_number,
                    'registration': doctor.registration,
                    'address': doctor.clinic_address,
                    'url': doctor.detail_url
                })
            
            # Search NMCDoctor
            nmc_doctors = NMCDoctor.objects.filter(
                Q(firstName__icontains=query) | 
                Q(lastName__icontains=query)
            )[:10]
            
            for doctor in nmc_doctors:
                full_name = f"{doctor.firstName} {doctor.lastName if doctor.lastName else ''}"
                results.append({
                    'id': doctor.id,
                    'name': full_name.strip(),
                    'source': 'nmc',
                    'location': doctor.address,
                    'experience': '',
                    'qualification': doctor.doctorDegree,
                    'rating': '',
                    'registration': doctor.registrationNo,
                })
                
            # Search NMCDentalDoctor
            from cpapp.models.nmc_dental import NMCDentalDoctor
            nmc_dental_doctors = NMCDentalDoctor.objects.filter(
                Q(full_name__icontains=query) | 
                Q(qualification__icontains=query)
            )[:10]
            
            for doctor in nmc_dental_doctors:
                results.append({
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'source': 'nmc_dental',
                    'location': doctor.state_medical_council if hasattr(doctor, 'state_medical_council') else '',
                    'experience': '',
                    'qualification': doctor.qualification,
                    'rating': '',
                    'registration': doctor.registration_number,
                })
            
            # Search BajajDoctor
            bajaj_doctors = BajajDoctor.objects.filter(
                Q(name__icontains=query) | 
                Q(specialities__icontains=query)
            )[:10]
            
            for doctor in bajaj_doctors:
                results.append({
                    'id': doctor.id,
                    'name': doctor.name,
                    'source': 'bajaj',
                    'speciality': doctor.specialities,
                    'location': doctor.clinic_location,
                    'experience': doctor.experience,
                    'qualification': doctor.qualifications,
                    'rating': doctor.rating_percent,
                    'rating_count': doctor.rating_count,
                    'address': doctor.clinic_address,
                    'clinic_name': doctor.clinic_name,
                    'hpr_id': doctor.hpr_id
                })
                
            # Search SaveinDoctor
            savein_doctors = SaveinDoctor.objects.filter(
                Q(name__icontains=query) | 
                Q(doctor_name__icontains=query) |
                Q(specialization__icontains=query)
            )[:10]
            
            for doctor in savein_doctors:
                results.append({
                    'id': doctor.id,
                    'name': doctor.doctor_name,
                    'source': 'savein',
                    'speciality': doctor.specialization,
                    'location': doctor.location,
                    'experience': doctor.experience,
                    'qualification': doctor.qualification,
                    'rating': doctor.rating,
                    'rating_count': doctor.reviews_count,
                    'address': doctor.address,
                    'consultation_fee': doctor.consultation_fee,
                    'price_category': doctor.price_category,
                    'services': doctor.services
                })
            
            # Search NewPractoDoctor
            new_practo_doctors = NewPractoDoctor.objects.filter(
                Q(doctor_name__icontains=query) | 
                Q(specialization__icontains=query)
            )[:10]
            
            for doctor in new_practo_doctors:
                try:
                    clinic_address = ""
                    
                    # Use the clinic_data property instead of handling raw data
                    if hasattr(doctor, 'clinic_data'):
                        clinic_data = doctor.clinic_data
                        if isinstance(clinic_data, dict):
                            clinic_address = clinic_data.get('address', '')
                    
                    results.append({
                        'id': doctor.id,
                        'name': doctor.doctor_name,
                        'source': 'new_practo',
                        'speciality': doctor.specialization,
                        'location': doctor.location,
                        'experience': doctor.experience,
                        'qualification': doctor.qualification,
                        'rating': doctor.rating,
                        'rating_count': doctor.rating_count,
                        'address': clinic_address,
                        'services': doctor.services,
                        'education': doctor.education,
                        'registration': doctor.registration,
                    })
                except Exception as e:
                    logger.error(f"Error processing NewPractoDoctor {doctor.id}: {str(e)}")
        
        # Search for clinics
        if entity_type in ['all', 'clinic']:
            # Search JustDialClinic
            jd_clinics = JustDialClinic.objects.filter(
                Q(name__icontains=query) | 
                Q(category__icontains=query)
            )[:10]
            
            for clinic in jd_clinics:
                results.append({
                    'id': clinic.id,
                    'name': clinic.name,
                    'source': 'justdial',
                    'category': clinic.category,
                    'speciality': clinic.category,
                    'location': clinic.address,
                    'rating': clinic.rating,
                    'address': clinic.address
                })
            
            # Search GoogleMapData
            logger.info(f"Searching GoogleMapData for query: {query}")
            google_map_results = GoogleMapData.objects.filter(
                Q(name__icontains=query) | 
                Q(category__icontains=query) |
                Q(full_address__icontains=query)
            )[:10]
            
            logger.info(f"Found {google_map_results.count()} GoogleMapData results")
            
            for place in google_map_results:
                results.append({
                    'id': place.id,
                    'name': place.name,
                    'source': 'googlemap',
                    'category': place.category,
                    'type': place.type,
                    'location': place.full_address,
                    'address': place.full_address,
                    'rating': place.rating,
                    'rating_count': place.reviews,
                    'verified': place.verified
                })
        
        # Serialize based on entity type
        if entity_type == 'doctor':
            serializer = DoctorSearchSerializer(results, many=True)
        elif entity_type == 'clinic':
            serializer = ClinicSearchSerializer(results, many=True)
        else:
            # For 'all', we'll handle mixed results
            doctor_results = [r for r in results if 'speciality' in r]
            clinic_results = [r for r in results if 'category' in r]
            
            doctor_serializer = DoctorSearchSerializer(doctor_results, many=True)
            clinic_serializer = ClinicSearchSerializer(clinic_results, many=True)
            
            return Response({
                'doctors': doctor_serializer.data,
                'clinics': clinic_serializer.data
            })
        
        return Response(serializer.data)


class ScoreAPIView(APIView):
    """API endpoint for scoring doctors and clinics"""
    
    def post(self, request):
        serializer = ScoreRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        entity_type = serializer.validated_data['entity_type']
        entity_id = serializer.validated_data['entity_id']
        source = serializer.validated_data['source']
        
        # Initialize scoring engine
        scoring_engine = DoctorScoringEngine()
        
        # Get the entity
        entity = None
        name = ""
        
        if entity_type == 'doctor':
            if source == 'practo':
                try:
                    entity = PractoDoctor.objects.get(id=entity_id)
                    name = entity.name
                except PractoDoctor.DoesNotExist:
                    return Response(
                        {"error": "Doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'justdial':
                try:
                    entity = JustDialDoctor.objects.get(id=entity_id)
                    name = entity.doctor_name
                except JustDialDoctor.DoesNotExist:
                    return Response(
                        {"error": "Doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'nmc':
                try:
                    entity = NMCDoctor.objects.get(id=entity_id)
                    name = f"{entity.firstName} {entity.lastName if entity.lastName else ''}".strip()
                except NMCDoctor.DoesNotExist:
                    return Response(
                        {"error": "Doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'nmc_dental':
                from cpapp.models.nmc_dental import NMCDentalDoctor
                try:
                    entity = NMCDentalDoctor.objects.get(id=entity_id)
                    name = entity.full_name
                except NMCDentalDoctor.DoesNotExist:
                    return Response(
                        {"error": "Dental doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'bajaj':
                try:
                    entity = BajajDoctor.objects.get(id=entity_id)
                    name = entity.name
                except BajajDoctor.DoesNotExist:
                    return Response(
                        {"error": "Bajaj doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'savein':
                try:
                    entity = SaveinDoctor.objects.get(id=entity_id)
                    name = entity.name or entity.doctor_name
                except SaveinDoctor.DoesNotExist:
                    return Response(
                        {"error": "Savein doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'new_practo':
                try:
                    entity = NewPractoDoctor.objects.get(id=entity_id)
                    name = entity.doctor_name
                except NewPractoDoctor.DoesNotExist:
                    return Response(
                        {"error": "New Practo doctor not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Score the doctor
            score_results = scoring_engine.score_doctor(entity, source)
            
        elif entity_type == 'clinic':
            if source == 'justdial':
                try:
                    entity = JustDialClinic.objects.get(id=entity_id)
                    name = entity.name
                except JustDialClinic.DoesNotExist:
                    return Response(
                        {"error": "Clinic not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            elif source == 'googlemap':
                try:
                    entity = GoogleMapData.objects.get(id=entity_id)
                    name = entity.name
                except GoogleMapData.DoesNotExist:
                    return Response(
                        {"error": "Google Maps place not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {"error": "Invalid source for clinic"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Score the clinic
            score_results = scoring_engine.score_clinic(entity, source)
        
        # Format response
        response_data = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'source': source,
            'name': name,
            'total_score': score_results['total_score'],
            'risk_category': score_results['risk_category'],
            'score_breakdown': {k: v for k, v in score_results.items() if k not in ['total_score', 'risk_category']},
            'created_at': timezone.now()
        }
        
        response_serializer = ScoreResponseSerializer(response_data)
        return Response(response_serializer.data)


class ReviewScoringAPIView(APIView):
    """API endpoint for scoring Google reviews from Outscraper API"""
    
    def post(self, request):
        """
        Submit a review scoring request.
        
        Fetches Google reviews using Outscraper API and scores them for authenticity.
        """
        serializer = ReviewScoringRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get API key from environment or settings
        api_key = os.getenv("VITE_OUTSCRAPER_API_KEY")
        if not api_key:
            return Response(
                {"error": "Outscraper API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Initialize the review analysis service
        review_service = ReviewAnalysisService(api_key)
        
        # Extract parameters
        query = serializer.validated_data['query']
        reviews_limit = serializer.validated_data.get('reviews_limit', 100)
        sort = serializer.validated_data.get('sort', 'most_relevant')
        language = serializer.validated_data.get('language', 'en')
        async_request = serializer.validated_data.get('async_request', True)
        
        # Fetch and score reviews
        logger.info(f"Fetching and scoring reviews for: {query}")
        
        try:
            # Process the reviews
            result = review_service.process_reviews(
                query=query,
                reviews_limit=reviews_limit,
                sort=sort,
                language=language,
                async_request=async_request
            )
            
            # Handle async requests
            if async_request and result.get("status") == "pending":
                return Response({
                    "status": "pending",
                    "request_id": result.get("request_id"),
                    "message": "Review fetching in progress. Check status using the request ID."
                })
            
            # Return the scored reviews
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error processing reviews: {str(e)}")
            return Response(
                {"error": f"Error processing reviews: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def get(self, request):
        """
        Check the status of an asynchronous review scoring request.
        """
        serializer = ReviewCheckStatusSerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
            
        request_id = serializer.validated_data['request_id']
        
        # Get API key from environment or settings
        api_key = os.getenv("VITE_OUTSCRAPER_API_KEY")
        if not api_key:
            return Response(
                {"error": "Outscraper API key not configured"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        # Initialize the review analysis service
        review_service = ReviewAnalysisService(api_key)
        
        try:
            # Get results for the request
            result = review_service.get_review_results(request_id)
            
            # If the request is still processing
            if result.get("status") == "pending":
                return Response({
                    "status": "pending",
                    "request_id": request_id,
                    "message": "Review fetching still in progress."
                })
                
            # If completed, score the reviews
            if result.get("status") == "finished" and "data" in result:
                reviews_data = []
                for place_data in result["data"]:
                    if "reviews_data" in place_data and place_data["reviews_data"]:
                        reviews_data.extend(place_data["reviews_data"])
                
                # Score the reviews
                if reviews_data:
                    scored_reviews = review_service.score_reviews(reviews_data)
                    
                    # Calculate statistics
                    total_reviews = len(scored_reviews)
                    genuine_reviews = sum(1 for r in scored_reviews if r['review_score'] > 0)
                    fake_reviews = total_reviews - genuine_reviews
                    avg_score = sum(r['review_score'] for r in scored_reviews) / total_reviews if total_reviews > 0 else 0
                    
                    return Response({
                        "status": "completed",
                        "request_id": request_id,
                        "total_reviews": total_reviews,
                        "genuine_reviews": genuine_reviews,
                        "fake_reviews": fake_reviews,
                        "average_score": round(avg_score, 2),
                        "scored_reviews": scored_reviews
                    })
                else:
                    return Response({
                        "status": "completed",
                        "request_id": request_id,
                        "message": "No reviews found for this query.",
                        "scored_reviews": []
                    })
            
            # Handle failed requests
            return Response({
                "status": "error",
                "message": "Failed to retrieve review results.",
                "response": result
            })
            
        except Exception as e:
            logger.error(f"Error checking review status: {str(e)}")
            return Response(
                {"error": f"Error checking review status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        