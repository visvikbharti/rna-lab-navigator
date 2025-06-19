import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BeakerIcon, 
  SparklesIcon, 
  LightBulbIcon, 
  ChartBarIcon,
  DocumentTextIcon,
  AcademicCapIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import { GlassCard, ColossalButton, GradientText, Loading } from './enhanced';
import { exploreHypothesis, exploreHypothesisEnhanced } from '../api/hypothesis';
import toast from 'react-hot-toast';

const HypothesisExplorer = () => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [useEnhancedMode, setUseEnhancedMode] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [showReasoningTrace, setShowReasoningTrace] = useState(false);
  
  // Lab context state
  const [researchArea, setResearchArea] = useState('');
  const [labExpertise, setLabExpertise] = useState([]);
  const [availableEquipment, setAvailableEquipment] = useState([]);
  const [constraints, setConstraints] = useState({ budget: '', timeline: '' });
  const [expertiseLevel, setExpertiseLevel] = useState('graduate');
  
  // Conversation history
  const [conversationHistory, setConversationHistory] = useState([]);

  const sampleQuestions = [
    "What if we could use CRISPR-Cas13 to target specific RNA isoforms in live cells?",
    "What if we developed a reversible RNA modification system for temporal gene regulation?",
    "What if we could visualize RNA-protein interactions in real-time at single-molecule resolution?"
  ];

  const commonExpertise = [
    "CRISPR", "RNA-seq", "qPCR", "Western Blot", "Flow Cytometry", 
    "Microscopy", "Cell Culture", "Protein Purification", "Cloning"
  ];

  const commonEquipment = [
    "qPCR machine", "Flow cytometer", "Confocal microscope", "Plate reader",
    "Nanodrop", "Thermocycler", "Incubator", "Centrifuge", "Gel imager"
  ];

  useEffect(() => {
    // Generate session ID on mount
    setSessionId(`hypothesis-${Date.now()}`);
  }, []);

  const handleExplore = async () => {
    if (!question.trim()) {
      toast.error('Please enter a hypothesis or question');
      return;
    }

    setIsLoading(true);
    try {
      let response;
      
      if (useEnhancedMode) {
        // Use enhanced API with context
        response = await exploreHypothesisEnhanced({
          question,
          sessionId,
          userContext: {
            expertise_level: expertiseLevel,
            research_area: researchArea
          },
          hypothesisContext: {
            research_area: researchArea,
            lab_expertise: labExpertise,
            available_equipment: availableEquipment,
            constraints,
            previous_experiments: conversationHistory.slice(-3) // Last 3 experiments
          }
        });
      } else {
        // Use basic API
        response = await exploreHypothesis(question, false);
      }
      
      if (response.success || response.question) {
        setResult(response);
        // Add to conversation history
        setConversationHistory([...conversationHistory, {
          question,
          timestamp: new Date().toISOString(),
          response: response.analysis?.summary || response.answer
        }]);
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

  const ReasoningStep = ({ step, index }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
      className="flex items-start space-x-3 mb-3"
    >
      <div className="w-6 h-6 rounded-full bg-plasma-cyan/20 flex items-center justify-center flex-shrink-0 mt-1">
        <span className="text-xs text-plasma-cyan">{index + 1}</span>
      </div>
      <div className="flex-1">
        <p className="text-white/80 text-sm">{step}</p>
      </div>
    </motion.div>
  );

  const ExpertiseTag = ({ expertise, selected, onToggle }) => (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onToggle}
      className={`px-3 py-1 rounded-full text-sm transition-all ${
        selected 
          ? 'bg-bio-emerald text-white' 
          : 'bg-white/10 text-white/60 hover:bg-white/20'
      }`}
    >
      {expertise}
    </motion.button>
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
            Explore "what if" scenarios with enhanced AI reasoning and multi-stage analysis
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
              className="text-sm text-white/60 hover:text-white/80 transition-colors flex items-center"
            >
              {showAdvancedOptions ? <ChevronUpIcon className="w-4 h-4 mr-1" /> : <ChevronDownIcon className="w-4 h-4 mr-1" />}
              {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
            </button>
            
            <AnimatePresence>
              {showAdvancedOptions && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-4 space-y-4 overflow-hidden"
                >
                  {/* Enhanced Mode Toggle */}
                  <label className="flex items-center space-x-3 text-white/70">
                    <input
                      type="checkbox"
                      checked={useEnhancedMode}
                      onChange={(e) => setUseEnhancedMode(e.target.checked)}
                      className="w-4 h-4 rounded bg-white/10 border-white/30"
                    />
                    <span>Use Enhanced Analysis Mode</span>
                    <span className="text-xs bg-bio-emerald/30 px-2 py-1 rounded">Recommended</span>
                  </label>

                  {/* Lab Context Fields */}
                  {useEnhancedMode && (
                    <div className="space-y-3 pl-7">
                      {/* Research Area */}
                      <div>
                        <label className="text-sm text-white/60 mb-1 block">Research Area</label>
                        <input
                          type="text"
                          value={researchArea}
                          onChange={(e) => setResearchArea(e.target.value)}
                          placeholder="e.g., RNA splicing, CRISPR diagnostics"
                          className="w-full p-2 bg-white/5 border border-white/20 rounded text-white placeholder-white/40 text-sm"
                        />
                      </div>

                      {/* Expertise Level */}
                      <div>
                        <label className="text-sm text-white/60 mb-1 block">Expertise Level</label>
                        <select
                          value={expertiseLevel}
                          onChange={(e) => setExpertiseLevel(e.target.value)}
                          className="w-full p-2 bg-white/5 border border-white/20 rounded text-white text-sm"
                        >
                          <option value="undergraduate">Undergraduate</option>
                          <option value="graduate">Graduate</option>
                          <option value="postdoc">Postdoc</option>
                          <option value="pi">PI/Faculty</option>
                        </select>
                      </div>

                      {/* Lab Expertise */}
                      <div>
                        <label className="text-sm text-white/60 mb-1 block">Lab Expertise (click to select)</label>
                        <div className="flex flex-wrap gap-2">
                          {commonExpertise.map((exp) => (
                            <ExpertiseTag
                              key={exp}
                              expertise={exp}
                              selected={labExpertise.includes(exp)}
                              onToggle={() => {
                                if (labExpertise.includes(exp)) {
                                  setLabExpertise(labExpertise.filter(e => e !== exp));
                                } else {
                                  setLabExpertise([...labExpertise, exp]);
                                }
                              }}
                            />
                          ))}
                        </div>
                      </div>

                      {/* Available Equipment */}
                      <div>
                        <label className="text-sm text-white/60 mb-1 block">Available Equipment</label>
                        <div className="flex flex-wrap gap-2">
                          {commonEquipment.map((equip) => (
                            <ExpertiseTag
                              key={equip}
                              expertise={equip}
                              selected={availableEquipment.includes(equip)}
                              onToggle={() => {
                                if (availableEquipment.includes(equip)) {
                                  setAvailableEquipment(availableEquipment.filter(e => e !== equip));
                                } else {
                                  setAvailableEquipment([...availableEquipment, equip]);
                                }
                              }}
                            />
                          ))}
                        </div>
                      </div>

                      {/* Constraints */}
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-sm text-white/60 mb-1 block">Budget</label>
                          <select
                            value={constraints.budget}
                            onChange={(e) => setConstraints({...constraints, budget: e.target.value})}
                            className="w-full p-2 bg-white/5 border border-white/20 rounded text-white text-sm"
                          >
                            <option value="">Not specified</option>
                            <option value="limited">Limited (&lt;$5k)</option>
                            <option value="moderate">Moderate ($5k-$20k)</option>
                            <option value="generous">Generous (&gt;$20k)</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-sm text-white/60 mb-1 block">Timeline</label>
                          <select
                            value={constraints.timeline}
                            onChange={(e) => setConstraints({...constraints, timeline: e.target.value})}
                            className="w-full p-2 bg-white/5 border border-white/20 rounded text-white text-sm"
                          >
                            <option value="">Not specified</option>
                            <option value="3 months">3 months</option>
                            <option value="6 months">6 months</option>
                            <option value="1 year">1 year</option>
                            <option value="2+ years">2+ years</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
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

          {/* Session Info */}
          {conversationHistory.length > 0 && (
            <div className="text-xs text-white/40 flex items-center">
              <ArrowPathIcon className="w-3 h-3 mr-1" />
              Session: {conversationHistory.length} questions analyzed
            </div>
          )}
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
            {/* Reasoning Trace */}
            {result.reasoning_trace && result.reasoning_trace.length > 0 && (
              <GlassCard className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-white flex items-center">
                    <CpuChipIcon className="w-6 h-6 mr-2 text-plasma-cyan" />
                    AI Reasoning Process
                  </h3>
                  <button
                    onClick={() => setShowReasoningTrace(!showReasoningTrace)}
                    className="text-sm text-white/60 hover:text-white/80"
                  >
                    {showReasoningTrace ? 'Hide' : 'Show'}
                  </button>
                </div>
                <AnimatePresence>
                  {showReasoningTrace && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                    >
                      {result.reasoning_trace.map((step, index) => (
                        <ReasoningStep key={index} step={step} index={index} />
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </GlassCard>
            )}

            {/* Confidence Analysis */}
            {result.confidence_analysis && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <ChartBarIcon className="w-6 h-6 mr-2 text-plasma-cyan" />
                  Confidence Analysis
                </h3>
                
                {/* Overall Confidence */}
                <div className="mb-6">
                  <ConfidenceIndicator 
                    label="Overall Confidence" 
                    score={result.confidence_analysis.overall || 0} 
                  />
                  <p className="text-sm text-white/60 mt-2">
                    {result.confidence_analysis.interpretation}
                  </p>
                </div>

                {/* Component Scores */}
                {result.confidence_analysis.components && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <ConfidenceIndicator 
                      label="Evidence Support" 
                      score={result.confidence_analysis.components.evidence_support || 0} 
                    />
                    <ConfidenceIndicator 
                      label="Analysis Depth" 
                      score={result.confidence_analysis.components.analysis_depth || 0} 
                    />
                    <ConfidenceIndicator 
                      label="RAG Confidence" 
                      score={result.confidence_analysis.components.rag_confidence || 0} 
                    />
                    <ConfidenceIndicator 
                      label="Experimental Feasibility" 
                      score={result.confidence_analysis.components.experimental_feasibility || 0} 
                    />
                  </div>
                )}

                {/* Recommendations */}
                {result.confidence_analysis.recommendations && result.confidence_analysis.recommendations.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm text-white/60 mb-2">Recommendations:</p>
                    <ul className="space-y-1">
                      {result.confidence_analysis.recommendations.map((rec, index) => (
                        <li key={index} className="text-sm text-white/80 flex items-start">
                          <span className="text-plasma-cyan mr-2">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </GlassCard>
            )}

            {/* Multi-Stage Analysis */}
            {result.analysis && (
              <>
                {/* Summary */}
                {result.analysis.summary && (
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <SparklesIcon className="w-6 h-6 mr-2 text-bio-emerald" />
                      Analysis Summary
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {result.analysis.summary}
                    </div>
                  </GlassCard>
                )}

                {/* Scientific Basis */}
                {result.analysis.scientific_basis && (
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <AcademicCapIcon className="w-6 h-6 mr-2 text-cosmic-purple" />
                      Scientific Basis
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {result.analysis.scientific_basis}
                    </div>
                  </GlassCard>
                )}

                {/* Feasibility Assessment */}
                {result.analysis.feasibility && (
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <BeakerIcon className="w-6 h-6 mr-2 text-plasma-cyan" />
                      Feasibility Assessment
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {result.analysis.feasibility}
                    </div>
                  </GlassCard>
                )}

                {/* Innovation Assessment */}
                {result.analysis.innovation_assessment && (
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <LightBulbIcon className="w-6 h-6 mr-2 text-electric-blue" />
                      Innovation Potential
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {result.analysis.innovation_assessment}
                    </div>
                  </GlassCard>
                )}

                {/* Risk Analysis */}
                {result.analysis.risk_analysis && (
                  <GlassCard className="p-6">
                    <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                      <ExclamationTriangleIcon className="w-6 h-6 mr-2 text-nebula-pink" />
                      Risk Analysis
                    </h3>
                    <div className="text-white/80 whitespace-pre-wrap leading-relaxed">
                      {result.analysis.risk_analysis}
                    </div>
                  </GlassCard>
                )}
              </>
            )}

            {/* Experimental Design */}
            {result.experimental_design && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <BeakerIcon className="w-6 h-6 mr-2 text-bio-emerald" />
                  Experimental Design Suggestions
                </h3>
                
                {/* Feasibility Score */}
                {result.experimental_design.feasibility_score !== undefined && (
                  <div className="mb-4">
                    <ConfidenceIndicator 
                      label="Design Feasibility" 
                      score={result.experimental_design.feasibility_score} 
                    />
                  </div>
                )}

                {/* Primary Design */}
                {result.experimental_design.primary_design && (
                  <div className="mb-4">
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Primary Experiment</h4>
                    <div className="text-white/70 whitespace-pre-wrap">
                      {result.experimental_design.primary_design}
                    </div>
                  </div>
                )}

                {/* Controls */}
                {result.experimental_design.controls && result.experimental_design.controls.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Control Experiments</h4>
                    <ul className="space-y-2">
                      {result.experimental_design.controls.map((control, index) => (
                        <li key={index} className="text-white/70 flex items-start">
                          <span className="text-plasma-cyan mr-2">•</span>
                          {control}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Timeline */}
                {result.experimental_design.timeline && (
                  <div className="mb-4">
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Timeline Estimate</h4>
                    <p className="text-white/70">{result.experimental_design.timeline}</p>
                  </div>
                )}

                {/* Alternative Approaches */}
                {result.experimental_design.alternatives && result.experimental_design.alternatives.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Alternative Approaches</h4>
                    <ul className="space-y-2">
                      {result.experimental_design.alternatives.map((alt, index) => (
                        <li key={index} className="text-white/70 flex items-start">
                          <span className="text-cosmic-purple mr-2">•</span>
                          {alt}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </GlassCard>
            )}

            {/* Knowledge Synthesis */}
            {result.knowledge_synthesis && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <DocumentTextIcon className="w-6 h-6 mr-2 text-cosmic-purple" />
                  Knowledge Gaps & Future Directions
                </h3>
                
                {/* Knowledge Gaps */}
                {result.knowledge_synthesis.knowledge_gaps && result.knowledge_synthesis.knowledge_gaps.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Critical Knowledge Gaps</h4>
                    <ul className="space-y-2">
                      {result.knowledge_synthesis.knowledge_gaps.map((gap, index) => (
                        <li key={index} className="text-white/70 flex items-start">
                          <span className="text-nebula-pink mr-2">•</span>
                          {gap}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Future Directions */}
                {result.knowledge_synthesis.future_directions && result.knowledge_synthesis.future_directions.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Future Research Directions</h4>
                    <ul className="space-y-2">
                      {result.knowledge_synthesis.future_directions.map((direction, index) => (
                        <li key={index} className="text-white/70 flex items-start">
                          <span className="text-bio-emerald mr-2">•</span>
                          {direction}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Collaboration Opportunities */}
                {result.knowledge_synthesis.collaboration_opportunities && result.knowledge_synthesis.collaboration_opportunities.length > 0 && (
                  <div>
                    <h4 className="text-lg font-semibold text-white/90 mb-2">Collaboration Opportunities</h4>
                    <ul className="space-y-2">
                      {result.knowledge_synthesis.collaboration_opportunities.map((collab, index) => (
                        <li key={index} className="text-white/70 flex items-start">
                          <span className="text-electric-blue mr-2">•</span>
                          {collab}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </GlassCard>
            )}

            {/* Related Research Papers */}
            {result.related_research && result.related_research.length > 0 && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                  <DocumentTextIcon className="w-6 h-6 mr-2 text-plasma-cyan" />
                  Related Research Papers
                </h3>
                <div className="space-y-3">
                  {result.related_research.map((paper, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-3 bg-white/5 rounded-lg"
                    >
                      <h4 className="font-medium text-plasma-cyan mb-1">
                        {paper.title || 'Unknown Title'}
                      </h4>
                      {paper.matched_concept && (
                        <p className="text-xs text-bio-emerald mb-1">
                          Matched concept: {paper.matched_concept}
                        </p>
                      )}
                      <p className="text-sm text-white/60 line-clamp-2">
                        {paper.snippet || paper.content || 'No preview available'}
                      </p>
                      {paper.score !== undefined && (
                        <div className="mt-2 flex items-center">
                          <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-plasma-cyan/50"
                              style={{ width: `${(paper.score * 100).toFixed(0)}%` }}
                            />
                          </div>
                          <span className="ml-2 text-xs text-white/50">
                            {(paper.score * 100).toFixed(0)}% relevant
                          </span>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </GlassCard>
            )}

            {/* Extracted Concepts */}
            {result.extracted_concepts && result.extracted_concepts.length > 0 && (
              <GlassCard className="p-6">
                <h3 className="text-xl font-bold text-white mb-4">
                  Key Concepts Identified
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.extracted_concepts.map((concept, index) => (
                    <motion.span
                      key={index}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={`px-3 py-1 rounded-full text-sm ${
                        concept.type === 'entity' 
                          ? 'bg-bio-emerald/20 text-bio-emerald' 
                          : 'bg-cosmic-purple/20 text-cosmic-purple'
                      }`}
                    >
                      {concept.concept}
                    </motion.span>
                  ))}
                </div>
              </GlassCard>
            )}

            {/* Legacy Analysis Format (for basic mode) */}
            {!result.analysis && result.analysis_sections && Object.entries(result.analysis_sections).map(([key, content]) => {
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

            {/* Source Documents (basic mode) */}
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