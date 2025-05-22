import axios from 'axios';

// Base URL for API calls
const API_URL = '/api/feedback';

/**
 * Submit enhanced feedback
 * @param {Object} feedbackData - The feedback data
 * @param {string} feedbackData.query_id - ID of the query
 * @param {string} feedbackData.rating - Rating (thumbs_up, thumbs_down, neutral)
 * @param {string} feedbackData.comment - User comment
 * @param {Array} feedbackData.specific_issues - List of specific issues
 * @param {string} feedbackData.category - Feedback category
 * @param {number} feedbackData.relevance_rating - Rating for relevance (1-5)
 * @param {number} feedbackData.accuracy_rating - Rating for accuracy (1-5)
 * @param {number} feedbackData.completeness_rating - Rating for completeness (1-5)
 * @param {number} feedbackData.clarity_rating - Rating for clarity (1-5)
 * @param {number} feedbackData.citation_rating - Rating for citation quality (1-5)
 * @param {Array} feedbackData.incorrect_sections - List of incorrect sections
 * @param {string} feedbackData.suggested_answer - User suggested answer
 * @param {Array} feedbackData.source_quality_issues - Issues with the sources
 * @returns {Promise} - Promise resolving to the submitted feedback data
 */
export const submitFeedback = async (feedbackData) => {
  try {
    const response = await axios.post(`${API_URL}/feedback/`, feedbackData);
    return response.data;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    throw error;
  }
};

/**
 * Get feedback for a specific query
 * @param {string} queryId - ID of the query
 * @returns {Promise} - Promise resolving to the feedback data
 */
export const getFeedback = async (queryId) => {
  try {
    const response = await axios.get(`${API_URL}/feedback/?query_history=${queryId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching feedback:', error);
    throw error;
  }
};

/**
 * Get feedback statistics for a specific query
 * @param {string} queryId - ID of the query
 * @returns {Promise} - Promise resolving to the feedback statistics
 */
export const getFeedbackStats = async (queryId) => {
  try {
    const response = await axios.get(`${API_URL}/feedback/${queryId}/stats/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching feedback statistics:', error);
    throw error;
  }
};

/**
 * Get system-wide feedback statistics
 * @returns {Promise} - Promise resolving to the system-wide feedback statistics
 */
export const getSystemFeedbackStats = async () => {
  try {
    const response = await axios.get(`${API_URL}/feedback/system-stats/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching system feedback statistics:', error);
    throw error;
  }
};

/**
 * Get available feedback categories
 * @returns {Promise} - Promise resolving to the list of available categories
 */
export const getFeedbackCategories = async () => {
  try {
    const response = await axios.get(`${API_URL}/categories/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching feedback categories:', error);
    throw error;
  }
};

/**
 * Get feedback themes
 * @param {Object} params - Query parameters
 * @param {string} params.status - Filter by status
 * @param {string} params.priority - Filter by priority
 * @returns {Promise} - Promise resolving to the list of feedback themes
 */
export const getFeedbackThemes = async (params = {}) => {
  try {
    const response = await axios.get(`${API_URL}/themes/`, { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching feedback themes:', error);
    throw error;
  }
};

/**
 * Get feedback analyses
 * @returns {Promise} - Promise resolving to the list of feedback analyses
 */
export const getFeedbackAnalyses = async () => {
  try {
    const response = await axios.get(`${API_URL}/analysis/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching feedback analyses:', error);
    throw error;
  }
};