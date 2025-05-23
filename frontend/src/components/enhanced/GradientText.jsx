import React from 'react';

const GradientText = ({ 
  children, 
  gradient = 'aurora', // cosmic, aurora, life, earth, custom
  className = '',
  animate = false,
  glow = false,
  customGradient
}) => {
  const gradientMap = {
    cosmic: 'var(--gradient-cosmic)',
    aurora: 'var(--gradient-aurora)',
    life: 'var(--gradient-life)',
    earth: 'var(--gradient-earth)',
    custom: customGradient || 'var(--gradient-aurora)'
  };

  return (
    <span
      className={`
        inline-block
        ${animate ? 'animate-pulse' : ''}
        ${glow ? 'glow-text' : ''}
        ${className}
      `}
      style={{
        background: gradientMap[gradient],
        backgroundClip: 'text',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundSize: animate ? '200% 200%' : '100% 100%',
        animation: animate ? 'cosmic-shift 5s ease infinite' : undefined
      }}
    >
      {children}
    </span>
  );
};

export default GradientText;