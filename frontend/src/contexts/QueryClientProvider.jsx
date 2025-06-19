import { QueryClient, QueryClientProvider as TanstackQueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Create a client with optimal caching settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Keep data fresh for 5 minutes
      staleTime: 5 * 60 * 1000,
      // Cache data for 10 minutes
      cacheTime: 10 * 60 * 1000,
      // Retry failed requests twice
      retry: 2,
      // Refetch on window focus
      refetchOnWindowFocus: false,
      // Don't refetch on mount if data is fresh
      refetchOnMount: 'always',
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
});

export function QueryClientProvider({ children }) {
  return (
    <TanstackQueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </TanstackQueryClientProvider>
  );
}

export { queryClient };