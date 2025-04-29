import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Building2, User, Guitar as Hospital, Star, Globe, Stethoscope, ChevronDown, ChevronUp } from 'lucide-react';
import { searchEntities, getEntityScore, getReviewScoring, customGoogleSearch } from './services/api';

interface SearchResult {
  entity_id: number;
  id?: number;
  name: string;
  entity_type: string;
  source: string;
  speciality?: string;
  location?: string;
  rating?: string;
  experience?: string;
  qualification?: string;
}

interface ScoreResponse {
  entity_type: string;
  entity_id: number;
  source: string;
  name: string;
  total_score: number;
  risk_category: string;
  score_breakdown: {
    qualification_score: number;
    experience_score: number;
    rating_score: number;
    weighted_rating_score: number;
    location_score: number;
    specialization_score: number;
    license_score: number;
    license_verified: boolean;
    normalized_qualification_score: number;
    normalized_experience_score: number;
    normalized_rating_score: number;
    normalized_weighted_rating_score: number;
    normalized_location_score: number;
    normalized_specialization_score: number;
    normalized_license_score: number;
    rating_count?: string;
  };
}

interface ReviewScoringResponse {
  status: string;
  query: string;
  total_reviews: number;
  genuine_reviews: number;
  fake_reviews: number;
  average_score: number;
  scored_reviews?: Array<{
    review_rating: number;
    review_text: string;
    author_title: string;
    review_score: number;
  }>;
}

interface GoogleReviewResult {
  // Original properties
  name?: string;
  address?: string;
  place_id?: string;
  cid?: string;
  rating?: number;
  reviews_count?: number;
  reviews?: Array<{
    text?: string;
    rating?: number;
    date?: string;
    likes?: number;
    author_name?: string;
    author_id?: string;
  }>;
  
  // Alternative property names in different response formats
  place_name?: string;
  full_address?: string;
  stars?: number;
  reviews_number?: number;
  reviews_data?: Array<{
    review_text?: string;
    review_rating?: number;
    review_datetime_utc?: string;
    name?: string;
    author_name?: string;
    [key: string]: any;
  }>;
  [key: string]: any; // Allow any other properties
}

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInputValue, setSearchInputValue] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('doctor');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [reviewsLimit, setReviewsLimit] = useState(60);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<SearchResult | null>(null);
  // Custom Google search state
  const [showGoogleSearch, setShowGoogleSearch] = useState(false);
  const [googleSearchQuery, setGoogleSearchQuery] = useState('');
  const [googleReviewsLimit, setGoogleReviewsLimit] = useState(100);
  const [googleResults, setGoogleResults] = useState<GoogleReviewResult[]>([]);
  const [isGoogleSearchLoading, setIsGoogleSearchLoading] = useState(false);

  const categories = [
    { id: 'doctor', label: 'Doctor', icon: User },
    { id: 'clinic', label: 'Clinic', icon: Hospital },
    { id: 'city', label: 'City', icon: Building2 },
    { id: 'speciality', label: 'Speciality', icon: Stethoscope },
  ];

  // Add debouncing for search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchQuery(searchInputValue);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInputValue]);

  // Update search query when debounced value changes
  useEffect(() => {
    setSearchQuery(debouncedSearchQuery);
  }, [debouncedSearchQuery]);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchInputValue(e.target.value);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const data = await searchEntities(searchQuery, selectedCategory);
      console.log('Search API response:', data);
      if (Array.isArray(data)) {
        setSearchResults(data);
      } else if (data && typeof data === 'object') {
        // If API returns data in a different format, try to extract the array
        const resultsArray = data.results || data.data || [];
        console.log('Extracted results array:', resultsArray);
        setSearchResults(resultsArray);
      } else {
        console.error('Unexpected API response format:', data);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    }
    setIsLoading(false);
  };

  const checkScore = async (entityId: number, entityType: string, source: string) => {
    try {
      const data = await getEntityScore(entityId, entityType, source);
      setScoreData(data);
    } catch (error) {
      console.error('Score check failed:', error);
    }
  };

  const viewDoctorDetails = (doctor: SearchResult) => {
    setSelectedDoctor(doctor);
  };

  // Updated custom Google search function
  const handleCustomGoogleSearch = async () => {
    if (!googleSearchQuery.trim()) return;
    
    setIsGoogleSearchLoading(true);
    // Don't clear google results immediately to prevent UI flashing
    
    try {
      console.log('Sending Google search request:', { query: googleSearchQuery, reviewsLimit: googleReviewsLimit });
      const data = await customGoogleSearch(googleSearchQuery, googleReviewsLimit);
      console.log('Raw Custom Google search response:', data);
      
      // Process the response data through our normalizer
      const processedResults = extractReviewsData(data);
      
      if (processedResults.length > 0) {
        console.log('Processed results:', processedResults);
        setGoogleResults(processedResults);
      } else {
        console.error('No results could be extracted from the response:', data);
        setGoogleResults([]);
      }
    } catch (error) {
      console.error('Custom Google search failed:', error);
      setGoogleResults([]);
    } finally {
      setIsGoogleSearchLoading(false);
    }
  };
  
  // Helper function to extract review data from different response formats
  const extractReviewsData = (data: any): GoogleReviewResult[] => {
    console.log('Extracting review data from:', data);
    
    // If data is already an array, check if it has the expected format
    if (Array.isArray(data)) {
      // Verify if array contains items that match our interface
      if (data.length > 0 && (data[0].name || data[0].place_name)) {
        return data.map(normalizeReviewItem);
      }
    }
    
    // Try different paths where the data might be
    if (data.data && Array.isArray(data.data)) {
      return data.data.map(normalizeReviewItem);
    } else if (data.results && Array.isArray(data.results)) {
      return data.results.map(normalizeReviewItem);
    } else if (data.response && data.response.data && Array.isArray(data.response.data)) {
      return data.response.data.map(normalizeReviewItem);
    }
    
    // If we have a single result object
    if ((data.name || data.place_name) && (data.reviews || data.reviews_data)) {
      return [normalizeReviewItem(data)];
    }
    
    // Last resort: look for any array property that might contain our data
    for (const key in data) {
      if (Array.isArray(data[key]) && data[key].length > 0) {
        // Check if array items look like review results
        const items = data[key];
        const sample = items[0];
        if (sample && (sample.name || sample.place_name)) {
          return items.map(normalizeReviewItem);
        }
      }
    }
    
    // If we can't find any obvious array, attempt to wrap the entire data object
    // if it has some properties we expect
    if (data && typeof data === 'object' && (data.name || data.place_name || data.address || data.rating)) {
      return [normalizeReviewItem(data)];
    }
    
    console.error('Could not extract any review data from response');
    return [];
  };
  
  // Helper function to normalize a review item to our interface
  const normalizeReviewItem = (item: any): GoogleReviewResult => {
    // Make a copy to avoid mutating the original
    const result: GoogleReviewResult = { ...item };
    
    // Normalize the main fields
    result.name = item.name || item.place_name || "Unknown Place";
    result.address = item.address || item.full_address || "";
    result.rating = parseFloat(String(item.rating || item.stars || 0));
    result.reviews_count = parseInt(String(item.reviews_count || item.reviews_number || 
      (item.reviews ? item.reviews.length : 0) || 
      (item.reviews_data ? item.reviews_data.length : 0) || 0));
    
    // Normalize the reviews array
    if (item.reviews_data && Array.isArray(item.reviews_data)) {
      result.reviews = item.reviews_data.map((review: any) => ({
        text: review.review_text || review.text || "",
        rating: parseFloat(String(review.review_rating || review.rating || 0)),
        date: review.review_datetime_utc || review.date || "",
        author_name: review.author_name || review.name || "Anonymous"
      }));
    } else if (item.reviews && Array.isArray(item.reviews)) {
      result.reviews = item.reviews.map((review: any) => ({
        text: review.text || review.review_text || "",
        rating: parseFloat(String(review.rating || review.review_rating || 0)),
        date: review.date || review.review_datetime_utc || "",
        author_name: review.author_name || review.name || "Anonymous"
      }));
    } else {
      result.reviews = [];
    }
    
    return result;
  };

  // Component for the Google review search
  const GoogleSearchComponent = () => {
    const [localGoogleSearchQuery, setLocalGoogleSearchQuery] = useState(googleSearchQuery);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [localReviewScoring, setLocalReviewScoring] = useState<ReviewScoringResponse | null>(null);
    const [localReviewsLimit, setLocalReviewsLimit] = useState(googleReviewsLimit);
    
    const handleGoogleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setLocalGoogleSearchQuery(e.target.value);
    };
    
    const handleReviewsLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      // Parse the input value as an integer
      const value = e.target.value === '' ? '' : e.target.value;
      setLocalReviewsLimit(value === '' ? 0 : parseInt(value, 10));
    };
    
    const handleGoogleSearchSubmit = () => {
      setGoogleSearchQuery(localGoogleSearchQuery);
      setGoogleReviewsLimit(localReviewsLimit);
      handleCustomGoogleSearch();
    };
    
    const handleAnalyzeReviews = async () => {
      if (!localGoogleSearchQuery.trim()) return;
      
      setIsAnalyzing(true);
      setLocalReviewScoring(null);
      try {
        const data = await getReviewScoring(localGoogleSearchQuery, localReviewsLimit);
        setLocalReviewScoring(data);
      } catch (error) {
        console.error('Review scoring analysis failed:', error);
      } finally {
        setIsAnalyzing(false);
      }
    };
    
    // Update local state when parent state changes
    useEffect(() => {
      setLocalGoogleSearchQuery(googleSearchQuery);
    }, [googleSearchQuery]);
    
    useEffect(() => {
      setLocalReviewsLimit(googleReviewsLimit);
    }, [googleReviewsLimit]);
    
    // Component to display review analysis results
    const ReviewAnalysisResults = () => {
      if (!localReviewScoring) return null;
      
      const { query, status, average_score, total_reviews, genuine_reviews, fake_reviews } = localReviewScoring;
      const fakePercentage = total_reviews > 0 ? (fake_reviews / total_reviews) * 100 : 0;
      
      return (
        <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h3 className="text-lg font-semibold mb-3">Review Analysis for "{query}"</h3>
          
          <div className="bg-blue-50 p-4 rounded-lg mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">Status:</span>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">{status}</span>
            </div>
            
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">Average Score:</span>
              <span className="text-yellow-500 font-bold">★ {average_score.toFixed(1)}</span>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="border rounded-lg p-3 text-center">
              <div className="text-lg font-bold">{total_reviews}</div>
              <div className="text-sm text-gray-600">Total Reviews</div>
            </div>
            
            <div className="border rounded-lg p-3 text-center bg-green-50">
              <div className="text-lg font-bold text-green-600">{genuine_reviews}</div>
              <div className="text-sm text-gray-600">Genuine Reviews</div>
            </div>
            
            <div className="border rounded-lg p-3 text-center bg-red-50">
              <div className="text-lg font-bold text-red-600">{fake_reviews}</div>
              <div className="text-sm text-gray-600">Fake Reviews</div>
            </div>
          </div>
          
          {fake_reviews > 0 && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm font-medium">
                Warning: {fakePercentage.toFixed(1)}% of reviews appear to be fake.
              </p>
            </div>
          )}
          
          {localReviewScoring.scored_reviews && localReviewScoring.scored_reviews.length > 0 && (
            <>
              <h4 className="font-medium mb-2">Sample Analyzed Reviews:</h4>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {localReviewScoring.scored_reviews.slice(0, 3).map((review, idx) => (
                  <div key={idx} className={`p-3 rounded ${review.review_score >= 0.5 ? 'bg-green-50' : 'bg-red-50'}`}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">{review.author_title || 'Anonymous'}</span>
                      <div className="flex items-center">
                        <Star className="h-4 w-4 text-yellow-500 mr-1" />
                        <span>{review.review_rating}</span>
                        <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                          review.review_score >= 0.5 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {review.review_score >= 0.5 ? 'Genuine' : 'Suspicious'}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700">{review.review_text}</p>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      );
    };
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Globe className="h-5 w-5 text-blue-600" />
          Google Reviews Search
        </h2>
        
        <div className="mb-4">
          <label htmlFor="googleSearch" className="block text-sm font-medium text-gray-700 mb-1">
            Search for place/business:
          </label>
          <div className="flex gap-4">
            <input
              id="googleSearch"
              type="text"
              value={localGoogleSearchQuery}
              onChange={handleGoogleSearchInputChange}
              placeholder="Search for restaurants, hotels, businesses..."
              className="flex-1 pl-3 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleGoogleSearchSubmit();
                }
              }}
            />
          </div>
        </div>
        
        <div className="mb-4">
          <label htmlFor="reviewsCount" className="block text-sm font-medium text-gray-700 mb-1">
            Number of reviews to fetch:
          </label>
          <div className="w-1/3">
            <input
              id="reviewsCount"
              type="number"
              min="1"
              max="500"
              value={localReviewsLimit}
              onChange={handleReviewsLimitChange}
              className="w-full pl-3 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="flex gap-4">
          <button
            onClick={handleGoogleSearchSubmit}
            disabled={isGoogleSearchLoading || !localGoogleSearchQuery.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 flex items-center"
          >
            {isGoogleSearchLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Search Google Reviews
              </>
            )}
          </button>
          
          <button
            onClick={handleAnalyzeReviews}
            disabled={isAnalyzing || !localGoogleSearchQuery.trim()}
            className="px-6 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 disabled:opacity-50 flex items-center"
          >
            {isAnalyzing ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </>
            ) : (
              <>
                <Star className="h-4 w-4 mr-2" />
                Analyze Reviews
              </>
            )}
          </button>
        </div>
        
        {/* Display analysis loading state */}
        {isAnalyzing && (
          <div className="mt-6 bg-gray-50 rounded-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
              <div className="h-4 bg-gray-200 rounded w-4/6"></div>
            </div>
          </div>
        )}
        
        {/* Display review analysis results */}
        {!isAnalyzing && <ReviewAnalysisResults />}
      </div>
    );
  };

  // Component to display Google review results or loading state
  const GoogleReviewResults = () => {
    // Show loading state when search is in progress
    if (isGoogleSearchLoading) {
      return (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">Searching...</h2>
          <div className="animate-pulse space-y-4">
            {[1, 2].map((i) => (
              <div key={i} className="border-b border-gray-200 pb-4 mb-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                  <div className="h-6 bg-gray-200 rounded w-1/6"></div>
                </div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
                
                <div className="space-y-3">
                  {[1, 2, 3].map((j) => (
                    <div key={j} className="bg-gray-50 p-3 rounded">
                      <div className="flex justify-between mb-2">
                        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/12"></div>
                      </div>
                      <div className="h-3 bg-gray-200 rounded w-full mb-1"></div>
                      <div className="h-3 bg-gray-200 rounded w-full mb-1"></div>
                      <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }
    
    // Return empty if no results
    if (googleResults.length === 0) return null;
    
    // Track which result has expanded reviews
    const [expandedReviewIndex, setExpandedReviewIndex] = useState<number | null>(null);
    
    // Create refs for each result item
    const resultRefs = useRef<(HTMLDivElement | null)[]>([]);
    
    // Toggle expanded reviews for a result
    const toggleExpandedReviews = (index: number) => {
      const wasExpanded = expandedReviewIndex === index;
      setExpandedReviewIndex(wasExpanded ? null : index);
      
      // If expanding, scroll to the element after state update
      if (!wasExpanded) {
        setTimeout(() => {
          resultRefs.current[index]?.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }, 100);
      }
    };
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Search Results</h2>
        
        {googleResults.map((result, index) => {
          // Determine if this result has expanded reviews
          const isExpanded = expandedReviewIndex === index;
          // Number of reviews to show
          const reviewsToShow = isExpanded ? result.reviews?.length || 0 : 3;
          
          return (
            <div 
              key={index} 
              ref={(el) => resultRefs.current[index] = el}
              className={`border-b border-gray-200 pb-4 mb-4 last:border-0 last:mb-0 last:pb-0 ${
                isExpanded ? 'bg-blue-50 p-4 rounded-lg -mx-2 transition-colors duration-300 ease-in-out' : ''
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">{result.name}</h3>
                <div className="flex items-center">
                  <Star className="h-5 w-5 text-yellow-500 mr-1" />
                  <span className="font-medium">{(result.rating || 0).toFixed(1)}</span>
                  <span className="text-gray-500 ml-1">({result.reviews_count || 0} reviews)</span>
                </div>
              </div>
              <p className="text-gray-600 mb-3">{result.address}</p>
              
              {result.reviews && result.reviews.length > 0 ? (
                <>
                  <h4 className="font-medium mb-2">Latest Reviews:</h4>
                  <div className="space-y-3">
                    {result.reviews.slice(0, reviewsToShow).map((review, reviewIndex) => {
                      // Show full text in expanded view, otherwise truncate
                      const shouldTruncate = !isExpanded && review.text && review.text.length > 200;
                      const displayText = shouldTruncate 
                        ? `${review.text?.substring(0, 200) || ''}...` 
                        : review.text || '';
                      
                      return (
                        <div 
                          key={reviewIndex} 
                          className="bg-gray-50 p-3 rounded transition-all duration-200 ease-in-out hover:bg-gray-100"
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-medium">{review.author_name}</span>
                            <div className="flex items-center">
                              <Star className="h-4 w-4 text-yellow-500 mr-1" />
                              <span>{review.rating}</span>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700">{displayText}</p>
                          <p className="text-xs text-gray-500 mt-1">{review.date}</p>
                        </div>
                      );
                    })}
                    {result.reviews.length > 3 && (
                      <button 
                        onClick={() => toggleExpandedReviews(index)}
                        className="text-sm text-blue-600 cursor-pointer hover:underline flex items-center mt-2 transition-colors duration-200 ease-in-out"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-4 h-4 mr-1" />
                            <span>Show less</span>
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-4 h-4 mr-1" />
                            <span>View more reviews</span>
                            <span className="ml-1 bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded-full">
                              {result.reviews.length - 3}
                            </span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-gray-500 italic">No reviews available</p>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  value={searchInputValue}
                  onChange={handleSearchInputChange}
                  placeholder="Search..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
            </div>
            <button
              onClick={handleSearch}
              disabled={isLoading || !searchQuery.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div className="flex gap-4 mb-6">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                    selectedCategory === category.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  {category.label}
                </button>
              );
            })}
          </div>
          
          <div className="flex justify-between mt-4">
            <button
              onClick={() => setShowGoogleSearch(!showGoogleSearch)}
              className="flex items-center gap-2 px-4 py-2 text-blue-600 border border-blue-200 rounded-lg hover:bg-blue-50"
            >
              <Globe className="h-5 w-5" />
              {showGoogleSearch ? 'Hide Google Search' : 'Search Google Reviews'}
            </button>
          </div>
        </div>
        
        {/* Google Review Search Section */}
        {showGoogleSearch && <div id="googleSearchSection"><GoogleSearchComponent /></div>}
        {showGoogleSearch && <GoogleReviewResults />}

        {searchResults.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/5">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/6">
                    Speciality
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/5">
                    Location
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/12">
                    Rating
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/12">
                    Source
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {searchResults.map((result, index) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <button 
                        onClick={() => viewDoctorDetails(result)}
                        className="text-blue-600 hover:underline text-left"
                      >
                        {result.name}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {result.speciality || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 truncate max-w-xs">
                      {result.location || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {result.rating ? `★ ${result.rating}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 capitalize">
                      {result.source || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => checkScore(result.id || result.entity_id, result.entity_type || selectedCategory, result.source)}
                          className="inline-flex items-center px-3 py-1 bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200"
                        >
                          <Star className="h-4 w-4 mr-1" />
                          Score
                        </button>
                        <button
                          onClick={() => {
                            setGoogleSearchQuery(result.name);
                            setShowGoogleSearch(true);
                            // Scroll to the Google search section
                            setTimeout(() => {
                              document.getElementById('googleSearchSection')?.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                              });
                            }, 100);
                          }}
                          className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                        >
                          <Globe className="h-4 w-4 mr-1" />
                          Reviews
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {scoreData && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
              <h3 className="text-xl font-semibold mb-4">{scoreData.name} - Score Details</h3>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-lg font-bold">{scoreData.total_score.toFixed(2)}</p>
                    <p className="text-sm">Total Score</p>
                  </div>
                  <div className={`px-4 py-2 rounded-full text-white font-medium ${
                    scoreData.risk_category === "Low Risk" 
                      ? "bg-green-500" 
                      : scoreData.risk_category === "Medium Risk" 
                        ? "bg-yellow-500" 
                        : "bg-red-500"
                  }`}>
                    {scoreData.risk_category}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Qualification</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.qualification_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_qualification_score}%</span>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Experience</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.experience_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_experience_score}%</span>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Rating</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.rating_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_rating_score}%</span>
                  </div>
                  {scoreData.score_breakdown.rating_count && (
                    <div className="mt-1 text-sm text-gray-500">
                      Based on {scoreData.score_breakdown.rating_count} ratings
                    </div>
                  )}
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Weighted Rating</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.weighted_rating_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_weighted_rating_score}%</span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    Weighted score based on rating value and count
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Location</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.location_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_location_score}%</span>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">Specialization</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.specialization_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_specialization_score}%</span>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-2">License</h4>
                  <div className="flex justify-between">
                    <span>Score: {scoreData.score_breakdown.license_score}</span>
                    <span>Normalized: {scoreData.score_breakdown.normalized_license_score}%</span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    License verified: {scoreData.score_breakdown.license_verified ? "Yes" : "No"}
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => setScoreData(null)}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Doctor Details Modal */}
        {selectedDoctor && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
              <h3 className="text-lg font-medium mb-4">{selectedDoctor.name}</h3>
              <div className="space-y-2">
                {selectedDoctor.speciality && (
                  <p className="text-gray-700"><span className="font-medium">Speciality:</span> {selectedDoctor.speciality}</p>
                )}
                {selectedDoctor.location && (
                  <p className="text-gray-700"><span className="font-medium">Location:</span> {selectedDoctor.location}</p>
                )}
                {selectedDoctor.experience && (
                  <p className="text-gray-700"><span className="font-medium">Experience:</span> {selectedDoctor.experience}</p>
                )}
                {selectedDoctor.qualification && (
                  <p className="text-gray-700"><span className="font-medium">Qualification:</span> {selectedDoctor.qualification}</p>
                )}
                {selectedDoctor.rating && (
                  <p className="text-gray-700"><span className="font-medium">Rating:</span> ★ {selectedDoctor.rating}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedDoctor(null)}
                className="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;