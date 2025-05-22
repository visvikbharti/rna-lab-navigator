import { useState, useEffect } from 'react';
import { getRankingProfiles } from '../api/search';

const SearchRankingSelector = ({ 
  selectedProfileId, 
  onProfileChange,
  className = ''
}) => {
  const [profiles, setProfiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  
  useEffect(() => {
    const loadProfiles = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getRankingProfiles();
        setProfiles(data.results || []);
      } catch (err) {
        console.error('Error loading ranking profiles:', err);
        setError('Failed to load search ranking profiles');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadProfiles();
  }, []);
  
  // Find the selected profile object
  const selectedProfile = profiles.find(p => p.id === selectedProfileId) || 
                          profiles.find(p => p.is_default) ||
                          (profiles.length > 0 ? profiles[0] : null);
  
  const handleProfileSelection = (profile) => {
    onProfileChange(profile.id);
    setIsExpanded(false);
  };
  
  if (isLoading) {
    return (
      <div className={`text-sm text-gray-500 animate-pulse ${className}`}>
        Loading search profiles...
      </div>
    );
  }
  
  if (error) {
    return (
      <div className={`text-sm text-red-500 ${className}`}>
        {error}
      </div>
    );
  }
  
  if (profiles.length === 0) {
    return null;
  }
  
  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="flex items-center">
          <TuneIcon className="w-4 h-4 mr-2 text-gray-500" />
          {selectedProfile?.name || 'Default search'}
        </span>
        <ChevronIcon 
          className={`w-4 h-4 ml-2 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
        />
      </button>
      
      {isExpanded && (
        <div className="absolute right-0 z-10 mt-2 overflow-hidden bg-white rounded-md shadow-lg w-72 ring-1 ring-black ring-opacity-5">
          <div className="p-3 border-b border-gray-200">
            <h3 className="text-sm font-medium text-gray-700">Search ranking profiles</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Adjust how search results are ranked
            </p>
          </div>
          <ul className="py-1">
            {profiles.map((profile) => (
              <li key={profile.id}>
                <button
                  type="button"
                  className={`flex items-start w-full px-4 py-2 text-sm ${
                    profile.id === selectedProfile?.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => handleProfileSelection(profile)}
                >
                  <div className="flex-1 text-left">
                    <div className="font-medium">{profile.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {profile.description}
                    </div>
                    <div className="flex flex-wrap gap-x-3 mt-1.5">
                      <ProfileStat 
                        label="Vector" 
                        value={`${Math.round(profile.vector_weight * 100)}%`} 
                      />
                      <ProfileStat 
                        label="Keyword" 
                        value={`${Math.round(profile.keyword_weight * 100)}%`} 
                      />
                      {profile.recency_boost > 0 && (
                        <ProfileStat 
                          label="Recency" 
                          value="On" 
                        />
                      )}
                    </div>
                  </div>
                  {profile.is_default && (
                    <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      Default
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Helper component for profile statistics
const ProfileStat = ({ label, value }) => (
  <div className="flex items-center">
    <span className="text-xs text-gray-500">{label}:</span>
    <span className="ml-1 text-xs font-medium text-gray-700">{value}</span>
  </div>
);

// SVG Icons
const TuneIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z" />
  </svg>
);

const ChevronIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z" />
  </svg>
);

export default SearchRankingSelector;