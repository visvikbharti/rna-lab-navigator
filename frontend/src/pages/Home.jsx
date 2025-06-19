import React, { useState } from 'react';
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
import { BeakerIcon, SparklesIcon, DocumentTextIcon, ChartBarIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import EnhancedSearchInterface from '../components/EnhancedSearchInterface';
import HypothesisExplorer from '../components/HypothesisExplorer';
import ProtocolBuilder from '../components/ProtocolBuilder';
import FeedbackAnalyticsDashboard from '../components/FeedbackAnalyticsDashboard';
import FilterChips from '../components/FilterChips';

const Home = () => {
  console.log('Home component rendered!');
  const [docType, setDocType] = useState('papers');
  const [activeSection, setActiveSection] = useState('hero');
  
  const sections = [
    { id: 'hero', label: 'HOME', offset: 0 },
    { id: 'discover', label: 'DISCOVER', offset: 100 },
    { id: 'hypothesize', label: 'HYPOTHESIZE', offset: 100 },
    { id: 'generate', label: 'GENERATE', offset: 100 },
    { id: 'visualize', label: 'VISUALIZE', offset: 100 }
  ];

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setActiveSection(sectionId);
    }
  };

  return (
    <div className="min-h-screen bg-deep-space overflow-x-hidden">
      {/* Background Effects */}
      <ParticleBackground type="dna-helix" count={200} />
      <FloatingOrbs />
      
      {/* Progress Bar */}
      <ScrollProgress />
      
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-deep-space/80 border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-electric-blue to-plasma-cyan flex items-center justify-center">
                <span className="text-white font-bold text-xl">R</span>
              </div>
              <span className="text-xl font-bold text-white">
                RNA Lab Navigator
              </span>
            </Link>

            <div className="flex items-center space-x-6">
              <Link to="/upload" className="text-white/70 hover:text-white transition-colors">
                Upload Protocol
              </Link>
              <Link to="/analytics" className="text-white/70 hover:text-white transition-colors">
                Analytics
              </Link>
              <Link to="/search-quality" className="text-white/70 hover:text-white transition-colors">
                Quality
              </Link>
              <Link to="/security" className="text-white/70 hover:text-white transition-colors">
                Security
              </Link>
              <Link to="/experiments" className="text-white/70 hover:text-white transition-colors">
                Experiments
              </Link>
              <Link to="/classic" className="text-white/50 hover:text-white/70 transition-colors text-sm">
                Classic UI
              </Link>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Production System Notice */}
      <div className="fixed top-20 right-8 z-50 max-w-sm">
        <div className="bg-green-500/20 backdrop-blur-md border border-green-400/30 rounded-lg p-3 text-white">
          <div className="text-sm font-medium text-green-300 mb-1">🟢 Production System</div>
          <div className="text-xs text-green-200/80">
            Real-time data analysis with o4-mini AI model
          </div>
        </div>
      </div>
      
      {/* Dot Navigation */}
      <ScrollDotNavigation sections={sections} />

      {/* Hero Section */}
      <section id="hero" className="min-h-screen flex items-center justify-center relative pt-20">
        <div className="text-center z-10 px-4 max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
          >
            <GradientText
              text="RNA LAB NAVIGATOR"
              className="text-6xl md:text-8xl lg:text-9xl font-bold mb-4"
              gradient="from-electric-blue via-plasma-cyan to-bio-emerald"
            />
          </motion.div>
          
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="text-2xl md:text-4xl text-white/80 mb-12"
          >
            Next-Generation Research Intelligence Platform
          </motion.h2>
          
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="flex justify-center gap-4 flex-wrap"
          >
            <ColossalButton
              variant="primary"
              size="large"
              icon={<MagnifyingGlassIcon className="w-5 h-5" />}
              onClick={() => scrollToSection('discover')}
            >
              Start Searching
            </ColossalButton>
            <ColossalButton
              variant="secondary"
              size="large"
              icon={<BeakerIcon className="w-5 h-5" />}
              onClick={() => scrollToSection('hypothesize')}
            >
              Explore Hypotheses
            </ColossalButton>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.2 }}
            className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto"
          >
            {[
              { label: 'Papers Indexed', value: '10,000+' },
              { label: 'Active Users', value: '21' },
              { label: 'Avg Response Time', value: '<5s' },
              { label: 'Query Accuracy', value: '85%' }
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl font-bold text-bio-emerald">{stat.value}</div>
                <div className="text-sm text-white/60">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* DISCOVER Section - Real Search */}
      <section id="discover" className="min-h-screen py-20 px-8">
        <SectionHeader
          label="DISCOVER"
          title="AI-Powered Research Search"
          subtitle="Find answers across papers, protocols, and theses"
          color="blue"
        />
        
        <div className="max-w-6xl mx-auto mt-16">
          <GlassCard className="p-8">
            <FilterChips selected={docType} onChange={setDocType} />
            <div className="mt-6">
              <EnhancedSearchInterface docType={docType} />
            </div>
          </GlassCard>
        </div>
      </section>

      {/* HYPOTHESIZE Section - Real Hypothesis Explorer */}
      <section id="hypothesize" className="min-h-screen py-20 px-8 bg-gradient-to-b from-deep-space to-earth-brown">
        <SectionHeader
          label="HYPOTHESIZE"
          title="Research Hypothesis Explorer"
          subtitle="Test ideas and explore research directions"
          color="green"
        />
        
        <div className="max-w-6xl mx-auto mt-16">
          <GlassCard className="p-8">
            <HypothesisExplorer />
          </GlassCard>
        </div>
      </section>

      {/* GENERATE Section - Real Protocol Builder */}
      <section id="generate" className="min-h-screen py-20 px-8">
        <SectionHeader
          label="GENERATE"
          title="Intelligent Protocol Generator"
          subtitle="Create custom protocols for your experiments"
          color="purple"
        />
        
        <div className="max-w-6xl mx-auto mt-16">
          <GlassCard className="p-8">
            <ProtocolBuilder />
          </GlassCard>
        </div>
      </section>

      {/* VISUALIZE Section - Real Analytics */}
      <section id="visualize" className="min-h-screen py-20 px-8 bg-gradient-to-b from-deep-space to-black">
        <SectionHeader
          label="VISUALIZE"
          title="Research Analytics Dashboard"
          subtitle="Track usage patterns and research trends"
          color="cyan"
        />
        
        <div className="max-w-6xl mx-auto mt-16">
          <GlassCard className="p-8">
            <FeedbackAnalyticsDashboard />
          </GlassCard>
        </div>
      </section>
    </div>
  );
};

export default Home;