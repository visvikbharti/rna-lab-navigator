import React, { useEffect, useRef } from 'react';

const ParticleBackground = ({ 
  particleCount = 50, 
  particleTypes = ['float', 'dna', 'quantum'],
  interactive = true 
}) => {
  const containerRef = useRef(null);
  const particlesRef = useRef([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Clear existing particles
    container.innerHTML = '';
    particlesRef.current = [];

    // Generate particles
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      const type = particleTypes[Math.floor(Math.random() * particleTypes.length)];
      
      particle.className = `particle ${type}-particle`;
      
      // Random positioning
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      
      // Random animation delay
      particle.style.animationDelay = `${Math.random() * 5}s`;
      
      // Random size variation
      const scale = 0.5 + Math.random() * 0.5;
      particle.style.transform = `scale(${scale})`;
      
      // Set custom properties for animations
      particle.style.setProperty('--random-x', `${-50 + Math.random() * 100}px`);
      particle.style.setProperty('--random-y', `${-50 + Math.random() * 100}px`);
      
      // Apply animation based on type
      switch(type) {
        case 'float':
          particle.style.animation = `particle-float-${1 + Math.floor(Math.random() * 3)} ${4 + Math.random() * 4}s ease-in-out infinite`;
          break;
        case 'dna':
          particle.style.animation = `dna-twist ${3 + Math.random() * 2}s ease-in-out infinite`;
          break;
        case 'quantum':
          particle.style.animation = `quantum-phase ${2 + Math.random() * 2}s ease-in-out infinite`;
          break;
      }
      
      container.appendChild(particle);
      particlesRef.current.push(particle);
    }

    // Interactive mouse effects
    if (interactive) {
      const handleMouseMove = (e) => {
        const { clientX, clientY } = e;
        const { left, top, width, height } = container.getBoundingClientRect();
        
        const x = (clientX - left) / width;
        const y = (clientY - top) / height;
        
        particlesRef.current.forEach((particle, index) => {
          const offsetX = (x - 0.5) * 50 * (index % 2 === 0 ? 1 : -1);
          const offsetY = (y - 0.5) * 50 * (index % 2 === 0 ? -1 : 1);
          
          particle.style.transform = `
            translate(${offsetX}px, ${offsetY}px) 
            scale(${particle.style.transform.match(/scale\((.*?)\)/)?.[1] || 1})
          `;
        });
      };

      const handleMouseLeave = () => {
        particlesRef.current.forEach((particle) => {
          const scale = particle.style.transform.match(/scale\((.*?)\)/)?.[1] || 1;
          particle.style.transform = `scale(${scale})`;
        });
      };

      container.addEventListener('mousemove', handleMouseMove);
      container.addEventListener('mouseleave', handleMouseLeave);

      return () => {
        container.removeEventListener('mousemove', handleMouseMove);
        container.removeEventListener('mouseleave', handleMouseLeave);
      };
    }
  }, [particleCount, particleTypes, interactive]);

  // Particle burst on click
  const handleClick = (e) => {
    if (!interactive) return;
    
    const { clientX, clientY } = e;
    const { left, top } = containerRef.current.getBoundingClientRect();
    
    const burst = document.createElement('div');
    burst.className = 'particle-burst';
    burst.style.left = `${clientX - left}px`;
    burst.style.top = `${clientY - top}px`;
    
    // Create burst particles
    for (let i = 0; i < 12; i++) {
      const burstParticle = document.createElement('div');
      burstParticle.className = 'burst-particle';
      
      const angle = (i / 12) * Math.PI * 2;
      burstParticle.style.setProperty('--burst-x', Math.cos(angle));
      burstParticle.style.setProperty('--burst-y', Math.sin(angle));
      
      burst.appendChild(burstParticle);
    }
    
    containerRef.current.appendChild(burst);
    
    // Remove burst after animation
    setTimeout(() => {
      burst.remove();
    }, 1000);
  };

  return (
    <div 
      ref={containerRef}
      className="particle-container"
      onClick={handleClick}
      style={{ cursor: interactive ? 'pointer' : 'default' }}
    />
  );
};

export default ParticleBackground;