import { useState, useEffect } from 'react';
import { getAvailableFacets, getFacetStats } from '../api/search';

const SearchFacets = ({ 
  facets, 
  onFacetChange, 
  collapsed = false,
  className = '',
  currentQuery = '',
  showFacetCounts = true,
  refreshTrigger = 0
}) => {
  const [availableFacets, setAvailableFacets] = useState([]);
  const [facetStats, setFacetStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStatsLoading, setIsStatsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(!collapsed);
  const [selectedFacets, setSelectedFacets] = useState(facets || []);
  
  // Load available facets on mount
  useEffect(() => {
    const loadFacets = async () => {
      try {
        setIsLoading(true);
        const data = await getAvailableFacets();
        // Handle different response formats - can be array or object
        if (data.facets) {
          // Object format with facets key
          setAvailableFacets(data.facets);
        } else if (Array.isArray(data)) {
          // Direct array format
          setAvailableFacets(data);
        } else {
          // Fallback
          setAvailableFacets([]);
          console.warn('Unexpected facet data format', data);
        }
      } catch (error) {
        console.error('Error loading facets:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadFacets();
  }, []);
  
  // Load facet statistics when query changes or refreshTrigger changes
  useEffect(() => {
    if (!currentQuery && !selectedFacets.length) {
      return; // Don't fetch stats for empty queries and no filters
    }
    
    const loadFacetStats = async () => {
      try {
        setIsStatsLoading(true);
        const data = await getFacetStats(currentQuery, selectedFacets);
        setFacetStats(data);
      } catch (error) {
        console.error('Error loading facet statistics:', error);
      } finally {
        setIsStatsLoading(false);
      }
    };
    
    loadFacetStats();
  }, [currentQuery, selectedFacets, refreshTrigger]);
  
  // Update selected facets when props change
  useEffect(() => {
    if (facets) {
      setSelectedFacets(facets);
    }
  }, [facets]);
  
  // Handle facet selection
  const handleFacetSelect = (facet, value) => {
    // Find if facet is already selected
    const existingIndex = selectedFacets.findIndex(f => f.name === facet.name);
    
    let updatedFacets;
    
    if (existingIndex >= 0) {
      // Facet exists, update its value
      updatedFacets = [...selectedFacets];
      updatedFacets[existingIndex] = {
        ...updatedFacets[existingIndex],
        value: value
      };
    } else {
      // Add new facet selection
      updatedFacets = [
        ...selectedFacets,
        {
          name: facet.name,
          value: value
        }
      ];
    }
    
    setSelectedFacets(updatedFacets);
    
    // Notify parent
    if (onFacetChange) {
      onFacetChange(updatedFacets);
    }
  };
  
  // Handle removing a facet
  const handleRemoveFacet = (facetName) => {
    const updatedFacets = selectedFacets.filter(f => f.name !== facetName);
    setSelectedFacets(updatedFacets);
    
    // Notify parent
    if (onFacetChange) {
      onFacetChange(updatedFacets);
    }
  };
  
  // Toggle expanded/collapsed state
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };
  
  if (isLoading) {
    return (
      <div className={`bg-gray-50 p-4 rounded-lg shadow-sm ${className}`}>
        <div className="animate-pulse text-gray-500">Loading facets...</div>
      </div>
    );
  }
  
  if (!availableFacets.length) {
    return null;
  }
  
  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header with toggle */}
      <div 
        className="bg-gray-50 px-4 py-3 border-b border-gray-200 cursor-pointer flex justify-between items-center"
        onClick={toggleExpanded}
      >
        <h3 className="font-medium text-gray-700">Search Filters</h3>
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
      
      {/* Selected facets summary (always visible) */}
      {selectedFacets.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
          <h4 className="text-xs text-gray-500 mb-1">Active filters:</h4>
          <div className="flex flex-wrap gap-2">
            {selectedFacets.map((facet) => {
              const facetDef = availableFacets.find(f => f.name === facet.name);
              return (
                <div 
                  key={facet.name}
                  className="inline-flex items-center bg-primary-50 text-primary-700 text-sm rounded-full px-3 py-1"
                >
                  <span className="mr-1 font-medium">{facetDef?.display_name || facet.name}:</span>
                  <span className="truncate max-w-[120px]">{renderFacetValue(facet.value)}</span>
                  <button
                    type="button"
                    className="ml-1.5 text-primary-500 hover:text-primary-700"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveFacet(facet.name);
                    }}
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              );
            })}
            
            {selectedFacets.length > 0 && (
              <button
                type="button"
                className="text-xs text-gray-500 hover:text-gray-700 underline"
                onClick={() => {
                  setSelectedFacets([]);
                  if (onFacetChange) {
                    onFacetChange([]);
                  }
                }}
              >
                Clear all
              </button>
            )}
          </div>
        </div>
      )}
      
      {/* Facet selectors (collapsible) */}
      {isExpanded && (
        <div className="p-4">
          {isStatsLoading && (
            <div className="bg-gray-50 p-2 rounded text-center mb-4">
              <div className="text-xs text-gray-500 animate-pulse">Updating facets...</div>
            </div>
          )}
          
          {/* Display total result count from facet stats if available */}
          {facetStats && (
            <div className="mb-4 text-sm text-gray-600 flex items-center">
              <span className="mr-1">Found</span>
              <span className="font-semibold">{facetStats.total_results}</span>
              <span className="ml-1">results</span>
              {currentQuery && <span className="ml-1">for "{currentQuery}"</span>}
            </div>
          )}
          
          <div className="space-y-4">
            {/* Handle both array and object formats for facets */}
            {Array.isArray(availableFacets) 
              ? availableFacets.map(facet => (
                  <FacetSelector
                    key={facet.name}
                    facet={{...facet, id: facet.name}}
                    value={selectedFacets.find(f => f.name === facet.name)?.value}
                    onSelect={(value) => handleFacetSelect(facet, value)}
                    stats={facetStats}
                    showCounts={showFacetCounts}
                  />
                ))
              : Object.entries(availableFacets).map(([facetId, facet]) => (
                  <FacetSelector
                    key={facetId}
                    facet={{...facet, id: facetId}}
                    value={selectedFacets.find(f => f.name === facetId)?.value}
                    onSelect={(value) => handleFacetSelect({name: facetId, ...facet}, value)}
                    stats={facetStats}
                    showCounts={showFacetCounts}
                  />
                ))
            }
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to render facet value in a readable format
const renderFacetValue = (value) => {
  if (value === null || value === undefined) {
    return 'Any';
  }
  
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    
    if (value.min !== undefined && value.max !== undefined) {
      return `${value.min} - ${value.max}`;
    }
    
    if (value.start !== undefined && value.end !== undefined) {
      return `${value.start} - ${value.end}`;
    }
    
    return JSON.stringify(value);
  }
  
  return String(value);
};

// Individual facet selector component
const FacetSelector = ({ facet, value, onSelect, stats = null, showCounts = true }) => {
  // Get statistics for this facet if available
  const facetStats = stats?.facets?.[facet.id] || null;
  
  // Render different facet types
  switch (facet.type) {
    case 'categorical':
      return (
        <div className="facet-selector">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {facet.display_name}
          </label>
          
          {/* If we have stats, show each option as a checkbox with count */}
          {facetStats && showCounts ? (
            <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
              <div 
                className="flex items-center mb-1.5 py-1 border-b border-gray-100"
                onClick={() => onSelect(null)}
              >
                <input
                  type="radio"
                  className="h-3.5 w-3.5 text-primary-600 border-gray-300 focus:ring-primary-500"
                  checked={!value}
                  onChange={() => onSelect(null)}
                  id={`${facet.id}_any`}
                />
                <label 
                  htmlFor={`${facet.id}_any`} 
                  className="ml-2 flex items-center justify-between w-full text-sm text-gray-700 cursor-pointer"
                >
                  <span>Any</span>
                  <span className="text-xs text-gray-500">{facetStats.values.reduce((sum, v) => sum + v.count, 0)}</span>
                </label>
              </div>
              
              {facetStats.values.map((option) => (
                <div 
                  key={option.id} 
                  className="flex items-center py-0.5 cursor-pointer"
                  onClick={() => onSelect(option.id)}
                >
                  <input
                    type="radio"
                    className="h-3.5 w-3.5 text-primary-600 border-gray-300 focus:ring-primary-500"
                    checked={value === option.id}
                    onChange={() => onSelect(option.id)}
                    id={`${facet.id}_${option.id}`}
                  />
                  <label 
                    htmlFor={`${facet.id}_${option.id}`} 
                    className="ml-2 flex items-center justify-between w-full text-sm text-gray-700 cursor-pointer"
                  >
                    <span className="truncate">{option.value}</span>
                    <span className="text-xs text-gray-500 whitespace-nowrap">{option.count}</span>
                  </label>
                </div>
              ))}
            </div>
          ) : (
            // Fallback to simple select when no stats
            <select
              className="w-full border border-gray-300 rounded-md py-2 px-3 text-sm"
              value={value || ''}
              onChange={(e) => onSelect(e.target.value === '' ? null : e.target.value)}
            >
              <option value="">Any</option>
              {facet.values?.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.value}
                </option>
              ))}
            </select>
          )}
        </div>
      );
      
    case 'numerical':
      // Get facet statistics if available
      const numericStats = stats?.facets?.[facet.id] || null;
      // Default min/max values - either from facet config, stats, or reasonable defaults
      const defaultMin = numericStats?.min || facet.config?.min || 0;
      const defaultMax = numericStats?.max || facet.config?.max || 100;
      // Current selected values or defaults
      const currentMin = (value?.min !== undefined && value?.min !== null) ? value.min : defaultMin;
      const currentMax = (value?.max !== undefined && value?.max !== null) ? value.max : defaultMax;
      
      return (
        <div className="facet-selector">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {facet.display_name}
          </label>
          
          {/* Value display */}
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{currentMin}</span>
            <span>{currentMax}</span>
          </div>
          
          {/* Slider */}
          <input
            type="range"
            min={defaultMin}
            max={defaultMax}
            value={currentMin}
            onChange={(e) => {
              const min = Number(e.target.value);
              onSelect({ min, max: currentMax });
            }}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mb-2"
          />
          
          <input
            type="range"
            min={defaultMin}
            max={defaultMax}
            value={currentMax}
            onChange={(e) => {
              const max = Number(e.target.value);
              onSelect({ min: currentMin, max });
            }}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mb-3"
          />
          
          {/* Input fields for precise values */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-gray-500">Min</label>
              <input
                type="number"
                className="w-full border border-gray-300 rounded-md py-1.5 px-2 text-sm"
                value={currentMin}
                onChange={(e) => {
                  const min = e.target.value === '' ? defaultMin : Number(e.target.value);
                  onSelect({ min, max: currentMax });
                }}
                placeholder="Min"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500">Max</label>
              <input
                type="number"
                className="w-full border border-gray-300 rounded-md py-1.5 px-2 text-sm"
                value={currentMax}
                onChange={(e) => {
                  const max = e.target.value === '' ? defaultMax : Number(e.target.value);
                  onSelect({ min: currentMin, max });
                }}
                placeholder="Max"
              />
            </div>
          </div>
          
          {/* Distribution visualization if stats available */}
          {numericStats?.distribution && (
            <div className="mt-3">
              <div className="h-12 bg-gray-50 rounded-md relative">
                {numericStats.distribution.map((point, index) => (
                  <div 
                    key={index}
                    style={{
                      position: 'absolute',
                      bottom: '0',
                      left: `${(point.value - defaultMin) / (defaultMax - defaultMin) * 100}%`,
                      height: `${point.count / numericStats.max_count * 100}%`,
                      width: '3px',
                      backgroundColor: 'rgba(79, 70, 229, 0.5)'
                    }}
                    title={`${point.value}: ${point.count} documents`}
                  />
                ))}
                
                {/* Highlight selected range */}
                <div 
                  className="absolute bottom-0 h-1 bg-primary-500"
                  style={{
                    left: `${(currentMin - defaultMin) / (defaultMax - defaultMin) * 100}%`,
                    width: `${(currentMax - currentMin) / (defaultMax - defaultMin) * 100}%`
                  }}
                />
              </div>
            </div>
          )}
          
          {/* Reset button */}
          <button
            type="button"
            className="mt-2 text-xs text-primary-600 hover:text-primary-800 underline"
            onClick={() => onSelect(null)}
          >
            Reset to default
          </button>
        </div>
      );
      
    case 'temporal':
      return (
        <div className="facet-selector">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {facet.display_name}
          </label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-gray-500">From</label>
              <input
                type="date"
                className="w-full border border-gray-300 rounded-md py-1.5 px-2 text-sm"
                value={value?.start || ''}
                onChange={(e) => {
                  onSelect({ start: e.target.value, end: value?.end });
                }}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500">To</label>
              <input
                type="date"
                className="w-full border border-gray-300 rounded-md py-1.5 px-2 text-sm"
                value={value?.end || ''}
                onChange={(e) => {
                  onSelect({ start: value?.start, end: e.target.value });
                }}
              />
            </div>
          </div>
        </div>
      );
      
    case 'hierarchical':
      // Simplified version - could be expanded with tree view
      return (
        <div className="facet-selector">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {facet.display_name}
          </label>
          <select
            className="w-full border border-gray-300 rounded-md py-2 px-3 text-sm"
            value={value || ''}
            onChange={(e) => onSelect(e.target.value === '' ? null : e.target.value)}
          >
            <option value="">All</option>
            {facet.config?.hierarchy?.map((item) => (
              <option key={item.path} value={item.path}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      );
      
    default:
      return null;
  }
};

export default SearchFacets;