import { useState, useEffect, useRef } from 'react';
import AnswerCard from './AnswerCard';
import EnhancedFeedbackForm from './EnhancedFeedbackForm';
import FeedbackAnalyticsSummary from './FeedbackAnalyticsSummary';
import { submitQuery } from '../api/query';

const ChatBox = ({ docType }) => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [streamedAnswer, setStreamedAnswer] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamMetadata, setStreamMetadata] = useState(null);
  const eventSourceRef = useRef(null);

  // Clean up EventSource on unmount or when starting a new query
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setIsLoading(true);
    setResponse(null);
    setError(null);
    setStreamedAnswer('');
    setStreamMetadata(null);
    
    // Close any existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    try {
      // Use streaming mode
      setIsStreaming(true);
      
      // Set up SSE connection using Vite's proxy
      const eventSource = new EventSource(`/api/query/?stream=true`);
      eventSourceRef.current = eventSource;
      
      // Post query data separately
      const requestBody = {
        query,
        doc_type: docType === 'all' ? '' : docType,
        use_hybrid: true,
        hybrid_alpha: 0.75
      };
      
      // Post the query data with the correct URL through proxy
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
      
      // Fall back to non-streaming mode using our fixed executeSearch function
      try {
        const result = await submitQuery(query, docType, false);
        setResponse(result);
        setIsLoading(false);
      } catch (fallbackError) {
        console.error('Fallback query also failed:', fallbackError);
        setError('Sorry, there was an error processing your request. Please try again later.');
        setIsLoading(false);
      }
    }
  };

  // Determine what to display (streaming or regular response)
  const showStreamingAnswer = isStreaming || (streamedAnswer && streamMetadata);
  const showRegularAnswer = !showStreamingAnswer && response;

  return (
    <div className="mt-6">
      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex flex-col md:flex-row gap-2">
          <textarea
            className="flex-grow border rounded-lg p-3 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Ask about protocols, papers, or theses..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-6 rounded-lg shadow-sm transition duration-150 ease-in-out md:self-end"
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? 'Searching...' : 'Ask'}
          </button>
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
                  <li key={index} className="text-sm text-gray-600">
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
      {showRegularAnswer && <AnswerCard response={response} />}
      
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

export default ChatBox;