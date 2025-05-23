import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ParticleBackground,
  GlassCard,
  SectionHeader,
  ColossalButton,
  GradientText,
  Navigation,
  FloatingOrbs,
  ScrollProgress,
  ScrollDotNavigation,
  Loading
} from '../components/enhanced';
import { BeakerIcon, SparklesIcon, DocumentTextIcon, ChartBarIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const ColossalShowcase = () => {
  const sections = [
    { id: 'hero', label: 'HERO', offset: 0 },
    { id: 'discover', label: 'DISCOVER', offset: 100 },
    { id: 'hypothesize', label: 'HYPOTHESIZE', offset: 100 },
    { id: 'generate', label: 'GENERATE', offset: 100 },
    { id: 'visualize', label: 'VISUALIZE', offset: 100 }
  ];

  return (
    <div className="min-h-screen bg-deep-space overflow-hidden">
      {/* Background Effects */}
      <ParticleBackground type="dna-helix" count={200} />
      <FloatingOrbs />
      
      {/* Progress Bar */}
      <ScrollProgress />
      
      {/* Navigation */}
      <Navigation />
      
      {/* Back to Home Button */}
      <Link 
        to="/" 
        className="fixed top-8 left-8 z-50 flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-md rounded-full text-white hover:bg-white/20 transition-all duration-300"
      >
        <ArrowLeftIcon className="w-5 h-5" />
        <span>Back to Lab</span>
      </Link>
      
      {/* Dot Navigation */}
      <ScrollDotNavigation sections={sections} />

      {/* Hero Section */}
      <section id="hero" className="min-h-screen flex items-center justify-center relative">
        <div className="text-center z-10 px-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
          >
            <GradientText
              text="DECODING RNA"
              className="text-7xl md:text-9xl font-bold mb-4"
              gradient="from-electric-blue via-plasma-cyan to-bio-emerald"
            />
          </motion.div>
          
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="text-2xl md:text-4xl text-white/80 mb-8"
          >
            Intelligence Platform
          </motion.h2>
          
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            <ColossalButton
              variant="primary"
              size="large"
              icon={<SparklesIcon className="w-5 h-5" />}
            >
              Begin Your Journey
            </ColossalButton>
          </motion.div>
        </div>
      </section>

      {/* DISCOVER Section */}
      <section id="discover" className="min-h-screen py-20 px-8">
        <SectionHeader
          label="DISCOVER"
          title="Search & Analyze Research"
          subtitle="Powered by Advanced RAG System"
          color="blue"
        />
        
        <div className="max-w-6xl mx-auto mt-16 grid md:grid-cols-2 gap-8">
          <GlassCard className="p-8">
            <h3 className="text-2xl font-bold text-white mb-4">Semantic Search</h3>
            <p className="text-white/70 mb-6">
              Find exactly what you need across thousands of papers, protocols, and theses
              with our intelligent search powered by GPT-4o.
            </p>
            <div className="space-y-3">
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-electric-blue"
                  initial={{ width: 0 }}
                  animate={{ width: '85%' }}
                  transition={{ duration: 2, ease: "easeOut" }}
                />
              </div>
              <p className="text-sm text-electric-blue">85% accuracy on test queries</p>
            </div>
          </GlassCard>
          
          <GlassCard className="p-8">
            <h3 className="text-2xl font-bold text-white mb-4">Citation Tracking</h3>
            <p className="text-white/70 mb-6">
              Every answer comes with precise citations, linking back to the exact
              source documents and page numbers.
            </p>
            <Loading type="rna-helix" />
          </GlassCard>
        </div>
      </section>

      {/* HYPOTHESIZE Section */}
      <section id="hypothesize" className="min-h-screen py-20 px-8 bg-gradient-to-b from-deep-space to-earth-brown">
        <SectionHeader
          label="HYPOTHESIZE"
          title="What-If Research Simulator"
          subtitle="Explore Possibilities with AI"
          color="green"
        />
        
        <div className="max-w-4xl mx-auto mt-16">
          <GlassCard className="p-12 text-center">
            <BeakerIcon className="w-16 h-16 text-bio-emerald mx-auto mb-6" />
            <h3 className="text-3xl font-bold text-white mb-4">
              Test Your Hypotheses
            </h3>
            <p className="text-white/70 text-lg mb-8">
              Use our multi-model AI system to explore research directions,
              validate hypotheses, and discover new connections.
            </p>
            <div className="flex justify-center gap-4">
              <ColossalButton variant="secondary">
                Start Simulation
              </ColossalButton>
              <ColossalButton variant="ghost">
                View Examples
              </ColossalButton>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* GENERATE Section */}
      <section id="generate" className="min-h-screen py-20 px-8">
        <SectionHeader
          label="GENERATE"
          title="Intelligent Protocol Builder"
          subtitle="From Idea to Implementation"
          color="purple"
        />
        
        <div className="max-w-6xl mx-auto mt-16">
          <div className="grid md:grid-cols-3 gap-6">
            {['Basic Protocols', 'Advanced Techniques', 'Custom Workflows'].map((title, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <GlassCard className="p-6 h-full">
                  <DocumentTextIcon className="w-10 h-10 text-cosmic-purple mb-4" />
                  <h4 className="text-xl font-bold text-white mb-2">{title}</h4>
                  <p className="text-white/60 text-sm">
                    Generate step-by-step protocols tailored to your specific needs
                  </p>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* VISUALIZE Section */}
      <section id="visualize" className="min-h-screen py-20 px-8 bg-gradient-to-b from-deep-space to-black">
        <SectionHeader
          label="VISUALIZE"
          title="Research Timeline Explorer"
          subtitle="See the Evolution of Science"
          color="cyan"
        />
        
        <div className="max-w-4xl mx-auto mt-16">
          <GlassCard className="p-12">
            <ChartBarIcon className="w-16 h-16 text-plasma-cyan mx-auto mb-6" />
            <h3 className="text-3xl font-bold text-white text-center mb-4">
              Coming Soon
            </h3>
            <p className="text-white/70 text-center text-lg">
              Visualize research trends, track citations over time, and discover
              emerging patterns in RNA biology.
            </p>
          </GlassCard>
        </div>
      </section>
    </div>
  );
};

export default ColossalShowcase;