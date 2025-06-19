import axios from 'axios';
import { mockSearchQualitySummary, mockQualityByDocType, mockPerformanceData } from '../utils/mockData';

/**
 * Get search quality summary metrics
 * @returns {Promise} - Promise resolving to the search quality metrics
 */
export const getSearchQualitySummary = async () => {
  try {
    // Return mock data - endpoint not implemented yet
    return mockSearchQualitySummary;
  } catch (error) {
    console.error('Error fetching search quality metrics:', error);
    return mockSearchQualitySummary;
  }
};

/**
 * Get search quality metrics broken down by document type
 * @returns {Promise} - Promise resolving to the quality metrics by document type
 */
export const getQualityByDocType = async () => {
  try {
    // Return mock data - endpoint not implemented yet
    return mockQualityByDocType;
  } catch (error) {
    console.error('Error fetching quality metrics by doc type:', error);
    return mockQualityByDocType;
  }
};

/**
 * Get search quality metrics broken down by ranking profile
 * @returns {Promise} - Promise resolving to the quality metrics by ranking profile
 */
export const getQualityByRankingProfile = async () => {
  try {
    // Return mock data - endpoint not implemented yet
    return {
      profiles: [
        { profile: "default", avg_confidence: 0.82, searches: 892 },
        { profile: "semantic", avg_confidence: 0.85, searches: 423 },
        { profile: "keyword", avg_confidence: 0.78, searches: 227 }
      ]
    };
  } catch (error) {
    console.error('Error fetching quality metrics by ranking profile:', error);
    return { profiles: [] };
  }
};

/**
 * Get metrics showing the impact of reranking on search quality
 * @returns {Promise} - Promise resolving to reranking impact metrics
 */
export const getRerankingImpact = async () => {
  try {
    // Return mock data - endpoint not implemented yet
    return {
      before_reranking: { avg_score: 0.68, top1_accuracy: 0.52 },
      after_reranking: { avg_score: 0.84, top1_accuracy: 0.78 },
      improvement: { score_increase: "+23.5%", accuracy_increase: "+50%" }
    };
  } catch (error) {
    console.error('Error fetching reranking impact metrics:', error);
    return { before_reranking: {}, after_reranking: {} };
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