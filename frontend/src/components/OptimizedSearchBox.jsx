import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearch, useQuerySuggestions, useSearchFeedback, usePrefetchSearch } from '../hooks/useSearch';
import { useDebounce } from 'react-use';
import AnswerCard from './AnswerCard';
import EnhancedFeedbackForm from './EnhancedFeedbackForm';
import QuerySuggestions from './QuerySuggestions';
import { AnswerCardSkeleton, SearchResultSkeleton, SuggestionSkeleton } from './SkeletonLoaders';
import DocumentPreview from './DocumentPreview';

const OptimizedSearchBox = ({ docType, ranking }) => {
  const [query, setQuery] = useState('');
  const [sessionId] = useState(() => uuidv4());
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [previewDocumentId, setPreviewDocumentId] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());
  
  const inputRef = useRef(null);
  const prefetchSearch = usePrefetchSearch();
  
  // Debounced query for suggestions
  const [debouncedQuery, setDebouncedQuery] = useState('');
  useDebounce(() => setDebouncedQuery(query), 300, [query]);
  
  // Search query with React Query
  const {
    data: searchResults,
    isLoading: isSearching,
    error: searchError,
    refetch: performSearch
  } = useSearch(query, docType, 10, {
    ranking,
    sessionId,
    queryOptions: {
      enabled: false, // Manual trigger
      retry: 1,
    }
  });
  
  // Query suggestions with React Query
  const {
    data: suggestions,
    isLoading: loadingSuggestions
  } = useQuerySuggestions(debouncedQuery, showSuggestions);
  
  // Search feedback mutation
  const { mutate: recordFeedback } = useSearchFeedback();
  
  // Prefetch suggestions on hover
  const handleSuggestionHover = useCallback((suggestionText) => {
    prefetchSearch(suggestionText, docType, 10, { ranking });
  }, [prefetchSearch, docType, ranking]);
  
  // Handle search submission
  const handleSearch = useCallback(async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    
    setShowSuggestions(false);
    await performSearch();
  }, [query, performSearch]);
  
  // Handle suggestion click
  const handleSuggestionClick = useCallback((suggestionText) => {
    setQuery(suggestionText);
    setShowSuggestions(false);
    inputRef.current?.focus();
    
    // Immediately trigger search
    setTimeout(() => handleSearch(), 0);
  }, [handleSearch]);
  
  // Handle feedback
  const handleFeedback = useCallback((documentId, feedbackType) => {
    if (searchResults?.metadata?.query_id) {
      recordFeedback({
        queryId: searchResults.metadata.query_id,
        documentId,
        feedbackType,
        sessionId
      });
    }
  }, [searchResults, recordFeedback, sessionId]);
  
  // Toggle card expansion
  const toggleCardExpansion = useCallback((id) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  }, []);
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Search Input */}
      <form onSubmit={handleSearch} className="relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="relative">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShowSuggestions(true);
              }}
              placeholder="Ask about protocols, papers, or experimental procedures..."
              className="w-full px-6 py-4 pr-24 text-lg bg-white/10 backdrop-blur-sm border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent text-white placeholder-gray-400"
            />
            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200"
            >
              {isSearching ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Searching...
                </span>
              ) : (
                'Search'
              )}
            </button>
          </div>
          
          {/* Query Suggestions */}
          <AnimatePresence>
            {showSuggestions && query.length >= 2 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="absolute z-10 w-full mt-2"
              >
                {loadingSuggestions ? (
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg border border-gray-600/50 p-2">
                    <SuggestionSkeleton />
                  </div>
                ) : suggestions?.length > 0 ? (
                  <QuerySuggestions
                    suggestions={suggestions}
                    onSuggestionClick={handleSuggestionClick}
                    onSuggestionHover={handleSuggestionHover}
                  />
                ) : null}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </form>
      
      {/* Search Results */}
      <AnimatePresence mode="wait">
        {isSearching && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <AnswerCardSkeleton />
            {[...Array(3)].map((_, i) => (
              <SearchResultSkeleton key={i} />
            ))}
          </motion.div>
        )}
        
        {searchError && (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-300"
          >
            <p>Error: {searchError.message}</p>
          </motion.div>
        )}
        
        {searchResults && !isSearching && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Answer Card */}
            {searchResults.answer && (
              <AnswerCard
                answer={searchResults.answer}
                sources={searchResults.sources || []}
                confidence={searchResults.confidence}
                isExpanded={expandedCards.has('answer')}
                onToggleExpand={() => toggleCardExpansion('answer')}
                onSourceClick={setPreviewDocumentId}
              />
            )}
            
            {/* Search Results */}
            {searchResults.results?.map((result, index) => (
              <motion.div
                key={result.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/5 backdrop-blur-sm rounded-lg p-6 border border-gray-600/50 hover:border-gray-500/50 transition-colors"
              >
                <h3 className="text-lg font-semibold text-white mb-2">{result.title}</h3>
                <p className="text-gray-300 mb-4 line-clamp-3">{result.content}</p>
                <div className="flex items-center justify-between">
                  <div className="flex gap-4 text-sm text-gray-400">
                    <span>{result.doc_type}</span>
                    {result.author && <span>{result.author}</span>}
                    {result.year && <span>{result.year}</span>}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleFeedback(result.id, 'relevant')}
                      className="p-2 hover:bg-white/10 rounded transition-colors"
                      title="Mark as relevant"
                    >
                      👍
                    </button>
                    <button
                      onClick={() => handleFeedback(result.id, 'not_relevant')}
                      className="p-2 hover:bg-white/10 rounded transition-colors"
                      title="Mark as not relevant"
                    >
                      👎
                    </button>
                    <button
                      onClick={() => setPreviewDocumentId(result.id)}
                      className="p-2 hover:bg-white/10 rounded transition-colors"
                      title="Preview document"
                    >
                      👁️
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
            
            {/* Feedback Form */}
            {searchResults.metadata?.query_id && (
              <EnhancedFeedbackForm
                queryId={searchResults.metadata.query_id}
                sessionId={sessionId}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Document Preview Modal */}
      {previewDocumentId && (
        <DocumentPreview
          documentId={previewDocumentId}
          onClose={() => setPreviewDocumentId(null)}
        />
      )}
    </div>
  );
};

export default OptimizedSearchBox;