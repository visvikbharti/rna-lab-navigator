import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

const ScrollDotNavigation = ({ sections = [] }) => {
  const [activeSection, setActiveSection] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  // Create refs for each section
  const sectionRefs = sections.map(() => {
    const [ref, inView] = useInView({
      threshold: 0.5,
      rootMargin: '-20% 0px -70% 0px'
    });
    return { ref, inView };
  });

  // Update active section based on which is in view
  useEffect(() => {
    sectionRefs.forEach((section, index) => {
      if (section.inView) {
        setActiveSection(index);
      }
    });
  }, [sectionRefs.map(s => s.inView).join(',')]);

  // Show/hide navigation based on scroll
  useEffect(() => {
    const handleScroll = () => {
      setIsVisible(window.scrollY > 100);
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll();

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (index) => {
    const element = document.getElementById(sections[index].id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <>
      {/* Section anchors */}
      {sections.map((section, index) => (
        <div
          key={section.id}
          id={section.id}
          ref={sectionRefs[index].ref}
          style={{ position: 'absolute', top: section.offset || 0 }}
        />
      ))}

      {/* Dot Navigation */}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 0.3 }}
            className="fixed right-8 top-1/2 -translate-y-1/2 z-50"
          >
            <div className="flex flex-col items-center space-y-3">
              {sections.map((section, index) => (
                <motion.div
                  key={section.id}
                  className="relative group"
                  whileHover={{ scale: 1.2 }}
                >
                  {/* Tooltip */}
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    whileHover={{ opacity: 1, x: -10 }}
                    className="absolute right-full mr-4 px-3 py-1 bg-gray-900/90 text-white text-sm rounded-md whitespace-nowrap pointer-events-none"
                  >
                    {section.label}
                  </motion.div>

                  {/* Dot */}
                  <button
                    onClick={() => scrollToSection(index)}
                    className={`
                      relative w-3 h-3 rounded-full transition-all duration-300
                      ${activeSection === index 
                        ? 'bg-electric-blue scale-125' 
                        : 'bg-white/30 hover:bg-white/50'
                      }
                    `}
                    aria-label={`Navigate to ${section.label}`}
                  >
                    {/* Active indicator ring */}
                    {activeSection === index && (
                      <motion.div
                        layoutId="activeDot"
                        className="absolute -inset-2 rounded-full border-2 border-electric-blue"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}

                    {/* Glow effect for active */}
                    {activeSection === index && (
                      <motion.div
                        className="absolute -inset-4 rounded-full bg-electric-blue/30 blur-xl"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                      />
                    )}
                  </button>

                  {/* Connection line */}
                  {index < sections.length - 1 && (
                    <div
                      className={`
                        absolute top-full left-1/2 -translate-x-1/2 w-px h-3
                        transition-all duration-300
                        ${activeSection > index 
                          ? 'bg-electric-blue' 
                          : 'bg-white/20'
                        }
                      `}
                    />
                  )}
                </motion.div>
              ))}
            </div>

            {/* Progress indicator */}
            <div className="mt-6 flex flex-col items-center">
              <div className="relative h-20 w-px bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="absolute top-0 left-0 w-full bg-gradient-to-b from-electric-blue to-plasma-cyan"
                  style={{
                    height: `${((activeSection + 1) / sections.length) * 100}%`
                  }}
                  transition={{ duration: 0.5, ease: "easeInOut" }}
                />
              </div>
              <div className="mt-2 text-white/50 text-xs">
                {activeSection + 1}/{sections.length}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile indicator (bottom) */}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 md:hidden"
          >
            <div className="flex items-center space-x-2">
              {sections.map((section, index) => (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(index)}
                  className={`
                    h-1 rounded-full transition-all duration-300
                    ${activeSection === index 
                      ? 'w-8 bg-electric-blue' 
                      : 'w-4 bg-white/30 hover:bg-white/50'
                    }
                  `}
                  aria-label={`Navigate to ${section.label}`}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default ScrollDotNavigation;