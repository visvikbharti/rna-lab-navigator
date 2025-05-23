import React from 'react';

const SectionHeader = ({ 
  label, 
  title, 
  subtitle,
  sectionType = 'discover' // discover, hypothesize, generate, visualize
}) => {
  const sectionClass = `section-${sectionType}`;
  
  return (
    <div className={`section-header ${sectionClass}`}>
      {label && (
        <div className="section-label">
          {label}
        </div>
      )}
      
      {title && (
        <h2 className="section-title">
          {title.split(' ').map((word, index) => (
            <span 
              key={index}
              className="dissolve-text"
              data-text={word}
              style={{ 
                display: 'inline-block',
                marginRight: '0.25em',
                animationDelay: `${index * 0.1}s` 
              }}
            >
              {word}
            </span>
          ))}
        </h2>
      )}
      
      {subtitle && (
        <p className="text-lg text-white/70 mt-4 fade-in-up" 
           style={{ animationDelay: '0.3s' }}>
          {subtitle}
        </p>
      )}
    </div>
  );
};

export default SectionHeader;