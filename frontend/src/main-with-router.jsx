import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import App from './App.jsx';
import SimpleSearch from './SimpleSearch.jsx';
import ChatApp from './ChatApp.jsx';
import './index.css';

function Main() {
  return (
    <Router>
      <Routes>
        {/* Chat Interface as the main route */}
        <Route path="/" element={<ChatApp />} />
        
        {/* Legacy search interfaces */}
        <Route path="/simple" element={<SimpleSearch />} />
        <Route path="/advanced" element={<App />} />
        
        {/* Redirect old routes */}
        <Route path="/chat" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Main />
  </React.StrictMode>
);