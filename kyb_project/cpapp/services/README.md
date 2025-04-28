# Google Review Scoring System

A comprehensive system for analyzing Google reviews from businesses, detecting fake/spam reviews, and providing authenticity scores.

## Features

- **Fake Review Detection**: Identify potentially fake or spam reviews with negative scores (-10 to 0)
- **Review Quality Scoring**: Score genuine reviews on a scale of 1 to 10
- **Advanced Analysis**: Detect patterns, language similarities, time clustering, and suspicious author behavior
- **Sentiment Analysis**: Analyze the sentiment of reviews and detect mismatches with star ratings
- **Batch Processing**: Process multiple reviews together for contextual analysis
- **Business Trust Score**: Calculate overall trust scores for businesses based on review analysis

## Requirements

- Python 3.6+
- NLTK
- NumPy
- Outscraper API Key

## Installation

1. Ensure you have the required Python packages:

```bash
pip install nltk numpy requests
```

2. Set up your Outscraper API key:

```bash
# For Linux/Mac
export OUTSCRAPER_API_KEY="your-api-key-here"

# For Windows PowerShell
$env:OUTSCRAPER_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Usage

```python
from services.review_scorer_integration import ReviewAnalysisService

# Initialize the service
service = ReviewAnalysisService()

# Fetch and score reviews for a business
result = service.fetch_and_score_reviews(
    query="Apollo Hospital Bangalore",
    reviews_limit=50,
    sort="most_relevant",
    language="en"
)

# Print summary of scored results
for place in result.get("data", []):
    print(f"Place: {place.get('name')}")
    analysis = place.get("review_analysis", {})
    print(f"Average Score: {analysis.get('average_score')}")
    print(f"Trust Score: {analysis.get('trust_score')}")
    print(f"Fake Reviews: {analysis.get('fake_reviews_percentage')}%")
    print(f"Total Reviews: {analysis.get('review_count')}")
```

### Advanced Usage

For more detailed analysis, use the advanced scoring system:

```python
from services.review_scorer_integration import ReviewAnalysisService

# Initialize with advanced scoring
service = ReviewAnalysisService(use_advanced_scoring=True)

# Fetch and score reviews with advanced analysis
result = service.fetch_and_score_reviews(
    query="Apollo Hospital Bangalore",
    reviews_limit=50
)

# Print detailed classification breakdown
for place in result.get("data", []):
    analysis = place.get("review_analysis", {})
    
    print(f"Place: {place.get('name')}")
    print(f"Trust Score: {analysis.get('trust_score')}/10")
    
    if "classification_breakdown" in analysis:
        print("\nReview Classification Breakdown:")
        for classification, count in analysis["classification_breakdown"].items():
            print(f"  - {classification}: {count}")
        print(f"Average Sentiment: {analysis.get('average_sentiment')}")
    
    # Examine individual reviews
    for review in place.get("reviews", [])[:3]:  # Show first 3 reviews
        print(f"\nReview: {review.get('review_text')[:100]}...")
        print(f"Score: {review.get('review_score')}")
        print(f"Classification: {review.get('review_classification', 'N/A')}")
```

## Scoring Criteria

### Basic Scoring Factors:

- **Duplicate Detection**: Heavily penalizes reviews that appear multiple times
- **Generic Language**: Penalizes reviews with generic praise and little substance
- **Negative Keywords**: Identifies reviews mentioning fraud, scams, etc.
- **Review Recency**: Considers the age of reviews (older reviews get lower scores)
- **Content Quality**: Analyzes the substance and uniqueness of the review text

### Advanced Scoring Factors (Advanced Mode Only):

- **Sentiment Analysis**: Analyzes emotional tone of reviews
- **Suspicious Patterns**: Detects common patterns in fake reviews
- **Content Similarity**: Identifies reviews with similar content to other reviews
- **Time Clustering**: Detects groups of reviews posted within short time periods
- **Author Behavior**: Analyzes patterns in an author's review history

## Score Interpretation

- **-10 to -7**: Likely Fake Negative (probably fraudulent negative review)
- **-7 to 0**: Suspicious Negative (potentially fake or very poor quality)
- **0**: Old or Irrelevant Review
- **1 to 3**: Low Quality Genuine Review
- **4 to 6**: Average Genuine Review
- **7 to 10**: High Quality Genuine Review

## Trust Score

The Trust Score is a business-level metric (0-10) that indicates the overall trustworthiness of a business's reviews. It's calculated based on the proportion of genuine vs. fake reviews, with adjustments for review quality.

## Handling Asynchronous Requests

For large queries, the Outscraper API may process requests asynchronously:

```python
result = service.fetch_and_score_reviews(query="Large Business Chain")

if result.get("status") == "pending":
    request_id = result.get("request_id")
    print(f"Request is processing. Request ID: {request_id}")
    
    # Check back later
    import time
    time.sleep(30)
    
    # Retrieve results
    result = service.get_scored_results(request_id)
```

## Sample Implementation

See `example_usage.py` for a full example of using the review scoring system with interactive prompts and detailed results display.

## API Reference

### ReviewScorer (Basic)

The base scoring system using pattern matching and text analysis.

```python
from services.review_scoring_system import ReviewScorer

scorer = ReviewScorer()
scored_review = scorer.calculate_review_score(review_data)
```

### AdvancedReviewScorer

Enhanced scoring with sentiment analysis and contextual fraud detection.

```python
from services.advanced_review_scoring import AdvancedReviewScorer

scorer = AdvancedReviewScorer()
scored_reviews = scorer.score_reviews(reviews_list)
```

### ReviewAnalysisService

Integration with Outscraper API for retrieving and scoring Google reviews.

```python
from services.review_scorer_integration import ReviewAnalysisService

service = ReviewAnalysisService(api_key="your-api-key", use_advanced_scoring=True)
result = service.fetch_and_score_reviews(query="Business Name")
```

## Limitations

- Requires a valid Outscraper API key with sufficient credits
- Advanced NLP analysis requires NLTK resources to be downloaded
- For large batches of reviews, processing may take time
- Sentiment analysis works best with English language reviews 