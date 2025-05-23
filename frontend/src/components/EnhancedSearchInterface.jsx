import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SparklesIcon, BeakerIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import AdvancedSearchBox from './AdvancedSearchBox';
import HypothesisExplorer from './HypothesisExplorer';
import ProtocolBuilder from './ProtocolBuilder';
import { GlassCard, ColossalButton, GradientText, Loading } from './enhanced';

const EnhancedSearchInterface = ({ docType }) => {
  const [mode, setMode] = useState('search'); // 'search', 'hypothesis', 'protocol'
  const [isProcessing, setIsProcessing] = useState(false);
  const searchRef = useRef(null);

  const modes = [
    {
      id: 'search',
      label: 'Search & Analyze',
      icon: <SparklesIcon className="w-5 h-5" />,
      description: 'Search through papers, protocols, and theses',
      gradient: 'from-electric-blue to-plasma-cyan'
    },
    {
      id: 'hypothesis',
      label: 'Hypothesis Mode',
      icon: <BeakerIcon className="w-5 h-5" />,
      description: 'Explore "what if" scenarios with AI',
      gradient: 'from-bio-emerald to-cosmic-purple'
    },
    {
      id: 'protocol',
      label: 'Protocol Builder',
      icon: <DocumentTextIcon className="w-5 h-5" />,
      description: 'Generate custom lab protocols',
      gradient: 'from-cosmic-purple to-nebula-pink'
    }
  ];

  const handleModeChange = (newMode) => {
    setMode(newMode);
    setIsProcessing(true);
    setTimeout(() => setIsProcessing(false), 800);
  };

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        {modes.map((m) => (
          <motion.div
            key={m.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <GlassCard
              className={`p-4 cursor-pointer transition-all duration-300 ${
                mode === m.id
                  ? 'border-2 border-white/30 bg-white/10'
                  : 'border border-white/10 hover:border-white/20'
              }`}
              onClick={() => handleModeChange(m.id)}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg bg-gradient-to-r ${m.gradient} text-white`}>
                  {m.icon}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-white mb-1">{m.label}</h3>
                  <p className="text-xs text-white/60">{m.description}</p>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>

      {/* Search Interface */}
      <AnimatePresence mode="wait">
        {isProcessing ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center py-12"
          >
            <Loading type="dna-helix" />
          </motion.div>
        ) : (
          <motion.div
            key={mode}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {mode === 'search' && (
              <div ref={searchRef}>
                <AdvancedSearchBox docType={docType} />
              </div>
            )}

            {mode === 'hypothesis' && <HypothesisExplorer />}

            {mode === 'protocol' && <ProtocolBuilder />}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EnhancedSearchInterface;