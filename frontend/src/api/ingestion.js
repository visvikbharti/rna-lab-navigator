import axios from 'axios';
import { API_BASE_URL } from './config';

const INGESTION_API = `${API_BASE_URL}/api/ingestion`;

// Create axios instance with auth headers
const api = axios.create({
  baseURL: INGESTION_API,
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`,
  },
});

// Add request interceptor to update auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Upload a single document
 * @param {FormData} formData - Form data with file and metadata
 * @returns {Promise} Processing response with processing_id
 */
export const uploadDocument = async (formData) => {
  try {
    const response = await api.post('/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Upload error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Upload multiple documents in batch
 * @param {FormData} formData - Form data with files and metadata list
 * @returns {Promise} Batch processing response
 */
export const uploadBatch = async (formData) => {
  try {
    const response = await api.post('/batch-upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Batch upload error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Validate a document before processing
 * @param {FormData} formData - Form data with file
 * @returns {Promise} Validation results
 */
export const validateDocument = async (formData) => {
  try {
    const response = await api.post('/validate/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Validation error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Generate document preview
 * @param {FormData} formData - Form data with file and preview options
 * @returns {Promise} Preview data
 */
export const previewDocument = async (formData) => {
  try {
    const response = await api.post('/preview/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Preview error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Get processing status
 * @param {string} processingId - Processing ID
 * @returns {Promise} Processing status
 */
export const getProcessingStatus = async (processingId) => {
  try {
    const response = await api.get(`/status/${processingId}/`);
    return response.data;
  } catch (error) {
    console.error('Status error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Get all documents
 * @param {Object} params - Query parameters
 * @returns {Promise} List of documents
 */
export const getDocuments = async (params = {}) => {
  try {
    const response = await api.get('/documents/', { params });
    return response.data;
  } catch (error) {
    console.error('Get documents error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Get document details
 * @param {number} documentId - Document ID
 * @returns {Promise} Document details
 */
export const getDocument = async (documentId) => {
  try {
    const response = await api.get(`/documents/${documentId}/`);
    return response.data;
  } catch (error) {
    console.error('Get document error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Get document figures
 * @param {number} documentId - Document ID
 * @returns {Promise} List of figures
 */
export const getDocumentFigures = async (documentId) => {
  try {
    const response = await api.get(`/documents/${documentId}/figures/`);
    return response.data;
  } catch (error) {
    console.error('Get figures error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Reprocess a document
 * @param {number} documentId - Document ID
 * @param {Object} options - Processing options
 * @returns {Promise} Processing response
 */
export const reprocessDocument = async (documentId, options) => {
  try {
    const response = await api.post(`/documents/${documentId}/reprocess/`, options);
    return response.data;
  } catch (error) {
    console.error('Reprocess error:', error);
    throw error.response?.data || error;
  }
};

/**
 * Delete a document
 * @param {number} documentId - Document ID
 * @returns {Promise} Deletion confirmation
 */
export const deleteDocument = async (documentId) => {
  try {
    const response = await api.delete(`/documents/${documentId}/`);
    return response.data;
  } catch (error) {
    console.error('Delete error:', error);
    throw error.response?.data || error;
  }
};

// WebSocket connection for real-time updates
export const createProcessingWebSocket = (processingId, handlers) => {
  const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/processing/${processingId}/`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected for processing:', processingId);
    if (handlers.onOpen) handlers.onOpen();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (handlers.onMessage) handlers.onMessage(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (handlers.onError) handlers.onError(error);
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
    if (handlers.onClose) handlers.onClose();
  };

  return {
    send: (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
    close: () => ws.close(),
  };
};

export default {
  uploadDocument,
  uploadBatch,
  validateDocument,
  previewDocument,
  getProcessingStatus,
  getDocuments,
  getDocument,
  getDocumentFigures,
  reprocessDocument,
  deleteDocument,
  createProcessingWebSocket,
};