import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Robust API call hook with error handling, loading states, and cancellation
 */
export const useApiCall = (apiFunction, options = {}) => {
  const {
    onSuccess,
    onError,
    retryCount = 3,
    retryDelay = 1000,
    timeout = 30000,
    enabled = true
  } = options;

  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);
  
  const abortControllerRef = useRef(null);
  const timeoutRef = useRef(null);
  const retryAttemptRef = useRef(0);
  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setRetrying(false);
    retryAttemptRef.current = 0;
  }, []);

  const execute = useCallback(async (...args) => {
    if (!enabled) return;

    // Cancel any in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setLoading(true);
    setError(null);

    // Set timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const timeoutPromise = new Promise((_, reject) => {
      timeoutRef.current = setTimeout(() => {
        abortControllerRef.current?.abort();
        reject(new Error(`Request timeout after ${timeout}ms`));
      }, timeout);
    });

    try {
      // Race between API call and timeout
      const result = await Promise.race([
        apiFunction(...args, { signal }),
        timeoutPromise
      ]);

      if (!isMountedRef.current) return;

      setData(result);
      setLoading(false);
      retryAttemptRef.current = 0;
      
      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err) {
      if (!isMountedRef.current) return;

      // Don't retry if request was aborted
      if (err.name === 'AbortError') {
        setLoading(false);
        return;
      }

      // Retry logic
      if (retryAttemptRef.current < retryCount) {
        retryAttemptRef.current += 1;
        setRetrying(true);
        
        // Exponential backoff
        const delay = retryDelay * Math.pow(2, retryAttemptRef.current - 1);
        
        setTimeout(() => {
          if (isMountedRef.current) {
            execute(...args);
          }
        }, delay);
        
        return;
      }

      // Max retries reached
      setError(err);
      setLoading(false);
      setRetrying(false);
      
      if (onError) {
        onError(err);
      }

      throw err;
    } finally {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    }
  }, [apiFunction, enabled, onSuccess, onError, retryCount, retryDelay, timeout]);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setRetrying(false);
  }, []);

  return {
    data,
    error,
    loading,
    retrying,
    execute,
    cancel,
    reset,
    isError: !!error,
    isSuccess: !!data && !error,
    isLoading: loading || retrying
  };
};

/**
 * Mutation hook for POST/PUT/DELETE operations
 */
export const useApiMutation = (apiFunction, options = {}) => {
  const result = useApiCall(apiFunction, { ...options, enabled: false });
  
  return {
    ...result,
    mutate: result.execute,
    mutateAsync: result.execute
  };
};

/**
 * Query hook for GET operations with automatic execution
 */
export const useApiQuery = (apiFunction, args = [], options = {}) => {
  const { execute, ...result } = useApiCall(apiFunction, options);

  useEffect(() => {
    if (options.enabled !== false) {
      execute(...args);
    }
  }, [...args, options.enabled]);

  return {
    ...result,
    refetch: execute
  };
};