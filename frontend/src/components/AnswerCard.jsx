import { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import EnhancedFeedbackForm from './EnhancedFeedbackForm';
import FeedbackAnalyticsSummary from './FeedbackAnalyticsSummary';
import FigureDisplay from './FigureDisplay';
import ReasoningTraceDisplay from './ReasoningTraceDisplay';
import FeedbackTracker from './FeedbackTracker';
import ErrorBoundary from './ErrorBoundary';
import { Skeleton } from './enhanced/Loading';
import { parseError, notifyError } from '../utils/errorHandler';

const AnswerCard = ({ response, onSourceClick, isLoading = false }) => {
  // Safe destructuring with defaults
  const { 
    answer = '', 
    sources = [], 
    figures = [], 
    confidence_score = 0, 
    query_id = null, 
    model_used = null, 
    cache_hit = false, 
    reasoning_trace = null, 
    knowledge_gaps = [], 
    follow_up_questions = [], 
    is_multihop = false 
  } = response || {};
  
  const [showModelInfo, setShowModelInfo] = useState(false);
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);

  // Memoize confidence level calculation
  const confidenceLevel = useMemo(() => {
    const score = parseFloat(confidence_score) || 0;
    if (score >= 0.7) return { text: 'High', color: 'bg-green-100 text-green-800' };
    if (score >= 0.45) return { text: 'Medium', color: 'bg-yellow-100 text-yellow-800' };
    return { text: 'Low', color: 'bg-red-100 text-red-800' };
  }, [confidence_score]);

  // Handle feedback submission with error handling
  const handleFeedbackSubmit = useCallback(async (feedback) => {
    setFeedbackSubmitting(true);
    try {
      // API call would go here
      console.log('Feedback submitted:', feedback);
      // Show success notification
      if (window.showNotification) {
        window.showNotification({
          type: 'success',
          message: 'Thank you for your feedback!'
        });
      }
    } catch (error) {
      const parsedError = parseError(error);
      notifyError(parsedError, { context: { action: 'submit_feedback' } });
    } finally {
      setFeedbackSubmitting(false);
    }
  }, []);

  const toggleModelInfo = useCallback(() => {
    setShowModelInfo(prev => !prev);
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mt-4">
        <Skeleton variant="text" lines={1} className="mb-4 w-32" />
        <Skeleton variant="text" lines={3} className="mb-6" />
        <Skeleton variant="rectangular" height={100} className="mb-4" />
        <Skeleton variant="text" lines={2} />
      </div>
    );
  }

  // No response state
  if (!response || !answer) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mt-4">
        <p className="text-gray-500 dark:text-gray-400 text-center">
          No answer available
        </p>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mt-4">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold text-lg text-gray-800 dark:text-gray-200">Answer</h3>
        <div className="flex flex-col items-end gap-2">
          <span
            className={`${confidenceLevel.color} text-xs font-medium px-2.5 py-0.5 rounded`}
            aria-label={`Confidence level: ${confidenceLevel.text}`}
          >
            {confidenceLevel.text} confidence ({Math.round((confidence_score || 0) * 100)}%)
          </span>
          
          {cache_hit && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
              Cached Response
            </span>
          )}
          
          {model_used && (
            <button 
              className="text-xs text-gray-500 hover:text-gray-700 underline"
              onClick={toggleModelInfo}
              aria-expanded={showModelInfo}
              aria-controls="model-info"
            >
              {showModelInfo ? 'Hide model info' : 'Show model info'}
            </button>
          )}
        </div>
      </div>
      
      {showModelInfo && model_used && (
        <div id="model-info" className="bg-gray-50 p-2 mb-4 rounded text-xs text-gray-600">
          Model: {model_used}
          {query_id && (
            <div className="mt-1">
              <ErrorBoundary fallback={() => <span>Unable to load analytics</span>}>
                <FeedbackAnalyticsSummary queryId={query_id} minimal={true} />
              </ErrorBoundary>
            </div>
          )}
        </div>
      )}
      
      <div className="prose max-w-none mb-6">
        <p className="text-gray-700 dark:text-gray-300">
          {answer || 'No answer available'}
        </p>
      </div>
      
      {/* Reasoning Trace - Show for multi-hop queries */}
      {is_multihop && reasoning_trace && (
        <div className="mb-6">
          <ErrorBoundary fallback={() => <p className="text-sm text-gray-500">Unable to display reasoning trace</p>}>
            <ReasoningTraceDisplay 
              reasoningTrace={reasoning_trace}
              knowledgeGaps={knowledge_gaps || []}
              followUpQuestions={follow_up_questions || []}
            />
          </ErrorBoundary>
        </div>
      )}
      
      {/* Display figures if available */}
      {Array.isArray(figures) && figures.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium text-sm text-gray-500 dark:text-gray-400 mb-3">Relevant Figures:</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {figures.map((figure, index) => (
              <ErrorBoundary key={figure?.figure_id || index} fallback={() => <div className="text-sm text-gray-500">Figure unavailable</div>}>
                <FigureDisplay figure={figure} />
              </ErrorBoundary>
            ))}
          </div>
        </div>
      )}
      
      {Array.isArray(sources) && sources.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-sm text-gray-500 dark:text-gray-400 mb-2">Sources:</h4>
          <ul className="space-y-1" role="list">
            {sources.map((source, index) => (
              <li 
                key={source?.id || index} 
                className="text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer"
                onClick={() => onSourceClick && source?.id && onSourceClick(source.id)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && onSourceClick && source?.id) {
                    onSourceClick(source.id);
                  }
                }}
              >
                {source?.title || 'Untitled'} ({source?.doc_type || 'Unknown'}
                {source?.author ? `, ${source.author}` : ''})
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Show feedback tracker for all responses with query_id */}
      {query_id && (
        <ErrorBoundary fallback={() => null}>
          <FeedbackTracker queryId={query_id} />
        </ErrorBoundary>
      )}
      
      {/* Show enhanced feedback form for non-cached responses */}
      {query_id && !cache_hit && (
        <ErrorBoundary fallback={() => <p className="text-sm text-gray-500">Feedback unavailable</p>}>
          <EnhancedFeedbackForm 
            queryId={query_id}
            onFeedbackSubmit={handleFeedbackSubmit}
            isSubmitting={feedbackSubmitting}
          />
        </ErrorBoundary>
      )}
      </div>
    </ErrorBoundary>
  );
};

// PropTypes validation
AnswerCard.propTypes = {
  response: PropTypes.shape({
    answer: PropTypes.string,
    sources: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      title: PropTypes.string,
      doc_type: PropTypes.string,
      author: PropTypes.string
    })),
    figures: PropTypes.array,
    confidence_score: PropTypes.number,
    query_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    model_used: PropTypes.string,
    cache_hit: PropTypes.bool,
    reasoning_trace: PropTypes.any,
    knowledge_gaps: PropTypes.array,
    follow_up_questions: PropTypes.array,
    is_multihop: PropTypes.bool
  }),
  onSourceClick: PropTypes.func,
  isLoading: PropTypes.bool
};

AnswerCard.defaultProps = {
  response: {},
  onSourceClick: null,
  isLoading: false
};

export default AnswerCard;