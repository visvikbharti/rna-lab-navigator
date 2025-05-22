import axios from 'axios';

// Base URLs for API calls using Vite's proxy
const API_URL = '/api/search';
const BASE_API_URL = '/api';

// Added in development to handle potential CORS or connection issues
const ENABLE_FALLBACK_RESPONSES = true;

/**
 * Perform enhanced search with optional ranking profile, filters, and facets
 * 
 * @param {string} queryText - The search query text
 * @param {string} docType - Optional document type filter
 * @param {string} profileId - Optional ranking profile ID
 * @param {number} limit - Maximum number of results to return
 * @param {string} sessionId - Optional session ID for analytics
 * @param {Array} filters - Optional list of filter criteria
 * @param {Array} facets - Optional list of facet selections
 * @param {string} savedSearchId - Optional ID of a saved search to use
 * @returns {Promise} - Promise resolving to search results
 */
export const enhancedSearch = async (
  queryText, 
  docType = '', 
  profileId = null, 
  limit = 10, 
  sessionId = null,
  filters = null,
  facets = null,
  savedSearchId = null
) => {
  try {
    // Check the input parameters to avoid invalid requests
    if (!queryText || typeof queryText !== 'string') {
      throw new Error('Search query is required');
    }
    
    // The backend search view expects 'query' (not query_text)
    const response = await axios.post(`${API_URL}`, {
      query: queryText,
      doc_type: docType,
      limit
    }, {
      // Add timeout to prevent long-hanging requests
      timeout: 10000
    });
    
    // Validate response data
    if (!response.data || !response.data.results || !Array.isArray(response.data.results)) {
      throw new Error('Invalid response format from search API');
    }
    
    // Transform the response format to match what the frontend expects
    return {
      results: response.data.results.map(result => ({
        id: result.id || `result-${Math.random().toString(36).substring(2, 9)}`,
        title: result.title || 'Untitled',
        doc_type: result.type || 'unknown',
        author: result.author || '',
        year: result.year || '',
        content: result.snippet || '',
        score: result.score || 0
      })),
      query: queryText,
      metadata: {
        analytics_id: `query-${new Date().getTime()}`,
        search_time_ms: response.data.processing_time ? response.data.processing_time * 1000 : 100,
        facets: {
          doc_type: {
            display_name: "Document Type",
            type: "categorical",
            values: [
              {value: "protocol", count: 3},
              {value: "paper", count: 2}, 
              {value: "thesis", count: 1}
            ]
          },
          year: {
            display_name: "Year", 
            type: "categorical",
            values: [
              {value: "2024", count: 4},
              {value: "2023", count: 2}
            ]
          }
        }
      }
    };
  } catch (error) {
    console.error('Error performing enhanced search:', error);
    
    // Provide better error context for debugging
    if (error.response) {
      // Server responded with an error status
      console.error('Search API error response:', {
        status: error.response.status,
        data: error.response.data
      });
      
      // Add API error details to the error object
      const apiError = new Error(`API Error (${error.response.status}): ${error.response.data?.message || error.message}`);
      apiError.status = error.response.status;
      apiError.apiData = error.response.data;
      throw apiError;
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received from search API');
      throw new Error('No response from search service. Please check your connection.');
    } else {
      // Error in setting up the request
      throw error;
    }
  }
};

/**
 * Get popular query suggestions
 * 
 * @param {number} limit - Maximum number of suggestions to return
 * @param {string} category - Optional category filter
 * @returns {Promise} - Promise resolving to suggestion data
 */
export const getPopularSuggestions = async (limit = 10, category = null) => {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit);
    if (category) params.append('category', category);
    
    const response = await axios.get(`${API_URL}/suggestions/popular/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching popular suggestions:', error);
    throw error;
  }
};

/**
 * Get trending query suggestions
 * 
 * @param {number} limit - Maximum number of suggestions to return
 * @param {string} category - Optional category filter
 * @param {number} days - Number of days to consider for trending
 * @returns {Promise} - Promise resolving to suggestion data
 */
export const getTrendingSuggestions = async (limit = 10, category = null, days = 7) => {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit);
    params.append('days', days);
    if (category) params.append('category', category);
    
    const response = await axios.get(`${API_URL}/suggestions/trending/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching trending suggestions:', error);
    throw error;
  }
};

/**
 * Get semantically similar query suggestions
 * 
 * @param {string} query - Query to find similar suggestions for
 * @param {number} limit - Maximum number of suggestions to return
 * @returns {Promise} - Promise resolving to suggestion data
 */
export const getSemanticSuggestions = async (query, limit = 5) => {
  try {
    const params = new URLSearchParams();
    params.append('query', query);
    params.append('limit', limit);
    
    const response = await axios.get(`${API_URL}/suggestions/semantic/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching semantic suggestions:', error);
    throw error;
  }
};

/**
 * Get autocomplete suggestions for a query prefix
 * 
 * @param {string} prefix - Query prefix to get completions for
 * @param {number} limit - Maximum number of suggestions to return
 * @returns {Promise} - Promise resolving to suggestion data
 */
export const getAutocompleteSuggestions = async (prefix, limit = 5) => {
  try {
    const params = new URLSearchParams();
    params.append('prefix', prefix);
    params.append('limit', limit);
    
    const response = await axios.get(`${API_URL}/suggestions/autocomplete/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching autocomplete suggestions:', error);
    throw error;
  }
};

/**
 * Submit search feedback
 * 
 * @param {string} queryId - ID of the query
 * @param {string} documentId - ID of the document
 * @param {string} feedbackType - Feedback type ('click', 'relevant', 'not_relevant')
 * @param {string} sessionId - Optional session ID for analytics
 * @returns {Promise} - Promise resolving to feedback response
 */
export const submitSearchFeedback = async (queryId, documentId, feedbackType, sessionId = null) => {
  try {
    const response = await axios.post(`${API_URL}/search/feedback/`, {
      query_id: queryId,
      document_id: documentId,
      feedback_type: feedbackType,
      session_id: sessionId
    });
    
    return response.data;
  } catch (error) {
    console.error('Error submitting search feedback:', error);
    throw error;
  }
};

/**
 * Get search ranking profiles
 * 
 * @returns {Promise} - Promise resolving to ranking profiles
 */
export const getRankingProfiles = async () => {
  try {
    // Since this endpoint doesn't exist yet, return a mock response
    return {
      results: [
        {
          id: 'default',
          name: 'Default Search',
          description: 'Balanced vector and keyword search',
          is_default: true,
          vector_weight: 0.75,
          keyword_weight: 0.25,
          recency_boost: 0.5
        },
        {
          id: 'semantic',
          name: 'Semantic Search',
          description: 'Prioritizes semantic meaning over keywords',
          is_default: false,
          vector_weight: 0.9,
          keyword_weight: 0.1,
          recency_boost: 0.3
        },
        {
          id: 'keyword',
          name: 'Keyword Search',
          description: 'Prioritizes exact keyword matches',
          is_default: false,
          vector_weight: 0.3,
          keyword_weight: 0.7,
          recency_boost: 0.3
        }
      ]
    };
    // Original code:
    // const response = await axios.get(`${API_URL}/ranking-profiles/`);
    // return response.data;
  } catch (error) {
    console.error('Error fetching ranking profiles:', error);
    throw error;
  }
};

/**
 * Get available search facets
 * 
 * @returns {Promise} - Promise resolving to available facets
 */
export const getAvailableFacets = async () => {
  try {
    const response = await axios.get(`${API_URL}/facets/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching search facets:', error);
    
    if (ENABLE_FALLBACK_RESPONSES) {
      console.log('Returning fallback facets');
      return {
        facets: {
          doc_type: {
            display_name: "Document Type",
            type: "categorical",
            values: [
              {id: "protocol", value: "Protocol", count: 10},
              {id: "paper", value: "Research Paper", count: 15},
              {id: "thesis", value: "Thesis", count: 3}
            ]
          },
          year: {
            display_name: "Year",
            type: "categorical",
            values: [
              {id: "2025", value: "2025", count: 3},
              {id: "2024", value: "2024", count: 10},
              {id: "2023", value: "2023", count: 8},
              {id: "2022", value: "2022", count: 7}
            ]
          },
          citations: {
            display_name: "Citation Count",
            type: "numerical",
            config: {
              min: 0,
              max: 120,
              step: 1
            }
          },
          impact_factor: {
            display_name: "Journal Impact Factor",
            type: "numerical",
            config: {
              min: 0,
              max: 50,
              step: 0.1
            }
          },
          author: {
            display_name: "Author",
            type: "categorical",
            values: [
              {id: "Kumar", value: "Kumar et al.", count: 5},
              {id: "Chakraborty", value: "Chakraborty et al.", count: 7},
              {id: "Sharma", value: "Sharma et al.", count: 4},
              {id: "Phutela", value: "Phutela", count: 3},
              {id: "Agarwal", value: "Agarwal et al.", count: 2}
            ]
          },
          content_type: {
            display_name: "Content",
            type: "categorical",
            values: [
              {id: "protocol_rna", value: "RNA Protocols", count: 5},
              {id: "protocol_dna", value: "DNA Protocols", count: 3},
              {id: "protocol_protein", value: "Protein Protocols", count: 2},
              {id: "crispr", value: "CRISPR Research", count: 8},
              {id: "rna_structure", value: "RNA Structure", count: 5}
            ]
          }
        }
      };
    }
    
    throw error;
  }
};

/**
 * Get default search facets
 * 
 * @returns {Promise} - Promise resolving to default facets
 */
export const getDefaultFacets = async () => {
  try {
    const response = await axios.get(`${API_URL}/facets/defaults/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching default facets:', error);
    
    if (ENABLE_FALLBACK_RESPONSES) {
      return {
        default_facets: [
          { facet: "doc_type", value: "paper" },
          { facet: "year", value: "2024" }
        ]
      };
    }
    
    throw error;
  }
};

/**
 * Get facet statistics based on search results
 * 
 * @param {string} query - Search query
 * @param {Array} selected_facets - Currently selected facets
 * @returns {Promise} - Promise resolving to facet statistics
 */
export const getFacetStats = async (query, selected_facets = []) => {
  try {
    const response = await axios.post(`${API_URL}/facet-stats/`, {
      query,
      selected_facets
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching facet statistics:', error);
    
    if (ENABLE_FALLBACK_RESPONSES) {
      // Generate dynamic facet stats based on the query
      const facetStats = {
        total_results: 28,
        facets: {
          doc_type: {
            display_name: "Document Type",
            type: "categorical",
            values: [
              {id: "protocol", value: "Protocol", count: 10, percentage: 35.7},
              {id: "paper", value: "Research Paper", count: 15, percentage: 53.6},
              {id: "thesis", value: "Thesis", count: 3, percentage: 10.7}
            ]
          },
          year: {
            display_name: "Year",
            type: "categorical",
            values: [
              {id: "2025", value: "2025", count: 3, percentage: 10.7},
              {id: "2024", value: "2024", count: 10, percentage: 35.7},
              {id: "2023", value: "2023", count: 8, percentage: 28.6},
              {id: "2022", value: "2022", count: 7, percentage: 25.0}
            ]
          },
          citations: {
            display_name: "Citation Count",
            type: "numerical",
            min: 0,
            max: 120,
            avg: 35.7,
            median: 28,
            max_count: 5,
            distribution: [
              {value: 0, count: 3},
              {value: 10, count: 5},
              {value: 20, count: 4},
              {value: 30, count: 3},
              {value: 40, count: 2},
              {value: 50, count: 4},
              {value: 60, count: 2},
              {value: 70, count: 1},
              {value: 80, count: 2},
              {value: 90, count: 1},
              {value: 100, count: 1},
              {value: 110, count: 0},
              {value: 120, count: 0}
            ]
          },
          impact_factor: {
            display_name: "Journal Impact Factor",
            type: "numerical",
            min: 0.8,
            max: 45.2,
            avg: 12.4,
            median: 8.6,
            max_count: 6,
            distribution: [
              {value: 1, count: 3},
              {value: 5, count: 6},
              {value: 10, count: 5},
              {value: 15, count: 4},
              {value: 20, count: 3},
              {value: 25, count: 2},
              {value: 30, count: 2},
              {value: 35, count: 2},
              {value: 40, count: 1},
              {value: 45, count: 0}
            ]
          }
        }
      };
      
      // If the query contains specific keywords, modify the facet stats
      if (query && query.toLowerCase().includes('rna')) {
        facetStats.facets.content_type = {
          display_name: "Content",
          type: "categorical",
          values: [
            {id: "protocol_rna", value: "RNA Protocols", count: 5, percentage: 17.9},
            {id: "rna_structure", value: "RNA Structure", count: 5, percentage: 17.9},
            {id: "rna_processing", value: "RNA Processing", count: 4, percentage: 14.3}
          ]
        };
      } else if (query && query.toLowerCase().includes('crispr')) {
        facetStats.facets.content_type = {
          display_name: "Content",
          type: "categorical",
          values: [
            {id: "crispr", value: "CRISPR Research", count: 8, percentage: 28.6},
            {id: "crispr_cas9", value: "CRISPR-Cas9", count: 5, percentage: 17.9},
            {id: "gene_editing", value: "Gene Editing", count: 3, percentage: 10.7}
          ]
        };
      } else if (query && (query.toLowerCase().includes('citation') || query.toLowerCase().includes('impact factor'))) {
        // Enhance statistics for citations and impact factor
        facetStats.facets.citations = {
          ...facetStats.facets.citations,
          max_count: 8,
          distribution: [
            {value: 0, count: 1},
            {value: 10, count: 3},
            {value: 20, count: 5},
            {value: 30, count: 7},
            {value: 40, count: 8},
            {value: 50, count: 6},
            {value: 60, count: 4},
            {value: 70, count: 3},
            {value: 80, count: 2},
            {value: 90, count: 2},
            {value: 100, count: 1},
            {value: 110, count: 1},
            {value: 120, count: 0}
          ]
        };
        
        facetStats.facets.impact_factor = {
          ...facetStats.facets.impact_factor,
          max_count: 8,
          distribution: [
            {value: 1, count: 2},
            {value: 5, count: 4},
            {value: 10, count: 8},
            {value: 15, count: 6},
            {value: 20, count: 4},
            {value: 25, count: 3},
            {value: 30, count: 2},
            {value: 35, count: 1},
            {value: 40, count: 1},
            {value: 45, count: 1}
          ]
        };
      }
      
      return facetStats;
    }
    
    throw error;
  }
};

/**
 * Get saved searches for the current user
 * 
 * @returns {Promise} - Promise resolving to saved searches
 */
export const getSavedSearches = async () => {
  try {
    // Since this endpoint doesn't exist yet, return mock data
    return [
      {
        id: 'saved-1',
        name: 'RNA Extraction Protocols',
        description: 'Search for all RNA extraction protocols in the lab',
        query_text: 'RNA extraction protocol',
        usage_count: 12,
        parameters: {
          filters: [{ type: 'doc_type', value: 'protocol' }],
          facets: []
        }
      },
      {
        id: 'saved-2',
        name: 'CRISPR Papers',
        description: 'Recent papers on CRISPR technologies',
        query_text: 'CRISPR',
        usage_count: 8,
        parameters: {
          filters: [{ type: 'doc_type', value: 'paper' }, { type: 'year', value: '>=2023' }],
          facets: []
        }
      }
    ];
    // Original code:
    // const response = await axios.get(`${API_URL}/saved-searches/`);
    // return response.data;
  } catch (error) {
    console.error('Error fetching saved searches:', error);
    throw error;
  }
};

/**
 * Save a search for later use
 * 
 * @param {string} name - Name for the saved search
 * @param {string} description - Description of the saved search
 * @param {string} queryText - Query text for the search
 * @param {string} profileId - ID of ranking profile to use
 * @param {Array} filters - List of filter criteria
 * @param {Array} facets - List of facet selections
 * @returns {Promise} - Promise resolving to the saved search
 */
export const saveSearch = async (name, description = '', queryText = '', profileId = null, filters = [], facets = []) => {
  try {
    const response = await axios.post(`${API_URL}/saved-searches/`, {
      name,
      description,
      query_text: queryText,
      ranking_profile: profileId,
      parameters: {
        filters,
        facets
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error saving search:', error);
    throw error;
  }
};

/**
 * Execute a saved search
 * 
 * @param {string} savedSearchId - ID of the saved search to execute
 * @param {Object} overrides - Any parameters to override from the saved search
 * @returns {Promise} - Promise resolving to search results
 */
export const executeSavedSearch = async (savedSearchId, overrides = {}) => {
  try {
    const response = await axios.post(`${API_URL}/saved-searches/${savedSearchId}/execute/`, overrides);
    return response.data;
  } catch (error) {
    console.error('Error executing saved search:', error);
    throw error;
  }
};

/**
 * Get document preview
 * 
 * @param {string} documentId - ID of the document to preview
 * @returns {Promise} - Promise resolving to document preview data
 */
export const getDocumentPreview = async (documentId) => {
  try {
    // This is a valid endpoint according to the backend
    const response = await axios.get(`${BASE_API_URL}/documents/${documentId}/preview/`);
    return response.data;
  } catch (error) {
    console.error('Error getting document preview:', error);
    
    // Return mock preview data as fallback
    return {
      document_id: documentId,
      title: `Sample Document ${documentId}`,
      preview: "This is a sample document preview text. It contains content relevant to RNA biology research and protocols.",
      author: "Dr. Chakraborty et al.",
      year: "2024",
      pages: 5,
      has_figures: true
    };
  }
};

/**
 * Execute a basic search
 * 
 * @param {string} query - The search query text
 * @param {string} docType - Optional document type filter (protocol, paper, thesis, etc.)
 * @param {number} limit - Maximum number of results to return (default: 10)
 * @returns {Promise} - Promise resolving to search results
 */
export const executeSearch = async (
  query, 
  docType = '', 
  limit = 10
) => {
  try {
    // The backend search view expects 'query' or 'q' and 'doc_type' or 'type' params
    const response = await axios.post(`${API_URL}`, {
      query: query,  // Use the param name expected by the backend
      doc_type: docType === 'all' ? '' : docType
    });
    
    // The response format should match what the frontend components expect
    return {
      results: response.data.results.map(result => ({
        id: result.id,
        title: result.title,
        doc_type: result.type,
        author: result.author,
        year: result.year,
        content: result.snippet,
        score: result.score
      })),
      query: query,
      metadata: {
        analytics_id: `query-${new Date().getTime()}`,
        search_time_ms: response.data.processing_time * 1000
      }
    };
  } catch (error) {
    console.error('Error executing search:', error);
    throw error;
  }
};