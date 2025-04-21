import { useState } from 'react';
import { Search, Building2, User, Guitar as Hospital, Star, Globe, Stethoscope } from 'lucide-react';
import { searchEntities, getEntityScore, getReviewScoring } from './services/api';

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

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('doctor');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [reviewScoring, setReviewScoring] = useState<ReviewScoringResponse | null>(null);
  const [reviewsLimit, setReviewsLimit] = useState(60);
  const [isLoading, setIsLoading] = useState(false);
  const [showReviewsModal, setShowReviewsModal] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<SearchResult | null>(null);

  const categories = [
    { id: 'doctor', label: 'Doctor', icon: User },
    { id: 'clinic', label: 'Clinic', icon: Hospital },
    { id: 'city', label: 'City', icon: Building2 },
    { id: 'speciality', label: 'Speciality', icon: Stethoscope },
  ];

  const handleSearch = async () => {
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

  const handleGoogleCheck = () => {
    setShowReviewsModal(true);
  };

  const checkGoogle = async () => {
    try {
      const data = await getReviewScoring(searchQuery, reviewsLimit);
      setReviewScoring(data);
      setShowReviewsModal(false);
    } catch (error) {
      console.error('Google check failed:', error);
    }
  };

  const viewDoctorDetails = (doctor: SearchResult) => {
    setSelectedDoctor(doctor);
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
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
            </div>
            <button
              onClick={handleSearch}
              disabled={isLoading}
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
        </div>

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
                          onClick={() => handleGoogleCheck()}
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

        {showReviewsModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
              <h3 className="text-lg font-medium mb-4">Set Reviews Limit</h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Number of reviews to analyze:
                </label>
                <input
                  type="number"
                  value={reviewsLimit}
                  onChange={(e) => setReviewsLimit(Number(e.target.value))}
                  min="10"
                  max="100"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Higher numbers provide more accurate analysis but may take longer.
                </p>
              </div>
              <div className="flex justify-end gap-4">
                <button
                  onClick={() => setShowReviewsModal(false)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={() => checkGoogle()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Analyze Reviews
                </button>
              </div>
            </div>
          </div>
        )}

        {reviewScoring && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
              <h3 className="text-xl font-semibold mb-4">Review Analysis for {reviewScoring.query}</h3>
              
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Status:</span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">{reviewScoring.status}</span>
                </div>
                
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Average Score:</span>
                  <span className="text-yellow-500 font-bold">★ {reviewScoring.average_score.toFixed(1)}</span>
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="border rounded-lg p-3 text-center">
                  <div className="text-lg font-bold">{reviewScoring.total_reviews}</div>
                  <div className="text-sm text-gray-600">Total Reviews</div>
                </div>
                
                <div className="border rounded-lg p-3 text-center bg-green-50">
                  <div className="text-lg font-bold text-green-600">{reviewScoring.genuine_reviews}</div>
                  <div className="text-sm text-gray-600">Genuine Reviews</div>
                </div>
                
                <div className="border rounded-lg p-3 text-center bg-red-50">
                  <div className="text-lg font-bold text-red-600">{reviewScoring.fake_reviews}</div>
                  <div className="text-sm text-gray-600">Fake Reviews</div>
                </div>
              </div>
              
              {reviewScoring.fake_reviews > 0 && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-700 text-sm font-medium">
                    Warning: {((reviewScoring.fake_reviews / reviewScoring.total_reviews) * 100).toFixed(1)}% of reviews appear to be fake.
                  </p>
                </div>
              )}
              
              <button
                onClick={() => setReviewScoring(null)}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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