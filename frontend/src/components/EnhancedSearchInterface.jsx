import { useState, useCallback, useMemo } from 'react';
import PropTypes from 'prop-types';
import { motion, AnimatePresence } from 'framer-motion';
import AdvancedSearchBox from './AdvancedSearchBox';
import SearchRankingSelector from './SearchRankingSelector';
import { GlassCard, GradientText, Loading } from './enhanced';
import { SparklesIcon, LightBulbIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import ErrorBoundary from './ErrorBoundary';

const EnhancedSearchInterface = ({ docType, onDocTypeChange, loading = false, error = null }) => {
  const [selectedRanking, setSelectedRanking] = useState('relevance');
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  // Initialize component
  useState(() => {
    // Simulate initialization
    setTimeout(() => setIsInitializing(false), 500);
  });

  const handleRankingChange = useCallback((newRanking) => {
    try {
      setSelectedRanking(newRanking);
    } catch (err) {
      console.error('Error changing ranking:', err);
    }
  }, []);

  const toggleAdvancedOptions = useCallback(() => {
    setShowAdvancedOptions(prev => !prev);
  }, []);

  const features = useMemo(() => [
    {
      id: 'ai-insights',
      icon: SparklesIcon,
      title: "AI-Powered Insights",
      description: "Advanced language models understand context and nuance"
    },
    {
      id: 'smart-suggestions',
      icon: LightBulbIcon,
      title: "Smart Suggestions",
      description: "Get intelligent query recommendations as you type"
    },
    {
      id: 'deep-search',
      icon: MagnifyingGlassIcon,
      title: "Deep Search",
      description: "Search across papers, protocols, and theses simultaneously"
    }
  ], []);

  // Loading state
  if (isInitializing || loading) {
    return (
      <div className="max-w-7xl mx-auto flex items-center justify-center min-h-[400px]">
        <Loading size="large" text="Initializing search interface..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto">
        <GlassCard className="p-8 text-center">
          <p className="text-red-400 mb-4">Unable to load search interface</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Retry
          </button>
        </GlassCard>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="max-w-7xl mx-auto">
      {/* Feature Cards */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
          >
            <GlassCard className="p-6 hover:bg-white/10 transition-all duration-300 group">
              {feature.icon && (
                <feature.icon className="w-8 h-8 text-blue-400 mb-3 group-hover:text-blue-300 transition-colors" />
              )}
              <h3 className="text-white font-semibold mb-2">{feature.title || 'Feature'}</h3>
              <p className="text-gray-400 text-sm">{feature.description || ''}</p>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>

      {/* Main Search Area */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <GlassCard className="p-8 backdrop-blur-xl bg-gradient-to-br from-gray-900/50 to-gray-800/50">
          {/* Search Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <GradientText className="text-2xl font-bold" gradient="aurora">
                Research Assistant
              </GradientText>
              <p className="text-gray-400 mt-1">
                Ask questions about your lab's research and get instant, cited answers
              </p>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleAdvancedOptions}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
            </motion.button>
          </div>

          {/* Advanced Options */}
          <AnimatePresence>
            {showAdvancedOptions && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden mb-6"
              >
                <div className="pb-4 border-b border-gray-700/50">
                  <SearchRankingSelector
                    selected={selectedRanking}
                    onChange={handleRankingChange}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search Component */}
          <AdvancedSearchBox 
            docType={docType}
            ranking={selectedRanking}
          />
        </GlassCard>
      </motion.div>

      {/* Quick Tips */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.8 }}
        className="mt-8 text-center"
      >
        <p className="text-gray-500 text-sm">
          💡 Pro tip: Try asking complex questions like "Compare CRISPR-Cas9 and Cas13 for RNA targeting"
        </p>
      </motion.div>
      </div>
    </ErrorBoundary>
  );
};

// PropTypes validation
EnhancedSearchInterface.propTypes = {
  docType: PropTypes.string,
  onDocTypeChange: PropTypes.func,
  loading: PropTypes.bool,
  error: PropTypes.object
};

EnhancedSearchInterface.defaultProps = {
  docType: 'all',
  onDocTypeChange: () => {},
  loading: false,
  error: null
};

export default EnhancedSearchInterface;