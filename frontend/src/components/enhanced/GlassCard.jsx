import React, { useRef, useEffect } from 'react';

const GlassCard = ({ 
  children, 
  className = '', 
  hover = true,
  glow = false,
  float = false,
  delay = 0
}) => {
  const cardRef = useRef(null);

  useEffect(() => {
    const card = cardRef.current;
    if (!card || !hover) return;

    const handleMouseMove = (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = (y - centerY) / 20;
      const rotateY = (centerX - x) / 20;
      
      card.style.transform = `
        perspective(1000px)
        rotateX(${rotateX}deg)
        rotateY(${rotateY}deg)
        ${float ? 'translateY(0)' : ''}
      `;
    };

    const handleMouseLeave = () => {
      card.style.transform = float ? '' : 'perspective(1000px) rotateX(0) rotateY(0)';
    };

    card.addEventListener('mousemove', handleMouseMove);
    card.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      card.removeEventListener('mousemove', handleMouseMove);
      card.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [hover, float]);

  return (
    <div
      ref={cardRef}
      className={`glass-card ${glow ? 'card-glow' : ''} ${float ? 'float-element' : ''} ${className}`}
      style={{
        animationDelay: `${delay}s`,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        transformStyle: 'preserve-3d'
      }}
    >
      {children}
    </div>
  );
};

export default GlassCard;