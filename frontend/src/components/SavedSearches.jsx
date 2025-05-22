import { useState, useEffect } from 'react';
import { getSavedSearches, saveSearch, executeSearch } from '../api/search';

const SavedSearches = ({
  onSearchSelect,
  onSaveSearch,
  collapsed = true,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(!collapsed);
  const [savedSearches, setSavedSearches] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [searchName, setSearchName] = useState('');
  const [searchDescription, setSearchDescription] = useState('');
  
  // Load saved searches on mount
  useEffect(() => {
    loadSavedSearches();
  }, []);
  
  // Load saved searches from API
  const loadSavedSearches = async () => {
    try {
      setIsLoading(true);
      const searches = await getSavedSearches();
      setSavedSearches(searches);
    } catch (error) {
      console.error('Error loading saved searches:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Toggle expanded/collapsed state
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };
  
  // Handle saving a search
  const handleSaveSearch = async (e) => {
    e.preventDefault();
    
    if (!searchName.trim()) {
      return;
    }
    
    try {
      await onSaveSearch(searchName, searchDescription);
      setSearchName('');
      setSearchDescription('');
      setShowSaveForm(false);
      loadSavedSearches();
    } catch (error) {
      console.error('Error saving search:', error);
    }
  };
  
  // Handle selecting a saved search
  const handleSelectSearch = (search) => {
    if (onSearchSelect) {
      onSearchSelect(search);
    }
  };
  
  if (isLoading && !savedSearches.length) {
    return (
      <div className={`bg-gray-50 p-4 rounded-lg shadow-sm ${className}`}>
        <div className="animate-pulse text-gray-500">Loading saved searches...</div>
      </div>
    );
  }
  
  if (!savedSearches.length && !showSaveForm) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
        <p className="text-sm text-gray-500 mb-3">No saved searches yet.</p>
        <button
          type="button"
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-primary-300 focus:shadow-outline-primary"
          onClick={() => setShowSaveForm(true)}
        >
          <svg className="mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Save Current Search
        </button>
      </div>
    );
  }
  
  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header with toggle */}
      <div 
        className="bg-gray-50 px-4 py-3 border-b border-gray-200 cursor-pointer flex justify-between items-center"
        onClick={toggleExpanded}
      >
        <h3 className="font-medium text-gray-700">Saved Searches</h3>
        <button 
          type="button"
          className="text-gray-500 hover:text-gray-700 focus:outline-none"
          aria-expanded={isExpanded}
        >
          <svg 
            className={`h-5 w-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      {/* Save form or saved searches list */}
      {isExpanded && (
        <div className="p-4">
          {showSaveForm ? (
            <form onSubmit={handleSaveSearch} className="space-y-3">
              <div>
                <label htmlFor="search-name" className="block text-sm font-medium text-gray-700">
                  Search Name
                </label>
                <input
                  type="text"
                  id="search-name"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  placeholder="Enter a name for this search"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="search-description" className="block text-sm font-medium text-gray-700">
                  Description (optional)
                </label>
                <textarea
                  id="search-description"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={searchDescription}
                  onChange={(e) => setSearchDescription(e.target.value)}
                  placeholder="Describe what this search is for"
                  rows={2}
                />
              </div>
              
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-primary-300 focus:shadow-outline-primary"
                  onClick={() => setShowSaveForm(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm leading-5 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-500 focus:outline-none focus:border-primary-700 focus:shadow-outline-primary"
                >
                  Save Search
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between items-center mb-2">
                <h4 className="text-sm font-medium text-gray-700">Your saved searches</h4>
                <button
                  type="button"
                  className="text-xs text-primary-600 hover:text-primary-500"
                  onClick={() => setShowSaveForm(true)}
                >
                  + Save current search
                </button>
              </div>
              
              <div className="space-y-2">
                {savedSearches.map((search) => (
                  <div 
                    key={search.id}
                    className="border border-gray-200 rounded-md p-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleSelectSearch(search)}
                  >
                    <div className="flex justify-between">
                      <h5 className="text-sm font-medium text-gray-800">{search.name}</h5>
                      <span className="text-xs text-gray-500">
                        Used {search.usage_count} time{search.usage_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                    
                    {search.description && (
                      <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                        {search.description}
                      </p>
                    )}
                    
                    <div className="mt-2 flex items-center text-xs text-gray-500">
                      <span>
                        {search.query_text ? `"${search.query_text}"` : 'No query text'}
                      </span>
                      
                      {search.parameters?.filters?.length > 0 && (
                        <span className="ml-2 bg-gray-100 px-1.5 py-0.5 rounded">
                          {search.parameters.filters.length} filter{search.parameters.filters.length !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SavedSearches;