import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  DocumentTextIcon, 
  BeakerIcon, 
  PlusIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { GlassCard, ColossalButton, GradientText, Loading, Input } from './enhanced';
import { generateProtocolEnhanced } from '../api/hypothesis';
import toast from 'react-hot-toast';

const ProtocolBuilder = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [generatedProtocol, setGeneratedProtocol] = useState(null);
  
  // Form state
  const [experimentType, setExperimentType] = useState('');
  const [sampleType, setSampleType] = useState('');
  const [sampleSize, setSampleSize] = useState('');
  const [objectives, setObjectives] = useState('');
  const [safetyLevel, setSafetyLevel] = useState('BSL-1');
  const [constraints, setConstraints] = useState('');
  
  // Lab capabilities
  const [equipment, setEquipment] = useState('');
  const [reagents, setReagents] = useState('');
  const [expertise, setExpertise] = useState('');
  
  // Optimization preferences
  const [optimizeFor, setOptimizeFor] = useState({
    time: false,
    cost: false,
    yield: false,
    quality: false
  });

  const handleGenerateProtocol = async () => {
    if (!experimentType.trim() || !sampleType.trim() || !objectives.trim()) {
      toast.error('Please fill in the required fields');
      return;
    }

    setIsLoading(true);
    try {
      const response = await generateProtocolEnhanced({
        experimentType: experimentType.trim(),
        sampleType: sampleType.trim(),
        sampleSize: sampleSize.trim(),
        objectives: objectives.trim(),
        labCapabilities: {
          equipment: equipment.split(',').map(e => e.trim()).filter(Boolean),
          reagents: reagents.split(',').map(r => r.trim()).filter(Boolean),
          expertise: expertise.split(',').map(e => e.trim()).filter(Boolean)
        },
        optimizationPreferences: optimizeFor,
        safetyLevel,
        constraints: constraints.split(',').map(c => c.trim()).filter(Boolean)
      });
      
      if (response.protocol || response.title) {
        setGeneratedProtocol(response.protocol || response);
        toast.success('Protocol generated successfully!');
      } else if (response.error) {
        toast.error(response.error);
      } else {
        toast.error('Failed to generate protocol');
      }
    } catch (error) {
      toast.error(error.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const ProtocolSection = ({ title, items, icon, variant = 'default' }) => {
    if (!items || items.length === 0) return null;
    
    const variantStyles = {
      default: 'text-white',
      warning: 'text-yellow-400',
      danger: 'text-red-400',
      success: 'text-green-400',
      info: 'text-blue-400'
    };
    
    return (
      <div className="mb-6">
        <h4 className={`text-lg font-medium ${variantStyles[variant]} mb-3 flex items-center`}>
          <span className="mr-2">{icon}</span>
          {title}
        </h4>
        <ul className="space-y-2">
          {items.map((item, index) => (
            <motion.li
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-start"
            >
              <span className={`${variantStyles[variant]} mr-2`}>•</span>
              <span className="text-white/80">{item}</span>
            </motion.li>
          ))}
        </ul>
      </div>
    );
  };

  const TimelineStep = ({ step, index }) => {
    const isCritical = step.critical || false;
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className={`relative p-4 rounded-lg border ${
          isCritical 
            ? 'bg-red-500/10 border-red-500/30' 
            : 'bg-white/5 border-white/20'
        }`}
      >
        <div className="flex items-start justify-between mb-2">
          <h5 className="text-white font-medium flex items-center">
            <span className="text-cosmic-purple mr-2">Step {step.step || index + 1}</span>
            {step.name || step.title}
            {isCritical && (
              <ExclamationTriangleIcon className="w-4 h-4 text-red-400 ml-2" />
            )}
          </h5>
          {(step.duration || step.time) && (
            <span className="text-white/60 text-sm flex items-center">
              <ClockIcon className="w-4 h-4 mr-1" />
              {step.duration || step.time}
            </span>
          )}
        </div>
        <p className="text-white/70 text-sm mb-2">{step.description}</p>
        {(step.note || (step.safety_notes && step.safety_notes.length > 0)) && (
          <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded">
            <p className="text-yellow-300 text-xs">
              {step.note || (step.safety_notes && step.safety_notes.join('; '))}
            </p>
          </div>
        )}
        {step.qc_checkpoint && (
          <div className="mt-2 p-2 bg-green-500/10 border border-green-500/30 rounded">
            <p className="text-green-300 text-xs flex items-center">
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              QC: {step.qc_checkpoint}
            </p>
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <GlassCard className="p-6">
        <div className="mb-6">
          <GradientText
            text="Enhanced Protocol Builder"
            className="text-2xl font-bold mb-2"
            gradient="from-cosmic-purple to-nebula-pink"
          />
          <p className="text-white/70">
            Generate comprehensive lab protocols with detailed parameters
          </p>
        </div>

        <div className="space-y-6">
          {/* Basic Information */}
          <div>
            <h3 className="text-lg font-medium text-white mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Experiment Type *"
                value={experimentType}
                onChange={(e) => setExperimentType(e.target.value)}
                placeholder="e.g., RNA extraction, PCR, Western blot"
              />
              <Input
                label="Sample Type *"
                value={sampleType}
                onChange={(e) => setSampleType(e.target.value)}
                placeholder="e.g., Mammalian cells, Tissue, Bacteria"
              />
              <Input
                label="Sample Size"
                value={sampleSize}
                onChange={(e) => setSampleSize(e.target.value)}
                placeholder="e.g., 10^6 cells, 100mg tissue"
              />
              <div>
                <label className="block text-white/70 text-sm mb-2">Safety Level *</label>
                <select
                  value={safetyLevel}
                  onChange={(e) => setSafetyLevel(e.target.value)}
                  className="w-full p-3 bg-white/5 border border-white/20 rounded-lg text-white focus:border-cosmic-purple focus:outline-none"
                >
                  <option value="BSL-1">BSL-1 (Minimal risk)</option>
                  <option value="BSL-2">BSL-2 (Moderate risk)</option>
                  <option value="BSL-3">BSL-3 (High risk)</option>
                  <option value="BSL-4">BSL-4 (Maximum risk)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Objectives */}
          <div>
            <label className="block text-white/70 text-sm mb-2">Experimental Objectives *</label>
            <textarea
              value={objectives}
              onChange={(e) => setObjectives(e.target.value)}
              placeholder="Describe your experimental goals and expected outcomes..."
              className="w-full h-24 p-4 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40 focus:border-cosmic-purple focus:outline-none resize-none"
            />
          </div>

          {/* Lab Capabilities */}
          <div>
            <h3 className="text-lg font-medium text-white mb-4">Lab Capabilities</h3>
            <div className="space-y-4">
              <Input
                label="Available Equipment"
                value={equipment}
                onChange={(e) => setEquipment(e.target.value)}
                placeholder="e.g., Centrifuge, PCR machine, -80°C freezer (comma-separated)"
              />
              <Input
                label="Available Reagents"
                value={reagents}
                onChange={(e) => setReagents(e.target.value)}
                placeholder="e.g., TRIzol, DNase, RNase inhibitor (comma-separated)"
              />
              <Input
                label="Team Expertise"
                value={expertise}
                onChange={(e) => setExpertise(e.target.value)}
                placeholder="e.g., Molecular biology, Cell culture, Bioinformatics (comma-separated)"
              />
            </div>
          </div>

          {/* Optimization Preferences */}
          <div>
            <h3 className="text-lg font-medium text-white mb-4">Optimization Preferences</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries({
                time: 'Minimize Time',
                cost: 'Minimize Cost',
                yield: 'Maximize Yield',
                quality: 'Maximize Quality'
              }).map(([key, label]) => (
                <label key={key} className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={optimizeFor[key]}
                    onChange={(e) => setOptimizeFor({ ...optimizeFor, [key]: e.target.checked })}
                    className="mr-2 rounded border-white/20 bg-white/10 text-cosmic-purple focus:ring-cosmic-purple"
                  />
                  <span className="text-white/70 text-sm">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Constraints */}
          <div>
            <Input
              label="Constraints"
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              placeholder="e.g., Limited budget, Time-sensitive, No access to specific equipment (comma-separated)"
            />
          </div>

          <ColossalButton
            variant="primary"
            size="large"
            onClick={handleGenerateProtocol}
            disabled={isLoading || !experimentType.trim() || !sampleType.trim() || !objectives.trim()}
            icon={<DocumentTextIcon className="w-5 h-5" />}
          >
            {isLoading ? 'Generating Enhanced Protocol...' : 'Generate Protocol'}
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

      {/* Generated Protocol */}
      <AnimatePresence>
        {generatedProtocol && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Main Protocol */}
            <GlassCard className="p-6">
              <h3 className="text-2xl font-bold text-white mb-6">
                {generatedProtocol.title || 'Generated Protocol'}
              </h3>

              {/* Overview if available */}
              {generatedProtocol.overview && (
                <div className="mb-6 p-4 bg-white/5 rounded-lg">
                  <p className="text-white/80">{generatedProtocol.overview}</p>
                </div>
              )}
              
              {/* Protocol Metadata */}
              {(generatedProtocol.estimated_time || generatedProtocol.estimated_cost || generatedProtocol.expected_duration || generatedProtocol.difficulty_level) && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  {generatedProtocol.estimated_time && (
                    <div className="p-4 bg-white/5 rounded-lg border border-white/20">
                      <div className="flex items-center text-white/60 mb-1">
                        <ClockIcon className="w-5 h-5 mr-2" />
                        <span className="text-sm">Estimated Time</span>
                      </div>
                      <p className="text-xl font-medium text-white">{generatedProtocol.estimated_time || generatedProtocol.expected_duration}</p>
                    </div>
                  )}
                  {generatedProtocol.estimated_cost && (
                    <div className="p-4 bg-white/5 rounded-lg border border-white/20">
                      <div className="flex items-center text-white/60 mb-1">
                        <CurrencyDollarIcon className="w-5 h-5 mr-2" />
                        <span className="text-sm">Estimated Cost</span>
                      </div>
                      <p className="text-xl font-medium text-white">{generatedProtocol.estimated_cost}</p>
                    </div>
                  )}
                  {generatedProtocol.difficulty_level && (
                    <div className="p-4 bg-white/5 rounded-lg border border-white/20">
                      <div className="flex items-center text-white/60 mb-1">
                        <LightBulbIcon className="w-5 h-5 mr-2" />
                        <span className="text-sm">Difficulty Level</span>
                      </div>
                      <p className="text-xl font-medium text-white">{generatedProtocol.difficulty_level}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Safety Guidelines/Warnings */}
              {(generatedProtocol.safety_warnings || generatedProtocol.safety_guidelines) && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <ProtocolSection
                    title="Safety Warnings"
                    items={generatedProtocol.safety_warnings || generatedProtocol.safety_guidelines}
                    icon={<ShieldCheckIcon className="w-5 h-5" />}
                    variant="danger"
                  />
                </div>
              )}

              {/* Materials and Equipment */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <ProtocolSection
                    title="Materials"
                    items={generatedProtocol.materials}
                    icon={<BeakerIcon className="w-5 h-5" />}
                  />
                </div>
                <div>
                  <ProtocolSection
                    title="Equipment"
                    items={generatedProtocol.equipment}
                    icon={<DocumentTextIcon className="w-5 h-5" />}
                  />
                </div>
              </div>

              {/* Procedure Timeline or Steps */}
              {(generatedProtocol.procedure_timeline || generatedProtocol.steps) && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-white mb-4 flex items-center">
                    <PlusIcon className="w-5 h-5 text-cosmic-purple mr-2" />
                    Procedure Timeline
                  </h4>
                  <div className="space-y-4">
                    {(generatedProtocol.procedure_timeline || generatedProtocol.steps).map((step, index) => (
                      <TimelineStep key={index} step={step} index={index} />
                    ))}
                  </div>
                </div>
              )}

              {/* Quality Control */}
              <ProtocolSection
                title="Quality Control Checkpoints"
                items={generatedProtocol.quality_control}
                icon={<CheckCircleIcon className="w-5 h-5" />}
                variant="success"
              />

              {/* Troubleshooting */}
              <ProtocolSection
                title="Troubleshooting Guide"
                items={generatedProtocol.troubleshooting}
                icon={<ExclamationTriangleIcon className="w-5 h-5" />}
                variant="warning"
              />
            </GlassCard>

            {/* Reasoning and Compatibility */}
            {generatedProtocol.reasoning && (
              <GlassCard className="p-6">
                <h4 className="text-lg font-medium text-white mb-4 flex items-center">
                  <LightBulbIcon className="w-5 h-5 text-cosmic-purple mr-2" />
                  Protocol Reasoning
                </h4>
                <div className="space-y-4">
                  {generatedProtocol.reasoning.optimization_notes && (
                    <div>
                      <h5 className="text-white/80 font-medium mb-2">Optimization Notes</h5>
                      <p className="text-white/60 text-sm">{generatedProtocol.reasoning.optimization_notes}</p>
                    </div>
                  )}
                  {generatedProtocol.reasoning.compatibility_check && (
                    <div>
                      <h5 className="text-white/80 font-medium mb-2">Compatibility Check</h5>
                      <p className="text-white/60 text-sm">{generatedProtocol.reasoning.compatibility_check}</p>
                    </div>
                  )}
                  {generatedProtocol.reasoning.alternative_approaches && (
                    <div>
                      <h5 className="text-white/80 font-medium mb-2">Alternative Approaches</h5>
                      <ul className="space-y-2">
                        {generatedProtocol.reasoning.alternative_approaches.map((alt, index) => (
                          <li key={index} className="text-white/60 text-sm">
                            • {alt}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </GlassCard>
            )}

            {/* Validation Criteria */}
            {generatedProtocol.validation_criteria && (
              <GlassCard className="p-6">
                <h4 className="text-lg font-medium text-white mb-4 flex items-center">
                  <CheckCircleIcon className="w-5 h-5 text-cosmic-purple mr-2" />
                  Validation Criteria
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {generatedProtocol.validation_criteria.map((criterion, index) => (
                    <div key={index} className="p-3 bg-white/5 rounded-lg border border-white/20">
                      <h5 className="text-white/80 font-medium mb-1">{criterion.metric}</h5>
                      <p className="text-white/60 text-sm">{criterion.expected_value}</p>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}

            {/* Actions */}
            <div className="flex gap-4">
              <ColossalButton variant="secondary" size="small">
                Download PDF
              </ColossalButton>
              <ColossalButton variant="ghost" size="small">
                Share Protocol
              </ColossalButton>
              <ColossalButton 
                variant="ghost" 
                size="small"
                icon={<ArrowPathIcon className="w-4 h-4" />}
                onClick={() => {
                  setGeneratedProtocol(null);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              >
                Generate New
              </ColossalButton>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProtocolBuilder;