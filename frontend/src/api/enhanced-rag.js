import axios from 'axios';

// Base URL for enhanced RAG API
const API_URL = '/api/search/enhanced-rag';

// Session management
let currentSessionId = null;

/**
 * Get or create a session ID for conversation memory
 */
const getSessionId = () => {
  if (!currentSessionId) {
    currentSessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    // Store in sessionStorage for persistence within the browser session
    sessionStorage.setItem('enhancedRagSessionId', currentSessionId);
  }
  return currentSessionId;
};

// Initialize from sessionStorage on load
if (typeof window !== 'undefined') {
  currentSessionId = sessionStorage.getItem('enhancedRagSessionId');
}

/**
 * Perform an enhanced conversational search with reasoning and memory
 * 
 * @param {string} query - The search query
 * @param {Object} userContext - Optional user context (expertise level, research area, etc.)
 * @returns {Promise} - Promise resolving to enhanced search results
 */
export const enhancedConversationalSearch = async (query, userContext = {}) => {
  try {
    const sessionId = getSessionId();
    
    const response = await axios.post(`${API_URL}/`, {
      query,
      session_id: sessionId,
      user_context: userContext
    }, {
      timeout: 30000 // 30 seconds for complex reasoning
    });
    
    // Transform response to match frontend expectations
    return {
      answer: response.data.answer,
      confidence: response.data.confidence,
      sources: response.data.sources || [],
      entities: response.data.entities || [],
      suggestions: response.data.suggestions || [],
      reasoning_trace: response.data.reasoning_trace || [],
      session_id: response.data.session_id,
      metadata: {
        has_reasoning: response.data.reasoning_trace && response.data.reasoning_trace.length > 0,
        entity_count: response.data.entities ? response.data.entities.length : 0
      }
    };
  } catch (error) {
    console.error('Enhanced RAG endpoint not available, falling back to standard query:', error);
    
    // Fallback to standard query endpoint
    try {
      const fallbackResponse = await axios.post('/api/query/', {
        query: query
      });
      
      // Transform standard response to enhanced format
      return {
        answer: fallbackResponse.data.answer,
        confidence: fallbackResponse.data.confidence_score,
        sources: fallbackResponse.data.sources || [],
        entities: [], // No entity extraction in standard mode
        suggestions: [],
        reasoning_trace: [],
        session_id: sessionId,
        metadata: {
          has_reasoning: false,
          entity_count: 0,
          fallback_used: true
        }
      };
    } catch (fallbackError) {
      console.error('Fallback to standard query also failed:', fallbackError);
      
      // If all else fails, still provide a minimal response to prevent UI from breaking
      return {
        answer: "I apologize, but I'm experiencing technical difficulties. Please try using the regular search mode or try again in a moment.",
        confidence: 0.1,
        sources: [],
        entities: [],
        suggestions: [],
        reasoning_trace: [],
        session_id: sessionId,
        metadata: {
          has_reasoning: false,
          entity_count: 0,
          fallback_used: true,
          error_mode: true
        }
      };
    }
  }
};

/**
 * Get intelligent auto-complete suggestions based on context
 * 
 * @param {string} partialQuery - The partial query to complete
 * @returns {Promise} - Promise resolving to suggestions
 */
export const getEnhancedAutocompleteSuggestions = async (partialQuery) => {
  try {
    const sessionId = getSessionId();
    
    const response = await axios.post(`${API_URL}/autocomplete/`, {
      partial_query: partialQuery,
      session_id: sessionId
    }, {
      timeout: 5000 // 5 seconds for autocomplete
    });
    
    return response.data.suggestions || [];
  } catch (error) {
    console.error('Error fetching enhanced autocomplete suggestions:', error);
    
    // Return empty array on error to not break the UI
    return [];
  }
};

/**
 * Submit feedback for an enhanced RAG response
 * 
 * @param {number} turnIndex - Index of the conversation turn
 * @param {number} rating - Rating from 1-5
 * @param {boolean} helpful - Whether the response was helpful
 * @param {Array} issues - List of issues (optional)
 * @returns {Promise} - Promise resolving to feedback response
 */
export const submitEnhancedFeedback = async (turnIndex, rating, helpful, issues = []) => {
  try {
    const sessionId = getSessionId();
    
    const response = await axios.post(`${API_URL}/feedback/`, {
      session_id: sessionId,
      turn_index: turnIndex,
      rating,
      helpful,
      issues
    });
    
    return response.data;
  } catch (error) {
    console.error('Error submitting enhanced feedback:', error);
    throw error;
  }
};

/**
 * Reset the current session (start a new conversation)
 */
export const resetSession = () => {
  currentSessionId = null;
  sessionStorage.removeItem('enhancedRagSessionId');
  getSessionId(); // Create new session
};

/**
 * Get conversation history for the current session
 * 
 * @returns {Promise} - Promise resolving to conversation history
 */
export const getConversationHistory = async () => {
  try {
    const sessionId = getSessionId();
    
    // This would require a new backend endpoint to fetch history
    // For now, return empty array
    return [];
  } catch (error) {
    console.error('Error fetching conversation history:', error);
    return [];
  }
};

/**
 * Helper function to format reasoning trace for display
 * 
 * @param {Array} reasoningTrace - The reasoning trace from the API
 * @returns {Array} - Formatted reasoning steps
 */
export const formatReasoningTrace = (reasoningTrace) => {
  if (!reasoningTrace || !Array.isArray(reasoningTrace)) {
    return [];
  }
  
  return reasoningTrace.map((step, index) => {
    switch (step.step) {
      case 'decomposition':
        return {
          title: 'Breaking down your question',
          content: step.output.map((q, i) => `${i + 1}. ${q}`).join('\n'),
          icon: '🔍'
        };
      
      case 'sub_answers':
        return {
          title: 'Analyzing each aspect',
          content: step.output.map(sa => 
            `Q: ${sa.question}\nConfidence: ${(sa.confidence * 100).toFixed(0)}%`
          ).join('\n\n'),
          icon: '📊'
        };
      
      case 'synthesis':
        return {
          title: 'Synthesizing complete answer',
          content: 'Combining findings from all aspects...',
          icon: '🧬'
        };
      
      default:
        return {
          title: `Step ${index + 1}`,
          content: JSON.stringify(step.output, null, 2),
          icon: '📝'
        };
    }
  });
};

/**
 * Helper function to check if a query should use enhanced RAG
 * 
 * @param {string} query - The search query
 * @returns {boolean} - Whether to use enhanced RAG
 */
export const shouldUseEnhancedRAG = (query) => {
  // Temporarily disable enhanced RAG to prevent 404 errors
  // This will make all queries use the working standard RAG system
  return false;
  
  // Original logic (commented out until enhanced endpoints are implemented):
  /*
  const complexityIndicators = [
    'compare', 'difference between', 'pros and cons',
    'troubleshoot', 'optimize', 'best practice',
    'step by step', 'detailed', 'comprehensive',
    'why', 'how does', 'explain', 'what if'
  ];
  
  const queryLower = query.toLowerCase();
  
  // Check for multiple questions
  if (query.split('?').length > 2) {
    return true;
  }
  
  // Check for complexity indicators
  for (const indicator of complexityIndicators) {
    if (queryLower.includes(indicator)) {
      return true;
    }
  }
  
  // Check query length (long queries often need decomposition)
  if (query.split(' ').length > 15) {
    return true;
  }
  
  return false;
  */
};