import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Hook to debounce a value
 * @param {any} value - Value to debounce
 * @param {number} delay - Delay in milliseconds
 * @returns {any} Debounced value
 */
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook to create a debounced callback function
 * @param {Function} callback - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @param {Array} dependencies - Dependencies array for useCallback
 * @returns {Function} Debounced function
 */
export const useDebouncedCallback = (callback, delay, dependencies = []) => {
  const timeoutRef = useRef(null);
  const callbackRef = useRef(callback);

  // Update callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args);
    }, delay);
  }, [delay, ...dependencies]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
};

/**
 * Hook for debounced search with loading state
 * @param {Function} searchFunction - Search function to call
 * @param {number} delay - Delay in milliseconds
 * @returns {Object} { search, loading, cancel }
 */
export const useDebouncedSearch = (searchFunction, delay = 300) => {
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef(null);
  const abortControllerRef = useRef(null);

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
  }, []);

  const search = useCallback(async (query) => {
    // Cancel previous search
    cancel();

    if (!query || query.trim() === '') {
      return;
    }

    setLoading(true);

    timeoutRef.current = setTimeout(async () => {
      try {
        // Create new abort controller
        abortControllerRef.current = new AbortController();
        
        await searchFunction(query, { signal: abortControllerRef.current.signal });
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Search error:', error);
          throw error;
        }
      } finally {
        setLoading(false);
      }
    }, delay);
  }, [searchFunction, delay, cancel]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancel();
    };
  }, [cancel]);

  return { search, loading, cancel };
};

/**
 * Hook to track if a value is being actively changed
 * Useful for showing "typing..." indicators
 * @param {any} value - Value to track
 * @param {number} delay - Delay to consider user stopped changing
 * @returns {boolean} isChanging
 */
export const useIsChanging = (value, delay = 1000) => {
  const [isChanging, setIsChanging] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    setIsChanging(true);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      setIsChanging(false);
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, delay]);

  return isChanging;
};