import { useState, useEffect } from 'react';
import axios from 'axios';

const FeedbackAnalyticsSummary = ({ queryId = null, minimal = false }) => {
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFeedbackStats = async () => {
      setLoading(true);
      try {
        // If queryId is provided, fetch stats for this specific query
        // Otherwise, fetch general system stats
        const endpoint = queryId 
          ? `/api/feedback/feedback/${queryId}/stats/` 
          : '/api/feedback/feedback/system-stats/';
        
        const response = await axios.get(endpoint);
        setFeedbackStats(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching feedback stats:', err);
        setError('Failed to load feedback statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchFeedbackStats();
  }, [queryId]);

  if (loading) {
    return minimal ? null : (
      <div className="p-4 text-center text-gray-500">
        Loading feedback statistics...
      </div>
    );
  }

  if (error || !feedbackStats) {
    return minimal ? null : (
      <div className="p-4 text-center text-red-500">
        {error || 'No feedback data available'}
      </div>
    );
  }

  // Minimal version for embedding in other components
  if (minimal) {
    return (
      <div className="text-sm text-gray-600 inline-flex items-center">
        <span className="mr-2">Feedback:</span>
        <span className="flex items-center text-green-600 mr-2">
          <span className="mr-1">👍</span>
          {feedbackStats.positive_count || 0}
        </span>
        <span className="flex items-center text-gray-600 mr-2">
          <span className="mr-1">😐</span>
          {feedbackStats.neutral_count || 0}
        </span>
        <span className="flex items-center text-red-600">
          <span className="mr-1">👎</span>
          {feedbackStats.negative_count || 0}
        </span>
      </div>
    );
  }

  // Full version with detailed statistics
  return (
    <div className="bg-white shadow rounded-lg p-4 mb-6">
      <h3 className="text-lg font-semibold mb-3">Feedback Summary</h3>
      
      <div className="mb-4 grid grid-cols-3 gap-4">
        <div className="bg-green-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-green-600">
            {feedbackStats.positive_count || 0}
          </div>
          <div className="text-sm text-green-800">👍 Positive</div>
        </div>
        
        <div className="bg-gray-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-gray-600">
            {feedbackStats.neutral_count || 0}
          </div>
          <div className="text-sm text-gray-800">😐 Neutral</div>
        </div>
        
        <div className="bg-red-50 p-3 rounded-lg text-center">
          <div className="text-2xl font-bold text-red-600">
            {feedbackStats.negative_count || 0}
          </div>
          <div className="text-sm text-red-800">👎 Negative</div>
        </div>
      </div>
      
      {feedbackStats.total_count > 0 && (
        <>
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Feedback Ratio</h4>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-green-600 h-2.5 rounded-full" 
                style={{ 
                  width: `${(feedbackStats.positive_count / feedbackStats.total_count) * 100}%`,
                  float: 'left'
                }}
              />
              <div 
                className="bg-gray-400 h-2.5 rounded-none" 
                style={{ 
                  width: `${(feedbackStats.neutral_count / feedbackStats.total_count) * 100}%`,
                  float: 'left'
                }}
              />
              <div 
                className="bg-red-600 h-2.5 rounded-full" 
                style={{ 
                  width: `${(feedbackStats.negative_count / feedbackStats.total_count) * 100}%`,
                  float: 'left'
                }}
              />
            </div>
          </div>
          
          {feedbackStats.rating_averages && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Average Ratings</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(feedbackStats.rating_averages).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">
                      {key.replace('_rating', '')}:
                    </span>
                    <div className="flex items-center">
                      <div className="flex text-yellow-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span key={i} className="text-sm">
                            {i < Math.round(value) ? '★' : '☆'}
                          </span>
                        ))}
                      </div>
                      <span className="ml-1 text-sm text-gray-600">
                        ({value.toFixed(1)})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {feedbackStats.common_issues && feedbackStats.common_issues.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Common Issues</h4>
              <ul className="text-sm text-gray-600">
                {feedbackStats.common_issues.slice(0, 5).map((issue, index) => (
                  <li key={index} className="flex items-center justify-between mb-1">
                    <span>{issue.name}</span>
                    <span className="text-gray-500">{issue.count} times</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {feedbackStats.recent_improvements && feedbackStats.recent_improvements.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Improvements</h4>
              <ul className="text-sm text-gray-600 list-disc list-inside">
                {feedbackStats.recent_improvements.slice(0, 3).map((improvement, index) => (
                  <li key={index} className="mb-1">{improvement}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default FeedbackAnalyticsSummary;