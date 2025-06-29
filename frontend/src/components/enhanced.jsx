// Enhanced UI Components for RNA Lab Navigator
import React from 'react';
import { motion } from 'framer-motion';

export const ParticleBackground = ({ type = 'dna', count = 100 }) => {
  return null; // Placeholder for particle animation
};

export const FloatingOrbs = () => {
  return null; // Placeholder for floating orbs animation
};

export const GlassCard = ({ children, className = '' }) => {
  return (
    <div className={`bg-white/10 backdrop-blur-md rounded-lg ${className}`}>
      {children}
    </div>
  );
};

export const GradientText = ({ children, className = '' }) => {
  return (
    <span className={`bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent ${className}`}>
      {children}
    </span>
  );
};