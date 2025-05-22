import { useState } from 'react';

/**
 * Component to display figures extracted from documents
 * Supports different figure types (images, tables, charts, etc.)
 * Includes modal for enlarged view
 */
const FigureDisplay = ({ figure }) => {
  const [showModal, setShowModal] = useState(false);
  
  if (!figure) return null;
  
  const { figure_id, figure_type, caption, doc_title, api_path } = figure;
  
  // Generate the full URL for the figure
  const figureUrl = api_path 
    ? `${window.location.origin}${api_path}`
    : null;
  
  // Function to open the modal with the enlarged figure
  const openModal = () => {
    setShowModal(true);
  };
  
  // Function to close the modal
  const closeModal = () => {
    setShowModal(false);
  };
  
  return (
    <div className="mb-4 border rounded-lg overflow-hidden bg-gray-50">
      <div className="p-3">
        <div className="flex justify-between items-start mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase">
            {figure_type}
          </span>
          <span className="text-xs text-gray-400">
            ID: {figure_id}
          </span>
        </div>
        
        {/* Figure thumbnail (clickable to enlarge) */}
        <div 
          className="cursor-pointer my-2 flex justify-center"
          onClick={openModal}
        >
          {figureUrl ? (
            <img 
              src={figureUrl} 
              alt={caption || "Figure"} 
              className="max-h-48 object-contain"
            />
          ) : (
            <div className="border rounded flex items-center justify-center p-4 w-full h-32 bg-gray-100 text-gray-400">
              Figure preview not available
            </div>
          )}
        </div>
        
        {/* Caption and source */}
        <p className="text-sm text-gray-600 italic mb-1">{caption || "No caption available"}</p>
        <p className="text-xs text-gray-500">Source: {doc_title}</p>
      </div>
      
      {/* Modal for enlarged view */}
      {showModal && (
        <div className="fixed inset-0 z-50 overflow-auto bg-black bg-opacity-70 flex items-center justify-center p-4">
          <div className="relative bg-white rounded-lg shadow-xl max-w-4xl max-h-full flex flex-col">
            {/* Modal header */}
            <div className="px-6 py-4 border-b">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">
                  {figure_type} from {doc_title}
                </h3>
                <button 
                  className="text-gray-400 hover:text-gray-500"
                  onClick={closeModal}
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Modal body */}
            <div className="px-6 py-4 overflow-auto">
              {figureUrl ? (
                <img 
                  src={figureUrl} 
                  alt={caption || "Figure"} 
                  className="max-w-full max-h-[70vh] object-contain mx-auto"
                />
              ) : (
                <div className="border rounded flex items-center justify-center p-8 w-full h-64 bg-gray-100 text-gray-400">
                  Figure image not available
                </div>
              )}
              
              {/* Caption */}
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-500">Caption:</h4>
                <p className="text-gray-700 mt-1">{caption || "No caption available"}</p>
              </div>
            </div>
            
            {/* Modal footer */}
            <div className="px-6 py-3 border-t">
              <div className="flex justify-end">
                <button
                  type="button"
                  className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-300"
                  onClick={closeModal}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FigureDisplay;