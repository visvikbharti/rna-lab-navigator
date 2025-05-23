/**
 * Animation Context - RNA Lab Navigator
 * Provides centralized animation and motion configuration
 * Phase 1: Foundation Setup
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

// Animation configuration
const ANIMATION_CONFIG = {
  // Durations (in seconds)
  durations: {
    fast: 0.15,
    normal: 0.25,
    slow: 0.4,
    slower: 0.6,
  },
  
  // Easing functions
  easing: {
    smooth: [0.4, 0, 0.2, 1],
    backOut: [0.175, 0.885, 0.32, 1.275],
    backIn: [0.68, -0.55, 0.265, 1.55],
    spring: [0.68, -0.55, 0.265, 1.55],
  },
  
  // Common animation variants for Framer Motion
  variants: {
    // Fade animations
    fadeIn: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
    },
    
    fadeInUp: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 },
    },
    
    fadeInDown: {
      hidden: { opacity: 0, y: -20 },
      visible: { opacity: 1, y: 0 },
    },
    
    fadeInLeft: {
      hidden: { opacity: 0, x: -20 },
      visible: { opacity: 1, x: 0 },
    },
    
    fadeInRight: {
      hidden: { opacity: 0, x: 20 },
      visible: { opacity: 1, x: 0 },
    },
    
    // Scale animations
    scaleIn: {
      hidden: { opacity: 0, scale: 0.9 },
      visible: { opacity: 1, scale: 1 },
    },
    
    scaleInUp: {
      hidden: { opacity: 0, scale: 0.9, y: 20 },
      visible: { opacity: 1, scale: 1, y: 0 },
    },
    
    // Slide animations
    slideInUp: {
      hidden: { y: '100%' },
      visible: { y: 0 },
    },
    
    slideInDown: {
      hidden: { y: '-100%' },
      visible: { y: 0 },
    },
    
    slideInLeft: {
      hidden: { x: '-100%' },
      visible: { x: 0 },
    },
    
    slideInRight: {
      hidden: { x: '100%' },
      visible: { x: 0 },
    },
    
    // Container animations (for staggered children)
    container: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
        },
      },
    },
    
    containerFast: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.05,
        },
      },
    },
    
    containerSlow: {
      hidden: { opacity: 0 },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren: 0.2,
        },
      },
    },
    
    // Interactive animations
    hover: {
      scale: 1.05,
      transition: { duration: 0.2 },
    },
    
    tap: {
      scale: 0.95,
      transition: { duration: 0.1 },
    },
    
    // Loading animations
    pulse: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    
    bounce: {
      y: [0, -10, 0],
      transition: {
        duration: 0.6,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    
    // RNA-specific animations
    rnaHelix: {
      rotate: [0, 360],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: 'linear',
      },
    },
    
    dnaStrand: {
      pathLength: [0, 1],
      transition: {
        duration: 2,
        ease: 'easeInOut',
      },
    },
  },
  
  // Transition presets
  transitions: {
    fast: { duration: 0.15, ease: [0.4, 0, 0.2, 1] },
    normal: { duration: 0.25, ease: [0.4, 0, 0.2, 1] },
    slow: { duration: 0.4, ease: [0.4, 0, 0.2, 1] },
    spring: { type: 'spring', stiffness: 300, damping: 30 },
    springBouncy: { type: 'spring', stiffness: 400, damping: 25 },
    springGentle: { type: 'spring', stiffness: 200, damping: 40 },
  },
};

// Animation Context
const AnimationContext = createContext({
  config: ANIMATION_CONFIG,
  reducedMotion: false,
  setReducedMotion: () => {},
  isAnimating: false,
  setIsAnimating: () => {},
  animationsEnabled: true,
  setAnimationsEnabled: () => {},
  animationSpeed: 1,
  setAnimationSpeed: () => {},
  particlesEnabled: true,
  setParticlesEnabled: () => {},
  particleCount: 50,
  setParticleCount: () => {},
  transitionsEnabled: true,
  setTransitionsEnabled: () => {},
});

/**
 * Animation Provider Component
 * Manages global animation state and preferences
 */
export const AnimationProvider = ({ children }) => {
  const [reducedMotion, setReducedMotion] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  const [animationSpeed, setAnimationSpeed] = useState(1); // 0.5 = slow, 1 = normal, 2 = fast
  const [particlesEnabled, setParticlesEnabled] = useState(true);
  const [particleCount, setParticleCount] = useState(50);
  const [transitionsEnabled, setTransitionsEnabled] = useState(true);

  // Check for user's motion preferences
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const prefersReduced = mediaQuery.matches;
    setReducedMotion(prefersReduced);
    
    // Auto-disable animations if user prefers reduced motion
    if (prefersReduced) {
      setAnimationsEnabled(false);
      setParticlesEnabled(false);
      setTransitionsEnabled(false);
    }

    const handleChange = (e) => {
      setReducedMotion(e.matches);
      if (e.matches) {
        setAnimationsEnabled(false);
        setParticlesEnabled(false);
        setTransitionsEnabled(false);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Load saved preferences from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('animationSettings');
    if (savedSettings && !reducedMotion) {
      try {
        const settings = JSON.parse(savedSettings);
        setAnimationsEnabled(settings.animationsEnabled ?? true);
        setAnimationSpeed(settings.animationSpeed ?? 1);
        setParticlesEnabled(settings.particlesEnabled ?? true);
        setParticleCount(settings.particleCount ?? 50);
        setTransitionsEnabled(settings.transitionsEnabled ?? true);
      } catch (error) {
        console.error('Error loading animation settings:', error);
      }
    }
  }, [reducedMotion]);

  // Save preferences to localStorage
  useEffect(() => {
    if (!reducedMotion) {
      localStorage.setItem('animationSettings', JSON.stringify({
        animationsEnabled,
        animationSpeed,
        particlesEnabled,
        particleCount,
        transitionsEnabled
      }));
    }
  }, [animationsEnabled, animationSpeed, particlesEnabled, particleCount, transitionsEnabled, reducedMotion]);

  // Animation timing utilities
  const getTransitionDuration = (baseDuration = 300) => {
    if (!transitionsEnabled || reducedMotion) return 0;
    return baseDuration / animationSpeed;
  };

  const getAnimationDuration = (baseDuration = 1000) => {
    if (!animationsEnabled || reducedMotion) return 0;
    return baseDuration / animationSpeed;
  };

  const getDelayDuration = (baseDelay = 0) => {
    if (!animationsEnabled || reducedMotion) return 0;
    return baseDelay / animationSpeed;
  };

  // Particle system configuration
  const particleConfig = {
    enabled: particlesEnabled && animationsEnabled && !reducedMotion,
    count: particleCount,
    speed: animationSpeed,
    size: {
      min: 1,
      max: 3
    },
    opacity: {
      min: 0.1,
      max: 0.4
    },
    color: '#60A5FA', // blue-400
    // Additional particle settings
    distance: 150,
    move: {
      speed: 0.5 * animationSpeed,
      direction: 'none',
      random: true,
      straight: false,
      outModes: {
        default: 'bounce'
      }
    }
  };

  // Enhanced config that respects all animation preferences
  const enhancedConfig = {
    ...ANIMATION_CONFIG,
    // Override durations based on settings
    durations: (reducedMotion || !animationsEnabled)
      ? { fast: 0, normal: 0, slow: 0, slower: 0 }
      : Object.fromEntries(
          Object.entries(ANIMATION_CONFIG.durations).map(([key, value]) => [
            key,
            value / animationSpeed
          ])
        ),
    
    // Override transitions based on settings
    transitions: (reducedMotion || !transitionsEnabled)
      ? Object.fromEntries(
          Object.entries(ANIMATION_CONFIG.transitions).map(([key, value]) => [
            key,
            { ...value, duration: 0 }
          ])
        )
      : Object.fromEntries(
          Object.entries(ANIMATION_CONFIG.transitions).map(([key, value]) => [
            key,
            value.duration ? { ...value, duration: value.duration / animationSpeed } : value
          ])
        ),
  };

  const value = {
    config: enhancedConfig,
    reducedMotion,
    setReducedMotion,
    isAnimating,
    setIsAnimating,
    animationsEnabled,
    setAnimationsEnabled,
    animationSpeed,
    setAnimationSpeed,
    particlesEnabled,
    setParticlesEnabled,
    particleCount,
    setParticleCount,
    transitionsEnabled,
    setTransitionsEnabled,
    // Utilities
    getTransitionDuration,
    getAnimationDuration,
    getDelayDuration,
    particleConfig,
  };

  return (
    <AnimationContext.Provider value={value}>
      {children}
    </AnimationContext.Provider>
  );
};

/**
 * Hook to use animation context
 */
export const useAnimation = () => {
  const context = useContext(AnimationContext);
  if (!context) {
    throw new Error('useAnimation must be used within an AnimationProvider');
  }
  return context;
};

/**
 * Hook to get animation variants with reduced motion support
 */
export const useAnimationVariants = (variantName) => {
  const { config, reducedMotion, animationsEnabled } = useAnimation();
  
  if (reducedMotion || !animationsEnabled) {
    // Return static variants for reduced motion or disabled animations
    return {
      hidden: {},
      visible: {},
    };
  }
  
  return config.variants[variantName] || config.variants.fadeIn;
};

/**
 * Hook to get transition config with reduced motion support
 */
export const useAnimationTransition = (transitionName = 'normal') => {
  const { config, reducedMotion, transitionsEnabled } = useAnimation();
  
  if (reducedMotion || !transitionsEnabled) {
    return { duration: 0 };
  }
  
  return config.transitions[transitionName] || config.transitions.normal;
};

/**
 * Hook for CSS transition classes
 */
export const useTransitionClasses = () => {
  const { transitionsEnabled, animationSpeed, reducedMotion } = useAnimation();
  
  if (!transitionsEnabled || reducedMotion) {
    return {
      base: '',
      fast: '',
      normal: '',
      slow: '',
    };
  }
  
  const getDuration = (ms) => Math.round(ms / animationSpeed);
  
  return {
    base: 'transition-all',
    fast: `transition-all duration-${getDuration(150)}`,
    normal: `transition-all duration-${getDuration(300)}`,
    slow: `transition-all duration-${getDuration(500)}`,
  };
};

/**
 * Hook for staggered animations
 */
export const useStaggerAnimation = (delayPerChild = 0.1) => {
  const { animationsEnabled, animationSpeed, reducedMotion } = useAnimation();
  
  if (!animationsEnabled || reducedMotion) {
    return {
      animate: {}
    };
  }
  
  return {
    animate: {
      transition: {
        staggerChildren: delayPerChild / animationSpeed
      }
    }
  };
};

/**
 * Higher-order component to add animation context
 */
export const withAnimation = (Component) => {
  return function AnimatedComponent(props) {
    return (
      <AnimationProvider>
        <Component {...props} />
      </AnimationProvider>
    );
  };
};

export default AnimationContext;