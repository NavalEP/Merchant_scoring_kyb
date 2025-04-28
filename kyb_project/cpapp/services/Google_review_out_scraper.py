# outscraper_maps_api.py

import requests
from typing import Dict, List, Union, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

class OutscraperMapsReviewsAPI:
    """
    A client for the Outscraper Google Maps Reviews API (v3)
    Documentation: https://api.app.outscraper.com/maps/reviews-v3
    """
    
    BASE_URL = "https://api.app.outscraper.com/maps/reviews-v3"
    
    def __init__(self, api_key: str):
        """
        Initialize with your Outscraper API key
        
        Args:
            api_key: Your Outscraper API key
        """
        self.api_key = api_key or os.getenv("OUTSCRAPER_API_KEY")
        self.headers = {
            "X-API-KEY": api_key,
            "Accept": "application/json"
        }
    
    def get_reviews(self, 
                   query: Union[str, List[str]], 
                   reviews_limit: int = 100,
                   reviews_query: Optional[str] = None,
                   limit: int = 1,
                   sort: str = "most_relevant",
                   last_pagination_id: Optional[str] = None,
                   start: Optional[int] = None,
                   cutoff: Optional[int] = None,
                   cutoff_rating: Optional[int] = None,
                   ignore_empty: bool = False,
                   source: Optional[str] = None,
                   language: str = "en",
                   region: Optional[str] = None,
                   fields: Optional[str] = None,
                   async_request: bool = True,
                   ui: bool = False,
                   webhook: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve Google Maps reviews for places based on search queries or specific place IDs.
        
        Args:
            query: Single query string or list of query strings
            reviews_limit: Maximum number of reviews to retrieve per place (0 = unlimited)
            reviews_query: Query to search within reviews content
            limit: Maximum number of places to retrieve per query
            sort: Sorting method ("most_relevant", "newest", "highest_rating", "lowest_rating")
            last_pagination_id: Pagination ID for retrieving next page of results
            start: Start timestamp for reviews (newest review date)
            cutoff: Cut-off timestamp for reviews (oldest review date)
            cutoff_rating: Maximum/minimum rating for reviews (depends on sort parameter)
            ignore_empty: Whether to ignore reviews without text
            source: Source filter (e.g., "google")
            language: Language code for results
            region: Country/region code for results
            fields: Specific fields to include in response
            async_request: Whether to use asynchronous request processing
            ui: Whether to execute as a UI task
            webhook: URL for callback when task is finished
            
        Returns:
            Dictionary with response data containing place and review information
        """
        params = {
            "query": query,
            "reviewsLimit": reviews_limit,
            "limit": limit,
            "sort": sort,
            "ignoreEmpty": str(ignore_empty).lower(),
            "language": language,
            "async": str(async_request).lower(),
            "ui": str(ui).lower()
        }
        
        # Add optional parameters if provided
        if reviews_query:
            params["reviewsQuery"] = reviews_query
        if last_pagination_id:
            params["lastPaginationId"] = last_pagination_id
        if start:
            params["start"] = start
        if cutoff:
            params["cutoff"] = cutoff
        if cutoff_rating:
            params["cutoffRating"] = cutoff_rating
        if source:
            params["source"] = source
        if region:
            params["region"] = region
        if fields:
            params["fields"] = fields
        if webhook:
            params["webhook"] = webhook
            
        try:
            response = requests.get(self.BASE_URL, headers=self.headers, params=params)
            response.raise_for_status()
            
            if response.status_code == 202:
                # Async request submitted, return request ID for later retrieval
                return {"status": "pending", "request_id": response.json().get("id")}
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Outscraper API: {str(e)}")
            raise
    
    def get_results(self, request_id: str) -> Dict[str, Any]:
        """
        Retrieve results for a previously submitted asynchronous request.
        
        Args:
            request_id: ID of the previously submitted request
            
        Returns:
            Dictionary with response data containing place and review information
        """
        url = f"https://api.app.outscraper.com/requests/{request_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error retrieving results from Outscraper API: {str(e)}")
            raise