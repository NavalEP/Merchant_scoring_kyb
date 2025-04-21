from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from typing import Dict, Any, List, Optional
from ...services.Google_review_out_scraper import OutscraperMapsReviewsAPI
from .serializers import OutscraperReviewsSerializer
import os

class OutscraperReviewsView(APIView):
    """
    API endpoint for retrieving Google Maps reviews using Outscraper
    """
    
    
    def post(self, request) -> Response:
        try:
            serializer = OutscraperReviewsSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get API key from environment variables
            api_key = os.getenv("VITE_OUTSCRAPER_API_KEY")
            if not api_key:
                return Response(
                    {"error": "OUTSCRAPER_API_KEY not found in environment variables"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            client = OutscraperMapsReviewsAPI(api_key=api_key)
            response = client.get_reviews(**serializer.validated_data)
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OutscraperReviewsResultsView(APIView):
    """
    API endpoint for retrieving results of an async Outscraper reviews request
    """
   
    
    def get(self, request, request_id: str) -> Response:
        try:
            # Get API key from environment variables
            api_key = os.getenv("VITE_OUTSCRAPER_API_KEY")
            if not api_key:
                return Response(
                    {"error": "OUTSCRAPER_API_KEY not found in environment variables"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            client = OutscraperMapsReviewsAPI(api_key=api_key)
            response = client.get_results(request_id)
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 