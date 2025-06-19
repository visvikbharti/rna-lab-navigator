# Animation Audit Report

## CSS Files with Animations

### 1. `/src/styles/animations.css`
- **float animation**: Elements move up/down by 5px over 10s
- **gradient-shift**: Background position shifts for gradient animations (15s)
- **glow-pulse**: Box shadow pulsing effect (4s)
- **dna-rotate**: Full 360-degree rotation (20s)
- **shimmer**: Moving shimmer effect across elements (4s)
- **Classes**: `.float-animation`, `.gradient-animate`, `.glow-pulse`, `.dna-rotate`, `.shimmer`, `.holographic`

### 2. `/src/styles/particle-animations.css`
- **particle-float-1, -2, -3**: Particles floating up with various transforms
- **dna-twist**: 360-degree Y-axis rotation (4s)
- **dust-dissolve**: Particles dissolving with blur effect (3s)
- **burst-out**: Burst animation for particles (1s)
- **orbit-rotate**: Continuous 360-degree rotation (20s)
- **wave-motion**: Wave-like movement pattern (4s)
- **trail-move**: Trail effect moving across screen (2s)
- **quantum-phase**: Scale and opacity changes (3s)

### 3. `/src/styles/ripple-animation.css`
- **ripple**: Expanding ripple effect (500px expansion)
- **card-hover-glow**: Box shadow animation on hover
- **text-reveal**: Text appearing with rotation effect
- **gradient-border**: Animated gradient borders (3s)
- **morph**: Shape morphing animation (8s)
- **glitch**: Glitch effect with transform and hue rotation (0.3s)
- **neon-glow**: Pulsing neon text effect (1.5s)
- **card-flip**: 3D card flip on hover (0.6s)
- **wave**: Wave animation across elements (2s)

### 4. `/src/styles/colossal-components.css`
- **cosmic-shift**: Background position animation (similar to gradient-shift)
- **float**: Elements moving in circular pattern (20s)
- Floating orbs with blur effects

### 5. `/src/styles/components.css`
- **hover:-translate-y-0.5**: Buttons move up slightly on hover
- **hover:scale-110**: Elements scale up 10% on hover
- **hover:-translate-y-1**: Cards move up on hover
- **hover:scale-105**: Badges scale up 5% on hover

### 6. `/src/index.css`
- **bounce-gentle**: Gentle bounce animation (3s)
- **hover:-translate-y-1**: Elements move up on hover
- **hover:shadow-xl**: Shadow increases on hover

### 7. `/src/styles/design-system.css`
- **bounce-gentle**: 4px vertical movement (2s)
- `.animate-bounce-gentle` class

## JSX Components with Animations

### 1. `/src/components/enhanced/FloatingOrbs.jsx`
- Uses `float` animation with random durations (15-25s)
- Multiple orbs with blur effects

## Animation Summary

### Most Problematic Animations (Excessive Movement):
1. **Float animations** - Continuous up/down movement
2. **Particle animations** - Multiple floating particles
3. **Wave motions** - Continuous wave effects
4. **Orbit rotations** - Constant 360-degree rotations
5. **Morph animations** - Shape changing effects
6. **Bounce animations** - Repetitive bouncing
7. **Glitch effects** - Jarring movements

### Hover Effects (Less Problematic):
- Small translations on hover (-0.5px to -1px)
- Slight scale increases (105% to 110%)
- Shadow changes

## Recommendations

To reduce excessive movement, disable or modify these animations:
1. All particle animations in `particle-animations.css`
2. Float animations in `animations.css` and `colossal-components.css`
3. Continuous animations like wave, orbit, morph
4. Reduce or remove bounce animations
5. Consider keeping only subtle hover effects

The animations are spread across multiple CSS files and some inline styles in JSX components, making them a significant contributor to the "wiggling" UI issue.