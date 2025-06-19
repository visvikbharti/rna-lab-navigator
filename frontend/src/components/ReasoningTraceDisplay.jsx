import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDownIcon, ChevronRightIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { GlassCard } from './enhanced';

const ReasoningTraceDisplay = ({ trace, knowledgeGaps, followUpQuestions }) => {
  const [expandedSteps, setExpandedSteps] = useState(new Set());
  const [showFullTrace, setShowFullTrace] = useState(false);

  const toggleStep = (stepNumber) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepNumber)) {
      newExpanded.delete(stepNumber);
    } else {
      newExpanded.add(stepNumber);
    }
    setExpandedSteps(newExpanded);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'text-green-400';
    if (confidence > 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceIcon = (confidence) => {
    if (confidence > 0.7) {
      return <CheckCircleIcon className="w-5 h-5 text-green-400" />;
    }
    return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400" />;
  };

  return (
    <div className="space-y-4">
      {/* Toggle to show/hide reasoning trace */}
      <motion.button
        onClick={() => setShowFullTrace(!showFullTrace)}
        className="flex items-center space-x-2 text-blue-400 hover:text-blue-300 transition-colors"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        {showFullTrace ? <ChevronDownIcon className="w-5 h-5" /> : <ChevronRightIcon className="w-5 h-5" />}
        <span className="font-medium">
          {showFullTrace ? 'Hide' : 'Show'} Reasoning Process ({trace?.length || 0} steps)
        </span>
      </motion.button>

      {/* Reasoning Steps */}
      <AnimatePresence>
        {showFullTrace && trace && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-3"
          >
            {trace.map((step, index) => (
              <motion.div
                key={step.step_number}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <GlassCard className="p-4 hover:bg-white/5 transition-all duration-200">
                  <div 
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => toggleStep(step.step_number)}
                  >
                    <div className="flex items-start space-x-3 flex-1">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 font-semibold text-sm">
                        {step.step_number}
                      </div>
                      <div className="flex-1">
                        <p className="text-white font-medium">{step.description}</p>
                        {expandedSteps.has(step.step_number) && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-3 space-y-2"
                          >
                            <p className="text-gray-300 text-sm">{step.conclusion}</p>
                            <div className="flex items-center space-x-4 text-sm">
                              <span className="text-gray-500">Sources: {step.source_count}</span>
                              <span className={`flex items-center space-x-1 ${getConfidenceColor(step.confidence)}`}>
                                {getConfidenceIcon(step.confidence)}
                                <span>{(step.confidence * 100).toFixed(0)}% confident</span>
                              </span>
                            </div>
                          </motion.div>
                        )}
                      </div>
                    </div>
                    <motion.div
                      animate={{ rotate: expandedSteps.has(step.step_number) ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDownIcon className="w-5 h-5 text-gray-400" />
                    </motion.div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Knowledge Gaps */}
      {knowledgeGaps && knowledgeGaps.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <GlassCard className="p-4 border-yellow-500/30">
            <h4 className="text-yellow-400 font-medium mb-2 flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              <span>Knowledge Gaps Identified</span>
            </h4>
            <ul className="space-y-1">
              {knowledgeGaps.map((gap, index) => (
                <li key={index} className="text-gray-300 text-sm flex items-start">
                  <span className="text-yellow-400 mr-2">•</span>
                  {gap}
                </li>
              ))}
            </ul>
          </GlassCard>
        </motion.div>
      )}

      {/* Follow-up Questions */}
      {followUpQuestions && followUpQuestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <h4 className="text-gray-400 font-medium mb-2">Suggested Follow-up Questions:</h4>
          <div className="space-y-2">
            {followUpQuestions.map((question, index) => (
              <motion.button
                key={index}
                className="w-full text-left p-3 rounded-lg bg-white/5 hover:bg-white/10 
                         border border-white/10 hover:border-blue-500/50 transition-all duration-200"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <span className="text-gray-300 text-sm">{question}</span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ReasoningTraceDisplay;