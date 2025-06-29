import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function AppMinimal() {
  return (
    <Router>
      <div style={{ padding: '20px' }}>
        <h1>RNA Lab Navigator - Minimal Test</h1>
        <Routes>
          <Route path="/" element={
            <div>
              <h2>Home Page</h2>
              <p>If you can see this, React Router is working!</p>
            </div>
          } />
          <Route path="/login" element={
            <div>
              <h2>Login Page</h2>
              <p>This is the login page.</p>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default AppMinimal;