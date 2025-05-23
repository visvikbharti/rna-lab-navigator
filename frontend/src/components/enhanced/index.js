/**
 * Enhanced Components - RNA Lab Navigator
 * Colossal.com-inspired component library
 * Phase 1: Foundation Setup
 */

// Button components
export { default as Button, ButtonGroup, IconButton, FloatingActionButton } from './Button';

// Card components  
export { 
  default as Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter,
  FeatureCard,
  StatCard 
} from './Card';

// Input components
export { 
  default as Input, 
  Textarea, 
  SearchInput, 
  FormGroup, 
  InputGroup 
} from './Input';

// Loading components
export { 
  default as Loading,
  Spinner,
  RNAHelixSpinner,
  PulseLoader,
  DotsLoader,
  ProgressLoader,
  LoadingOverlay,
  Skeleton
} from './Loading';

// Re-export animation context and hooks
export { 
  AnimationProvider, 
  useAnimation, 
  useAnimationVariants, 
  useAnimationTransition,
  withAnimation 
} from '../../contexts/AnimationContext';

// Export new Colossal-inspired components
export { default as ParticleBackground } from './ParticleBackground';
export { default as GlassCard } from './GlassCard';
export { default as SectionHeader } from './SectionHeader';
export { default as ColossalButton } from './ColossalButton';
export { default as GradientText } from './GradientText';
export { default as Navigation } from './Navigation';
export { default as FloatingOrbs } from './FloatingOrbs';
export { default as ScrollProgress } from './ScrollProgress';
export { default as ScrollDotNavigation } from './ScrollDotNavigation';