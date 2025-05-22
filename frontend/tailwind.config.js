/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Custom color palette inspired by RNA structure and colossal.com
      colors: {
        rna: {
          // Primary RNA-inspired colors
          'deep-teal': '#0d4650',
          'bright-teal': '#2dd4bf',
          'aqua': '#67e8f9',
          'seafoam': '#a7f3d0',
          
          // Neutral foundation
          'charcoal': '#1f2937',
          'graphite': '#64748b',
          'silver': '#94a3b8',
          'platinum': '#f8fafc',
          'pearl': '#f1f5f9',
          'white': '#ffffff',
          
          // Semantic colors
          'helix-blue': '#3b82f6',
          'enzyme-green': '#10b981',
          'warning-amber': '#f59e0b',
          'error-red': '#ef4444',
          'info-indigo': '#6366f1',
        },
        
        // Legacy primary colors (for backward compatibility)
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
      },
      
      // Typography system
      fontFamily: {
        'primary': ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'],
        'mono': ['SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'monospace'],
      },
      
      fontSize: {
        'hero': ['3.5rem', { lineHeight: '1.1', fontWeight: '700' }],
        'h1': ['2.25rem', { lineHeight: '1.2', fontWeight: '600' }],
        'h2': ['1.875rem', { lineHeight: '1.3', fontWeight: '600' }],
        'h3': ['1.5rem', { lineHeight: '1.4', fontWeight: '600' }],
        'h4': ['1.25rem', { lineHeight: '1.5', fontWeight: '500' }],
        'body': ['1rem', { lineHeight: '1.5', fontWeight: '400' }],
        'small': ['0.875rem', { lineHeight: '1.6', fontWeight: '400' }],
        'micro': ['0.75rem', { lineHeight: '1.5', fontWeight: '400' }],
      },
      
      // Enhanced spacing scale
      spacing: {
        '18': '4.5rem',   // 72px
        '88': '22rem',    // 352px
        '128': '32rem',   // 512px
      },
      
      // Enhanced border radius
      borderRadius: {
        'xl': '1rem',     // 16px
        '2xl': '1.5rem',  // 24px
        '3xl': '2rem',    // 32px
      },
      
      // Enhanced shadows with colored variants
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'teal': '0 10px 25px -5px rgba(45, 212, 191, 0.3)',
        'blue': '0 10px 25px -5px rgba(59, 130, 246, 0.3)',
        'green': '0 10px 25px -5px rgba(16, 185, 129, 0.3)',
        'glow': '0 0 20px rgba(45, 212, 191, 0.4)',
        'glow-lg': '0 0 40px rgba(45, 212, 191, 0.3)',
      },
      
      // Background gradients
      backgroundImage: {
        'gradient-hero': 'linear-gradient(135deg, #0d4650 0%, #2dd4bf 100%)',
        'gradient-card': 'linear-gradient(145deg, #ffffff 0%, #f1f5f9 100%)',
        'gradient-interactive': 'linear-gradient(135deg, #3b82f6 0%, #2dd4bf 100%)',
        'gradient-success': 'linear-gradient(135deg, #10b981 0%, #a7f3d0 100%)',
        'gradient-subtle': 'linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)',
        'gradient-depth': 'linear-gradient(145deg, #ffffff 0%, #f8fafc 100%)',
        'gradient-glass': 'linear-gradient(145deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.8) 100%)',
      },
      
      // Animation and transitions
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
        'back-out': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        'back-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'spring': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      },
      
      transitionDuration: {
        '250': '250ms',
        '400': '400ms',
        '600': '600ms',
        '750': '750ms',
      },
      
      // Container sizes
      maxWidth: {
        'container': '1200px',
        'container-lg': '1400px',
      },
      
      // Z-index scale
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
      
      // Animation keyframes
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in-down': {
          '0%': { opacity: '0', transform: 'translateY(-20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'slide-in-left': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'bounce-gentle': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'shimmer': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(45, 212, 191, 0.5)' },
          '50%': { boxShadow: '0 0 20px rgba(45, 212, 191, 0.8)' },
        },
        'rna-helix': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      
      animation: {
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-in-up': 'fade-in-up 0.4s ease-out',
        'fade-in-down': 'fade-in-down 0.4s ease-out',
        'slide-in-right': 'slide-in-right 0.3s ease-out',
        'slide-in-left': 'slide-in-left 0.3s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'bounce-gentle': 'bounce-gentle 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'rna-helix': 'rna-helix 3s linear infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
    },
  },
  plugins: [
    // Plugin for focus-visible support
    function({ addUtilities, theme }) {
      const focusUtilities = {
        '.focus-ring': {
          '&:focus-visible': {
            outline: 'none',
            boxShadow: `0 0 0 3px ${theme('colors.rna.bright-teal')}40`,
          },
        },
        '.focus-ring-blue': {
          '&:focus-visible': {
            outline: 'none',
            boxShadow: `0 0 0 3px ${theme('colors.rna.helix-blue')}40`,
          },
        },
      };
      addUtilities(focusUtilities);
    },
    
    // Plugin for reduced motion support
    function({ addUtilities }) {
      addUtilities({
        '@media (prefers-reduced-motion: reduce)': {
          '.motion-safe-only': {
            animation: 'none !important',
            transition: 'none !important',
          },
        },
      });
    },
    
    // Plugin for component variants
    function({ addComponents, theme }) {
      addComponents({
        '.btn-primary': {
          backgroundColor: theme('colors.rna.bright-teal'),
          color: theme('colors.white'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.lg'),
          fontWeight: theme('fontWeight.medium'),
          transition: 'all 0.15s ease-out',
          border: 'none',
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: theme('colors.rna.deep-teal'),
            transform: 'translateY(-1px)',
            boxShadow: theme('boxShadow.teal'),
          },
          '&:focus': {
            outline: 'none',
            boxShadow: `0 0 0 3px ${theme('colors.rna.bright-teal')}40`,
          },
          '&:disabled': {
            backgroundColor: theme('colors.rna.silver'),
            cursor: 'not-allowed',
            transform: 'none',
            boxShadow: 'none',
          },
        },
        
        '.btn-secondary': {
          backgroundColor: theme('colors.white'),
          color: theme('colors.rna.deep-teal'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.lg'),
          fontWeight: theme('fontWeight.medium'),
          transition: 'all 0.15s ease-out',
          border: `1px solid ${theme('colors.rna.bright-teal')}`,
          cursor: 'pointer',
          '&:hover': {
            backgroundColor: theme('colors.rna.bright-teal'),
            color: theme('colors.white'),
            transform: 'translateY(-1px)',
            boxShadow: theme('boxShadow.teal'),
          },
        },
        
        '.card-interactive': {
          backgroundColor: theme('colors.white'),
          borderRadius: theme('borderRadius.xl'),
          padding: theme('spacing.6'),
          boxShadow: theme('boxShadow.md'),
          transition: 'all 0.2s ease-out',
          cursor: 'pointer',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: theme('boxShadow.xl'),
          },
        },
        
        '.input-primary': {
          width: '100%',
          padding: `${theme('spacing.3')} ${theme('spacing.4')}`,
          borderRadius: theme('borderRadius.lg'),
          border: `1px solid ${theme('colors.gray.300')}`,
          fontSize: theme('fontSize.base'),
          transition: 'all 0.15s ease-out',
          '&:focus': {
            outline: 'none',
            borderColor: theme('colors.rna.bright-teal'),
            boxShadow: `0 0 0 3px ${theme('colors.rna.bright-teal')}20`,
          },
        },
      });
    },
  ],
}