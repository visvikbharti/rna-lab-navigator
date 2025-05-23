import { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

function SimpleApp() {
  const [docType, setDocType] = useState('all');
  const [enhancedUI, setEnhancedUI] = useState(true);

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <div className="container mx-auto p-8">
          <h1 className="text-4xl font-bold mb-4">RNA Lab Navigator</h1>
          <p className="text-gray-600 mb-8">Your AI assistant for lab protocols, papers, and theses</p>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Search & Analyze</h2>
            <input 
              type="text" 
              placeholder="Ask about RNA, CRISPR, protocols..."
              className="w-full p-3 border rounded-lg"
            />
            <button className="mt-4 bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600">
              Search
            </button>
          </div>

          <div className="mt-8 text-center">
            <Link to="/showcase" className="text-blue-500 hover:underline">
              View Colossal Showcase →
            </Link>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default SimpleApp;