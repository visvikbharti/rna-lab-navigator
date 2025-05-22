import { useState, useEffect } from 'react';
import { getDocumentPreview } from '../api/search';

/**
 * Component to display document previews.
 * Shows document metadata and a text preview of the content.
 * Provides a modal view for a larger preview.
 */
const DocumentPreview = ({ documentId, onClose }) => {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchDocument = async () => {
      if (!documentId) return;
      
      setLoading(true);
      try {
        const data = await getDocumentPreview(documentId);
        setDocument(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching document preview:', err);
        setError('Failed to load document preview');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDocument();
  }, [documentId]);
  
  // Handle document not found
  if (!loading && !document && !error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800">Document Preview</h2>
            <button 
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-6 text-center">
            <p className="text-gray-500">Document not found</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800">Document Preview</h2>
            <button 
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-6 text-center">
            <div className="animate-pulse">Loading document preview...</div>
          </div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800">Document Preview</h2>
            <button 
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="p-6 text-center">
            <p className="text-red-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">Document Preview</h2>
          <button 
            className="text-gray-400 hover:text-gray-500"
            onClick={onClose}
          >
            <span className="sr-only">Close</span>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* Document metadata */}
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">{document.title}</h3>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            <span className="px-2.5 py-0.5 bg-blue-100 text-blue-800 rounded-full">
              {document.doc_type}
            </span>
            
            {document.author && (
              <span className="text-gray-600">By {document.author}</span>
            )}
            
            {document.year && (
              <span className="text-gray-600">Published in {document.year}</span>
            )}
            
            <span className="text-gray-500">
              Added {new Date(document.created_at).toLocaleDateString()}
            </span>
          </div>
          
          <div className="mt-3">
            <div className="text-xs text-gray-500">Citation:</div>
            <div className="text-sm text-gray-700">{document.citation}</div>
          </div>
        </div>
        
        {/* Document content preview */}
        <div className="px-6 py-4 overflow-y-auto flex-grow">
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Content Preview</h4>
            <div className="whitespace-pre-line text-gray-800 text-sm font-mono">
              {document.preview_text || 'No content available for preview.'}
            </div>
          </div>
          
          <div className="text-center text-sm text-gray-500 mt-4">
            This is a preview of the document. Full content is available in the document itself.
          </div>
        </div>
        
        {/* Footer with buttons */}
        <div className="px-6 py-3 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-800 rounded hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentPreview;