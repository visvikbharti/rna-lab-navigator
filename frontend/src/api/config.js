/**
 * API Configuration for RNA Lab Navigator
 * Contains configuration and constants for API connectivity
 */

// Base URL for API requests
export const API_BASE_URL = 'http://localhost:8000/api';

// Default timeout for API requests (in milliseconds)
export const API_TIMEOUT = 30000;

// Default headers to include with API requests
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
};

// API endpoints organized by feature
export const ENDPOINTS = {
  // Query endpoints
  QUERY: `${API_BASE_URL}/query/`,
  
  // Search endpoints
  SEARCH: `${API_BASE_URL}/search/`,
  SEARCH_QUALITY: `${API_BASE_URL}/search/quality/`,
  
  // Feedback endpoints
  FEEDBACK: `${API_BASE_URL}/feedback/`,
  FEEDBACK_ANALYTICS: `${API_BASE_URL}/feedback/analytics/`,
  
  // Security endpoints
  SECURITY: `${API_BASE_URL}/security/`,
  SECURITY_DASHBOARD: `${API_BASE_URL}/security/dashboard/`,
  
  // Authentication endpoints
  AUTH: `${API_BASE_URL}/auth/`,
  LOGIN: `${API_BASE_URL}/auth/login/`,
  LOGOUT: `${API_BASE_URL}/auth/logout/`,
};

// Upload endpoints and configuration
export const UPLOAD = {
  PROTOCOL: `${API_BASE_URL}/upload/protocol/`,
  DOCUMENT: `${API_BASE_URL}/upload/document/`,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB in bytes
  ALLOWED_FORMATS: ['.pdf', '.docx', '.doc', '.txt'],
};

// API response status codes
export const STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
};

// API feature flags
export const FEATURES = {
  STREAMING_ENABLED: true,
  ADVANCED_SEARCH_ENABLED: true,
  FEEDBACK_ANALYTICS_ENABLED: true,
};

export default {
  API_BASE_URL,
  API_TIMEOUT,
  DEFAULT_HEADERS,
  ENDPOINTS,
  UPLOAD,
  STATUS,
  FEATURES,
};