import React, { useState, useEffect } from 'react';

const ScrollProgress = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollProgress = (window.scrollY / totalHeight) * 100;
      setProgress(scrollProgress);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 h-1 z-50 overflow-hidden">
      <div
        className="h-full bg-gradient-to-r from-colossal-electric-blue via-colossal-plasma-cyan to-colossal-bio-emerald transition-transform duration-150"
        style={{
          transform: `translateX(${progress - 100}%)`,
          boxShadow: '0 0 10px currentColor'
        }}
      />
    </div>
  );
};

export default ScrollProgress;