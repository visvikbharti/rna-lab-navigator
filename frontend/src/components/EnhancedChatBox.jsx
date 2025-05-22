import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import AnswerCard from './AnswerCard';
import EnhancedFeedbackForm from './EnhancedFeedbackForm';
import QuerySuggestions from './QuerySuggestions';
import SearchRankingSelector from './SearchRankingSelector';
import { submitQuery } from '../api/query';
import { enhancedSearch, submitSearchFeedback } from '../api/search';

const EnhancedChatBox = ({ docType }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamMetadata, setStreamMetadata] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [selectedProfileId, setSelectedProfileId] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const eventSourceRef = useRef(null);
  const inputRef = useRef(null);

  // Create a session ID on component mount
  useEffect(() => {
    setSessionId(uuidv4());
  }, []);
  
  // Clean up EventSource on unmount or when starting a new query
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSuggestionClick = (suggestionText) => {
    setQuery(suggestionText);
    setShowSuggestions(false);
    
    // Focus the input
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };
  
  const handleSearchWithRanking = async () => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    setResponse(null);
    setError(null);
    setStreamedAnswer('');
    setStreamMetadata(null);
    setShowSuggestions(false);
    
    try {
      // Use the enhanced search API
      const result = await enhancedSearch(
        query,
        docType === 'all' ? '' : docType,
        selectedProfileId,
        10,
        sessionId
      );
      
      setResponse(result);
      setIsLoading(false);
    } catch (error) {
      console.error('Error with enhanced search:', error);
      setError('Sorry, there was an error with the enhanced search. Falling back to standard search.');
      
      // Fall back to the standard search
      try {
        const result = await submitQuery(query, docType);
        setResponse(result);
      } catch (fallbackError) {
        console.error('Fallback search also failed:', fallbackError);
        setError('Sorry, there was an error processing your request. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleStreamingSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setIsLoading(true);
    setResponse(null);
    setError(null);
    setStreamedAnswer('');
    setStreamMetadata(null);
    setShowSuggestions(false);
    
    // Close any existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    try {
      // Use streaming mode
      setIsStreaming(true);
      
      // Set up SSE connection
      const eventSource = new EventSource(`/api/query/?stream=true`);
      eventSourceRef.current = eventSource;
      
      // Post query data separately
      const requestBody = {
        query,
        doc_type: docType === 'all' ? '' : docType,
        use_hybrid: true,
        hybrid_alpha: 0.75,
        session_id: sessionId
      };
      
      // Post the query data
      fetch('/api/query/?stream=true', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      // Set up event handlers
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'metadata') {
          // Initial metadata with sources
          setStreamMetadata(data);
        } else if (data.type === 'content') {
          // Content streaming
          setStreamedAnswer(prev => prev + data.content);
        } else if (data.type === 'final') {
          // Final metadata (confidence, status)
          setStreamMetadata(prev => ({ ...prev, ...data }));
          setIsLoading(false);
          setIsStreaming(false);
          
          // Close the EventSource
          eventSource.close();
          eventSourceRef.current = null;
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        setError('Error with streaming connection. Please try again.');
        setIsLoading(false);
        setIsStreaming(false);
        eventSource.close();
        eventSourceRef.current = null;
      };
    } catch (error) {
      console.error('Error querying API:', error);
      setError('Sorry, there was an error processing your request. Please try again.');
      setIsLoading(false);
      setIsStreaming(false);
      
      // Fall back to enhanced search
      try {
        await handleSearchWithRanking();
      } catch (fallbackError) {
        console.error('Fallback query also failed:', fallbackError);
      }
    }
  };
  
  const handleResultClick = (documentId) => {
    // Only record feedback if we have the necessary IDs
    if (streamMetadata?.query_id && documentId) {
      submitSearchFeedback(
        streamMetadata.query_id,
        documentId,
        'click',
        sessionId
      ).catch(error => {
        console.error('Error recording click feedback:', error);
      });
    }
  };

  // Determine what to display (streaming or regular response)
  const showStreamingAnswer = isStreaming || (streamedAnswer && streamMetadata);
  const showRegularAnswer = !showStreamingAnswer && response;

  return (
    <div className="mt-6">
      <form onSubmit={handleStreamingSearch} className="mb-4">
        <div className="flex flex-col gap-2">
          <div className="flex flex-col md:flex-row gap-2">
            <div className="flex-grow relative">
              <textarea
                ref={inputRef}
                className="w-full border rounded-lg p-3 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Ask about protocols, papers, or theses..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
              />
              
              {/* Query suggestions */}
              {showSuggestions && query && !isLoading && (
                <div className="absolute w-full z-10">
                  <QuerySuggestions
                    query={query}
                    onSuggestionClick={handleSuggestionClick}
                    showPopular={query.length < 2}
                    showTrending={query.length < 2}
                    showSemantic={query.length >= 5}
                    showAutocomplete={query.length >= 2}
                  />
                </div>
              )}
            </div>
            
            <div className="flex flex-col md:flex-row gap-2 md:self-end">
              <SearchRankingSelector
                selectedProfileId={selectedProfileId}
                onProfileChange={setSelectedProfileId}
                className="w-full md:w-auto"
              />
              
              <button
                type="submit"
                className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-6 rounded-lg shadow-sm transition duration-150 ease-in-out"
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? 'Searching...' : 'Ask'}
              </button>
            </div>
          </div>
          
          {/* Search options */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-gray-500">
            <div className="flex items-center">
              <input
                type="radio"
                id="stream-mode"
                name="search-mode"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                checked={true}
                onChange={() => {}} // We're not implementing toggle in this version
              />
              <label htmlFor="stream-mode" className="ml-2">
                Stream answer (faster)
              </label>
            </div>
          </div>
        </div>
      </form>

      {isLoading && !showStreamingAnswer && (
        <div className="text-center py-10">
          <div className="animate-pulse">Searching for information...</div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-4">
          {error}
        </div>
      )}

      {/* Streaming Answer */}
      {showStreamingAnswer && streamMetadata && (
        <div className="bg-white rounded-lg shadow-md p-6 mt-4">
          <div className="flex justify-between items-start mb-4">
            <h3 className="font-semibold text-lg text-gray-800">Answer</h3>
            <div className="flex flex-col items-end gap-2">
              {streamMetadata.confidence_score && (
                <span
                  className={`${
                    streamMetadata.confidence_score >= 0.7
                      ? 'bg-green-100 text-green-800'
                      : streamMetadata.confidence_score >= 0.45
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  } text-xs font-medium px-2.5 py-0.5 rounded`}
                >
                  {streamMetadata.confidence_score >= 0.7
                    ? 'High'
                    : streamMetadata.confidence_score >= 0.45
                    ? 'Medium'
                    : 'Low'} confidence ({Math.round((streamMetadata.confidence_score || 0) * 100)}%)
                </span>
              )}
              
              {streamMetadata.model_used && (
                <span className="text-xs text-gray-500">
                  Model: {streamMetadata.model_used}
                </span>
              )}
            </div>
          </div>
          
          <div className="prose max-w-none mb-6">
            <p className="text-gray-700">
              {streamedAnswer}
              {isStreaming && (
                <span className="inline-block animate-pulse">▎</span>
              )}
            </p>
          </div>
          
          {streamMetadata.sources && streamMetadata.sources.length > 0 && (
            <div className="mb-4">
              <h4 className="font-medium text-sm text-gray-500 mb-2">Sources:</h4>
              <ul className="space-y-1">
                {streamMetadata.sources.map((source, index) => (
                  <li 
                    key={index} 
                    className="text-sm text-gray-600 hover:text-primary-600 cursor-pointer"
                    onClick={() => handleResultClick(source.id)}
                  >
                    {source.title} ({source.doc_type}
                    {source.author ? `, ${source.author}` : ''})
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Show enhanced feedback form when streaming is complete and we have a query_id */}
          {!isStreaming && streamMetadata.query_id && (
            <>
              <EnhancedFeedbackForm 
                queryId={streamMetadata.query_id} 
                onFeedbackSubmit={(feedback) => {
                  console.log('Feedback submitted:', feedback);
                }}
              />
            </>
          )}
        </div>
      )}

      {/* Regular Answer */}
      {showRegularAnswer && (
        <AnswerCard 
          response={response} 
          onSourceClick={handleResultClick}
        />
      )}
      
      {/* Low Confidence Warning */}
      {(showRegularAnswer && response.status === 'low_confidence') || 
       (showStreamingAnswer && streamMetadata && streamMetadata.status === 'low_confidence') ? (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
          <p className="text-sm">
            <strong>Note:</strong> The system has low confidence in this answer. 
            Consider rephrasing your query or checking additional sources.
          </p>
        </div>
      ) : null}
    </div>
  );
};

export default EnhancedChatBox;