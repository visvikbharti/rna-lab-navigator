/**
 * Enhanced Input Component - RNA Lab Navigator
 * Colossal.com-inspired form inputs with animations
 * Phase 1: Foundation Setup
 */

import React, { forwardRef, useState } from 'react';
import { motion } from 'framer-motion';
import { cva } from 'class-variance-authority';
import { clsx } from 'clsx';
import { EyeIcon, EyeSlashIcon, ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { useAnimation } from '../../contexts/AnimationContext';

// Input variant styles using CVA
const inputVariants = cva(
  // Base styles
  [
    'w-full font-primary transition-all duration-200 ease-smooth',
    'border border-gray-300 bg-white',
    'focus:outline-none focus:ring-3 focus:ring-rna-bright-teal/20',
    'focus:border-rna-bright-teal',
    'placeholder:text-rna-silver',
    'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
  ],
  {
    variants: {
      size: {
        sm: 'px-3 py-2 text-sm rounded-md',
        md: 'px-4 py-3 text-base rounded-lg',
        lg: 'px-5 py-4 text-lg rounded-lg',
      },
      variant: {
        default: '',
        search: [
          'bg-rna-pearl/50 border-transparent',
          'focus:bg-white focus:border-rna-bright-teal',
          'pl-12',
        ],
        ghost: [
          'bg-transparent border-transparent',
          'focus:bg-white focus:border-rna-bright-teal',
        ],
      },
      state: {
        default: '',
        error: [
          'border-rna-error-red',
          'focus:border-rna-error-red',
          'focus:ring-rna-error-red/20',
        ],
        success: [
          'border-rna-enzyme-green',
          'focus:border-rna-enzyme-green',
          'focus:ring-rna-enzyme-green/20',
        ],
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
      state: 'default',
    },
  }
);

// Label animation variants
const labelVariants = {
  default: {
    y: 0,
    scale: 1,
    color: '#64748b',
    transition: { duration: 0.2 }
  },
  focused: {
    y: -24,
    scale: 0.85,
    color: '#2dd4bf',
    transition: { duration: 0.2 }
  },
  filled: {
    y: -24,
    scale: 0.85,
    color: '#64748b',
    transition: { duration: 0.2 }
  },
};

/**
 * Enhanced Input Component
 */
const Input = forwardRef(({
  className,
  type = 'text',
  size = 'md',
  variant = 'default',
  state = 'default',
  label,
  placeholder,
  helperText,
  errorMessage,
  successMessage,
  leftIcon,
  rightIcon,
  disabled = false,
  required = false,
  floating = false,
  value,
  onChange,
  onFocus,
  onBlur,
  ...props
}, ref) => {
  const { reducedMotion } = useAnimation();
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const isPasswordType = type === 'password';
  const inputType = isPasswordType && showPassword ? 'text' : type;
  const hasValue = value && value.toString().length > 0;
  const hasError = state === 'error' || errorMessage;
  const hasSuccess = state === 'success' || successMessage;

  // Determine final state
  const finalState = hasError ? 'error' : hasSuccess ? 'success' : 'default';

  const handleFocus = (e) => {
    setFocused(true);
    onFocus?.(e);
  };

  const handleBlur = (e) => {
    setFocused(false);
    onBlur?.(e);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  // Label animation state
  const labelState = focused ? 'focused' : hasValue ? 'filled' : 'default';

  const MotionLabel = reducedMotion ? 'label' : motion.label;

  return (
    <div className="relative w-full">
      {/* Floating label */}
      {floating && label && (
        <MotionLabel
          className={clsx(
            'absolute left-4 pointer-events-none',
            'font-medium origin-left z-10',
            size === 'sm' && 'top-2 text-sm',
            size === 'md' && 'top-3 text-base',
            size === 'lg' && 'top-4 text-lg',
          )}
          variants={reducedMotion ? {} : labelVariants}
          animate={reducedMotion ? {} : labelState}
        >
          {label}
          {required && <span className="text-rna-error-red ml-1">*</span>}
        </MotionLabel>
      )}

      {/* Static label */}
      {!floating && label && (
        <label className="block text-sm font-medium text-rna-charcoal mb-2">
          {label}
          {required && <span className="text-rna-error-red ml-1">*</span>}
        </label>
      )}

      {/* Input container */}
      <div className="relative">
        {/* Left icon */}
        {leftIcon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-rna-silver pointer-events-none">
            {leftIcon}
          </div>
        )}

        {/* Input field */}
        <input
          ref={ref}
          type={inputType}
          className={clsx(
            inputVariants({ size, variant, state: finalState }),
            leftIcon && 'pl-10',
            (rightIcon || isPasswordType) && 'pr-10',
            floating && 'placeholder-transparent',
            className
          )}
          placeholder={floating ? ' ' : placeholder}
          disabled={disabled}
          required={required}
          value={value}
          onChange={onChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          {...props}
        />

        {/* Right icon or password toggle */}
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-2">
          {/* State icons */}
          {hasError && (
            <ExclamationCircleIcon className="w-5 h-5 text-rna-error-red" />
          )}
          {hasSuccess && (
            <CheckCircleIcon className="w-5 h-5 text-rna-enzyme-green" />
          )}

          {/* Password toggle */}
          {isPasswordType && (
            <button
              type="button"
              onClick={togglePasswordVisibility}
              className="p-1 text-rna-graphite hover:text-rna-deep-teal transition-colors duration-150"
              tabIndex={-1}
            >
              {showPassword ? (
                <EyeSlashIcon className="w-4 h-4" />
              ) : (
                <EyeIcon className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Custom right icon */}
          {rightIcon && !hasError && !hasSuccess && (
            <div className="text-rna-silver">
              {rightIcon}
            </div>
          )}
        </div>
      </div>

      {/* Helper text, error message, or success message */}
      {(helperText || errorMessage || successMessage) && (
        <div className="mt-2 flex items-center gap-1">
          {errorMessage && (
            <>
              <ExclamationCircleIcon className="w-4 h-4 text-rna-error-red flex-shrink-0" />
              <p className="text-sm text-rna-error-red">{errorMessage}</p>
            </>
          )}
          
          {successMessage && !errorMessage && (
            <>
              <CheckCircleIcon className="w-4 h-4 text-rna-enzyme-green flex-shrink-0" />
              <p className="text-sm text-rna-enzyme-green">{successMessage}</p>
            </>
          )}
          
          {helperText && !errorMessage && !successMessage && (
            <p className="text-sm text-rna-graphite">{helperText}</p>
          )}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

// Textarea component
export const Textarea = forwardRef(({
  className,
  rows = 4,
  resize = 'vertical',
  ...props
}, ref) => {
  return (
    <Input
      ref={ref}
      as="textarea"
      rows={rows}
      className={clsx(
        'min-h-[120px]',
        resize === 'none' && 'resize-none',
        resize === 'vertical' && 'resize-y',
        resize === 'horizontal' && 'resize-x',
        resize === 'both' && 'resize',
        className
      )}
      {...props}
    />
  );
});

Textarea.displayName = 'Textarea';

// Search input component
export const SearchInput = forwardRef(({
  onSearch,
  onClear,
  className,
  placeholder = 'Search...',
  ...props
}, ref) => {
  return (
    <Input
      ref={ref}
      type="search"
      variant="search"
      placeholder={placeholder}
      leftIcon={
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      }
      className={className}
      {...props}
    />
  );
});

SearchInput.displayName = 'SearchInput';

// Form group component
export const FormGroup = ({ children, className, ...props }) => {
  return (
    <div className={clsx('space-y-2', className)} {...props}>
      {children}
    </div>
  );
};

// Input group component for multiple related inputs
export const InputGroup = ({ children, className, ...props }) => {
  return (
    <div 
      className={clsx(
        'flex',
        '[&>*:not(:first-child)]:ml-px [&>*:not(:first-child)]:rounded-l-none',
        '[&>*:not(:last-child)]:rounded-r-none',
        className
      )} 
      {...props}
    >
      {children}
    </div>
  );
};

export default Input;