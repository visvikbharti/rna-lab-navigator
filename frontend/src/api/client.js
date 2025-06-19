import axios from 'axios';
import { ApiError, NetworkError, parseError } from '../utils/errorHandler';

// Create axios instance with defaults
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Successful response
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle network errors
    if (!window.navigator.onLine) {
      return Promise.reject(new NetworkError());
    }

    // Handle 401 - Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Try to refresh token
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await apiClient.post('/auth/refresh', { refreshToken });
          const { accessToken } = response.data;
          localStorage.setItem('authToken', accessToken);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }

    // Parse and throw standardized error
    throw parseError(error);
  }
);

/**
 * Make API request with retry logic
 */
export const makeRequest = async (config, options = {}) => {
  const {
    retries = 3,
    retryDelay = 1000,
    onRetry,
    signal,
  } = options;

  let lastError;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await apiClient({
        ...config,
        signal,
      });
      
      return response.data;
    } catch (error) {
      lastError = error;
      
      // Don't retry on certain errors
      if (
        error instanceof ApiError && 
        [400, 401, 403, 404].includes(error.status)
      ) {
        throw error;
      }
      
      // Don't retry if request was cancelled
      if (error.name === 'CanceledError' || error.name === 'AbortError') {
        throw error;
      }
      
      // Last attempt, throw error
      if (attempt === retries) {
        throw error;
      }
      
      // Calculate delay with exponential backoff
      const delay = retryDelay * Math.pow(2, attempt);
      
      if (onRetry) {
        onRetry(attempt + 1, delay, error);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

/**
 * API methods
 */
export const api = {
  // GET request
  get: (url, params = {}, options = {}) => {
    return makeRequest({
      method: 'GET',
      url,
      params,
    }, options);
  },

  // POST request
  post: (url, data = {}, options = {}) => {
    return makeRequest({
      method: 'POST',
      url,
      data,
    }, options);
  },

  // PUT request
  put: (url, data = {}, options = {}) => {
    return makeRequest({
      method: 'PUT',
      url,
      data,
    }, options);
  },

  // PATCH request
  patch: (url, data = {}, options = {}) => {
    return makeRequest({
      method: 'PATCH',
      url,
      data,
    }, options);
  },

  // DELETE request
  delete: (url, options = {}) => {
    return makeRequest({
      method: 'DELETE',
      url,
    }, options);
  },

  // Upload file
  upload: async (url, formData, options = {}) => {
    const { onUploadProgress, ...otherOptions } = options;
    
    return makeRequest({
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onUploadProgress ? (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onUploadProgress(percentCompleted, progressEvent);
      } : undefined,
    }, otherOptions);
  },

  // Stream response (for SSE or large downloads)
  stream: async (url, params = {}, options = {}) => {
    const { onChunk, ...otherOptions } = options;
    
    const response = await apiClient({
      method: 'GET',
      url,
      params,
      responseType: 'stream',
      ...otherOptions,
    });

    if (onChunk) {
      const reader = response.data.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        onChunk(chunk);
      }
    }

    return response;
  },
};

/**
 * Create a cancellable request
 */
export const createCancellableRequest = () => {
  const controller = new AbortController();
  
  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
  };
};

/**
 * Batch multiple requests
 */
export const batchRequests = async (requests, options = {}) => {
  const { maxConcurrent = 5 } = options;
  
  const results = [];
  const errors = [];
  
  // Process in chunks
  for (let i = 0; i < requests.length; i += maxConcurrent) {
    const chunk = requests.slice(i, i + maxConcurrent);
    const chunkResults = await Promise.allSettled(
      chunk.map(request => makeRequest(request, options))
    );
    
    chunkResults.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        results.push({ index: i + index, data: result.value });
      } else {
        errors.push({ index: i + index, error: result.reason });
      }
    });
  }
  
  return { results, errors };
};

export default apiClient;