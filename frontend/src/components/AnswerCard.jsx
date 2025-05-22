import { useState } from 'react';
import EnhancedFeedbackForm from './EnhancedFeedbackForm';
import FeedbackAnalyticsSummary from './FeedbackAnalyticsSummary';
import FigureDisplay from './FigureDisplay';

const AnswerCard = ({ response, onSourceClick }) => {
  const { answer, sources, figures, confidence_score, query_id, model_used, cache_hit } = response;
  const [showModelInfo, setShowModelInfo] = useState(false);

  // Function to determine confidence level styling
  const getConfidenceLevel = (score) => {
    if (score >= 0.7) return { text: 'High', color: 'bg-green-100 text-green-800' };
    if (score >= 0.45) return { text: 'Medium', color: 'bg-yellow-100 text-yellow-800' };
    return { text: 'Low', color: 'bg-red-100 text-red-800' };
  };

  const confidenceLevel = getConfidenceLevel(confidence_score);

  // Handle feedback submission
  const handleFeedbackSubmit = (feedback) => {
    console.log('Feedback submitted:', feedback);
    // Could add additional logic here (e.g., show a thank you message)
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-4">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold text-lg text-gray-800">Answer</h3>
        <div className="flex flex-col items-end gap-2">
          <span
            className={`${confidenceLevel.color} text-xs font-medium px-2.5 py-0.5 rounded`}
          >
            {confidenceLevel.text} confidence ({Math.round(confidence_score * 100)}%)
          </span>
          
          {cache_hit && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
              Cached Response
            </span>
          )}
          
          {model_used && (
            <button 
              className="text-xs text-gray-500 hover:text-gray-700 underline"
              onClick={() => setShowModelInfo(!showModelInfo)}
            >
              {showModelInfo ? 'Hide model info' : 'Show model info'}
            </button>
          )}
        </div>
      </div>
      
      {showModelInfo && model_used && (
        <div className="bg-gray-50 p-2 mb-4 rounded text-xs text-gray-600">
          Model: {model_used}
          {query_id && (
            <div className="mt-1">
              <FeedbackAnalyticsSummary queryId={query_id} minimal={true} />
            </div>
          )}
        </div>
      )}
      
      <div className="prose max-w-none mb-6">
        <p className="text-gray-700">{answer}</p>
      </div>
      
      {/* Display figures if available */}
      {figures && figures.length > 0 && (
        <div className="mb-6">
          <h4 className="font-medium text-sm text-gray-500 mb-3">Relevant Figures:</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {figures.map((figure, index) => (
              <FigureDisplay key={figure.figure_id || index} figure={figure} />
            ))}
          </div>
        </div>
      )}
      
      {sources && sources.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-sm text-gray-500 mb-2">Sources:</h4>
          <ul className="space-y-1">
            {sources.map((source, index) => (
              <li 
                key={index} 
                className="text-sm text-gray-600 hover:text-primary-600 cursor-pointer"
                onClick={() => onSourceClick && onSourceClick(source.id)}
              >
                {source.title} ({source.doc_type}
                {source.author ? `, ${source.author}` : ''})
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Show enhanced feedback form for non-cached responses */}
      {query_id && !cache_hit && (
        <EnhancedFeedbackForm 
          queryId={query_id}
          onFeedbackSubmit={handleFeedbackSubmit}
        />
      )}
    </div>
  );
};

export default AnswerCard;