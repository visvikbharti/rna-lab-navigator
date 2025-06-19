import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  ParticleBackground,
  FloatingOrbs,
  ScrollProgress,
  GradientText,
  ColossalButton,
  GlassCard
} from '../components/enhanced';
import { 
  MagnifyingGlassIcon,
  BeakerIcon,
  DocumentTextIcon,
  ChartBarIcon,
  UserGroupIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const HomeSimple = () => {
  const [activeSection, setActiveSection] = useState(0);
  
  // Section IDs for navigation
  const sections = [
    { id: 'hero', label: 'Home' },
    { id: 'features', label: 'Features' },
    { id: 'research', label: 'Research' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'team', label: 'Team' }
  ];
  
  // Simple scroll detection
  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY + window.innerHeight / 2;
      
      sections.forEach((section, index) => {
        const element = document.getElementById(section.id);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
            setActiveSection(index);
          }
        }
      });
    };
    
    window.addEventListener('scroll', handleScroll);
    handleScroll();
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  return (
    <div className="min-h-screen bg-deep-space overflow-x-hidden">
      {/* Background Effects */}
      <ParticleBackground type="dna-helix" count={200} />
      <FloatingOrbs />
      
      {/* Progress Bar */}
      <ScrollProgress />
      
      {/* Simple Navigation */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
        className="fixed top-0 left-0 right-0 z-50 bg-deep-space/80 backdrop-blur-lg border-b border-white/10"
      >
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-bold">
              <GradientText gradient="life">RNA Lab</GradientText>
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/app" className="text-white/80 hover:text-white transition-colors">
                Platform
              </Link>
              <a 
                href="#features" 
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-white/80 hover:text-white transition-colors cursor-pointer"
              >
                Features
              </a>
              <a 
                href="#research" 
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('research')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-white/80 hover:text-white transition-colors cursor-pointer"
              >
                Tools
              </a>
              <a 
                href="#analytics" 
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('analytics')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-white/80 hover:text-white transition-colors cursor-pointer"
              >
                Analytics
              </a>
              <Link to="/showcase" className="text-electric-blue hover:text-plasma-cyan transition-colors">
                ✨ Visual Demo
              </Link>
              <Link to="/app">
                <ColossalButton variant="secondary" size="small">
                  Launch App
                </ColossalButton>
              </Link>
            </div>
            {/* Mobile menu button */}
            <button className="md:hidden text-white">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </motion.nav>
      
      {/* Simple Scroll Dot Navigation */}
      <div className="fixed right-8 top-1/2 -translate-y-1/2 z-40 hidden lg:block">
        <div className="flex flex-col items-center space-y-4">
          {sections.map((section, index) => (
            <div key={section.id} className="relative group">
              {/* Tooltip */}
              <div className="absolute right-full mr-4 px-3 py-1 bg-gray-900/90 text-white text-sm rounded-md whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                {section.label}
              </div>
              
              {/* Dot */}
              <button
                onClick={() => {
                  const element = document.getElementById(section.id);
                  if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }
                }}
                className={`
                  relative w-3 h-3 rounded-full transition-all duration-300
                  ${activeSection === index 
                    ? 'bg-cyan-400 scale-125' 
                    : 'bg-white/30 hover:bg-white/50'
                  }
                `}
                aria-label={`Navigate to ${section.label}`}
              >
                {activeSection === index && (
                  <div className="absolute -inset-2 rounded-full border-2 border-cyan-400 animate-pulse" />
                )}
              </button>
              
              {/* Connection line */}
              {index < sections.length - 1 && (
                <div className="absolute top-full left-1/2 -translate-x-1/2 w-px h-4 bg-white/20" />
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Hero Section */}
      <section id="hero" className="min-h-screen flex items-center justify-center relative pt-20">
        <div className="text-center z-10 px-4 max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
          >
            <GradientText
              className="text-6xl md:text-8xl lg:text-9xl font-bold mb-4"
              gradient="life"
              animate={true}
            >
              RNA LAB NAVIGATOR
            </GradientText>
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
            <Link to="/app">
              <ColossalButton
                variant="primary"
                size="large"
                icon={<MagnifyingGlassIcon className="w-5 h-5" />}
              >
                Start Searching
              </ColossalButton>
            </Link>
          </motion.div>
        </div>
      </section>
      
      {/* Features Section */}
      <section id="features" className="min-h-screen flex items-center justify-center relative py-20">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <GradientText className="text-5xl md:text-6xl font-bold mb-4" gradient="plasma">
              Powerful Features
            </GradientText>
            <p className="text-xl text-white/60">Everything you need for RNA research</p>
          </motion.div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { 
                icon: MagnifyingGlassIcon, 
                title: 'Search & Analyze', 
                desc: 'Search through papers, protocols, and theses with real citations',
                color: 'text-electric-blue',
                link: '/app',
                stats: '85% accuracy'
              },
              { 
                icon: BeakerIcon, 
                title: 'Hypothesis Mode', 
                desc: 'Explore "what if" scenarios with AI-powered analysis',
                color: 'text-bio-emerald',
                link: '/app',
                stats: 'Multi-stage analysis'
              },
              { 
                icon: DocumentTextIcon, 
                title: 'Protocol Builder', 
                desc: 'Generate custom lab protocols with detailed steps',
                color: 'text-cosmic-purple',
                link: '/app',
                stats: 'QC checkpoints'
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
                viewport={{ once: true }}
              >
                <Link to={feature.link} className="block">
                  <GlassCard className="p-8 text-center hover:scale-105 transition-transform duration-300 h-full">
                    <motion.div
                      whileHover={{ rotate: [0, -5, 5, -5, 0] }}
                      transition={{ duration: 0.5 }}
                    >
                      <feature.icon className={`w-16 h-16 mx-auto mb-4 ${feature.color}`} />
                    </motion.div>
                    <h3 className="text-2xl font-bold text-white mb-2">{feature.title}</h3>
                    <p className="text-white/60 mb-4">{feature.desc}</p>
                    <div className={`text-sm font-medium ${feature.color}`}>
                      {feature.stats}
                    </div>
                  </GlassCard>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Research Tools Section */}
      <section id="research" className="min-h-screen flex items-center justify-center relative py-20">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <GradientText className="text-5xl md:text-6xl font-bold mb-4" gradient="sunset">
              Advanced Research Tools
            </GradientText>
            <p className="text-xl text-white/70 max-w-3xl mx-auto">
              Access cutting-edge tools designed specifically for RNA biology research
            </p>
          </motion.div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: ChartBarIcon,
                title: 'Experiment Mapper',
                desc: 'Map experiments and analyze factors',
                link: '/experiments',
                color: 'text-plasma-cyan'
              },
              {
                icon: UserGroupIcon,
                title: 'Feedback Analytics',
                desc: 'Track research quality metrics',
                link: '/analytics',
                color: 'text-bio-emerald'
              },
              {
                icon: BeakerIcon,
                title: 'Protocol Upload',
                desc: 'Share and manage lab protocols',
                link: '/upload',
                color: 'text-cosmic-purple'
              },
              {
                icon: SparklesIcon,
                title: 'Search Quality',
                desc: 'Monitor search performance',
                link: '/search-quality',
                color: 'text-electric-blue'
              }
            ].map((tool, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Link to={tool.link}>
                  <GlassCard className="p-6 h-full hover:scale-105 transition-transform duration-300">
                    <tool.icon className={`w-12 h-12 mb-4 ${tool.color}`} />
                    <h4 className="text-xl font-bold text-white mb-2">{tool.title}</h4>
                    <p className="text-white/60 text-sm">{tool.desc}</p>
                  </GlassCard>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Analytics Section */}
      <section id="analytics" className="min-h-screen flex items-center justify-center relative py-20">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <GradientText className="text-5xl md:text-6xl font-bold mb-6" gradient="ocean">
              Real-Time Analytics
            </GradientText>
            <p className="text-xl text-white/70 mb-12 max-w-3xl mx-auto">
              Monitor your research progress with powerful analytics and insights.
              Track experiments, measure outcomes, and optimize your workflow.
            </p>
            
            <GlassCard className="p-12">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[
                  { label: 'Active Users', value: '21+', icon: UserGroupIcon },
                  { label: 'Answer Accuracy', value: '85%', icon: ChartBarIcon },
                  { label: 'Query Speed', value: '<5s', icon: SparklesIcon }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.5 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className="text-center"
                  >
                    <stat.icon className="w-12 h-12 mx-auto mb-4 text-emerald-400" />
                    <motion.p 
                      className="text-4xl font-bold text-white mb-2"
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
                      viewport={{ once: true }}
                    >
                      {stat.value}
                    </motion.p>
                    <p className="text-white/60">{stat.label}</p>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </section>
      
      {/* Team Section */}
      <section id="team" className="min-h-screen flex items-center justify-center relative py-20">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <GradientText className="text-5xl md:text-6xl font-bold mb-4" gradient="plasma">
              Join Our Community
            </GradientText>
            <p className="text-xl text-white/70 max-w-3xl mx-auto">
              Connect with researchers worldwide and accelerate scientific discovery together.
            </p>
          </motion.div>
          
          <div className="flex justify-center">
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="max-w-lg"
            >
              <GlassCard className="p-12 text-center">
                <UserGroupIcon className="w-24 h-24 mx-auto mb-6 text-indigo-400" />
                <h3 className="text-3xl font-bold text-white mb-4">21+ Researchers</h3>
                <p className="text-white/60 mb-8">
                  Join a growing community of RNA biology researchers pushing the boundaries of science.
                </p>
                <Link to="/app">
                  <ColossalButton variant="primary" size="large">
                    Get Started Today
                  </ColossalButton>
                </Link>
              </GlassCard>
            </motion.div>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="relative py-12 bg-deep-space/50 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <GradientText className="text-2xl font-bold mb-4" gradient="life">
            RNA Lab Navigator
          </GradientText>
          <p className="text-white/60 mb-8">
            © 2025 CSIR-IGIB. Advancing RNA Biology Research.
          </p>
          <div className="flex justify-center gap-6">
            <Link to="/app" className="text-white/60 hover:text-white transition-colors">
              Platform
            </Link>
            <a 
              href="#features" 
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-white/60 hover:text-white transition-colors cursor-pointer"
            >
              Features
            </a>
            <a 
              href="#research" 
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('research')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-white/60 hover:text-white transition-colors cursor-pointer"
            >
              Research
            </a>
            <a 
              href="#team" 
              onClick={(e) => {
                e.preventDefault();
                document.getElementById('team')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-white/60 hover:text-white transition-colors cursor-pointer"
            >
              Community
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomeSimple;