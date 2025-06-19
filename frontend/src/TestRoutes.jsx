import React from 'react';
import MultiAgentAnalysis from './components/MultiAgentAnalysis';
import ProtocolDesigner from './components/ProtocolDesigner';

const TestRoutes = () => {
  return (
    <div style={{ 
      backgroundColor: '#1a1a1a', 
      color: 'white', 
      minHeight: '100vh', 
      padding: '20px' 
    }}>
      <h1 style={{ color: 'white', marginBottom: '20px' }}>Testing Components Directly</h1>
      
      <div style={{ marginBottom: '40px', border: '2px solid #60a5fa', padding: '20px' }}>
        <h2 style={{ color: '#60a5fa' }}>Multi-Agent Analysis Component</h2>
        <MultiAgentAnalysis />
      </div>
      
      <div style={{ border: '2px solid #60a5fa', padding: '20px' }}>
        <h2 style={{ color: '#60a5fa' }}>Protocol Designer Component</h2>
        <ProtocolDesigner />
      </div>
    </div>
  );
};

export default TestRoutes;