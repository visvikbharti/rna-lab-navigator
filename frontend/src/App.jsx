import { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './components/NotificationSystem';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/auth/Login';
import PrivateRoute from './components/auth/PrivateRoute';
import UserProfile from './components/auth/UserProfile';
import TermsAcceptance from './components/auth/TermsAcceptance';
import UserMenu from './components/auth/UserMenu';
import EnhancedSearchInterface from './components/EnhancedSearchInterface';
import FilterChips from './components/FilterChips';
import DocumentUploader from './components/DocumentUploader';
import { 
  HypothesisExplorer, 
  ProtocolBuilder, 
  GapExplorer,
  CrossPaperInsights,
  KnowledgeGraphExplorer,
  ExperimentMapper,
  MultiAgentAnalysis,
  ProtocolDesigner,
  FeedbackAnalyticsDashboard,
  SecurityAuditDashboard,
  SearchQualityDashboard
} from './components/placeholders';
import SimpleSearch from './SimpleSearch';
import { AnimationProvider } from './contexts/AnimationContext';
import { DarkModeProvider } from './contexts/DarkModeContext';
import DarkModeToggle from './components/DarkModeToggle';
import { ParticleBackground, FloatingOrbs, GlassCard, GradientText } from './components/enhanced';
import { MagnifyingGlassIcon, BeakerIcon, DocumentTextIcon, ChartBarIcon, ShieldCheckIcon, MapIcon, CloudArrowUpIcon, SparklesIcon, LightBulbIcon, LinkIcon, Bars3Icon, XMarkIcon, CubeTransparentIcon, UsersIcon } from '@heroicons/react/24/outline';
import TestRoutes from './TestRoutes';
import ChatInterface from './components/ChatInterface';
import AdminDashboard from './components/admin/AdminDashboard';
import UserManagement from './components/admin/UserManagement';
import AuditLogs from './components/admin/AuditLogs';
// Use clean, working CSS
// import './styles/app-clean.css';

function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  return (
    <motion.nav 
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 glass-ultra border-b border-white/10"
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <SparklesIcon className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold" style={{ color: '#ffffff' }}>
                RNA Lab Navigator
              </span>
            </Link>
            <div className="hidden lg:flex space-x-1">
              <NavLink to="/" icon={MagnifyingGlassIcon}>Search</NavLink>
              <NavLink to="/upload" icon={CloudArrowUpIcon}>Upload</NavLink>
              <NavLink to="/gaps" icon={LightBulbIcon}>Gap Analysis</NavLink>
              <NavLink to="/insights" icon={LinkIcon}>Cross-Paper</NavLink>
              <NavLink to="/graph" icon={CubeTransparentIcon}>Knowledge Graph</NavLink>
              <NavLink to="/experiments" icon={MapIcon}>Experiments</NavLink>
              <NavLink to="/agents" icon={SparklesIcon}>AI Agents</NavLink>
              <NavLink to="/protocol-designer" icon={BeakerIcon}>Protocols</NavLink>
              <NavLink to="/analytics" icon={ChartBarIcon}>Analytics</NavLink>
              <NavLink to="/security" icon={ShieldCheckIcon}>Security</NavLink>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <DarkModeToggle />
            <UserMenu />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-all"
            >
              {mobileMenuOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="lg:hidden border-t border-white/10"
            >
              <div className="px-4 py-2 space-y-1">
                <MobileNavLink to="/" icon={MagnifyingGlassIcon} onClick={() => setMobileMenuOpen(false)}>Search</MobileNavLink>
                <MobileNavLink to="/upload" icon={CloudArrowUpIcon} onClick={() => setMobileMenuOpen(false)}>Upload</MobileNavLink>
                <MobileNavLink to="/gaps" icon={LightBulbIcon} onClick={() => setMobileMenuOpen(false)}>Gap Analysis</MobileNavLink>
                <MobileNavLink to="/insights" icon={LinkIcon} onClick={() => setMobileMenuOpen(false)}>Cross-Paper</MobileNavLink>
                <MobileNavLink to="/graph" icon={CubeTransparentIcon} onClick={() => setMobileMenuOpen(false)}>Knowledge Graph</MobileNavLink>
                <MobileNavLink to="/experiments" icon={MapIcon} onClick={() => setMobileMenuOpen(false)}>Experiments</MobileNavLink>
                <MobileNavLink to="/agents" icon={SparklesIcon} onClick={() => setMobileMenuOpen(false)}>AI Agents</MobileNavLink>
                <MobileNavLink to="/protocol-designer" icon={BeakerIcon} onClick={() => setMobileMenuOpen(false)}>Protocols</MobileNavLink>
                <MobileNavLink to="/analytics" icon={ChartBarIcon} onClick={() => setMobileMenuOpen(false)}>Analytics</MobileNavLink>
                <MobileNavLink to="/security" icon={ShieldCheckIcon} onClick={() => setMobileMenuOpen(false)}>Security</MobileNavLink>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
}

function NavLink({ to, icon: Icon, children }) {
  return (
    <Link 
      to={to} 
      className="flex items-center space-x-2 px-4 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200"
    >
      <Icon className="w-4 h-4" />
      <span className="text-sm font-medium">{children}</span>
    </Link>
  );
}

function MobileNavLink({ to, icon: Icon, children, onClick }) {
  return (
    <Link 
      to={to} 
      onClick={onClick}
      className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-all duration-200 w-full"
    >
      <Icon className="w-5 h-5" />
      <span className="font-medium">{children}</span>
    </Link>
  );
}

function MainSearch() {
  const [docType, setDocType] = useState('all');
  const [activeMode, setActiveMode] = useState('search');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950/20 to-purple-950/20 relative overflow-hidden">
      {/* Animated Background Elements */}
      <ParticleBackground type="dna" count={150} />
      <FloatingOrbs />
      
      {/* Gradient Overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent pointer-events-none" />
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl animate-pulse animation-delay-2000" />
      <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl float-animation" />
      <div className="absolute bottom-1/3 left-1/2 w-80 h-80 bg-pink-500/20 rounded-full blur-3xl float-animation animation-delay-3000" />
      
      <Navigation />
      
      <div className="container mx-auto px-4 py-8 max-w-7xl relative z-10 mt-16">
        {/* Hero Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12 mt-8"
        >
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight hero-title">
            Next-Generation Research Intelligence
          </h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.3 }}
            className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed"
          >
            Unlock the power of your lab's knowledge with 
            <span className="text-cyan-400 font-semibold"> AI-driven insights</span> and 
            <span className="text-purple-400 font-semibold"> breakthrough discoveries</span>
          </motion.p>
          
          {/* Statistics */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="mt-8 flex justify-center gap-8 text-sm"
          >
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">28+</div>
              <div className="text-gray-500">Documents</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">&lt;1s</div>
              <div className="text-gray-500">Query Time</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-cyan-400">95%</div>
              <div className="text-gray-500">Accuracy</div>
            </div>
          </motion.div>
        </motion.div>

        {/* Mode Selection with Glass Effect */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex justify-center mb-8"
        >
          <GlassCard className="inline-flex p-1">
            <ModeButton
              active={activeMode === 'search'}
              onClick={() => setActiveMode('search')}
              icon={MagnifyingGlassIcon}
              label="Search & Analyze"
            />
            <ModeButton
              active={activeMode === 'hypothesis'}
              onClick={() => setActiveMode('hypothesis')}
              icon={BeakerIcon}
              label="Hypothesis Mode"
            />
            <ModeButton
              active={activeMode === 'protocol'}
              onClick={() => setActiveMode('protocol')}
              icon={DocumentTextIcon}
              label="Protocol Builder"
            />
          </GlassCard>
        </motion.div>

        {/* Document Type Filter */}
        {activeMode === 'search' && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="mb-6 flex justify-center"
          >
            <FilterChips 
              selected={docType} 
              onChange={setDocType} 
            />
          </motion.div>
        )}

        {/* Main Content with Animation */}
        <motion.main
          key={activeMode}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.4 }}
        >
          {activeMode === 'search' && (
            <EnhancedSearchInterface 
              docType={docType}
              onDocTypeChange={setDocType}
            />
          )}
          
          {activeMode === 'hypothesis' && (
            <HypothesisExplorer />
          )}
          
          {activeMode === 'protocol' && (
            <ProtocolBuilder />
          )}
        </motion.main>
      </div>
    </div>
  );
}

function ModeButton({ active, onClick, icon: Icon, label }) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        relative flex items-center space-x-2 px-6 py-3 rounded-xl 
        transition-all duration-300 overflow-hidden group
        ${active 
          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25' 
          : 'text-gray-400 hover:text-white hover:bg-white/10'
        }
      `}
    >
      {/* Hover effect */}
      {!active && (
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 
                        translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
      )}
      
      <Icon className={`w-5 h-5 relative z-10 ${active ? 'animate-pulse' : ''}`} />
      <span className="font-medium relative z-10">{label}</span>
      
      {active && (
        <motion.div
          layoutId="activeModeIndicator"
          className="absolute bottom-0 left-0 right-0 h-1 bg-white"
        />
      )}
    </motion.button>
  );
}

function PageWrapper({ children, title, subtitle, icon: Icon }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950/20 to-purple-950/20 relative overflow-hidden">
      <ParticleBackground type="dna" count={100} />
      <FloatingOrbs />
      
      <Navigation />
      
      <div className="container mx-auto px-4 py-8 mt-16 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8 text-center"
        >
          <div className="flex justify-center mb-4">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              {Icon && <Icon className="w-10 h-10 text-white" />}
            </div>
          </div>
          <h2 className="text-4xl font-bold mb-2" style={{ color: '#ffffff' }}>
            {title}
          </h2>
          {subtitle && (
            <p className="text-gray-400 text-lg">{subtitle}</p>
          )}
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          {children}
        </motion.div>
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <NotificationProvider>
        <DarkModeProvider>
          <AnimationProvider>
            <AuthProvider>
              <Router>
                <Routes>
                  {/* Public routes */}
                  <Route path="/login" element={<Login />} />
                  
                  {/* Protected routes */}
                  <Route path="/accept-terms" element={
                    <PrivateRoute>
                      <TermsAcceptance />
                    </PrivateRoute>
                  } />
                  
                  <Route path="/profile" element={
                    <PrivateRoute>
                      <PageWrapper title="My Profile" icon={MagnifyingGlassIcon}>
                        <UserProfile />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  {/* Chat interface is the default route */}
                  <Route path="/" element={
                    <PrivateRoute>
                      <ChatInterface />
                    </PrivateRoute>
                  } />
                  
                  {/* Old search interface */}
                  <Route path="/old-search" element={
                    <PrivateRoute>
                      <MainSearch />
                    </PrivateRoute>
                  } />
                  
                  {/* Simple search interface for demo */}
                  <Route path="/simple" element={
                    <PrivateRoute>
                      <SimpleSearch />
                    </PrivateRoute>
                  } />
                  
                  {/* Secondary features */}
                  <Route path="/upload" element={
                    <PrivateRoute requiredPermission="canUploadDocuments">
                      <PageWrapper 
                        title="Upload Documents" 
                        subtitle="Add new research materials to your knowledge base"
                        icon={CloudArrowUpIcon}
                      >
                        <DocumentUploader />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/gaps" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="Knowledge Gap Explorer" 
                        subtitle="Discover research opportunities and unexplored areas"
                        icon={LightBulbIcon}
                      >
                        <GapExplorer />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/insights" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="Cross-Paper Insights" 
                        subtitle="Uncover connections and patterns across research papers"
                        icon={LinkIcon}
                      >
                        <CrossPaperInsights />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/graph" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="Knowledge Graph Explorer" 
                        subtitle="Visualize research connections in real-time"
                        icon={LinkIcon}
                      >
                        <KnowledgeGraphExplorer />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/experiments" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="Experiment Mapper" 
                        subtitle="Visualize and analyze experimental relationships"
                        icon={MapIcon}
                      >
                        <ExperimentMapper />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/agents" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="Multi-Agent Research Analysis" 
                        subtitle="AI research team analyzing papers for patterns and contradictions"
                        icon={SparklesIcon}
                      >
                        <MultiAgentAnalysis />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/protocol-designer" element={
                    <PrivateRoute>
                      <PageWrapper 
                        title="AI Protocol Designer" 
                        subtitle="Generate complete experimental protocols from hypotheses"
                        icon={BeakerIcon}
                      >
                        <ProtocolDesigner />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/analytics" element={
                    <PrivateRoute requiredRole={['ADMIN', 'PI']}>
                      <PageWrapper 
                        title="Analytics Dashboard" 
                        subtitle="Track performance and user insights"
                        icon={ChartBarIcon}
                      >
                        <FeedbackAnalyticsDashboard />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/security" element={
                    <PrivateRoute requiredRole="ADMIN">
                      <PageWrapper 
                        title="Security Audit" 
                        subtitle="Monitor and protect your research data"
                        icon={ShieldCheckIcon}
                      >
                        <SecurityAuditDashboard />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/search-quality" element={
                    <PrivateRoute requiredRole={['ADMIN', 'PI']}>
                      <PageWrapper 
                        title="Search Quality" 
                        subtitle="Optimize search performance and accuracy"
                        icon={ChartBarIcon}
                      >
                        <SearchQualityDashboard />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  {/* Test route */}
                  <Route path="/test" element={<TestRoutes />} />
                  
                  {/* Admin Routes */}
                  <Route path="/admin" element={
                    <PrivateRoute requiredRole={['ADMIN', 'PI']}>
                      <PageWrapper 
                        title="Admin Panel" 
                        subtitle="Manage users and system settings"
                        icon={ShieldCheckIcon}
                      >
                        <AdminDashboard />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/admin/users" element={
                    <PrivateRoute requiredRole={['ADMIN', 'PI']}>
                      <PageWrapper 
                        title="User Management" 
                        subtitle="Create, edit, and manage user accounts"
                        icon={UsersIcon}
                      >
                        <UserManagement />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  <Route path="/admin/audit-logs" element={
                    <PrivateRoute requiredRole={['ADMIN', 'PI']}>
                      <PageWrapper 
                        title="Audit Logs" 
                        subtitle="View system activity and security events"
                        icon={ShieldCheckIcon}
                      >
                        <AuditLogs />
                      </PageWrapper>
                    </PrivateRoute>
                  } />
                  
                  {/* Redirect old routes */}
                  <Route path="/app" element={<Navigate to="/" replace />} />
                  <Route path="/showcase" element={<Navigate to="/" replace />} />
                </Routes>
                
                {/* Toast notifications with glass effect */}
                <Toaster
                  position="top-right"
                  toastOptions={{
                    duration: 4000,
                    style: {
                      background: 'rgba(17, 24, 39, 0.8)',
                      backdropFilter: 'blur(10px)',
                      color: '#ffffff',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '12px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                    },
                  }}
                />
              </Router>
            </AuthProvider>
          </AnimationProvider>
        </DarkModeProvider>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;