import { useState, useEffect } from 'react';
import axios from 'axios';

const EnhancedFeedbackForm = ({ queryId, onFeedbackSubmit }) => {
  // Basic feedback states
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackType, setFeedbackType] = useState(null);
  const [comment, setComment] = useState('');
  const [specificIssues, setSpecificIssues] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  // Enhanced feedback states
  const [category, setCategory] = useState('general');
  const [relevanceRating, setRelevanceRating] = useState(null);
  const [accuracyRating, setAccuracyRating] = useState(null);
  const [completenessRating, setCompletenessRating] = useState(null);
  const [clarityRating, setClarityRating] = useState(null);
  const [citationRating, setCitationRating] = useState(null);
  const [incorrectSections, setIncorrectSections] = useState('');
  const [suggestedAnswer, setSuggestedAnswer] = useState('');
  const [sourceQualityIssues, setSourceQualityIssues] = useState([]);
  const [availableCategories, setAvailableCategories] = useState([]);
  const [showDetailedForm, setShowDetailedForm] = useState(false);

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

  // Source quality issues
  const possibleSourceIssues = [
    'Irrelevant sources retrieved',
    'Missing key sources',
    'Sources misinterpreted',
    'Citations don\'t match content',
    'Outdated sources',
    'Low-quality sources'
  ];

  // Fetch available feedback categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get('/api/feedback/categories/');
        const activeCategories = response.data.filter(cat => cat.is_active && cat.type === 'category');
        setAvailableCategories(activeCategories);
      } catch (error) {
        console.error('Error fetching feedback categories:', error);
        // Use default categories if API call fails
        setAvailableCategories([
          { id: 'relevance', name: 'Answer Relevance' },
          { id: 'accuracy', name: 'Information Accuracy' },
          { id: 'completeness', name: 'Answer Completeness' },
          { id: 'clarity', name: 'Clarity/Readability' },
          { id: 'citations', name: 'Citation Quality' },
          { id: 'general', name: 'General Feedback' },
        ]);
      }
    };

    fetchCategories();
  }, []);

  // Toggle an issue in the selected list
  const toggleIssue = (issue) => {
    if (specificIssues.includes(issue)) {
      setSpecificIssues(specificIssues.filter(i => i !== issue));
    } else {
      setSpecificIssues([...specificIssues, issue]);
    }
  };

  // Toggle a source quality issue
  const toggleSourceIssue = (issue) => {
    if (sourceQualityIssues.includes(issue)) {
      setSourceQualityIssues(sourceQualityIssues.filter(i => i !== issue));
    } else {
      setSourceQualityIssues([...sourceQualityIssues, issue]);
    }
  };

  // Handle initial feedback button click
  const handleFeedbackClick = (type) => {
    setFeedbackType(type);
    
    if (type === 'thumbs_up') {
      // For positive feedback, show minimal form
      setShowFeedbackForm(true);
      setShowDetailedForm(false);
    } else if (type === 'thumbs_down') {
      // For negative feedback, show form for additional input
      setShowFeedbackForm(true);
      setShowDetailedForm(false);
    } else {
      // For neutral feedback
      setShowFeedbackForm(true);
      setShowDetailedForm(false);
    }
  };

  // Toggle detailed feedback form
  const toggleDetailedForm = () => {
    setShowDetailedForm(!showDetailedForm);
  };

  // Handle form submission
  const submitFeedback = async () => {
    if (!queryId) {
      setError('Missing query ID. Cannot submit feedback.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    // Prepare the payload
    const feedbackData = {
      query_id: queryId,
      rating: feedbackType,
      comment: comment,
      specific_issues: specificIssues,
      category: category,
      // Include detailed ratings only if they were provided
      ...(relevanceRating && { relevance_rating: relevanceRating }),
      ...(accuracyRating && { accuracy_rating: accuracyRating }),
      ...(completenessRating && { completeness_rating: completenessRating }),
      ...(clarityRating && { clarity_rating: clarityRating }),
      ...(citationRating && { citation_rating: citationRating }),
      // Include learning-oriented fields if provided
      ...(incorrectSections && { incorrect_sections: incorrectSections.split('\n') }),
      ...(suggestedAnswer && { suggested_answer: suggestedAnswer }),
      ...(sourceQualityIssues.length > 0 && { source_quality_issues: sourceQualityIssues })
    };

    try {
      await axios.post('/api/feedback/feedback/', feedbackData);

      setSubmitted(true);
      
      if (onFeedbackSubmit) {
        onFeedbackSubmit(feedbackData);
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
    setShowDetailedForm(false);
    setFeedbackType(null);
    setComment('');
    setSpecificIssues([]);
    setCategory('general');
    setRelevanceRating(null);
    setAccuracyRating(null);
    setCompletenessRating(null);
    setClarityRating(null);
    setCitationRating(null);
    setIncorrectSections('');
    setSuggestedAnswer('');
    setSourceQualityIssues([]);
  };

  // Render star rating component
  const StarRating = ({ value, onChange, label }) => {
    return (
      <div className="mb-2">
        <div className="flex items-center">
          <span className="text-sm text-gray-700 w-32">{label}:</span>
          <div className="flex">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => onChange(star)}
                className={`w-6 h-6 ${
                  value >= star 
                    ? 'text-yellow-400' 
                    : 'text-gray-300'
                }`}
                aria-label={`Rate ${star} out of 5`}
              >
                ★
              </button>
            ))}
          </div>
          {value && (
            <span className="ml-2 text-sm text-gray-600">{value}/5</span>
          )}
        </div>
      </div>
    );
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
            onClick={() => handleFeedbackClick('neutral')}
            className="bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition duration-150 ease-in-out flex items-center"
            disabled={isSubmitting}
          >
            <span className="mr-2">😐</span>
            Neutral
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
            {feedbackType === 'thumbs_up' 
              ? "What was helpful?" 
              : feedbackType === 'thumbs_down' 
                ? "What could be improved?" 
                : "Your feedback"}
          </h3>
          
          {/* Basic feedback section */}
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2">
              Feedback category:
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availableCategories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          
          {feedbackType !== 'thumbs_up' && (
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
          )}
          
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="comment">
              Comments: (optional)
            </label>
            <textarea
              id="comment"
              rows="3"
              className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={feedbackType === 'thumbs_up' 
                ? "What made this answer helpful?" 
                : "Please provide any additional feedback..."}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>

          {/* Toggle for detailed feedback */}
          <div className="mb-4">
            <button
              type="button"
              onClick={toggleDetailedForm}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center"
            >
              {showDetailedForm ? 'Hide detailed feedback' : 'Provide detailed feedback'} 
              <svg className={`w-4 h-4 ml-1 transition-transform ${showDetailedForm ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path>
              </svg>
            </button>
          </div>
          
          {/* Detailed feedback section */}
          {showDetailedForm && (
            <div className="border-t border-gray-200 pt-4 mb-4">
              <h4 className="font-medium text-md mb-3">Detailed Ratings</h4>
              
              <div className="space-y-2 mb-4">
                <StarRating 
                  value={relevanceRating} 
                  onChange={setRelevanceRating} 
                  label="Relevance" 
                />
                <StarRating 
                  value={accuracyRating} 
                  onChange={setAccuracyRating} 
                  label="Accuracy" 
                />
                <StarRating 
                  value={completenessRating} 
                  onChange={setCompletenessRating} 
                  label="Completeness" 
                />
                <StarRating 
                  value={clarityRating} 
                  onChange={setClarityRating} 
                  label="Clarity" 
                />
                <StarRating 
                  value={citationRating} 
                  onChange={setCitationRating} 
                  label="Citations" 
                />
              </div>
              
              {feedbackType !== 'thumbs_up' && (
                <>
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-medium mb-2">
                      Source quality issues: (optional)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {possibleSourceIssues.map((issue) => (
                        <button
                          key={issue}
                          type="button"
                          onClick={() => toggleSourceIssue(issue)}
                          className={`text-xs py-1 px-2 rounded-full ${
                            sourceQualityIssues.includes(issue)
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
                    <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="incorrectSections">
                      Incorrect sections: (optional)
                    </label>
                    <textarea
                      id="incorrectSections"
                      rows="2"
                      className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="List any incorrect sections (one per line)"
                      value={incorrectSections}
                      onChange={(e) => setIncorrectSections(e.target.value)}
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-medium mb-2" htmlFor="suggestedAnswer">
                      Suggested correction: (optional)
                    </label>
                    <textarea
                      id="suggestedAnswer"
                      rows="3"
                      className="w-full border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Suggest a better answer or correction"
                      value={suggestedAnswer}
                      onChange={(e) => setSuggestedAnswer(e.target.value)}
                    />
                  </div>
                </>
              )}
            </div>
          )}
          
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

export default EnhancedFeedbackForm;