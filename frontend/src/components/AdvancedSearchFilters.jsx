import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

const AdvancedSearchFilters = ({
  filters,
  onFiltersChange,
  collapsed = true,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(!collapsed);
  const [searchFilters, setSearchFilters] = useState(filters || []);
  const [fields, setFields] = useState([
    { value: 'doc_type', label: 'Document Type', type: 'term' },
    { value: 'author', label: 'Author', type: 'term' },
    { value: 'year', label: 'Year', type: 'range' },
    { value: 'title', label: 'Title', type: 'text' },
    { value: 'content', label: 'Content', type: 'text' }
  ]);

  // Update filters when props change
  useEffect(() => {
    if (filters) {
      setSearchFilters(filters);
    }
  }, [filters]);

  // Toggle expanded/collapsed state
  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  // Add a new filter
  const addFilter = () => {
    const defaultField = fields[0];
    const newFilter = {
      id: uuidv4(),
      field: defaultField.value,
      type: defaultField.type,
      value: ''
    };
    
    const updatedFilters = [...searchFilters, newFilter];
    setSearchFilters(updatedFilters);
    
    // Notify parent
    if (onFiltersChange) {
      onFiltersChange(updatedFilters);
    }
  };

  // Update a filter
  const updateFilter = (id, key, value) => {
    const updatedFilters = searchFilters.map(filter => {
      if (filter.id === id) {
        // If changing the field, also update the filter type
        if (key === 'field') {
          const fieldDef = fields.find(f => f.value === value);
          return { 
            ...filter, 
            [key]: value,
            type: fieldDef?.type || 'term'
          };
        }
        
        return { ...filter, [key]: value };
      }
      return filter;
    });
    
    setSearchFilters(updatedFilters);
    
    // Notify parent
    if (onFiltersChange) {
      onFiltersChange(updatedFilters);
    }
  };

  // Remove a filter
  const removeFilter = (id) => {
    const updatedFilters = searchFilters.filter(filter => filter.id !== id);
    setSearchFilters(updatedFilters);
    
    // Notify parent
    if (onFiltersChange) {
      onFiltersChange(updatedFilters);
    }
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchFilters([]);
    
    // Notify parent
    if (onFiltersChange) {
      onFiltersChange([]);
    }
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg overflow-hidden ${className}`}>
      {/* Header with toggle */}
      <div 
        className="bg-gray-50 px-4 py-3 border-b border-gray-200 cursor-pointer flex justify-between items-center"
        onClick={toggleExpanded}
      >
        <h3 className="font-medium text-gray-700">Advanced Filters</h3>
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
      
      {/* Active filters summary (always visible) */}
      {searchFilters.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h4 className="text-xs text-gray-500">
              {searchFilters.length} active filter{searchFilters.length !== 1 ? 's' : ''}
            </h4>
            <button
              type="button"
              className="text-xs text-gray-500 hover:text-gray-700 underline"
              onClick={clearFilters}
            >
              Clear all
            </button>
          </div>
        </div>
      )}
      
      {/* Filter controls (collapsible) */}
      {isExpanded && (
        <div className="p-4">
          <div className="space-y-4">
            {searchFilters.map((filter) => (
              <FilterRow
                key={filter.id}
                filter={filter}
                fields={fields}
                onUpdate={(key, value) => updateFilter(filter.id, key, value)}
                onRemove={() => removeFilter(filter.id)}
              />
            ))}
            
            <div className="pt-2">
              <button
                type="button"
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm leading-5 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:border-primary-300 focus:shadow-outline-primary"
                onClick={addFilter}
              >
                <svg className="mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Filter
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const FilterRow = ({ filter, fields, onUpdate, onRemove }) => {
  // Get the current field definition
  const fieldDef = fields.find(f => f.value === filter.field) || fields[0];
  
  // Render inputs based on filter type
  const renderFilterInput = () => {
    switch (filter.type) {
      case 'term':
        // For term filters, show a text input
        return (
          <input
            type="text"
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            value={filter.value || ''}
            onChange={(e) => onUpdate('value', e.target.value)}
            placeholder={`Enter ${fieldDef.label}`}
          />
        );
        
      case 'range':
        // For numerical ranges, show min/max inputs
        return (
          <div className="grid grid-cols-2 gap-2 mt-1">
            <input
              type="number"
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              value={filter.min || ''}
              onChange={(e) => {
                const min = e.target.value === '' ? null : Number(e.target.value);
                onUpdate('min', min);
              }}
              placeholder="Min"
            />
            <input
              type="number"
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              value={filter.max || ''}
              onChange={(e) => {
                const max = e.target.value === '' ? null : Number(e.target.value);
                onUpdate('max', max);
              }}
              placeholder="Max"
            />
          </div>
        );
        
      case 'text':
        // For text search, show a textarea
        return (
          <textarea
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            value={filter.text || ''}
            onChange={(e) => onUpdate('text', e.target.value)}
            placeholder={`Search in ${fieldDef.label}`}
            rows={2}
          />
        );
        
      case 'multi_term':
        // For multi-term filters, show a comma-separated input
        return (
          <div className="mt-1">
            <input
              type="text"
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              value={Array.isArray(filter.values) ? filter.values.join(', ') : ''}
              onChange={(e) => {
                const values = e.target.value.split(',').map(v => v.trim()).filter(Boolean);
                onUpdate('values', values);
              }}
              placeholder="Enter comma-separated values"
            />
            <p className="mt-1 text-xs text-gray-500">
              Enter values separated by commas
            </p>
          </div>
        );
        
      case 'date_range':
        // For date ranges, show date inputs
        return (
          <div className="grid grid-cols-2 gap-2 mt-1">
            <div>
              <label className="block text-xs text-gray-500">From</label>
              <input
                type="date"
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={filter.start || ''}
                onChange={(e) => onUpdate('start', e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500">To</label>
              <input
                type="date"
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={filter.end || ''}
                onChange={(e) => onUpdate('end', e.target.value)}
              />
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="bg-gray-50 p-3 rounded border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-gray-700">
          Filter by {fieldDef.label}
        </label>
        <button
          type="button"
          className="text-gray-400 hover:text-gray-500"
          onClick={onRemove}
        >
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      
      <div className="space-y-2">
        <select
          className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          value={filter.field}
          onChange={(e) => onUpdate('field', e.target.value)}
        >
          {fields.map((field) => (
            <option key={field.value} value={field.value}>
              {field.label}
            </option>
          ))}
        </select>
        
        {renderFilterInput()}
      </div>
    </div>
  );
};

export default AdvancedSearchFilters;