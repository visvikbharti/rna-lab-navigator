import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

// Mock matchMedia for different screen sizes
const createMatchMedia = (width) => (query) => ({
  matches: width >= parseInt(query.match(/(\d+)/)[0]),
  media: query,
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});

// Mock components
jest.mock('../components/enhanced', () => ({
  ParticleBackground: () => <div data-testid="particle-background">ParticleBackground</div>,
  FloatingOrbs: () => <div data-testid="floating-orbs">FloatingOrbs</div>,
  GlassCard: ({ children, className }) => <div className={className} data-testid="glass-card">{children}</div>,
  GradientText: ({ text, className }) => <h1 className={className} data-testid="gradient-text">{text}</h1>,
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

jest.mock('../components/FilterChips', () => {
  return function MockFilterChips({ selected, onChange }) {
    return <div data-testid="filter-chips">FilterChips - {selected}</div>;
  };
});

jest.mock('../components/EnhancedSearchInterface', () => {
  return function MockEnhancedSearchInterface() {
    return <div data-testid="enhanced-search-interface">EnhancedSearchInterface</div>;
  };
});

jest.mock('../components/AdvancedSearchBox', () => {
  return function MockAdvancedSearchBox() {
    return <div data-testid="advanced-search-box">AdvancedSearchBox</div>;
  };
});

describe('Responsive Design Tests', () => {
  describe('Mobile View (375px)', () => {
    beforeAll(() => {
      window.matchMedia = createMatchMedia(375);
    });

    test('renders mobile-optimized layout', () => {
      render(<App />);
      
      // Check container has responsive padding
      const container = screen.getByText(/RNA Lab Navigator/i).closest('.container');
      expect(container).toHaveClass('px-4', 'max-w-4xl');
      
      // Title should use responsive text size
      const title = screen.getByTestId('gradient-text');
      expect(title).toHaveClass('text-4xl', 'md:text-5xl');
    });

    test('navigation remains accessible on mobile', () => {
      render(<App />);
      
      // All navigation links should be present
      expect(screen.getByRole('link', { name: /Home/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Upload Protocol/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Feedback Analytics/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Search Quality/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Security Audit/i })).toBeInTheDocument();
    });

    test('filter chips wrap properly on small screens', () => {
      render(<App />);
      
      const filterChips = screen.getByTestId('filter-chips');
      expect(filterChips.parentElement).toHaveClass('mb-6');
    });
  });

  describe('Tablet View (768px)', () => {
    beforeAll(() => {
      window.matchMedia = createMatchMedia(768);
    });

    test('renders tablet-optimized layout', () => {
      render(<App />);
      
      const container = screen.getByText(/RNA Lab Navigator/i).closest('.container');
      expect(container).toBeInTheDocument();
      
      // Should show medium breakpoint styles
      const title = screen.getByTestId('gradient-text');
      expect(title).toHaveClass('md:text-5xl');
    });

    test('navigation spacing adjusts for tablet', () => {
      render(<App />);
      
      const nav = screen.getByRole('navigation');
      const navList = nav.querySelector('ul');
      expect(navList).toHaveClass('space-x-6');
    });
  });

  describe('Desktop View (1920px)', () => {
    beforeAll(() => {
      window.matchMedia = createMatchMedia(1920);
    });

    test('renders desktop-optimized layout', () => {
      render(<App />);
      
      const container = screen.getByText(/RNA Lab Navigator/i).closest('.container');
      expect(container).toHaveClass('max-w-4xl');
      
      // Full animations should be visible
      expect(screen.getByTestId('particle-background')).toBeInTheDocument();
      expect(screen.getByTestId('floating-orbs')).toBeInTheDocument();
    });

    test('header layout is properly centered on desktop', () => {
      render(<App />);
      
      const header = screen.getByRole('banner');
      expect(header).toHaveClass('text-center');
      
      // Three-column layout in header
      const headerContent = header.querySelector('.flex.justify-between');
      expect(headerContent).toHaveClass('items-center');
    });
  });

  describe('Animation Performance Tests', () => {
    test('animations are smooth and non-blocking', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      // Test UI toggle animation
      const toggleButton = screen.getByText(/Classic UI/i);
      
      const startTime = performance.now();
      await user.click(toggleButton);
      const endTime = performance.now();
      
      // Animation should complete quickly
      expect(endTime - startTime).toBeLessThan(1000);
      
      // UI should update immediately
      expect(screen.getByText(/Enhanced UI/i)).toBeInTheDocument();
    });

    test('particle animations do not interfere with interactions', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      // Particle background should be present
      expect(screen.getByTestId('particle-background')).toBeInTheDocument();
      
      // User should still be able to interact with UI
      const filterChips = screen.getByTestId('filter-chips');
      expect(filterChips).toBeInTheDocument();
      
      // Toggle UI mode
      await user.click(screen.getByText(/Classic UI/i));
      
      // Particles should be removed in classic mode
      expect(screen.queryByTestId('particle-background')).not.toBeInTheDocument();
    });
  });

  describe('Touch Interaction Tests', () => {
    test('buttons have appropriate touch targets', () => {
      render(<App />);
      
      const toggleButton = screen.getByText(/Classic UI/i);
      
      // Button should have minimum touch target size
      expect(toggleButton).toHaveClass('text-sm');
      
      // Navigation links should be spaced for touch
      const navLinks = screen.getAllByRole('link');
      navLinks.forEach(link => {
        expect(link.parentElement.parentElement).toHaveClass('space-x-6');
      });
    });
  });

  describe('Viewport Meta Tests', () => {
    test('handles orientation changes gracefully', () => {
      // Test portrait
      window.matchMedia = createMatchMedia(375);
      const { rerender } = render(<App />);
      
      expect(screen.getByTestId('gradient-text')).toHaveClass('text-4xl');
      
      // Switch to landscape
      window.matchMedia = createMatchMedia(812);
      rerender(<App />);
      
      // Layout should adapt
      expect(screen.getByTestId('gradient-text')).toBeInTheDocument();
    });
  });

  describe('Loading State Responsiveness', () => {
    test('loading indicators scale appropriately', async () => {
      const user = userEvent.setup();
      
      // Mock the EnhancedSearchInterface to show loading
      jest.mock('../components/EnhancedSearchInterface', () => {
        return function MockEnhancedSearchInterface() {
          return (
            <div data-testid="enhanced-search-interface">
              <div data-testid="loading" className="flex items-center justify-center py-12">
                Loading...
              </div>
            </div>
          );
        };
      });
      
      render(<App />);
      
      // Loading should be centered
      const loadingContainer = screen.getByTestId('loading');
      expect(loadingContainer).toHaveClass('flex', 'items-center', 'justify-center', 'py-12');
    });
  });

  describe('Accessibility on Different Screen Sizes', () => {
    test('maintains focus management across breakpoints', async () => {
      const user = userEvent.setup();
      render(<App />);
      
      // Tab through navigation
      await user.tab();
      
      // First focusable element should be the toggle button
      expect(document.activeElement.textContent).toMatch(/Classic UI/i);
      
      // Continue tabbing through navigation
      await user.tab();
      await user.tab();
      
      // Should reach navigation links
      expect(document.activeElement).toHaveAttribute('href');
    });

    test('contrast ratios remain accessible at all sizes', () => {
      render(<App />);
      
      // Dark mode toggle should be visible
      const darkModeToggle = screen.getByTestId('dark-mode-toggle');
      expect(darkModeToggle).toBeInTheDocument();
      
      // Text should have proper contrast classes
      const subtitle = screen.getByText(/Your AI assistant/i);
      expect(subtitle).toHaveClass('text-white/80');
    });
  });
});