import React from 'react';

const FloatingOrbs = ({ count = 3 }) => {
  const orbs = Array.from({ length: count }, (_, i) => ({
    id: i,
    size: 200 + Math.random() * 300,
    x: Math.random() * 100,
    y: Math.random() * 100,
    duration: 15 + Math.random() * 10,
    delay: Math.random() * 5
  }));

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      {orbs.map((orb) => (
        <div
          key={orb.id}
          className="absolute rounded-full"
          style={{
            width: `${orb.size}px`,
            height: `${orb.size}px`,
            left: `${orb.x}%`,
            top: `${orb.y}%`,
            transform: 'translate(-50%, -50%)',
            background: `radial-gradient(circle at 30% 30%, 
              ${orb.id % 2 === 0 ? 'var(--colossal-electric-blue)' : 'var(--colossal-plasma-cyan)'} 0%, 
              transparent 70%)`,
            opacity: 0.1,
            animation: `float ${orb.duration}s ease-in-out ${orb.delay}s infinite`,
            filter: 'blur(40px)'
          }}
        />
      ))}
    </div>
  );
};

export default FloatingOrbs;