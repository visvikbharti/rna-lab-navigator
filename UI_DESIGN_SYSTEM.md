# UI Design System - RNA Lab Intelligence Platform

## 🎨 Visual Philosophy

> "Scientific precision meets artistic expression - where every pixel serves both beauty and function"

## Color System

### Primary Palette (Colossal-Inspired)
```css
:root {
  /* Core Colors */
  --cosmic-purple: #6B46C1;
  --electric-blue: #3B82F6;
  --neon-pink: #EC4899;
  --deep-black: #0A0A0A;
  
  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #6B46C1 0%, #3B82F6 100%);
  --gradient-accent: linear-gradient(135deg, #EC4899 0%, #F59E0B 100%);
  --gradient-dark: linear-gradient(180deg, #0A0A0A 0%, #1A1A2E 100%);
  
  /* Glass Effects */
  --glass-white: rgba(255, 255, 255, 0.1);
  --glass-border: rgba(255, 255, 255, 0.2);
  --glass-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}
```

### Semantic Colors
```css
/* Status Colors */
--success: #10B981;
--warning: #F59E0B;
--error: #EF4444;
--info: #3B82F6;

/* Model Indicators */
--gpt4-color: #6B46C1;
--o3-color: #3B82F6;
--rag-color: #10B981;
```

## Typography System

### Font Stack
```css
/* Headings - Futuristic */
font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;

/* Body - Clean & Readable */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* Code/Technical */
font-family: 'JetBrains Mono', 'Fira Code', monospace;
```

### Type Scale
```css
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */
--text-5xl: 3rem;       /* 48px */
```

## Animation Principles

### Core Animations
```javascript
// Smooth Transitions
export const smoothTransition = {
  type: "spring",
  stiffness: 100,
  damping: 15
}

// Stagger Children
export const staggerContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

// Floating Effect
export const floatingAnimation = {
  y: [0, -10, 0],
  transition: {
    duration: 3,
    repeat: Infinity,
    ease: "easeInOut"
  }
}
```

### Interaction States
```css
/* Hover Effects */
.interactive-element {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.interactive-element:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px rgba(107, 70, 193, 0.3);
}

/* Active/Click */
.interactive-element:active {
  transform: scale(0.98);
}
```

## Component Patterns

### Glass Morphism Card
```jsx
const GlassCard = styled.div`
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
`;
```

### Neon Glow Button
```jsx
const NeonButton = styled(motion.button)`
  background: linear-gradient(135deg, #6B46C1 0%, #3B82F6 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }
  
  &:hover::before {
    left: 100%;
  }
  
  &:hover {
    box-shadow: 0 0 20px rgba(107, 70, 193, 0.6),
                0 0 40px rgba(107, 70, 193, 0.4);
  }
`;
```

### Animated Background
```jsx
const AnimatedBackground = () => (
  <div className="fixed inset-0 -z-10">
    {/* Gradient Orbs */}
    <div className="absolute top-20 left-20 w-72 h-72 bg-purple-600 rounded-full filter blur-3xl opacity-20 animate-pulse" />
    <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-600 rounded-full filter blur-3xl opacity-20 animate-pulse animation-delay-2000" />
    
    {/* Particle Field */}
    <ParticleField />
    
    {/* Grid Pattern */}
    <div className="absolute inset-0 bg-grid-pattern opacity-5" />
  </div>
);
```

## Layout System

### Spacing Scale
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
```

### Container Widths
```css
--max-width-xs: 20rem;    /* 320px */
--max-width-sm: 24rem;    /* 384px */
--max-width-md: 28rem;    /* 448px */
--max-width-lg: 32rem;    /* 512px */
--max-width-xl: 36rem;    /* 576px */
--max-width-2xl: 42rem;   /* 672px */
--max-width-3xl: 48rem;   /* 768px */
--max-width-4xl: 56rem;   /* 896px */
--max-width-5xl: 64rem;   /* 1024px */
--max-width-6xl: 72rem;   /* 1152px */
--max-width-7xl: 80rem;   /* 1280px */
```

## Special Effects

### DNA Helix Animation
```jsx
const DNAHelix = () => {
  return (
    <Canvas>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <Helix>
        <meshStandardMaterial
          color="#6B46C1"
          emissive="#6B46C1"
          emissiveIntensity={0.5}
        />
      </Helix>
    </Canvas>
  );
};
```

### Typing Effect
```jsx
const TypewriterText = ({ text, delay = 50 }) => {
  const [displayText, setDisplayText] = useState('');
  
  useEffect(() => {
    let index = 0;
    const timer = setInterval(() => {
      if (index < text.length) {
        setDisplayText(prev => prev + text[index]);
        index++;
      } else {
        clearInterval(timer);
      }
    }, delay);
    
    return () => clearInterval(timer);
  }, [text, delay]);
  
  return <span>{displayText}<span className="animate-blink">|</span></span>;
};
```

### Loading States
```jsx
const QuantumLoader = () => (
  <div className="flex space-x-2">
    {[0, 1, 2].map(i => (
      <motion.div
        key={i}
        className="w-3 h-3 bg-purple-600 rounded-full"
        animate={{
          scale: [1, 1.5, 1],
          opacity: [1, 0.5, 1],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          delay: i * 0.2,
        }}
      />
    ))}
  </div>
);
```

## Responsive Design

### Breakpoints
```css
--screen-sm: 640px;
--screen-md: 768px;
--screen-lg: 1024px;
--screen-xl: 1280px;
--screen-2xl: 1536px;
```

### Mobile Adaptations
```css
/* Touch-friendly targets */
@media (max-width: 768px) {
  .touch-target {
    min-height: 44px;
    min-width: 44px;
  }
  
  /* Simplified animations on mobile */
  .complex-animation {
    animation: none;
    transition: opacity 0.2s;
  }
}
```

## Accessibility

### Focus States
```css
.focusable:focus-visible {
  outline: 2px solid #6B46C1;
  outline-offset: 2px;
  border-radius: 4px;
}
```

### Color Contrast
- Text on dark: #FFFFFF (AAA compliant)
- Text on glass: #FFFFFF with backdrop-filter
- Interactive elements: Minimum 4.5:1 contrast ratio

## Implementation Checklist

- [ ] Install required fonts (Space Grotesk, Inter, JetBrains Mono)
- [ ] Set up Tailwind config with custom colors
- [ ] Create reusable component library
- [ ] Implement animation utilities
- [ ] Add sound effects library
- [ ] Create loading state components
- [ ] Build responsive grid system
- [ ] Test across devices and browsers

## Screenshots & Inspiration
*[Awaiting screenshots - to be added here]*

---

This design system creates a cohesive, futuristic interface that makes researchers feel like they're using cutting-edge technology from the future. Every interaction should feel smooth, every transition should delight, and every component should inspire confidence in the platform's capabilities. 🚀