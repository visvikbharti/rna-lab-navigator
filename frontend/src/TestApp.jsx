import React from 'react';

function TestApp() {
  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1>RNA Lab Navigator - Debug Test</h1>
      <p>If you see this, React is working!</p>
      <button onClick={() => alert('Button clicked!')}>Test Button</button>
    </div>
  );
}

export default TestApp;