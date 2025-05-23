import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BeakerIcon, SparklesIcon, LightBulbIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { GlassCard, ColossalButton, GradientText, Loading } from './enhanced';
import { exploreHypothesis } from '../api/hypothesis';
import toast from 'react-hot-toast';

const HypothesisExplorer = () => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [useAdvancedModel, setUseAdvancedModel] = useState(false);

  const sampleQuestions = [
    "What if we could use CRISPR-Cas13 to target specific RNA isoforms in live cells?",
    "What if we developed a reversible RNA modification system for temporal gene regulation?",
    "What if we could visualize RNA-protein interactions in real-time at single-molecule resolution?"
  ];

  const handleExplore = async () => {
    if (!question.trim()) {
      toast.error('Please enter a hypothesis or question');
      return;
    }

    setIsLoading(true);
    try {
      const response = await exploreHypothesis(question, useAdvancedModel);
      
      if (response.success) {
        setResult(response);
        toast.success('Hypothesis analysis complete!');
      } else {
        toast.error(response.error || 'Failed to analyze hypothesis');
      }
    } catch (error) {
      toast.error(error.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const ConfidenceIndicator = ({ label, score }) => (
    <div className="mb-3">
      <div className="flex justify-between text-sm text-white/70 mb-1">
        <span>{label}</span>
        <span>{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score * 100}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className={`h-full ${
            score > 0.7 ? 'bg-bio-emerald' : 
            score > 0.4 ? 'bg-plasma-cyan' : 
            'bg-nebula-pink'
          }`}
        />
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <GlassCard className="p-6">
        <div className="mb-4">
          <GradientText
            text="Hypothesis Explorer"
            className="text-2xl font-bold mb-2"
            gradient="from-bio-emerald to-cosmic-purple"
          />
          <p className="text-white/70">
            Explore "what if" scenarios with advanced AI reasoning
          </p>
        </div>

        <div className="space-y-4">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter your hypothesis or 'what if' question..."
            className="w-full h-32 p-4 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40 focus:border-bio-emerald focus:outline-none resize-none"
          />

          {/* Sample Questions */}
          <div className="space-y-2">
            <p className="text-sm text-white/50">Try these examples:</p>
            {sampleQuestions.map((sample, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setQuestion(sample)}
                className="text-left text-sm text-plasma-cyan hover:text-electric-blue p-2 bg-white/5 rounded hover:bg-white/10 transition-all w-full"
              >
                <LightBulbIcon className="w-4 h-4 inline mr-2" />
                {sample}
              </motion.button>
            ))}
          </div>

          {/* Advanced Options */}
          <div>
            <button
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              className="text-sm text-white/60 hover:text-white/80 transition-colors"
            >
              {showAdvancedOptions ? '− Hide' : '+ Show'} Advanced Options
            </button>
            
            <AnimatePresence>
              {showAdvancedOptions && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-4 space-y-3 overflow-hidden"
                >
                  <label className="flex items-center space-x-3 text-white/70">
                    <input
                      type="checkbox"
                      checked={useAdvancedModel}
                      onChange={(e) => setUseAdvancedModel(e.target.checked)}
                      className="w-4 h-4 rounded bg-white/10 border-white/30"
                      disabled
                    />
                    <span>Use Advanced Model (o3) - Coming Soon</span>
                    <span className="text-xs bg-cosmic-purple/30 px-2 py-1 rounded">Premium</span>
                  </label>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <ColossalButton
            variant="primary"
            size="large"
            onClick={handleExplore}
            disabled={isLoading || !question.trim()}
            icon={<BeakerIcon className="w-5 h-5" />}
          >
            {isLoading ? 'Analyzing...' : 'Explore Hypothesis'}
          </ColossalButton>
        </div>
      </GlassCard>

      {/* Loading State */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex justify-center py-12"
        >
          <Loading type="dna-helix" />
        </motion.div>
      )}

      {/* Results Section */}
      <AnimatePresence>
        {result && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Confidence Scores */}
            {result.confidence_scores && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <ChartBarIcon className="w-6 h-6 mr-2 text-plasma-cyan" />
                  Confidence Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <ConfidenceIndicator 
                    label="Scientific Grounding" 
                    score={result.confidence_scores.scientific_grounding || 0} 
                  />
                  <ConfidenceIndicator 
                    label="Feasibility" 
                    score={result.confidence_scores.feasibility || 0} 
                  />
                  <ConfidenceIndicator 
                    label="Experimental Clarity" 
                    score={result.confidence_scores.experimental_clarity || 0} 
                  />
                  <ConfidenceIndicator 
                    label="Overall Confidence" 
                    score={result.confidence_scores.overall || 0} 
                  />
                </div>
              </GlassCard>
            )}

            {/* Analysis Sections */}
            {result.analysis && Object.entries(result.analysis).map(([key, content]) => {
              if (!content) return null;
              
              const sectionTitles = {
                hypothesis_analysis: 'Hypothesis Analysis',
                scientific_basis: 'Scientific Basis',
                feasibility_assessment: 'Feasibility Assessment',
                recommended_experiments: 'Recommended Experiments',
                potential_challenges: 'Potential Challenges',
                related_directions: 'Related Research Directions'
              };

              const sectionIcons = {
                hypothesis_analysis: <BeakerIcon className="w-6 h-6" />,
                scientific_basis: <SparklesIcon className="w-6 h-6" />,
                feasibility_assessment: <ChartBarIcon className="w-6 h-6" />,
                recommended_experiments: <LightBulbIcon className="w-6 h-6" />,
                potential_challenges: <BeakerIcon className="w-6 h-6" />,
                related_directions: <SparklesIcon className="w-6 h-6" />
              };

              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <span className="text-bio-emerald mr-2">{sectionIcons[key]}</span>
                      {sectionTitles[key] || key}
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {content}
                    </div>
                  </GlassCard>
                </motion.div>
              );
            })}

            {/* Source Documents */}
            {result.source_documents && result.source_documents.length > 0 && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  Reference Documents
                </h3>
                <div className="space-y-3">
                  {result.source_documents.map((doc, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-3 bg-white/5 rounded-lg"
                    >
                      <h4 className="font-medium text-plasma-cyan mb-1">
                        {doc.title}
                      </h4>
                      <p className="text-sm text-white/60 line-clamp-2">
                        {doc.content}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </GlassCard>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default HypothesisExplorer;