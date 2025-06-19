import React from 'react';
import ReactDOM from 'react-dom/client';
import DebugApp from './DebugApp';
import './index.css';

console.log('main-debug.jsx: Starting to load');

// Log any errors
window.addEventListener('error', (e) => {
  console.error('Window error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
  console.error('Unhandled promise rejection:', e.reason);
});

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountApp);
} else {
  mountApp();
}

function mountApp() {
  console.log('main-debug.jsx: DOM ready, mounting app');
  
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('Root element not found!');
    document.body.innerHTML = '<div style="color: red; padding: 20px;">Error: Root element not found</div>';
    return;
  }
  
  console.log('main-debug.jsx: Found root element, creating React root');
  
  try {
    const root = ReactDOM.createRoot(rootElement);
    root.render(
      <React.StrictMode>
        <DebugApp />
      </React.StrictMode>
    );
    console.log('main-debug.jsx: App rendered successfully');
  } catch (error) {
    console.error('main-debug.jsx: Error rendering app:', error);
    rootElement.innerHTML = `<div style="color: red; padding: 20px;">Error rendering app: ${error.message}</div>`;
  }
}