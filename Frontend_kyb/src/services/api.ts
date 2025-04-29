import axios from 'axios';

// Prioritize environment variables, with fallback to localhost for development
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/';

// Log the API base URL for debugging purposes
console.log('API Base URL:', BASE_URL);

const apiService = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable credentials for CORS if needed
  withCredentials: false
});

// Add response interceptor for debugging
apiService.interceptors.response.use(
  response => {
    console.log('API Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const searchEntities = async (query: string, entityType: string) => {
  try {
    console.log('Searching for:', query, 'Type:', entityType);
    const response = await apiService.get(`/api/scoring/search/?query=${encodeURIComponent(query)}&entity_type=${entityType}`);
    console.log('Search response:', response.data);
    // If the API returns results in a specific format, handle it here
    return response.data?.results || response.data;
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
};

export const getEntityScore = async (entityId: number, entityType: string, source: string) => {
  try {
    const response = await apiService.post('/api/scoring/score/', {
      entity_type: entityType,
      entity_id: entityId,
      source: source,
    });
    return response.data;
  } catch (error) {
    console.error('Score check failed:', error);
    throw error;
  }
};

export const getReviewScoring = async (query: string, reviewsLimit: number = 60) => {
  try {
    const response = await apiService.post('/api/scoring/review-scoring/', {
      query,
      reviews_limit: reviewsLimit,
      sort: "most_relevant",
      language: "en",
      async_request: false
    });
    console.log('Review scoring response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Review scoring failed:', error);
    throw error;
  }
};

export const customGoogleSearch = async (query: string, reviewsLimit: number = 100) => {
  try {
    console.log('Sending Google search request:', { query, reviewsLimit });
    const response = await apiService.post('/api/outscraper_reviews/custom-search/', {
      query,
      reviews_limit: reviewsLimit
    });
    
    console.log('Raw Custom Google search response:', response);
    
    // Just return the raw data and let the component handle the formatting
    return response.data;
  } catch (error) {
    console.error('Custom Google search failed:', error);
    throw error;
  }
};

export default apiService; 