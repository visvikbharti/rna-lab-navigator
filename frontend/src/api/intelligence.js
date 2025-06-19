import axios from 'axios';
import { API_BASE_URL } from './config';

const api = axios.create({
  baseURL: `${API_BASE_URL}/intelligence`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add CSRF token to requests
api.interceptors.request.use(config => {
  const token = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  
  if (token) {
    config.headers['X-CSRFToken'] = token;
  }
  
  return config;
});

/**
 * Generate cross-paper insights
 */
export const generateCrossPaperInsights = async ({
  query,
  paper_ids = [],
  insight_types = null,
  min_confidence = 0.6
}) => {
  try {
    const response = await api.post('/cross-paper-insights/', {
      query,
      paper_ids,
      insight_types,
      min_confidence
    });
    return response.data;
  } catch (error) {
    console.error('Error generating insights:', error);
    throw error;
  }
};

/**
 * Get research connection graph
 */
export const getResearchConnections = async ({
  query = null,
  paper_ids = null,
  connection_types = null
}) => {
  try {
    const params = new URLSearchParams();
    
    if (query) params.append('query', query);
    if (paper_ids) params.append('paper_ids', paper_ids);
    if (connection_types) params.append('connection_types', connection_types);
    
    const response = await api.get(`/research-connections/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error getting research connections:', error);
    throw error;
  }
};

/**
 * Validate a research connection/insight
 */
export const validateConnection = async ({ insight }) => {
  try {
    const response = await api.post('/validate-connection/', { insight });
    return response.data;
  } catch (error) {
    console.error('Error validating connection:', error);
    throw error;
  }
};

/**
 * Rank insights by relevance and quality
 */
export const rankInsights = async ({
  insights,
  user_query = null,
  preferences = {}
}) => {
  try {
    const response = await api.post('/rank-insights/', {
      insights,
      user_query,
      preferences
    });
    return response.data;
  } catch (error) {
    console.error('Error ranking insights:', error);
    throw error;
  }
};

/**
 * Get trending research connections
 */
export const getTrendingConnections = async () => {
  try {
    const response = await api.get('/trending-connections/');
    return response.data;
  } catch (error) {
    console.error('Error getting trending connections:', error);
    throw error;
  }
};

// Export all functions
export default {
  generateCrossPaperInsights,
  getResearchConnections,
  validateConnection,
  rankInsights,
  getTrendingConnections
};