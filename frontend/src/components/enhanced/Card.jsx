/**
 * Enhanced Card Component - RNA Lab Navigator
 * Colossal.com-inspired interactive card with animations
 * Phase 1: Foundation Setup
 */

import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { useAnimation } from '../../contexts/AnimationContext';

// Card variant styles using CVA
const cardVariants = cva(
  // Base styles
  [
    'bg-white rounded-xl overflow-hidden',
    'transition-all duration-200 ease-smooth',
  ],
  {
    variants: {
      variant: {
        default: 'shadow-md border border-gray-100',
        interactive: [
          'shadow-md border border-gray-100 cursor-pointer',
          'hover:shadow-xl hover:-translate-y-1',
          'focus-ring',
        ],
        glass: [
          'backdrop-blur-lg bg-white/80 border border-white/20',
          'shadow-lg',
        ],
        gradient: [
          'bg-gradient-card border border-white/50',
          'shadow-lg',
        ],
        outline: 'border-2 border-rna-bright-teal/20 shadow-sm',
        elevated: 'shadow-xl border border-gray-50',
      },
      size: {
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
        xl: 'p-10',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
        xl: 'p-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

// Animation variants for the card
const cardAnimationVariants = {
  rest: { 
    scale: 1, 
    y: 0,
    rotateX: 0,
    rotateY: 0,
  },
  hover: { 
    scale: 1.02, 
    y: -4,
    rotateX: 5,
    rotateY: 5,
    transition: { 
      duration: 0.3,
      ease: [0.175, 0.885, 0.32, 1.275]
    }
  },
  tap: { 
    scale: 0.98, 
    y: 0,
    transition: { duration: 0.1 }
  },
};

// Entrance animation variants
const entranceVariants = {
  hidden: { 
    opacity: 0, 
    y: 20, 
    scale: 0.9 
  },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.175, 0.885, 0.32, 1.275]
    }
  },
};

/**
 * Enhanced Card Component
 */
const Card = forwardRef(({
  children,
  className,
  variant = 'default',
  size,
  padding,
  interactive = false,
  animate = true,
  entrance = false,
  onClick,
  ...props
}, ref) => {
  const { reducedMotion } = useAnimation();

  // Use interactive variant if onClick is provided
  const finalVariant = onClick || interactive ? 'interactive' : variant;
  
  // Use size for padding if padding is not explicitly set
  const finalPadding = padding || size;

  const handleClick = (e) => {
    if (onClick) {
      onClick(e);
    }
  };

  const MotionCard = reducedMotion ? 'div' : motion.div;

  const motionProps = reducedMotion ? {} : {
    ...(animate && {
      variants: cardAnimationVariants,
      initial: 'rest',
      whileHover: finalVariant === 'interactive' ? 'hover' : undefined,
      whileTap: finalVariant === 'interactive' ? 'tap' : undefined,
    }),
    ...(entrance && {
      variants: entranceVariants,
      initial: 'hidden',
      animate: 'visible',
    }),
  };

  return (
    <MotionCard
      ref={ref}
      className={clsx(
        cardVariants({ variant: finalVariant, padding: finalPadding }),
        className
      )}
      onClick={handleClick}
      {...motionProps}
      {...props}
    >
      {children}
    </MotionCard>
  );
});

Card.displayName = 'Card';

// Card Header component
export const CardHeader = forwardRef(({
  children,
  className,
  ...props
}, ref) => {
  return (
    <div
      ref={ref}
      className={clsx(
        'flex items-start justify-between',
        'pb-4 border-b border-gray-100',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

CardHeader.displayName = 'CardHeader';

// Card Title component
export const CardTitle = forwardRef(({
  children,
  className,
  as: Component = 'h3',
  ...props
}, ref) => {
  return (
    <Component
      ref={ref}
      className={clsx(
        'text-h3 font-semibold text-rna-charcoal',
        'leading-tight',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
});

CardTitle.displayName = 'CardTitle';

// Card Description component
export const CardDescription = forwardRef(({
  children,
  className,
  ...props
}, ref) => {
  return (
    <p
      ref={ref}
      className={clsx(
        'text-body text-rna-graphite',
        'leading-relaxed',
        className
      )}
      {...props}
    >
      {children}
    </p>
  );
});

CardDescription.displayName = 'CardDescription';

// Card Content component
export const CardContent = forwardRef(({
  children,
  className,
  ...props
}, ref) => {
  return (
    <div
      ref={ref}
      className={clsx('py-4', className)}
      {...props}
    >
      {children}
    </div>
  );
});

CardContent.displayName = 'CardContent';

// Card Footer component
export const CardFooter = forwardRef(({
  children,
  className,
  ...props
}, ref) => {
  return (
    <div
      ref={ref}
      className={clsx(
        'flex items-center justify-between',
        'pt-4 border-t border-gray-100',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});

CardFooter.displayName = 'CardFooter';

// Feature Card component for showcasing features
export const FeatureCard = forwardRef(({
  icon,
  title,
  description,
  className,
  interactive = true,
  ...props
}, ref) => {
  return (
    <Card
      ref={ref}
      variant={interactive ? 'interactive' : 'default'}
      className={clsx('text-center', className)}
      entrance={true}
      {...props}
    >
      {icon && (
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 text-rna-bright-teal">
            {icon}
          </div>
        </div>
      )}
      
      {title && (
        <CardTitle className="mb-2 text-center">
          {title}
        </CardTitle>
      )}
      
      {description && (
        <CardDescription className="text-center">
          {description}
        </CardDescription>
      )}
    </Card>
  );
});

FeatureCard.displayName = 'FeatureCard';

// Stat Card component for displaying metrics
export const StatCard = forwardRef(({
  label,
  value,
  change,
  changeType = 'neutral',
  icon,
  className,
  ...props
}, ref) => {
  const changeColors = {
    positive: 'text-rna-enzyme-green',
    negative: 'text-rna-error-red',
    neutral: 'text-rna-graphite',
  };

  return (
    <Card
      ref={ref}
      variant="elevated"
      className={clsx('relative', className)}
      entrance={true}
      {...props}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {label && (
            <p className="text-small text-rna-graphite font-medium mb-1">
              {label}
            </p>
          )}
          
          {value && (
            <p className="text-2xl font-bold text-rna-charcoal mb-1">
              {value}
            </p>
          )}
          
          {change && (
            <p className={clsx('text-small font-medium', changeColors[changeType])}>
              {change}
            </p>
          )}
        </div>
        
        {icon && (
          <div className="w-8 h-8 text-rna-bright-teal flex-shrink-0">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
});

StatCard.displayName = 'StatCard';

export default Card;