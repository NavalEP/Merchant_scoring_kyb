from typing import Dict, List, Any, Optional, Union
import logging
from .Google_review_out_scraper import OutscraperMapsReviewsAPI
from .review_scoring_system import ReviewScorer

# Initialize logging
logger = logging.getLogger(__name__)

class ReviewAnalysisService:
    """
    Service to fetch Google reviews from Outscraper API and
    analyze their authenticity using the ReviewScorer
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the ReviewAnalysisService
        
        Args:
            api_key: Outscraper API key
        """
        self.api_key = api_key
        self.outscraper_client = OutscraperMapsReviewsAPI(api_key)
        self.review_scorer = ReviewScorer()
        
    def fetch_reviews(self, 
                     query: str,
                     reviews_limit: int = 100,
                     sort: str = "most_relevant",
                     language: str = "en",
                     async_request: bool = True) -> Dict[str, Any]:
        """
        Fetch reviews from Outscraper API
        
        Args:
            query: Search query for Google Maps place
            reviews_limit: Maximum number of reviews to fetch
            sort: Sort method for reviews
            language: Language code for reviews
            async_request: Whether to use async processing
            
        Returns:
            Dictionary with response from Outscraper API
        """
        try:
            logger.info(f"Fetching reviews for query: {query}")
            response = self.outscraper_client.get_reviews(
                query=query,
                reviews_limit=reviews_limit,
                sort=sort,
                language=language,
                async_request=async_request
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching reviews: {e}")
            raise
    
    def get_review_results(self, request_id: str) -> Dict[str, Any]:
        """
        Get results for an async review request
        
        Args:
            request_id: ID of the async request
            
        Returns:
            Dictionary with results from Outscraper API
        """
        try:
            logger.info(f"Getting results for request ID: {request_id}")
            response = self.outscraper_client.get_results(request_id)
            return response
        except Exception as e:
            logger.error(f"Error getting review results: {e}")
            raise
    
    def score_reviews(self, reviews_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score reviews using the ReviewScorer
        
        Args:
            reviews_data: List of review data from Outscraper API
            
        Returns:
            List of scored reviews with authenticity scores
        """
        try:
            logger.info(f"Scoring {len(reviews_data)} reviews")
            scored_reviews = self.review_scorer.score_reviews(reviews_data)
            return scored_reviews
        except Exception as e:
            logger.error(f"Error scoring reviews: {e}")
            raise
    
    def process_reviews(self, 
                       query: str,
                       reviews_limit: int = 100,
                       sort: str = "most_relevant",
                       language: str = "en",
                       async_request: bool = True) -> Dict[str, Any]:
        """
        Complete process to fetch and score reviews
        
        Args:
            query: Search query for Google Maps place
            reviews_limit: Maximum number of reviews to fetch
            sort: Sort method for reviews
            language: Language code for reviews
            async_request: Whether to use async processing
            
        Returns:
            Dictionary with fetched and scored reviews
        """
        # Step 1: Fetch reviews from Outscraper
        fetch_response = self.fetch_reviews(
            query=query,
            reviews_limit=reviews_limit,
            sort=sort,
            language=language,
            async_request=async_request
        )
        
        # Step 2: Handle async vs sync response
        if async_request and fetch_response.get("status") == "pending":
            # Return the request ID for later checking
            return {
                "status": "pending",
                "request_id": fetch_response.get("request_id"),
                "message": "Review fetching in progress. Check status using the request ID."
            }
        
        # Step 3: For sync requests or completed async, get reviews
        if "data" in fetch_response and fetch_response["data"]:
            reviews_data = []
            for place_data in fetch_response["data"]:
                if "reviews_data" in place_data and place_data["reviews_data"]:
                    reviews_data.extend(place_data["reviews_data"])
            
            # Step 4: Score the reviews
            if reviews_data:
                scored_reviews = self.score_reviews(reviews_data)
                
                # Step 5: Calculate overall statistics
                total_reviews = len(scored_reviews)
                genuine_reviews = sum(1 for r in scored_reviews if r['review_score'] > 0)
                fake_reviews = total_reviews - genuine_reviews
                avg_score = sum(r['review_score'] for r in scored_reviews) / total_reviews if total_reviews > 0 else 0
                
                return {
                    "status": "completed",
                    "query": query,
                    "total_reviews": total_reviews,
                    "genuine_reviews": genuine_reviews,
                    "fake_reviews": fake_reviews,
                    "average_score": round(avg_score, 2),
                    "scored_reviews": scored_reviews
                }
            else:
                return {
                    "status": "completed",
                    "query": query,
                    "message": "No reviews found for this query.",
                    "scored_reviews": []
                }
        
        return {
            "status": "error",
            "message": "Failed to retrieve reviews.",
            "response": fetch_response
        }
