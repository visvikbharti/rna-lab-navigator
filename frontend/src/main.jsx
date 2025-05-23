import React from 'react';
import ReactDOM from 'react-dom/client';
// import TestApp from './TestApp.jsx';
// import MainApp from './App.jsx';
// import SimpleApp from './SimpleApp.jsx';
import WorkingApp from './WorkingApp.jsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <WorkingApp />
  </React.StrictMode>
);