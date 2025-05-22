import { useState, useEffect, useRef } from 'react';
import { 
  getPopularSuggestions, 
  getTrendingSuggestions, 
  getSemanticSuggestions,
  getAutocompleteSuggestions
} from '../api/search';

const QuerySuggestions = ({ 
  query, 
  onSuggestionClick, 
  showPopular = true,
  showTrending = true,
  showSemantic = true,
  showAutocomplete = true,
  maxSuggestionsPerType = 3
}) => {
  const [popularSuggestions, setPopularSuggestions] = useState([]);
  const [trendingSuggestions, setTrendingSuggestions] = useState([]);
  const [semanticSuggestions, setSemanticSuggestions] = useState([]);
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const autocompleteDebounceRef = useRef(null);
  
  // Load initial popular and trending suggestions
  useEffect(() => {
    if (showPopular || showTrending) {
      const loadInitialSuggestions = async () => {
        try {
          setIsLoading(true);
          
          // Load suggestions in parallel
          const promises = [];
          
          if (showPopular) {
            promises.push(
              getPopularSuggestions(maxSuggestionsPerType)
                .then(data => setPopularSuggestions(data))
            );
          }
          
          if (showTrending) {
            promises.push(
              getTrendingSuggestions(maxSuggestionsPerType)
                .then(data => setTrendingSuggestions(data))
            );
          }
          
          await Promise.all(promises);
        } catch (error) {
          console.error('Error loading suggestions:', error);
        } finally {
          setIsLoading(false);
        }
      };
      
      loadInitialSuggestions();
    }
  }, [showPopular, showTrending, maxSuggestionsPerType]);
  
  // Load semantic suggestions when query changes and has meaningful content
  useEffect(() => {
    if (showSemantic && query && query.length > 4) {
      const loadSemanticSuggestions = async () => {
        try {
          const data = await getSemanticSuggestions(query, maxSuggestionsPerType);
          setSemanticSuggestions(data);
        } catch (error) {
          console.error('Error loading semantic suggestions:', error);
        }
      };
      
      loadSemanticSuggestions();
    } else {
      setSemanticSuggestions([]);
    }
  }, [query, showSemantic, maxSuggestionsPerType]);
  
  // Load autocomplete suggestions with debounce
  useEffect(() => {
    if (showAutocomplete && query && query.length > 1) {
      // Clear previous timeout
      if (autocompleteDebounceRef.current) {
        clearTimeout(autocompleteDebounceRef.current);
      }
      
      // Set new timeout
      autocompleteDebounceRef.current = setTimeout(async () => {
        try {
          const data = await getAutocompleteSuggestions(query, maxSuggestionsPerType);
          setAutocompleteSuggestions(data);
        } catch (error) {
          console.error('Error loading autocomplete suggestions:', error);
        }
      }, 300); // 300ms debounce
    } else {
      setAutocompleteSuggestions([]);
    }
    
    // Cleanup
    return () => {
      if (autocompleteDebounceRef.current) {
        clearTimeout(autocompleteDebounceRef.current);
      }
    };
  }, [query, showAutocomplete, maxSuggestionsPerType]);
  
  // Only show component if we have suggestions
  const hasSuggestions = (
    popularSuggestions.length > 0 || 
    trendingSuggestions.length > 0 || 
    semanticSuggestions.length > 0 || 
    autocompleteSuggestions.length > 0
  );
  
  if (!hasSuggestions && !isLoading) {
    return null;
  }
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-3 mt-2">
      {isLoading ? (
        <div className="text-sm text-gray-500 animate-pulse">Loading suggestions...</div>
      ) : (
        <>
          {/* Autocomplete Suggestions */}
          {showAutocomplete && autocompleteSuggestions.length > 0 && (
            <div className="mb-3">
              <h3 className="text-xs font-medium text-gray-500 mb-1">Complete your query</h3>
              <div className="flex flex-wrap gap-2">
                {autocompleteSuggestions.map((suggestion, index) => (
                  <SuggestionChip
                    key={`autocomplete-${index}`}
                    suggestion={suggestion}
                    onClick={() => onSuggestionClick(suggestion.completion || suggestion.query_text)}
                    type="autocomplete"
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Semantic Suggestions */}
          {showSemantic && semanticSuggestions.length > 0 && (
            <div className="mb-3">
              <h3 className="text-xs font-medium text-gray-500 mb-1">Similar questions</h3>
              <div className="flex flex-wrap gap-2">
                {semanticSuggestions.map((suggestion, index) => (
                  <SuggestionChip
                    key={`semantic-${index}`}
                    suggestion={suggestion}
                    onClick={() => onSuggestionClick(suggestion.query_text)}
                    type="semantic"
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Popular Suggestions */}
          {showPopular && popularSuggestions.length > 0 && (
            <div className="mb-3">
              <h3 className="text-xs font-medium text-gray-500 mb-1">Popular searches</h3>
              <div className="flex flex-wrap gap-2">
                {popularSuggestions.map((suggestion, index) => (
                  <SuggestionChip
                    key={`popular-${index}`}
                    suggestion={suggestion}
                    onClick={() => onSuggestionClick(suggestion.query_text)}
                    type="popular"
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* Trending Suggestions */}
          {showTrending && trendingSuggestions.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-gray-500 mb-1">Trending searches</h3>
              <div className="flex flex-wrap gap-2">
                {trendingSuggestions.map((suggestion, index) => (
                  <SuggestionChip
                    key={`trending-${index}`}
                    suggestion={suggestion}
                    onClick={() => onSuggestionClick(suggestion.query_text)}
                    type="trending"
                  />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Helper component for suggestion chips
const SuggestionChip = ({ suggestion, onClick, type }) => {
  let chipClasses = "text-sm py-1 px-3 rounded-full cursor-pointer transition-colors ";
  let icon = null;
  
  switch (type) {
    case 'popular':
      chipClasses += "bg-blue-50 hover:bg-blue-100 text-blue-700";
      icon = <PopularIcon className="w-3 h-3 mr-1" />;
      break;
    case 'trending':
      chipClasses += "bg-green-50 hover:bg-green-100 text-green-700";
      icon = <TrendingIcon className="w-3 h-3 mr-1" />;
      break;
    case 'semantic':
      chipClasses += "bg-purple-50 hover:bg-purple-100 text-purple-700";
      break;
    case 'autocomplete':
      chipClasses += "bg-gray-100 hover:bg-gray-200 text-gray-700";
      break;
    default:
      chipClasses += "bg-gray-100 hover:bg-gray-200 text-gray-700";
  }
  
  return (
    <button 
      onClick={onClick}
      className={chipClasses}
    >
      <div className="flex items-center">
        {icon}
        <span className="truncate max-w-[200px]">
          {suggestion.completion || suggestion.query_text}
        </span>
      </div>
    </button>
  );
};

// Simple SVG icons
const PopularIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
  </svg>
);

const TrendingIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" />
  </svg>
);

export default QuerySuggestions;