from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from typing import Dict, Any, List, Optional
from ...services.Google_review_out_scraper import OutscraperMapsReviewsAPI
from .serializers import OutscraperReviewsSerializer, CustomSearchSerializer
import os
import logging

logger = logging.getLogger(__name__)

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
            api_key = os.getenv("OUTSCRAPER_API_KEY") or os.getenv("VITE_OUTSCRAPER_API_KEY")
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
            api_key = os.getenv("OUTSCRAPER_API_KEY") or os.getenv("VITE_OUTSCRAPER_API_KEY")
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

class CustomSearchView(APIView):
    """
    API endpoint for simplified search using Outscraper Google Reviews API
    """
    
    def post(self, request) -> Response:
        try:
            logger.info(f"CustomSearchView received request: {request.data}")
            
            serializer = CustomSearchSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Invalid request data: {serializer.errors}")
                return Response(
                    {"error": f"Invalid request data: {serializer.errors}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get API key from environment variables
            api_key = os.getenv("OUTSCRAPER_API_KEY") or os.getenv("VITE_OUTSCRAPER_API_KEY")
            logger.debug(f"API key present: {bool(api_key)}")
            
            if not api_key:
                logger.error("OUTSCRAPER_API_KEY not found in environment variables")
                return Response(
                    {"error": "OUTSCRAPER_API_KEY not found in environment variables. Please configure the API key."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Extract data from the serializer
            query = serializer.validated_data["query"]
            reviews_limit = serializer.validated_data["reviews_limit"]
            
            logger.info(f"Processing search for query: '{query}' with reviews_limit: {reviews_limit}")
            
            # Set up parameters for OutScraper API
            params = {
                "query": query,
                "reviews_limit": reviews_limit,
                "sort": "most_relevant",
                "language": "en",
                "async_request": False
            }
            
            client = OutscraperMapsReviewsAPI(api_key=api_key)
            logger.debug("Calling Outscraper API...")
            
            try:
                response = client.get_reviews(**params)
                logger.info(f"Received response from Outscraper API: {type(response)}")
                logger.debug(f"Response details: {response}")
                
                # Check if response contains data
                if not response or (isinstance(response, dict) and not response.get('data') and not response.get('results')):
                    logger.warning(f"Empty response received: {response}")
                    return Response(
                        {"error": "No results found for your query. Please try a different search term."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                return Response(response, status=status.HTTP_200_OK)
            except Exception as api_error:
                logger.exception(f"Error from Outscraper API: {str(api_error)}")
                return Response(
                    {"error": f"Outscraper API error: {str(api_error)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.exception(f"Unhandled exception in CustomSearchView: {str(e)}")
            return Response(
                {"error": f"Server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 