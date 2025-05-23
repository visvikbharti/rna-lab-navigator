import React, { useState } from 'react';

const ColossalButton = ({ 
  children, 
  onClick, 
  variant = 'default', // default, primary, ghost
  size = 'md', // sm, md, lg
  disabled = false,
  loading = false,
  icon,
  className = ''
}) => {
  const [ripples, setRipples] = useState([]);

  const handleClick = (e) => {
    if (disabled || loading) return;
    
    // Create ripple effect
    const button = e.currentTarget;
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ripple = {
      x,
      y,
      id: Date.now()
    };
    
    setRipples([...ripples, ripple]);
    
    // Remove ripple after animation
    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== ripple.id));
    }, 1000);
    
    if (onClick) onClick(e);
  };

  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  };

  const variantClasses = {
    default: 'colossal-btn',
    primary: 'colossal-btn colossal-btn-primary',
    ghost: 'colossal-btn bg-transparent hover:bg-white/5'
  };

  return (
    <button
      className={`
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${loading ? 'cursor-wait' : ''}
        relative overflow-hidden
        ${className}
      `}
      onClick={handleClick}
      disabled={disabled || loading}
    >
      <span className="relative z-10 flex items-center justify-center gap-2">
        {loading && (
          <div className="colossal-loader w-4 h-4" />
        )}
        {icon && !loading && (
          <span className="inline-block">{icon}</span>
        )}
        {children}
      </span>
      
      {/* Ripple effects */}
      {ripples.map(ripple => (
        <span
          key={ripple.id}
          className="absolute"
          style={{
            left: ripple.x,
            top: ripple.y,
            transform: 'translate(-50%, -50%)',
            animation: 'ripple 1s ease-out'
          }}
        >
          <span className="block w-2 h-2 bg-white/30 rounded-full animate-ping" />
        </span>
      ))}
    </button>
  );
};

export default ColossalButton;