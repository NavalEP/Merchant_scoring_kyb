import re
from typing import Dict, List, Any, Union, Optional
from datetime import datetime, timedelta
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK resources...")
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('stopwords')

# Adding this fix for punkt_tab resource issue
try:
    nltk.data.find('tokenizers/punkt/english.pickle')
except LookupError:
    logger.info("Downloading additional NLTK resources...")
    nltk.download('punkt')

class ReviewScorer:
    """
    A system to score Google reviews based on authenticity and content analysis.
    
    This system analyzes reviews to determine if they are:
    - Fake/spam (negative score: -10 to 0)
    - Genuine (positive score: 1 to 10)
    """
    
    def __init__(self):
        """Initialize the ReviewScorer with necessary parameters and dictionaries."""
        # Negative keywords that indicate a bad review
        self.negative_keywords = [
            'fraud', 'scam', 'cheat', 'cheater', 'bad doctor', 'terrible', 'worst', 
            'awful', 'rude', 'unprofessional', 'incompetent', 'money grabbing', 
            'corrupt', 'avoid', 'stay away', 'horrible', 'waste', 'regret', 'mistake',
            'useless', 'unqualified', 'illegal', 'dangerous', 'malpractice'
        ]
        
        # Generic phrases that might indicate fake reviews
        self.generic_phrases = [
            'best doctor', 'great service', 'highly recommend', 'excellent service',
            'very good', 'good experience', 'nice staff', 'friendly staff',
            'amazing experience', 'wonderful experience', 'highly recommended',
            'professional staff', 'highly professional', 'satisfied with the service',
            'great experience', 'good doctor', 'best service', 'very professional',
            'excellent doctor', 'excellent treatment', 'very helpful'
        ]
        
        # Get English stopwords
        self.stop_words = set(stopwords.words('english'))
        
        # Threshold for review recency (in months)
        self.recency_threshold = 6
        
        # Track seen review texts for duplicate detection
        self.seen_reviews = Counter()
        self.total_reviews = 0
        self.negative_keyword_prevalence = {}
        
    def detect_duplicates(self, review_text: str) -> bool:
        """Check if a review text appears multiple times, indicating potential fake reviews."""
        # Normalize text for comparison
        normalized_text = self._normalize_text(review_text)
        
        # Count this review
        self.seen_reviews[normalized_text] += 1
        
        # If we've seen this review more than once, it might be fake
        return self.seen_reviews[normalized_text] > 1
    
    def is_generic(self, review_text: str) -> float:
        """
        Determine how generic a review is based on phrase matching.
        Returns a score from 0.0 (not generic) to 1.0 (completely generic).
        """
        if not review_text:
            return 1.0  # Empty reviews are considered generic
            
        # Ensure review_text is a string
        review_text = str(review_text) if review_text is not None else ""
        review_lower = review_text.lower()
        generic_count = 0
        
        # Check for generic phrases
        for phrase in self.generic_phrases:
            if phrase.lower() in review_lower:
                generic_count += 1
                
        # Calculate generic score
        if generic_count == 0:
            return 0.0
        
        return min(generic_count / 5, 1.0)  # Cap at 1.0, consider 5+ matches as fully generic
    
    def has_negative_keywords(self, review_text: str) -> float:
        """
        Check if the review contains negative keywords.
        Returns a score from 0.0 (no negative keywords) to 1.0 (many negative keywords).
        """
        if not review_text:
            return 0.0
            
        # Ensure review_text is a string
        review_text = str(review_text) if review_text is not None else ""
        review_lower = review_text.lower()
        negative_count = 0
        common_found = False

        # Check for negative keywords and determine prevalence-based penalty
        for keyword in self.negative_keywords:
            if keyword.lower() in review_lower:
                negative_count += 1
                if self.total_reviews and self.negative_keyword_prevalence.get(keyword, 0) / self.total_reviews >= 0.25:
                    common_found = True

        if common_found:
            return 1.0

        if negative_count == 0:
            return 0.0

        return min(negative_count / 3, 1.0)
    
    def is_recent(self, review_timestamp: Union[int, str, None]) -> bool:
        """Check if the review is recent (within the recency threshold)."""
        if not review_timestamp:
            return False
            
        # Convert timestamp to datetime
        if isinstance(review_timestamp, int):
            review_date = datetime.fromtimestamp(review_timestamp)
        elif isinstance(review_timestamp, str):
            try:
                # Try to parse as "MM/DD/YYYY HH:MM:SS" format
                review_date = datetime.strptime(review_timestamp, "%m/%d/%Y %H:%M:%S")
            except ValueError:
                logger.warning(f"Could not parse timestamp: {review_timestamp}")
                return False
        else:
            logger.warning(f"Unknown timestamp format: {review_timestamp}")
            return False
            
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=30 * self.recency_threshold)
        
        return review_date >= cutoff_date
    
    def analyze_content_quality(self, review_text: str) -> float:
        """
        Analyze the quality of the review content.
        Returns a score from 0.0 (poor quality) to 1.0 (high quality).
        """
        if not review_text:
            return 0.0
        
        # Ensure review_text is a string
        review_text = str(review_text) if review_text is not None else ""
            
        try:
            # Tokenize the review
            words = word_tokenize(review_text.lower())
            
            # Remove stopwords
            meaningful_words = [word for word in words if word not in self.stop_words and word.isalpha()]
            
            # Check word count
            if len(meaningful_words) < 3:
                return 0.0
                
            # Unique word ratio (diversity of vocabulary)
            unique_ratio = len(set(meaningful_words)) / max(len(meaningful_words), 1)
            
            # Length score (longer reviews with more substance get higher scores)
            length_score = min(len(meaningful_words) / 20, 1.0)  # Cap at 1.0 for reviews with 20+ meaningful words
            
            # NEW: Check for specific details that indicate authenticity
            specificity_indicators = [
                r'\b(?:on|in|at|during)\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',  # Dates/days
                r'\b(?:morning|afternoon|evening|night|today|yesterday|last\s+week|last\s+month|last\s+year)\b',  # Time references
                r'\b(?:room|office|building|floor|desk|chair|waiting\s+area|lobby|bathroom)\b',  # Location details
                r'\b(?:doctor|nurse|staff|receptionist|assistant|technician)\s+(?:\w+)\b',  # Staff references with specifics
                r'\b(?:procedure|treatment|surgery|appointment|consultation|check-up|test|diagnosis|prescription|medication)\b',  # Medical terms
                r'\b(?:\d+(?::\d+)?)\s*(?:am|pm|hour|minute|second)\b',  # Specific times
                r'\$\d+(?:\.\d+)?|\d+\s+dollars',  # Cost mentions
            ]
            
            specificity_score = 0.0
            review_text_lower = review_text.lower()
            for pattern in specificity_indicators:
                if re.search(pattern, review_text_lower, re.IGNORECASE):
                    specificity_score += 0.15
            specificity_score = min(specificity_score, 1.0)  # Cap at 1.0
            
            # NEW: Check for emotional language and personal experience markers
            emotional_markers = [
                r'\b(?:i|we|my|our)\b',  # First-person pronouns
                r'\b(?:feel|felt|feeling|experienced|noticed|saw|heard|thought)\b',  # Experiential verbs
                r'\b(?:happy|satisfied|pleased|impressed|disappointed|frustrated|angry|upset|worried|concerned)\b',  # Emotional states
                r'\b(?:thanks|thank\s+you|grateful|appreciate|appreciated|helped|recommend|recommended)\b',  # Gratitude/recommendation
                r'[!?]',  # Exclamation or question marks
            ]
            
            emotional_score = 0.0
            for pattern in emotional_markers:
                if re.search(pattern, review_text_lower, re.IGNORECASE):
                    emotional_score += 0.15
            emotional_score = min(emotional_score, 1.0)  # Cap at 1.0
            
            # NEW: Check for coherence and flow (basic implementation)
            sentences = re.split(r'[.!?]+', review_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            coherence_score = 0.0
            if len(sentences) >= 2:
                # More sentences suggest a more detailed, coherent review
                coherence_score = min(len(sentences) / 5, 1.0)
            
            # Combine scores with weights
            quality_score = (
                (unique_ratio * 0.2) + 
                (length_score * 0.2) + 
                (specificity_score * 0.3) + 
                (emotional_score * 0.2) + 
                (coherence_score * 0.1)
            )
            
            return quality_score
        except Exception as e:
            # Fallback tokenization if NLTK's tokenizer fails
            logger.warning(f"Error in tokenization: {str(e)}. Using fallback method.")
            
            # Simple fallback tokenization by splitting on whitespace
            words = review_text.lower().split()
            
            # Basic cleaning and stopword removal
            meaningful_words = [word for word in words 
                               if word not in self.stop_words 
                               and word.isalpha() 
                               and len(word) > 2]
            
            if len(meaningful_words) < 3:
                return 0.0
                
            unique_ratio = len(set(meaningful_words)) / max(len(meaningful_words), 1)
            length_score = min(len(meaningful_words) / 20, 1.0)
            
            # Simplified scoring for fallback method
            quality_score = (unique_ratio * 0.5) + (length_score * 0.5)
            
            return quality_score
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison purposes."""
        if not text:
            return ""
            
        # Ensure text is a string
        text = str(text) if text is not None else ""
            
        # Remove punctuation, convert to lowercase, and remove extra whitespace
        normalized = re.sub(r'[^\w\s]', '', text.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_review_score(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a score for a review based on various factors.
        Returns the original review data with added scoring information.
        
        Scoring range:
        - Fake/spam reviews: -10 to 0
        - Genuine reviews: 1 to 10
        """
        review_text = review_data.get('review_text', '')
        review_timestamp = review_data.get('review_timestamp') or review_data.get('review_datetime_utc')
        
        # Initialize scoring factors
        is_duplicate = self.detect_duplicates(review_text)
        generic_score = self.is_generic(review_text)
        negative_score = self.has_negative_keywords(review_text)
        is_recent = self.is_recent(review_timestamp)
        content_quality = self.analyze_content_quality(review_text)
        
        # Start with a neutral base score
        final_score = 5.0
        
        # Apply negative factors first
        if is_duplicate:
            # Heavily penalize duplicates
            final_score -= 10
        else:
            # Apply generic penalty (up to -5 points)
            final_score -= generic_score * 5
            
            # Apply recency check
            if not is_recent:
                final_score -= 3  # Penalty for older reviews, but not an automatic zero
                
            # Apply negative keywords (up to -10 points for highly negative reviews)
            if negative_score > 0:
                final_score = -negative_score * 10
            else:
                # NEW: Enhanced content quality scoring
                # High quality content can significantly boost the score (up to +5 points)
                quality_boost = content_quality * 5
                
                # Extra boost for very high quality reviews that have specific details
                if content_quality > 0.7:
                    quality_boost += 2
                
                final_score += quality_boost
                
        # Ensure final score is within bounds
        if final_score > 0:
            # Genuine reviews: 1 to 10
            final_score = max(1, min(10, final_score))
        else:
            # Fake or negative reviews: -10 to 0
            final_score = max(-10, min(0, final_score))
            
        # Round to one decimal place
        final_score = round(final_score, 1)
        
        # Add scoring information to the review data
        scored_review = review_data.copy()
        scored_review['review_score'] = final_score
        scored_review['scoring_factors'] = {
            'is_duplicate': is_duplicate,
            'generic_score': round(generic_score, 2),
            'negative_score': round(negative_score, 2),
            'is_recent': is_recent,
            'content_quality': round(content_quality, 2)
        }
        
        return scored_review
    
    def score_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score a list of reviews."""
        # Reset the seen reviews counter for a fresh batch
        self.seen_reviews = Counter()
        
        # Precompute negative keyword prevalence across reviews
        total_reviews = len(reviews)
        prevalence = {}
        for review in reviews:
            review_text = review.get('review_text', '')
            # Ensure review_text is a string
            review_text = str(review_text) if review_text is not None else ""
            review_text_lower = review_text.lower()
            for keyword in self.negative_keywords:
                if keyword.lower() in review_text_lower:
                    prevalence[keyword] = prevalence.get(keyword, 0) + 1
        self.total_reviews = total_reviews
        self.negative_keyword_prevalence = prevalence
        
        # NEW: Check if there is any review in the batch that is recent
        any_recent = any(self.is_recent(review.get('review_timestamp') or review.get('review_datetime_utc')) for review in reviews)
        
        scored_reviews = []
        for review in reviews:
            scored_review = self.calculate_review_score(review)
            if not any_recent:
                # If no review in the batch is recent, mark as red flag
                scored_review['review_score'] = -10
                scored_review.setdefault('scoring_factors', {})['global_recency'] = False
            else:
                scored_review.setdefault('scoring_factors', {})['global_recency'] = True
            scored_reviews.append(scored_review)
            
        return scored_reviews


