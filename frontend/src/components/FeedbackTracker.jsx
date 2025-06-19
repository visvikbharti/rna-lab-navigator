import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { API_BASE_URL } from '../api/config';

const FeedbackTracker = ({ queryId }) => {
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchFeedbackStats();
  }, [queryId]);

  const fetchFeedbackStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/feedback/?query_history_id=${queryId}`);
      const feedbackData = response.data.results || response.data;
      
      // Calculate stats
      const stats = {
        total: feedbackData.length,
        positive: feedbackData.filter(f => f.rating === 'thumbs_up').length,
        negative: feedbackData.filter(f => f.rating === 'thumbs_down').length,
        neutral: feedbackData.filter(f => f.rating === 'neutral').length,
        comments: feedbackData.filter(f => f.comment).map(f => ({
          rating: f.rating,
          comment: f.comment,
          created_at: f.created_at
        }))
      };
      
      setFeedbackStats(stats);
    } catch (error) {
      console.error('Error fetching feedback stats:', error);
      // Set empty stats on error
      setFeedbackStats({
        total: 0,
        positive: 0,
        negative: 0,
        neutral: 0,
        comments: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) return null;
  if (!feedbackStats || feedbackStats.total === 0) return null;

  const positivePercentage = (feedbackStats.positive / feedbackStats.total) * 100;
  const negativePercentage = (feedbackStats.negative / feedbackStats.total) * 100;
  const neutralPercentage = (feedbackStats.neutral / feedbackStats.total) * 100;

  return (
    <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Community Feedback
        </h4>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          {showDetails ? 'Hide details' : 'Show details'}
        </button>
      </div>

      {/* Feedback bar */}
      <div className="flex h-6 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
        {positivePercentage > 0 && (
          <div 
            className="bg-green-500 flex items-center justify-center text-xs text-white font-medium"
            style={{ width: `${positivePercentage}%` }}
          >
            {positivePercentage >= 20 && `${Math.round(positivePercentage)}%`}
          </div>
        )}
        {neutralPercentage > 0 && (
          <div 
            className="bg-gray-400 flex items-center justify-center text-xs text-white font-medium"
            style={{ width: `${neutralPercentage}%` }}
          >
            {neutralPercentage >= 20 && `${Math.round(neutralPercentage)}%`}
          </div>
        )}
        {negativePercentage > 0 && (
          <div 
            className="bg-red-500 flex items-center justify-center text-xs text-white font-medium"
            style={{ width: `${negativePercentage}%` }}
          >
            {negativePercentage >= 20 && `${Math.round(negativePercentage)}%`}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <span className="text-gray-600 dark:text-gray-400">
            Helpful ({feedbackStats.positive})
          </span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
          <span className="text-gray-600 dark:text-gray-400">
            Neutral ({feedbackStats.neutral})
          </span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500 rounded-full"></div>
          <span className="text-gray-600 dark:text-gray-400">
            Not Helpful ({feedbackStats.negative})
          </span>
        </div>
      </div>

      {/* Detailed comments */}
      <AnimatePresence>
        {showDetails && feedbackStats.comments.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 space-y-2 max-h-60 overflow-y-auto"
          >
            <h5 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Recent Comments:
            </h5>
            {feedbackStats.comments.slice(0, 5).map((comment, index) => (
              <div key={index} className="p-2 bg-white dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    comment.rating === 'thumbs_up' 
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                      : comment.rating === 'thumbs_down'
                      ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-600 dark:text-gray-300'
                  }`}>
                    {comment.rating === 'thumbs_up' ? '👍' : comment.rating === 'thumbs_down' ? '👎' : '😐'}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(comment.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-xs text-gray-700 dark:text-gray-300 italic">
                  "{comment.comment}"
                </p>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FeedbackTracker;