import axios from 'axios';

// Base URL for API calls using Vite's proxy
const API_URL = '/api';

/**
 * Submit a query to the RNA Lab Navigator API
 * @param {string} query - The user's question
 * @param {string} docType - Optional document type filter ('protocol', 'paper', 'thesis', or 'all')
 * @param {boolean} useHybrid - Whether to use hybrid search (vector + keyword)
 * @param {number} hybridAlpha - Weight for vector search in hybrid mode (0-1)
 * @param {boolean} stream - Whether to use streaming response
 * @returns {Promise} - Promise resolving to the response data or EventSource for streaming
 */
export const submitQuery = async (query, docType = '', useHybrid = true, hybridAlpha = 0.75, stream = false) => {
  // For non-streaming response
  if (!stream) {
    try {
      // Make sure we're sending the expected parameter names and values
      const response = await axios.post(`${API_URL}/query/`, {
        query: query,
        doc_type: docType === 'all' ? '' : docType,
        use_hybrid: useHybrid,
        hybrid_alpha: hybridAlpha
      });
      
      return response.data;
    } catch (error) {
      console.error('Error submitting query:', error);
      throw error;
    }
  }
  
  // For streaming response
  return new Promise((resolve, reject) => {
    try {
      // Create a new URLSearchParams with 'stream=true'
      const params = new URLSearchParams();
      params.append('stream', 'true');
      
      // Make the POST request
      axios.post(`${API_URL}/query/?${params.toString()}`, {
        query,
        doc_type: docType === 'all' ? '' : docType,
        use_hybrid: useHybrid,
        hybrid_alpha: hybridAlpha
      }, {
        responseType: 'text',
        onDownloadProgress: (progressEvent) => {
          // Get the response text so far
          const responseText = progressEvent.event.target.responseText;
          
          // Check if we have any data to process
          if (responseText) {
            // Split the text by double newlines (SSE format)
            const lines = responseText.split('\n\n');
            
            // Process each SSE event
            lines.forEach(line => {
              if (line.startsWith('data: ')) {
                const jsonStr = line.substring(6); // Remove 'data: ' prefix
                try {
                  const data = JSON.parse(jsonStr);
                  resolve(data);
                } catch (e) {
                  console.warn('Invalid JSON in SSE event:', e);
                }
              }
            });
          }
        }
      }).catch(error => {
        console.error('Error in streaming query:', error);
        reject(error);
      });
    } catch (error) {
      console.error('Error setting up streaming query:', error);
      reject(error);
    }
  });
};