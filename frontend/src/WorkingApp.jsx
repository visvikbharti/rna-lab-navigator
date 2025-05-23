import { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import EnhancedSearchInterface from './components/EnhancedSearchInterface';
import ColossalShowcase from './pages/ColossalShowcase';
import ProtocolUploader from './components/ProtocolUploader';
import { FeedbackAnalyticsDashboard } from './components/feedback';
import SearchQualityDashboard from './components/SearchQualityDashboard';
import SecurityAuditDashboard from './components/SecurityAuditDashboard';
import './App.css';

function HomePage() {
  const [docType, setDocType] = useState('all');
  const [enhancedUI, setEnhancedUI] = useState(true);

  return (
    <div className="min-h-screen bg-deep-space">
      {/* Particle Background */}
      {enhancedUI && (
        <div className="fixed inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-deep-space via-cosmic-purple to-deep-space" />
          <div className="particle-container">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="particle"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 20}s`,
                  animationDuration: `${20 + Math.random() * 10}s`
                }}
              />
            ))}
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-8 max-w-4xl relative z-10">
        <header className="mb-8 text-center">
          <div className="flex justify-between items-center mb-4">
            <div className="flex-1">
              <button
                onClick={() => setEnhancedUI(!enhancedUI)}
                className="text-sm text-white/60 hover:text-white/80 transition-colors"
              >
                {enhancedUI ? '🎨 Classic UI' : '✨ Enhanced UI'}
              </button>
            </div>
            <div className="flex-1">
              <h1 className="text-4xl md:text-5xl font-bold mb-2 text-white">
                RNA Lab Navigator
              </h1>
              <p className="text-white/80">
                Your AI assistant for lab protocols, papers, and theses
              </p>
              <Link to="/showcase" className="text-sm text-plasma-cyan hover:text-electric-blue mt-2 inline-block transition-colors">
                ✨ View Colossal Showcase →
              </Link>
            </div>
            <div className="flex-1 flex justify-end">
              {/* Dark mode toggle placeholder */}
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="mt-4">
            <ul className="flex justify-center space-x-6">
              <li>
                <Link to="/" className="text-primary-400 hover:text-primary-300 font-medium">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/upload" className="text-primary-400 hover:text-primary-300 font-medium">
                  Upload Protocol
                </Link>
              </li>
              <li>
                <Link to="/analytics" className="text-primary-400 hover:text-primary-300 font-medium">
                  Feedback Analytics
                </Link>
              </li>
              <li>
                <Link to="/search-quality" className="text-primary-400 hover:text-primary-300 font-medium">
                  Search Quality
                </Link>
              </li>
              <li>
                <Link to="/security" className="text-primary-400 hover:text-primary-300 font-medium">
                  Security Audit
                </Link>
              </li>
            </ul>
          </nav>
        </header>

        <main>
          <EnhancedSearchInterface 
            enhancedUI={enhancedUI}
            onDocTypeChange={setDocType}
            docType={docType}
          />
        </main>
      </div>
    </div>
  );
}

function WorkingApp() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/showcase" element={<ColossalShowcase />} />
        <Route path="/upload" element={<ProtocolUploader />} />
        <Route path="/analytics" element={<FeedbackAnalyticsDashboard />} />
        <Route path="/search-quality" element={<SearchQualityDashboard />} />
        <Route path="/security" element={<SecurityAuditDashboard />} />
      </Routes>
    </Router>
  );
}

export default WorkingApp;