import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DocumentTextIcon, BeakerIcon, PlusIcon } from '@heroicons/react/24/outline';
import { GlassCard, ColossalButton, GradientText, Loading } from './enhanced';
import { generateProtocol } from '../api/hypothesis';
import toast from 'react-hot-toast';

const ProtocolBuilder = () => {
  const [requirements, setRequirements] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [generatedProtocol, setGeneratedProtocol] = useState(null);

  const handleGenerateProtocol = async () => {
    if (!requirements.trim()) {
      toast.error('Please describe your protocol requirements');
      return;
    }

    setIsLoading(true);
    try {
      const response = await generateProtocol(requirements);
      
      if (response.success) {
        setGeneratedProtocol(response.protocol);
        toast.success('Protocol generated successfully!');
      } else {
        toast.error(response.error || 'Failed to generate protocol');
      }
    } catch (error) {
      toast.error(error.message || 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const ProtocolSection = ({ title, items, icon }) => {
    if (!items || items.length === 0) return null;
    
    return (
      <div className="mb-6">
        <h4 className="text-lg font-medium text-white mb-3 flex items-center">
          <span className="text-cosmic-purple mr-2">{icon}</span>
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
              <span className="text-cosmic-purple mr-2">•</span>
              <span className="text-white/80">{item}</span>
            </motion.li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <GlassCard className="p-6">
        <div className="mb-4">
          <GradientText
            text="Protocol Builder"
            className="text-2xl font-bold mb-2"
            gradient="from-cosmic-purple to-nebula-pink"
          />
          <p className="text-white/70">
            Generate custom lab protocols based on your requirements
          </p>
        </div>

        <div className="space-y-4">
          <textarea
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            placeholder="Describe your protocol requirements... (e.g., 'I need a protocol for RNA extraction from mammalian cells using TRIzol, optimized for small sample sizes')"
            className="w-full h-40 p-4 bg-white/5 border border-white/20 rounded-lg text-white placeholder-white/40 focus:border-cosmic-purple focus:outline-none resize-none"
          />

          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <p className="text-sm text-white/50 mb-2">
              🚧 Coming Soon: Advanced Features
            </p>
            <ul className="text-xs text-white/40 space-y-1">
              <li>• Drag-and-drop protocol steps</li>
              <li>• Template library</li>
              <li>• Version control</li>
              <li>• Collaborative editing</li>
            </ul>
          </div>

          <ColossalButton
            variant="primary"
            size="large"
            onClick={handleGenerateProtocol}
            disabled={isLoading || !requirements.trim()}
            icon={<DocumentTextIcon className="w-5 h-5" />}
          >
            {isLoading ? 'Generating...' : 'Generate Protocol'}
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
          >
            <GlassCard className="p-6">
              <h3 className="text-2xl font-bold text-white mb-6">
                {generatedProtocol.title || 'Generated Protocol'}
              </h3>

              {generatedProtocol.safety_warnings && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <h4 className="text-lg font-medium text-red-400 mb-2 flex items-center">
                    ⚠️ Safety Warnings
                  </h4>
                  <ul className="space-y-1">
                    {generatedProtocol.safety_warnings.map((warning, index) => (
                      <li key={index} className="text-sm text-red-300">
                        • {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <ProtocolSection
                title="Materials"
                items={generatedProtocol.materials}
                icon={<BeakerIcon className="w-5 h-5" />}
              />

              <ProtocolSection
                title="Equipment"
                items={generatedProtocol.equipment}
                icon={<DocumentTextIcon className="w-5 h-5" />}
              />

              <ProtocolSection
                title="Procedure"
                items={generatedProtocol.steps}
                icon={<PlusIcon className="w-5 h-5" />}
              />

              <ProtocolSection
                title="Quality Control"
                items={generatedProtocol.quality_control}
                icon={<BeakerIcon className="w-5 h-5" />}
              />

              <ProtocolSection
                title="Troubleshooting"
                items={generatedProtocol.troubleshooting}
                icon={<DocumentTextIcon className="w-5 h-5" />}
              />

              <div className="mt-6 flex gap-4">
                <ColossalButton variant="secondary" size="small">
                  Download PDF
                </ColossalButton>
                <ColossalButton variant="ghost" size="small">
                  Share Protocol
                </ColossalButton>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProtocolBuilder;