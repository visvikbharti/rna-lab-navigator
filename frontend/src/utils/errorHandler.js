/**
 * Centralized error handling utilities
 */

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.timestamp = new Date().toISOString();
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network connection error') {
    super(message);
    this.name = 'NetworkError';
    this.timestamp = new Date().toISOString();
  }
}

export class ValidationError extends Error {
  constructor(message, fields = {}) {
    super(message);
    this.name = 'ValidationError';
    this.fields = fields;
    this.timestamp = new Date().toISOString();
  }
}

/**
 * Parse error response and return standardized error object
 */
export const parseError = (error) => {
  // Network error
  if (!window.navigator.onLine || error.message === 'Network Error') {
    return new NetworkError();
  }

  // Timeout error
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return new ApiError('Request timeout. Please try again.', 408);
  }

  // API error response
  if (error.response) {
    const { status, data } = error.response;
    
    // Handle specific status codes
    switch (status) {
      case 400:
        return new ValidationError(
          data.message || 'Invalid request',
          data.errors || {}
        );
      case 401:
        return new ApiError('Authentication required', status, data);
      case 403:
        return new ApiError('Access denied', status, data);
      case 404:
        return new ApiError('Resource not found', status, data);
      case 429:
        return new ApiError('Too many requests. Please slow down.', status, data);
      case 500:
        return new ApiError('Server error. Please try again later.', status, data);
      default:
        return new ApiError(
          data.message || `Request failed with status ${status}`,
          status,
          data
        );
    }
  }

  // Aborted request
  if (error.name === 'AbortError') {
    return new ApiError('Request cancelled', 0);
  }

  // Generic error
  return new ApiError(error.message || 'An unexpected error occurred', 0);
};

/**
 * Get user-friendly error message
 */
export const getErrorMessage = (error) => {
  if (error instanceof NetworkError) {
    return 'No internet connection. Please check your network.';
  }

  if (error instanceof ValidationError) {
    const fieldErrors = Object.values(error.fields).flat();
    return fieldErrors.length > 0 
      ? fieldErrors.join(', ')
      : error.message;
  }

  if (error instanceof ApiError) {
    return error.message;
  }

  return 'Something went wrong. Please try again.';
};

/**
 * Error recovery suggestions
 */
export const getErrorRecovery = (error) => {
  if (error instanceof NetworkError) {
    return {
      title: 'Connection Issue',
      actions: [
        { label: 'Check your internet connection', icon: 'wifi' },
        { label: 'Try again in a moment', icon: 'refresh' }
      ]
    };
  }

  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        return {
          title: 'Authentication Required',
          actions: [
            { label: 'Log in', action: '/login', icon: 'login' }
          ]
        };
      case 429:
        return {
          title: 'Rate Limited',
          actions: [
            { label: 'Wait a moment and try again', icon: 'clock' }
          ]
        };
      case 500:
        return {
          title: 'Server Error',
          actions: [
            { label: 'Refresh the page', action: () => window.location.reload(), icon: 'refresh' },
            { label: 'Contact support', action: '/support', icon: 'help' }
          ]
        };
      default:
        return {
          title: 'Error',
          actions: [
            { label: 'Try again', icon: 'refresh' }
          ]
        };
    }
  }

  return {
    title: 'Unexpected Error',
    actions: [
      { label: 'Refresh the page', action: () => window.location.reload(), icon: 'refresh' }
    ]
  };
};

/**
 * Log error for monitoring
 */
export const logError = (error, context = {}) => {
  const errorData = {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    context,
    userAgent: window.navigator.userAgent,
    url: window.location.href
  };

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.error('Error logged:', errorData);
  }

  // Send to error tracking service (e.g., Sentry)
  if (window.Sentry) {
    window.Sentry.captureException(error, {
      extra: context
    });
  }

  // Send to custom analytics
  if (window.analytics) {
    window.analytics.track('Error Occurred', errorData);
  }
};

/**
 * Error notification helper
 */
export const notifyError = (error, options = {}) => {
  const message = getErrorMessage(error);
  const recovery = getErrorRecovery(error);

  // Use your notification system
  if (window.showNotification) {
    window.showNotification({
      type: 'error',
      title: recovery.title,
      message,
      actions: recovery.actions,
      duration: options.duration || 5000
    });
  }

  // Log the error
  logError(error, options.context || {});
};