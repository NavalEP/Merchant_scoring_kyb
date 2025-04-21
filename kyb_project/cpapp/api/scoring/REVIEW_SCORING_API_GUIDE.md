# Review Scoring API Guide

This guide explains how to use the Review Scoring API with Postman to test the Google review scoring system.

## API Endpoints

The Review Scoring API has three main endpoints:

1. **Review Scoring** - Submit a query to fetch and score Google reviews
2. **Check Status** - Check the status of an asynchronous request
3. **Submit Feedback** - Provide feedback on review scoring results

## Prerequisites

- Postman installed on your computer
- Outscraper API key (set as an environment variable in your server)
- Your backend server running (typically on `http://localhost:8000` or similar URL)

## Testing with Postman

### 1. Scoring Reviews

#### Endpoint: `/api/scoring/review-scoring/`

#### Method: POST

#### Headers:
- Content-Type: application/json

#### Request Body:
```json
{
  "query": "Apollo Hospital Bangalore",
  "reviews_limit": 20,
  "sort": "most_relevant",
  "language": "en",
  "async_request": true
}
```

#### Parameters:

- `query` (required): Search query or specific place name to fetch reviews for
- `reviews_limit` (optional): Maximum number of reviews to fetch per place (default: 20)
- `sort` (optional): Sorting method for reviews (options: "most_relevant", "newest", "highest_rating", "lowest_rating")
- `language` (optional): Language code for results (default: "en")
- `async_request` (optional): Whether to use asynchronous request processing (default: true)

#### Response (Async Request):
```json
{
  "status": "pending",
  "request_id": "abc123xyz456",
  "message": "Reviews are being fetched asynchronously. Use get_scored_results to retrieve them later."
}
```

#### Response (Sync Request or Completed Async):
```json
{
  "data": [
    {
      "name": "Apollo Hospital",
      "address": "123 Main St, Bangalore",
      "reviews": [
        {
          "review_id": "ABC123",
          "author_title": "John Doe",
          "review_text": "Great hospital with excellent doctors.",
          "review_rating": 5,
          "review_timestamp": 1731695928,
          "review_score": 8.5,
          "scoring_factors": {
            "is_duplicate": false,
            "generic_score": 0.4,
            "negative_score": 0.0,
            "is_recent": true,
            "content_quality": 0.65
          }
        },
        // More reviews...
      ],
      "review_analysis": {
        "average_score": 7.2,
        "review_count": 20,
        "fake_reviews_count": 2,
        "fake_reviews_percentage": 10.0,
        "trust_score": 9.0
      }
    }
  ],
  "scoring_info": {
    "scoring_system": "ReviewScorer v1.0",
    "score_range": {
      "fake_reviews": "-10 to 0",
      "genuine_reviews": "1 to 10"
    }
  }
}
```

#### Using GET Method (Alternative)

You can also use the GET method with query parameters:

```
GET /api/scoring/review-scoring/?query=Apollo%20Hospital%20Bangalore&reviews_limit=20&sort=most_relevant&language=en&async_request=true
```

### 2. Checking Status of Async Request

#### Endpoint: `/api/scoring/review-status/`

#### Method: POST

#### Headers:
- Content-Type: application/json

#### Request Body:
```json
{
  "request_id": "abc123xyz456"
}
```

#### Parameters:
- `request_id` (required): ID of the previously submitted request

#### Response (Still Processing):
```json
{
  "status": "pending",
  "message": "The request is still processing. Please try again later."
}
```

#### Response (Completed):
Same as the completed response for the review scoring endpoint.

#### Using GET Method (Alternative)

You can also use the GET method with query parameters:

```
GET /api/scoring/review-status/?request_id=abc123xyz456
```

### 3. Providing Feedback on Review Scoring

#### Endpoint: `/api/scoring/review-feedback/`

#### Method: POST

#### Headers:
- Content-Type: application/json

#### Request Body:
```json
{
  "review_id": "ABC123",
  "is_correct": false,
  "feedback_type": "score_too_low",
  "comments": "This review seems legitimate but got a low score."
}
```

#### Parameters:
- `review_id` (required): ID of the review
- `is_correct` (required): Whether the review scoring was correct
- `feedback_type` (required): Type of feedback (options: "false_positive", "false_negative", "score_too_high", "score_too_low", "other")
- `comments` (optional): Additional comments

#### Response:
```json
{
  "status": "success",
  "message": "Feedback received successfully",
  "feedback": {
    "review_id": "ABC123",
    "is_correct": false,
    "feedback_type": "score_too_low",
    "comments": "This review seems legitimate but got a low score.",
    "timestamp": "2023-11-15T18:30:00.000000Z"
  }
}
```

## Understanding the Response

### Review Score Interpretation

- **-10 to 0**: Fake or spam reviews (more negative = more likely to be fake)
- **1 to 10**: Genuine reviews (higher score = higher quality and reliability)

### Scoring Factors

- **is_duplicate**: Whether this review text has been seen before
- **generic_score**: How generic/template-like the review is (0-1)
- **negative_score**: Whether it contains negative keywords like "fraud" (0-1)
- **is_recent**: Whether the review is recent (within last 6 months)
- **content_quality**: Analysis of text quality and substance (0-1)

### Business-Level Metrics

- **average_score**: Average score of all reviews
- **fake_reviews_count**: Number of reviews with negative scores
- **fake_reviews_percentage**: Percentage of reviews that are likely fake
- **trust_score**: Overall trustworthiness score for the business (0-10)

## Common Issues

1. **API Key Not Found**: Ensure the OUTSCRAPER_API_KEY environment variable is set on your server
2. **Empty Results**: Check if the query is specific enough to find the right business
3. **Request Timeout**: For businesses with many reviews, use async_request=true and check status later

## Example Postman Workflow

1. Create a new request in Postman pointing to your backend server
2. Set up a POST request to `/api/scoring/review-scoring/`
3. Add the JSON body with your query (e.g., a clinic or doctor name)
4. Submit the request
5. If you get a request_id, use the status endpoint to check for results
6. Examine the scored results to identify fake or suspicious reviews

## Postman Collection

You can import the following collection into Postman to get started quickly:

```json
{
  "info": {
    "name": "Review Scoring API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Score Reviews",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"Apollo Hospital Bangalore\",\n  \"reviews_limit\": 20,\n  \"sort\": \"most_relevant\",\n  \"language\": \"en\",\n  \"async_request\": true\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/scoring/review-scoring/",
          "host": ["{{base_url}}"],
          "path": ["api", "scoring", "review-scoring", ""]
        }
      }
    },
    {
      "name": "Check Status",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"request_id\": \"your_request_id_here\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/scoring/review-status/",
          "host": ["{{base_url}}"],
          "path": ["api", "scoring", "review-status", ""]
        }
      }
    },
    {
      "name": "Submit Feedback",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"review_id\": \"ABC123\",\n  \"is_correct\": false,\n  \"feedback_type\": \"score_too_low\",\n  \"comments\": \"This review seems legitimate but got a low score.\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/scoring/review-feedback/",
          "host": ["{{base_url}}"],
          "path": ["api", "scoring", "review-feedback", ""]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    }
  ]
}
``` 