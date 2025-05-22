/**
 * Enhanced Button Component - RNA Lab Navigator
 * Colossal.com-inspired interactive button with animations
 * Phase 1: Foundation Setup
 */

import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { useAnimation } from '../../contexts/AnimationContext';

// Button variant styles using CVA
const buttonVariants = cva(
  // Base styles
  [
    'inline-flex items-center justify-center gap-2',
    'font-medium transition-all duration-200 ease-smooth',
    'focus-ring cursor-pointer select-none',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'relative overflow-hidden',
  ],
  {
    variants: {
      variant: {
        primary: [
          'bg-rna-bright-teal text-white',
          'hover:bg-rna-deep-teal',
          'shadow-md hover:shadow-teal',
          'disabled:bg-rna-silver',
        ],
        secondary: [
          'bg-white text-rna-deep-teal',
          'border border-rna-bright-teal',
          'hover:bg-rna-bright-teal hover:text-white',
          'shadow-sm hover:shadow-teal',
        ],
        ghost: [
          'bg-transparent text-rna-graphite',
          'hover:bg-rna-pearl hover:text-rna-deep-teal',
        ],
        outline: [
          'bg-transparent text-rna-deep-teal',
          'border border-rna-bright-teal',
          'hover:bg-rna-bright-teal hover:text-white',
        ],
        danger: [
          'bg-rna-error-red text-white',
          'hover:bg-red-600',
          'shadow-md hover:shadow-red-300',
        ],
        success: [
          'bg-rna-enzyme-green text-white',
          'hover:bg-green-600',
          'shadow-md hover:shadow-green-300',
        ],
      },
      size: {
        sm: 'px-3 py-2 text-sm rounded-md',
        md: 'px-4 py-2.5 text-base rounded-lg',
        lg: 'px-6 py-3 text-lg rounded-lg',
        xl: 'px-8 py-4 text-xl rounded-xl',
        icon: 'p-2 rounded-lg',
      },
      fullWidth: {
        true: 'w-full',
        false: 'w-auto',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
      fullWidth: false,
    },
  }
);

// Animation variants for the button
const buttonAnimationVariants = {
  rest: { scale: 1, y: 0 },
  hover: { 
    scale: 1.02, 
    y: -1,
    transition: { duration: 0.2 }
  },
  tap: { 
    scale: 0.98, 
    y: 0,
    transition: { duration: 0.1 }
  },
};

// Shimmer effect animation
const shimmerVariants = {
  initial: { x: '-100%' },
  animate: { 
    x: '100%',
    transition: {
      duration: 1.5,
      ease: 'easeInOut',
    }
  },
};

/**
 * Enhanced Button Component
 */
const Button = forwardRef(({
  children,
  className,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  disabled = false,
  loading = false,
  leftIcon,
  rightIcon,
  shimmer = false,
  onClick,
  type = 'button',
  ...props
}, ref) => {
  const { reducedMotion } = useAnimation();

  const handleClick = (e) => {
    if (disabled || loading) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
  };

  const MotionButton = reducedMotion ? 'button' : motion.button;

  const motionProps = reducedMotion ? {} : {
    variants: buttonAnimationVariants,
    initial: 'rest',
    whileHover: 'hover',
    whileTap: 'tap',
  };

  return (
    <MotionButton
      ref={ref}
      type={type}
      className={clsx(
        buttonVariants({ variant, size, fullWidth }),
        className
      )}
      disabled={disabled || loading}
      onClick={handleClick}
      {...motionProps}
      {...props}
    >
      {/* Shimmer effect overlay */}
      {shimmer && !reducedMotion && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
          variants={shimmerVariants}
          initial="initial"
          animate="animate"
          style={{ willChange: 'transform' }}
        />
      )}

      {/* Loading spinner */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Button content */}
      <div className={clsx('flex items-center gap-2', loading && 'opacity-0')}>
        {leftIcon && (
          <span className="flex-shrink-0">
            {leftIcon}
          </span>
        )}
        
        {children && (
          <span className="truncate">
            {children}
          </span>
        )}
        
        {rightIcon && (
          <span className="flex-shrink-0">
            {rightIcon}
          </span>
        )}
      </div>
    </MotionButton>
  );
});

Button.displayName = 'Button';

// Button group component for related actions
export const ButtonGroup = ({ children, className, orientation = 'horizontal', ...props }) => {
  return (
    <div
      className={clsx(
        'inline-flex',
        orientation === 'horizontal' ? 'flex-row' : 'flex-col',
        '[&>*:not(:first-child)]:ml-px [&>*:not(:first-child)]:rounded-l-none',
        '[&>*:not(:last-child)]:rounded-r-none',
        orientation === 'vertical' && '[&>*:not(:first-child)]:mt-px [&>*:not(:first-child)]:rounded-t-none [&>*:not(:last-child)]:rounded-b-none',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

// Icon button component
export const IconButton = forwardRef(({
  icon,
  'aria-label': ariaLabel,
  size = 'md',
  ...props
}, ref) => {
  if (!ariaLabel) {
    console.warn('IconButton requires an aria-label for accessibility');
  }

  return (
    <Button
      ref={ref}
      size="icon"
      aria-label={ariaLabel}
      className={clsx(
        size === 'sm' && 'w-8 h-8 p-1.5',
        size === 'md' && 'w-10 h-10 p-2',
        size === 'lg' && 'w-12 h-12 p-2.5',
      )}
      {...props}
    >
      {icon}
    </Button>
  );
});

IconButton.displayName = 'IconButton';

// Floating Action Button component
export const FloatingActionButton = forwardRef(({
  icon,
  className,
  size = 'md',
  ...props
}, ref) => {
  return (
    <Button
      ref={ref}
      variant="primary"
      className={clsx(
        'fixed bottom-6 right-6 z-50 rounded-full shadow-xl hover:shadow-glow',
        size === 'sm' && 'w-12 h-12 p-3',
        size === 'md' && 'w-14 h-14 p-3.5',
        size === 'lg' && 'w-16 h-16 p-4',
        className
      )}
      {...props}
    >
      {icon}
    </Button>
  );
});

FloatingActionButton.displayName = 'FloatingActionButton';

export default Button;