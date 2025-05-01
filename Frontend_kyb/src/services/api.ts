import axios from 'axios';
import { AxiosError } from 'axios';

// Prioritize environment variables, with fallback to localhost for development
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export const getReviewScoring = async (query: string, reviewsLimit: number = 100) => {
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
    console.log('Using API base URL:', BASE_URL);
    
    // Ensure the reviews_limit parameter is correctly named to match backend expectations
    const requestData = {
      query,
      reviews_limit: reviewsLimit
    };
    
    console.log('Request payload:', requestData);
    
    const response = await apiService.post('/api/outscraper_reviews/custom-search/', requestData);
    
    console.log('Raw Custom Google search response:', response);
    
    // Just return the raw data and let the component handle the formatting
    return response.data;
  } catch (error: unknown) {
    // More detailed error logging
    console.error('Custom Google search failed:', error);
    
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      if (axiosError.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error('Error status:', axiosError.response.status);
        console.error('Error data:', axiosError.response.data);
        console.error('Error headers:', axiosError.response.headers);
      } else if (axiosError.request) {
        // The request was made but no response was received
        console.error('No response received:', axiosError.request);
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Error message:', axiosError.message);
      }
    } else {
      console.error('Unexpected error:', error);
    }
    
    throw error;
  }
};

export default apiService; 