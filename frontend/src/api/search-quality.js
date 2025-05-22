import axios from 'axios';

/**
 * Get search quality summary metrics
 * @returns {Promise} - Promise resolving to the search quality metrics
 */
export const getSearchQualitySummary = async () => {
  try {
    const response = await axios.get('/api/search/quality/');
    return response.data;
  } catch (error) {
    console.error('Error fetching search quality metrics:', error);
    throw error;
  }
};

/**
 * Get search quality metrics broken down by document type
 * @returns {Promise} - Promise resolving to the quality metrics by document type
 */
export const getQualityByDocType = async () => {
  try {
    const response = await axios.get('/api/search/quality/quality_by_doc_type/');
    return response.data;
  } catch (error) {
    console.error('Error fetching quality metrics by doc type:', error);
    throw error;
  }
};

/**
 * Get search quality metrics broken down by ranking profile
 * @returns {Promise} - Promise resolving to the quality metrics by ranking profile
 */
export const getQualityByRankingProfile = async () => {
  try {
    const response = await axios.get('/api/search/quality/quality_by_ranking_profile/');
    return response.data;
  } catch (error) {
    console.error('Error fetching quality metrics by ranking profile:', error);
    throw error;
  }
};

/**
 * Get metrics showing the impact of reranking on search quality
 * @returns {Promise} - Promise resolving to reranking impact metrics
 */
export const getRerankingImpact = async () => {
  try {
    const response = await axios.get('/api/search/quality/reranking_impact/');
    return response.data;
  } catch (error) {
    console.error('Error fetching reranking impact metrics:', error);
    throw error;
  }
};

/**
 * Get common issues reported in search-related feedback
 * @returns {Promise} - Promise resolving to categorized issues with counts
 */
export const getSearchIssues = async () => {
  try {
    const response = await axios.get('/api/search/quality/common_issues/');
    return response.data;
  } catch (error) {
    console.error('Error fetching search issues:', error);
    throw error;
  }
};

/**
 * Get search performance metrics over time
 * @param {Object} params - Query parameters
 * @param {number} params.days - Number of days to look back (default 30)
 * @param {string} params.interval - Interval for grouping (day, week, month) (default 'day')
 * @returns {Promise} - Promise resolving to time series data for search performance metrics
 */
export const getSearchPerformanceOverTime = async (params = {}) => {
  try {
    const response = await axios.get('/api/search/quality/performance_over_time/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching search performance over time:', error);
    throw error;
  }
};