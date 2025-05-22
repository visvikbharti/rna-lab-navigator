import { useState } from 'react';
import axios from 'axios';

const FeedbackButtons = ({ queryId, onFeedbackSubmit }) => {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackType, setFeedbackType] = useState(null);
  const [comment, setComment] = useState('');
  const [specificIssues, setSpecificIssues] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  // Common issues to choose from
  const possibleIssues = [
    'Incorrect information',
    'Missing information',
    'Not directly answering the question',
    'Incorrect citations',
    'Hallucinated content',
    'Too verbose',
    'Too brief',
    'Not specific enough'
  ];

  // Toggle an issue in the selected list
  const toggleIssue = (issue) => {
    if (specificIssues.includes(issue)) {
      setSpecificIssues(specificIssues.filter(i => i !== issue));
    } else {
      setSpecificIssues([...specificIssues, issue]);
    }
  };

  // Handle initial feedback button click
  const handleFeedbackClick = (type) => {
    setFeedbackType(type);
    
    if (type === 'thumbs_up') {
      // For positive feedback, submit immediately without further input
      submitFeedback(type, '', []);
    } else {
      // For negative feedback, show form for additional input
      setShowFeedbackForm(true);
    }
  };

  // Handle form submission
  const submitFeedback = async (rating, userComment, issues) => {
    if (!queryId) {
      setError('Missing query ID. Cannot submit feedback.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await axios.post('/api/feedback/', {
        query_id: queryId,
        rating: rating || feedbackType,
        comment: userComment || comment,
        specific_issues: issues || specificIssues
      });

      setSubmitted(true);
      
      if (onFeedbackSubmit) {
        onFeedbackSubmit({
          rating: rating || feedbackType,
          comment: userComment || comment,
          specific_issues: issues || specificIssues
        });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    submitFeedback();
  };

  // Handle form cancelation
  const handleCancel = () => {
    setShowFeedbackForm(false);
    setFeedbackType(null);
    setComment('');
    setSpecificIssues([]);
  };

  // If already submitted
  if (submitted) {
    return (
      <div className="mt-4 text-center">
        <p className="text-green-600 font-medium">
          Thank you for your feedback!
        </p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      {!showFeedbackForm ? (
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => handleFeedbackClick('thumbs_up')}
            className="bg-green-100 hover:bg-green-200 text-green-800 font-medium py-2 px-4 rounded-lg transition duration-150 ease-in-out flex items-center"
            disabled={isSubmitting}
          >
            <span className="mr-2">👍</span>
            Helpful
          </button>
          <button
            onClick={() => handleFeedbackClick('thumbs_down')}
            className="bg-red-100 hover:bg-red-200 text-red-800 font-medium py-2 px-4 rounded-lg transition duration-150 ease-in-out flex items-center"
            disabled={isSubmitting}
          >
            <span className="mr-2">👎</span>
            Not Helpful
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-medium text-lg mb-3">
            What could be improved?
          </h3>
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">
              Select any issues: (optional)
            </label>
            <div className="flex flex-wrap gap-2">
              {possibleIssues.map((issue) => (
                <button
                  key={issue}
                  type="button"
                  onClick={() => toggleIssue(issue)}
                  className={`text-xs py-1 px-2 rounded-full ${
                    specificIssues.includes(issue)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  }`}
                >
                  {issue}
                </button>
              ))}
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="comment">
              Additional comments: (optional)
            </label>
            <textarea
              id="comment"
              rows="3"
              className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Please provide any additional feedback..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>
          
          {error && (
            <div className="text-red-600 mb-4">
              {error}
            </div>
          )}
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={handleCancel}
              className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition duration-150 ease-in-out"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg shadow-sm transition duration-150 ease-in-out"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default FeedbackButtons;