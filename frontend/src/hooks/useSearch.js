import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchDocuments, getQuerySuggestions } from '../api/search';
import { recordSearchFeedback } from '../api/feedback';

// Hook for search queries with caching
export function useSearch(queryText, docType = null, limit = 10, options = {}) {
  return useQuery({
    queryKey: ['search', queryText, docType, limit, options.filters, options.facets],
    queryFn: () => searchDocuments(queryText, docType, limit, options),
    enabled: !!queryText && queryText.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    ...options.queryOptions,
  });
}

// Hook for query suggestions
export function useQuerySuggestions(partialQuery, enabled = true) {
  return useQuery({
    queryKey: ['suggestions', partialQuery],
    queryFn: () => getQuerySuggestions(partialQuery),
    enabled: enabled && partialQuery && partialQuery.length >= 2,
    staleTime: 10 * 60 * 1000, // 10 minutes
    cacheTime: 15 * 60 * 1000, // 15 minutes
  });
}

// Hook for popular queries
export function usePopularQueries(limit = 10, category = null) {
  return useQuery({
    queryKey: ['popular-queries', limit, category],
    queryFn: async () => {
      const response = await fetch(
        `/api/search/suggestions/popular/?limit=${limit}${category ? `&category=${category}` : ''}`
      );
      if (!response.ok) throw new Error('Failed to fetch popular queries');
      return response.json();
    },
    staleTime: 30 * 60 * 1000, // 30 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  });
}

// Hook for trending queries
export function useTrendingQueries(limit = 10, days = 7) {
  return useQuery({
    queryKey: ['trending-queries', limit, days],
    queryFn: async () => {
      const response = await fetch(
        `/api/search/suggestions/trending/?limit=${limit}&days=${days}`
      );
      if (!response.ok) throw new Error('Failed to fetch trending queries');
      return response.json();
    },
    staleTime: 15 * 60 * 1000, // 15 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });
}

// Hook for recording search feedback
export function useSearchFeedback() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ queryId, documentId, feedbackType, sessionId }) =>
      recordSearchFeedback(queryId, documentId, feedbackType, sessionId),
    onSuccess: () => {
      // Optionally invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['search-analytics'] });
    },
  });
}

// Hook for prefetching search results
export function usePrefetchSearch() {
  const queryClient = useQueryClient();
  
  return (queryText, docType = null, limit = 10, options = {}) => {
    return queryClient.prefetchQuery({
      queryKey: ['search', queryText, docType, limit, options.filters, options.facets],
      queryFn: () => searchDocuments(queryText, docType, limit, options),
      staleTime: 5 * 60 * 1000,
    });
  };
}

// Hook for search with optimistic updates
export function useOptimisticSearch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ queryText, docType, limit, options }) =>
      searchDocuments(queryText, docType, limit, options),
    onMutate: async ({ queryText }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['search'] });
      
      // Optimistically update to show loading state
      const previousData = queryClient.getQueryData(['search', queryText]);
      
      return { previousData };
    },
    onError: (err, variables, context) => {
      // Revert the optimistic update
      if (context?.previousData) {
        queryClient.setQueryData(
          ['search', variables.queryText],
          context.previousData
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ 
        queryKey: ['search', variables.queryText] 
      });
    },
  });
}