import { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { motion } from 'framer-motion';
import ChatBox from './components/ChatBox';
import EnhancedChatBox from './components/EnhancedChatBox';
import AdvancedSearchBox from './components/AdvancedSearchBox';
import EnhancedSearchInterface from './components/EnhancedSearchInterface';
import FilterChips from './components/FilterChips';
import ProtocolUploader from './components/ProtocolUploader';
import { FeedbackAnalyticsDashboard } from './components/feedback';
import SearchQualityDashboard from './components/SearchQualityDashboard';
import SecurityAuditDashboard from './components/SecurityAuditDashboard';
import EnhancedComponentsDemo from './components/enhanced/Demo';
import ColossalShowcase from './pages/ColossalShowcase';
import { AnimationProvider } from './contexts/AnimationContext';
import { DarkModeProvider } from './contexts/DarkModeContext';
import DarkModeToggle from './components/DarkModeToggle';
import { ParticleBackground, FloatingOrbs, GlassCard, GradientText, Navigation } from './components/enhanced';
import './App.css';

function MainApp() {
  const [docType, setDocType] = useState('all');
  const [enhancedUI, setEnhancedUI] = useState(true);

  return (
    <div className="min-h-screen bg-deep-space dark:bg-gray-900 transition-all duration-500 relative overflow-hidden">
      {/* Background Effects */}
      {enhancedUI && (
        <>
          <ParticleBackground type="dna" count={100} />
          <FloatingOrbs />
        </>
      )}
      
      <div className="container mx-auto px-4 py-8 max-w-4xl relative z-10">
        <motion.header 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8 text-center"
        >
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
              {enhancedUI ? (
                <GradientText
                  text="RNA Lab Navigator"
                  className="text-4xl md:text-5xl font-bold mb-2"
                  gradient="from-electric-blue via-plasma-cyan to-bio-emerald"
                />
              ) : (
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-2">RNA Lab Navigator</h1>
              )}
              <p className={enhancedUI ? "text-white/80" : "text-gray-600 dark:text-gray-400"}>
                Your AI assistant for lab protocols, papers, and theses
              </p>
              <Link to="/showcase" className={enhancedUI ? "text-sm text-plasma-cyan hover:text-electric-blue mt-2 inline-block transition-colors" : "text-sm text-primary-600 hover:text-primary-700 mt-2 inline-block"}>
                ✨ View Colossal Showcase →
              </Link>
            </div>
            <div className="flex-1 flex justify-end">
              <DarkModeToggle />
            </div>
          </div>
        
        <nav className="mt-4">
          <ul className="flex justify-center space-x-6">
            <li>
              <Link to="/" className="text-primary-600 hover:text-primary-800 font-medium">
                Home
              </Link>
            </li>
            <li>
              <Link to="/upload" className="text-primary-600 hover:text-primary-800 font-medium">
                Upload Protocol
              </Link>
            </li>
            <li>
              <Link to="/analytics" className="text-primary-600 hover:text-primary-800 font-medium">
                Feedback Analytics
              </Link>
            </li>
            <li>
              <Link to="/search-quality" className="text-primary-600 hover:text-primary-800 font-medium">
                Search Quality
              </Link>
            </li>
            <li>
              <Link to="/security" className="text-primary-600 hover:text-primary-800 font-medium">
                Security Audit
              </Link>
            </li>
            <li>
              <Link to="/demo" className="text-primary-600 hover:text-primary-800 font-medium">
                Component Demo
              </Link>
            </li>
          </ul>
        </nav>
        </motion.header>

        <motion.main
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {enhancedUI ? (
            <>
              <GlassCard className="p-6 mb-6">
                <FilterChips selected={docType} onChange={setDocType} />
              </GlassCard>
              <EnhancedSearchInterface docType={docType} />
            </>
          ) : (
            <>
              <FilterChips selected={docType} onChange={setDocType} />
              <AdvancedSearchBox docType={docType} />
            </>
          )}
        </motion.main>

        <motion.footer 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className={enhancedUI ? "mt-12 text-center text-white/60 text-sm" : "mt-12 text-center text-gray-500 text-sm"}
        >
          <p>© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab (CSIR-IGIB)</p>
        </motion.footer>
      </div>
    </div>
  );
}

function UploadPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">RNA Lab Navigator</h1>
        <p className="text-gray-600">
          Upload Protocol Documents
        </p>
        
        <nav className="mt-4">
          <ul className="flex justify-center space-x-6">
            <li>
              <Link to="/" className="text-primary-600 hover:text-primary-800 font-medium">
                Home
              </Link>
            </li>
            <li>
              <Link to="/upload" className="text-gray-800 font-bold">
                Upload Protocol
              </Link>
            </li>
            <li>
              <Link to="/analytics" className="text-primary-600 hover:text-primary-800 font-medium">
                Feedback Analytics
              </Link>
            </li>
            <li>
              <Link to="/search-quality" className="text-primary-600 hover:text-primary-800 font-medium">
                Search Quality
              </Link>
            </li>
            <li>
              <Link to="/security" className="text-primary-600 hover:text-primary-800 font-medium">
                Security Audit
              </Link>
            </li>
          </ul>
        </nav>
      </header>

      <main>
        <ProtocolUploader />
      </main>

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab (CSIR-IGIB)</p>
      </footer>
    </div>
  );
}

function AnalyticsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">RNA Lab Navigator</h1>
        <p className="text-gray-600">
          Feedback Analytics Dashboard
        </p>
        
        <nav className="mt-4">
          <ul className="flex justify-center space-x-6">
            <li>
              <Link to="/" className="text-primary-600 hover:text-primary-800 font-medium">
                Home
              </Link>
            </li>
            <li>
              <Link to="/upload" className="text-primary-600 hover:text-primary-800 font-medium">
                Upload Protocol
              </Link>
            </li>
            <li>
              <Link to="/analytics" className="text-gray-800 font-bold">
                Feedback Analytics
              </Link>
            </li>
            <li>
              <Link to="/search-quality" className="text-primary-600 hover:text-primary-800 font-medium">
                Search Quality
              </Link>
            </li>
            <li>
              <Link to="/security" className="text-primary-600 hover:text-primary-800 font-medium">
                Security Audit
              </Link>
            </li>
          </ul>
        </nav>
      </header>

      <main>
        <FeedbackAnalyticsDashboard />
      </main>

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab (CSIR-IGIB)</p>
      </footer>
    </div>
  );
}

function SearchQualityPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">RNA Lab Navigator</h1>
        <p className="text-gray-600">
          Search Quality Dashboard
        </p>
        
        <nav className="mt-4">
          <ul className="flex justify-center space-x-6">
            <li>
              <Link to="/" className="text-primary-600 hover:text-primary-800 font-medium">
                Home
              </Link>
            </li>
            <li>
              <Link to="/upload" className="text-primary-600 hover:text-primary-800 font-medium">
                Upload Protocol
              </Link>
            </li>
            <li>
              <Link to="/analytics" className="text-primary-600 hover:text-primary-800 font-medium">
                Feedback Analytics
              </Link>
            </li>
            <li>
              <Link to="/search-quality" className="text-gray-800 font-bold">
                Search Quality
              </Link>
            </li>
          </ul>
        </nav>
      </header>

      <main>
        <SearchQualityDashboard />
      </main>

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab (CSIR-IGIB)</p>
      </footer>
    </div>
  );
}

function SecurityAuditPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">RNA Lab Navigator</h1>
        <p className="text-gray-600">
          Security Audit Dashboard
        </p>
        
        <nav className="mt-4">
          <ul className="flex justify-center space-x-6">
            <li>
              <Link to="/" className="text-primary-600 hover:text-primary-800 font-medium">
                Home
              </Link>
            </li>
            <li>
              <Link to="/upload" className="text-primary-600 hover:text-primary-800 font-medium">
                Upload Protocol
              </Link>
            </li>
            <li>
              <Link to="/analytics" className="text-primary-600 hover:text-primary-800 font-medium">
                Feedback Analytics
              </Link>
            </li>
            <li>
              <Link to="/search-quality" className="text-primary-600 hover:text-primary-800 font-medium">
                Search Quality
              </Link>
            </li>
            <li>
              <Link to="/security" className="text-gray-800 font-bold">
                Security Audit
              </Link>
            </li>
          </ul>
        </nav>
      </header>

      <main>
        <SecurityAuditDashboard />
      </main>

      <footer className="mt-12 text-center text-gray-500 text-sm">
        <p>© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab (CSIR-IGIB)</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <DarkModeProvider>
      <AnimationProvider>
        <Router>
          <div className="min-h-screen bg-rna-platinum dark:bg-gray-900">
          <Routes>
            <Route path="/" element={<MainApp />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/search-quality" element={<SearchQualityPage />} />
            <Route path="/security" element={<SecurityAuditPage />} />
            <Route path="/demo" element={<EnhancedComponentsDemo />} />
            <Route path="/showcase" element={<ColossalShowcase />} />
          </Routes>
          
          {/* Global toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#ffffff',
                color: '#1f2937',
                border: '1px solid #e5e7eb',
                borderRadius: '12px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#ffffff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#ffffff',
                },
              },
            }}
          />
          </div>
        </Router>
      </AnimationProvider>
    </DarkModeProvider>
  );
}

export default MainApp;