import React, { useState, useEffect } from 'react';
import ParticleBackground from '../components/enhanced/ParticleBackground';
import GlassCard from '../components/enhanced/GlassCard';
import SectionHeader from '../components/enhanced/SectionHeader';
import ColossalButton from '../components/enhanced/ColossalButton';
import GradientText from '../components/enhanced/GradientText';
import Navigation from '../components/enhanced/Navigation';
import FloatingOrbs from '../components/enhanced/FloatingOrbs';
import ScrollProgress from '../components/enhanced/ScrollProgress';

const ColossalDemo = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('discover');

  useEffect(() => {
    // Add fade-in animation to elements as they come into view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll('.fade-in-up').forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const features = [
    {
      title: 'Intelligent Search',
      description: 'AI-powered search across papers, protocols, and theses',
      icon: '🔍',
      gradient: 'aurora'
    },
    {
      title: 'Real-time Analysis',
      description: 'Get instant insights from your research data',
      icon: '⚡',
      gradient: 'life'
    },
    {
      title: 'Collaborative Tools',
      description: 'Share findings and collaborate with your team',
      icon: '🤝',
      gradient: 'earth'
    }
  ];

  const researchAreas = [
    { label: 'CRISPR', count: 147 },
    { label: 'RNA Sequencing', count: 89 },
    { label: 'Gene Expression', count: 234 },
    { label: 'Molecular Biology', count: 156 }
  ];

  return (
    <div className="colossal-container bg-cosmic">
      <ScrollProgress />
      <FloatingOrbs count={5} />
      <ParticleBackground particleCount={80} interactive={true} />
      
      <Navigation />

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center relative px-6 pt-20">
        <div className="container mx-auto max-w-6xl text-center">
          <div className="space-y-8">
            <h1 className="text-hero fade-in-up">
              RNA Lab Navigator
            </h1>
            
            <p className="text-2xl text-white/80 max-w-3xl mx-auto fade-in-up" 
               style={{ animationDelay: '0.2s' }}>
              Accelerate your research with <GradientText gradient="aurora" animate>AI-powered insights</GradientText> from 
              papers, protocols, and institutional knowledge
            </p>

            {/* Search Box */}
            <div className="max-w-2xl mx-auto fade-in-up" style={{ animationDelay: '0.4s' }}>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search papers, protocols, or ask a research question..."
                  className="colossal-input w-full pl-12 pr-32 py-4 text-lg"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl">
                  🔍
                </span>
                <ColossalButton
                  variant="primary"
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                  onClick={() => console.log('Search:', searchQuery)}
                >
                  Search
                </ColossalButton>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex justify-center gap-8 text-white/70 fade-in-up" 
                 style={{ animationDelay: '0.6s' }}>
              <div>
                <span className="text-3xl font-bold text-white">10K+</span>
                <p>Papers</p>
              </div>
              <div>
                <span className="text-3xl font-bold text-white">500+</span>
                <p>Protocols</p>
              </div>
              <div>
                <span className="text-3xl font-bold text-white">50+</span>
                <p>Theses</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6">
        <div className="container mx-auto max-w-6xl">
          <SectionHeader
            label="DISCOVER"
            title="Transform Your Research Workflow"
            subtitle="Harness the power of AI to accelerate discoveries"
            sectionType="discover"
          />

          <div className="grid md:grid-cols-3 gap-8 mt-16">
            {features.map((feature, index) => (
              <GlassCard
                key={index}
                hover
                glow
                float
                delay={index * 0.1}
                className="fade-in-up"
              >
                <div className="text-center space-y-4">
                  <div className="text-5xl mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-bold text-white">
                    <GradientText gradient={feature.gradient}>
                      {feature.title}
                    </GradientText>
                  </h3>
                  <p className="text-white/70">{feature.description}</p>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Research Areas */}
      <section className="py-24 px-6 bg-aurora relative overflow-hidden">
        <div className="container mx-auto max-w-6xl relative z-10">
          <SectionHeader
            label="HYPOTHESIZE"
            title="Explore Research Areas"
            subtitle="Dive deep into specialized domains"
            sectionType="hypothesize"
          />

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
            {researchAreas.map((area, index) => (
              <GlassCard
                key={index}
                hover
                className="fade-in-up cursor-pointer group"
                delay={index * 0.1}
              >
                <div className="space-y-2">
                  <h4 className="text-lg font-semibold text-white group-hover:text-colossal-plasma-cyan transition-colors">
                    {area.label}
                  </h4>
                  <p className="text-3xl font-bold">
                    <GradientText gradient="aurora">{area.count}</GradientText>
                  </p>
                  <p className="text-sm text-white/60">Documents</p>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <GlassCard className="p-12">
            <h2 className="text-3xl font-bold mb-6">
              <GradientText gradient="life" animate>
                Ready to accelerate your research?
              </GradientText>
            </h2>
            <p className="text-lg text-white/70 mb-8 max-w-2xl mx-auto">
              Join researchers who are discovering insights faster with our AI-powered platform
            </p>
            <div className="flex gap-4 justify-center">
              <ColossalButton variant="primary" size="lg">
                Get Started Free
              </ColossalButton>
              <ColossalButton variant="ghost" size="lg">
                Watch Demo
              </ColossalButton>
            </div>
          </GlassCard>
        </div>
      </section>
    </div>
  );
};

export default ColossalDemo;