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
 * Detect knowledge gaps in research
 */
export const detectKnowledgeGaps = async ({
  query = null,
  paper_ids = [],
  threshold = 0.5,
  gap_types = null
}) => {
  try {
    const response = await api.post('/knowledge-gaps/', {
      query,
      paper_ids,
      threshold,
      gap_types
    });
    return response.data;
  } catch (error) {
    console.error('Error detecting knowledge gaps:', error);
    throw error;
  }
};

/**
 * Get gap analysis for a specific research area
 */
export const getGapAnalysis = async (researchArea) => {
  try {
    const response = await api.get(`/gap-analysis/?area=${encodeURIComponent(researchArea)}`);
    return response.data;
  } catch (error) {
    console.error('Error getting gap analysis:', error);
    throw error;
  }
};

/**
 * Get topic evolution timeline
 */
export const getTopicEvolution = async ({ topic, start_year = null, end_year = null }) => {
  try {
    const params = new URLSearchParams();
    params.append('topic', topic);
    if (start_year) params.append('start_year', start_year);
    if (end_year) params.append('end_year', end_year);
    
    const response = await api.get(`/topic-evolution/?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error getting topic evolution:', error);
    throw error;
  }
};

/**
 * Get knowledge gap heatmap data
 */
export const getKnowledgeGapHeatmap = async () => {
  try {
    const response = await api.get('/knowledge-gap-heatmap/');
    return response.data;
  } catch (error) {
    console.error('Error getting heatmap data:', error);
    throw error;
  }
};

/**
 * Suggest research questions based on gaps
 */
export const suggestResearchQuestions = async ({ gaps, context = null }) => {
  try {
    const response = await api.post('/suggest-questions/', {
      gaps,
      context
    });
    return response.data;
  } catch (error) {
    console.error('Error suggesting questions:', error);
    throw error;
  }
};

// Export all functions
export default {
  detectKnowledgeGaps,
  getGapAnalysis,
  getTopicEvolution,
  getKnowledgeGapHeatmap,
  suggestResearchQuestions
};