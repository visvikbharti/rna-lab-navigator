/**
 * Enhanced Loading Component - RNA Lab Navigator
 * Colossal.com-inspired loading states and spinners
 * Phase 1: Foundation Setup
 */

import React from 'react';
import { motion } from 'framer-motion';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { useAnimation } from '../../contexts/AnimationContext';

// Spinner variant styles using CVA
const spinnerVariants = cva(
  // Base styles
  [
    'border-solid rounded-full animate-spin',
  ],
  {
    variants: {
      size: {
        xs: 'w-3 h-3 border',
        sm: 'w-4 h-4 border',
        md: 'w-6 h-6 border-2',
        lg: 'w-8 h-8 border-2',
        xl: 'w-12 h-12 border-3',
      },
      variant: {
        primary: 'border-gray-200 border-t-rna-bright-teal',
        secondary: 'border-gray-200 border-t-rna-helix-blue',
        white: 'border-white/30 border-t-white',
        dark: 'border-gray-700 border-t-gray-900',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'primary',
    },
  }
);

// RNA Helix animation variants
const helixVariants = {
  animate: {
    rotate: [0, 360],
    transition: {
      duration: 3,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};

// Pulse animation variants
const pulseVariants = {
  animate: {
    scale: [1, 1.2, 1],
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Dots animation variants
const dotsContainerVariants = {
  animate: {
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const dotVariants = {
  animate: {
    y: [0, -10, 0],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

/**
 * Basic Spinner Component
 */
export const Spinner = ({ size = 'md', variant = 'primary', className, ...props }) => {
  return (
    <div
      className={clsx(spinnerVariants({ size, variant }), className)}
      role="status"
      aria-label="Loading"
      {...props}
    />
  );
};

/**
 * RNA Helix Spinner
 */
export const RNAHelixSpinner = ({ size = 'md', className, color = 'rna-bright-teal' }) => {
  const { reducedMotion } = useAnimation();
  const MotionDiv = reducedMotion ? 'div' : motion.div;

  const sizeClasses = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const motionProps = reducedMotion ? {} : {
    variants: helixVariants,
    animate: 'animate',
  };

  return (
    <MotionDiv
      className={clsx(sizeClasses[size], className)}
      role="status"
      aria-label="Loading"
      {...motionProps}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className={`w-full h-full text-${color}`}
      >
        <path
          d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="31.416"
          strokeDashoffset="15.708"
        />
        <path
          d="M12 6v12"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M8 8l8 8M16 8l-8 8"
          stroke="currentColor"
          strokeWidth="1"
          strokeLinecap="round"
        />
      </svg>
    </MotionDiv>
  );
};

/**
 * Pulse Loader
 */
export const PulseLoader = ({ size = 'md', className, color = 'rna-bright-teal' }) => {
  const { reducedMotion } = useAnimation();
  const MotionDiv = reducedMotion ? 'div' : motion.div;

  const sizeClasses = {
    xs: 'w-2 h-2',
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8',
  };

  const motionProps = reducedMotion ? {} : {
    variants: pulseVariants,
    animate: 'animate',
  };

  return (
    <MotionDiv
      className={clsx(
        sizeClasses[size],
        `bg-${color}`,
        'rounded-full',
        className
      )}
      role="status"
      aria-label="Loading"
      {...motionProps}
    />
  );
};

/**
 * Dots Loader
 */
export const DotsLoader = ({ size = 'md', className, color = 'rna-bright-teal' }) => {
  const { reducedMotion } = useAnimation();
  const MotionDiv = reducedMotion ? 'div' : motion.div;

  const sizeClasses = {
    xs: 'w-1.5 h-1.5',
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
    xl: 'w-6 h-6',
  };

  const gapClasses = {
    xs: 'gap-1',
    sm: 'gap-1.5',
    md: 'gap-2',
    lg: 'gap-3',
    xl: 'gap-4',
  };

  const containerProps = reducedMotion ? {} : {
    variants: dotsContainerVariants,
    animate: 'animate',
  };

  const dotProps = reducedMotion ? {} : {
    variants: dotVariants,
  };

  return (
    <MotionDiv
      className={clsx('flex items-center', gapClasses[size], className)}
      role="status"
      aria-label="Loading"
      {...containerProps}
    >
      {[0, 1, 2].map((index) => (
        <MotionDiv
          key={index}
          className={clsx(
            sizeClasses[size],
            `bg-${color}`,
            'rounded-full'
          )}
          {...dotProps}
        />
      ))}
    </MotionDiv>
  );
};

/**
 * Progress Bar Loader
 */
export const ProgressLoader = ({ 
  progress = 0, 
  size = 'md', 
  variant = 'primary',
  animated = false,
  className 
}) => {
  const heightClasses = {
    xs: 'h-1',
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
    xl: 'h-6',
  };

  const colorClasses = {
    primary: 'bg-rna-bright-teal',
    secondary: 'bg-rna-helix-blue',
    success: 'bg-rna-enzyme-green',
    warning: 'bg-rna-warning-amber',
    error: 'bg-rna-error-red',
  };

  return (
    <div
      className={clsx(
        'w-full bg-gray-200 rounded-full overflow-hidden',
        heightClasses[size],
        className
      )}
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        className={clsx(
          heightClasses[size],
          colorClasses[variant],
          'rounded-full transition-all duration-300',
          animated && 'bg-gradient-to-r from-current via-white/20 to-current bg-[length:200%_100%] animate-[shimmer_2s_infinite]'
        )}
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />
    </div>
  );
};

/**
 * Full Page Loading Overlay
 */
export const LoadingOverlay = ({ 
  loading = true,
  message = 'Loading...',
  variant = 'spinner',
  backdrop = true,
  className,
  children 
}) => {
  const { reducedMotion } = useAnimation();

  if (!loading) return children || null;

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const contentVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { delay: 0.1 }
    },
  };

  const MotionDiv = reducedMotion ? 'div' : motion.div;

  const overlayProps = reducedMotion ? {} : {
    variants: overlayVariants,
    initial: 'hidden',
    animate: 'visible',
    exit: 'hidden',
  };

  const contentProps = reducedMotion ? {} : {
    variants: contentVariants,
    initial: 'hidden',
    animate: 'visible',
  };

  return (
    <MotionDiv
      className={clsx(
        'fixed inset-0 z-50 flex items-center justify-center',
        backdrop && 'bg-black/50 backdrop-blur-sm',
        className
      )}
      {...overlayProps}
    >
      <MotionDiv
        className="flex flex-col items-center gap-4 p-6 bg-white rounded-xl shadow-xl"
        {...contentProps}
      >
        {/* Loader */}
        <div className="flex items-center justify-center">
          {variant === 'spinner' && <Spinner size="lg" />}
          {variant === 'helix' && <RNAHelixSpinner size="lg" />}
          {variant === 'pulse' && <PulseLoader size="lg" />}
          {variant === 'dots' && <DotsLoader size="lg" />}
        </div>

        {/* Message */}
        {message && (
          <p className="text-rna-charcoal font-medium text-center">
            {message}
          </p>
        )}
      </MotionDiv>
    </MotionDiv>
  );
};

/**
 * Skeleton Loader
 */
export const Skeleton = ({ 
  className,
  variant = 'rectangular',
  width,
  height,
  lines = 1,
  ...props 
}) => {
  const baseClasses = 'bg-gray-200 animate-pulse';
  
  if (variant === 'text') {
    return (
      <div className={clsx('space-y-2', className)} {...props}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={clsx(
              baseClasses,
              'h-4 rounded',
              index === lines - 1 && lines > 1 && 'w-3/4'
            )}
            style={{ width: index === 0 ? width : undefined }}
          />
        ))}
      </div>
    );
  }

  if (variant === 'circular') {
    return (
      <div
        className={clsx(baseClasses, 'rounded-full', className)}
        style={{ width: width || height, height: height || width }}
        {...props}
      />
    );
  }

  return (
    <div
      className={clsx(baseClasses, 'rounded', className)}
      style={{ width, height }}
      {...props}
    />
  );
};

/**
 * Default Loading Component
 */
const Loading = ({ 
  variant = 'spinner', 
  size = 'md', 
  message,
  className,
  ...props 
}) => {
  return (
    <div className={clsx('flex flex-col items-center gap-3', className)} {...props}>
      {variant === 'spinner' && <Spinner size={size} />}
      {variant === 'helix' && <RNAHelixSpinner size={size} />}
      {variant === 'pulse' && <PulseLoader size={size} />}
      {variant === 'dots' && <DotsLoader size={size} />}
      
      {message && (
        <p className="text-rna-graphite text-sm font-medium">
          {message}
        </p>
      )}
    </div>
  );
};

export default Loading;