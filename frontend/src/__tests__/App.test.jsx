import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

// Mock components to isolate App testing
jest.mock('../components/ChatBox', () => {
  return function MockChatBox() {
    return <div data-testid="chat-box">ChatBox Component</div>;
  };
});

jest.mock('../components/EnhancedChatBox', () => {
  return function MockEnhancedChatBox() {
    return <div data-testid="enhanced-chat-box">EnhancedChatBox Component</div>;
  };
});

jest.mock('../components/AdvancedSearchBox', () => {
  return function MockAdvancedSearchBox({ docType }) {
    return <div data-testid="advanced-search-box">AdvancedSearchBox Component - DocType: {docType}</div>;
  };
});

jest.mock('../components/EnhancedSearchInterface', () => {
  return function MockEnhancedSearchInterface({ docType }) {
    return <div data-testid="enhanced-search-interface">EnhancedSearchInterface Component - DocType: {docType}</div>;
  };
});

jest.mock('../components/FilterChips', () => {
  return function MockFilterChips({ selected, onChange }) {
    return (
      <div data-testid="filter-chips">
        FilterChips Component - Selected: {selected}
        <button onClick={() => onChange('papers')}>Papers</button>
        <button onClick={() => onChange('protocols')}>Protocols</button>
      </div>
    );
  };
});

jest.mock('../components/enhanced', () => ({
  ParticleBackground: () => <div data-testid="particle-background">ParticleBackground</div>,
  FloatingOrbs: () => <div data-testid="floating-orbs">FloatingOrbs</div>,
  GlassCard: ({ children, className }) => <div className={className} data-testid="glass-card">{children}</div>,
  GradientText: ({ text }) => <h1 data-testid="gradient-text">{text}</h1>,
  Navigation: () => <nav data-testid="navigation">Navigation</nav>,
}));

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test('renders main app with title and navigation', () => {
    render(<App />);
    
    expect(screen.getByText(/RNA Lab Navigator/i)).toBeInTheDocument();
    expect(screen.getByText(/Your AI assistant for lab protocols, papers, and theses/i)).toBeInTheDocument();
    
    // Check navigation links
    expect(screen.getByRole('link', { name: /Home/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Upload Protocol/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Feedback Analytics/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Search Quality/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Security Audit/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Component Demo/i })).toBeInTheDocument();
  });

  test('toggles between enhanced and classic UI', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Initially shows enhanced UI
    expect(screen.getByTestId('particle-background')).toBeInTheDocument();
    expect(screen.getByTestId('floating-orbs')).toBeInTheDocument();
    expect(screen.getByTestId('enhanced-search-interface')).toBeInTheDocument();
    
    // Click toggle button
    const toggleButton = screen.getByText(/Classic UI/i);
    await user.click(toggleButton);
    
    // Should switch to classic UI
    expect(screen.queryByTestId('particle-background')).not.toBeInTheDocument();
    expect(screen.queryByTestId('floating-orbs')).not.toBeInTheDocument();
    expect(screen.getByTestId('advanced-search-box')).toBeInTheDocument();
    expect(screen.getByText(/Enhanced UI/i)).toBeInTheDocument();
  });

  test('updates docType when filter chips are clicked', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Initially shows 'all' docType
    expect(screen.getByText(/DocType: all/i)).toBeInTheDocument();
    
    // Click Papers filter
    const papersButton = screen.getByRole('button', { name: /Papers/i });
    await user.click(papersButton);
    
    // Should update docType
    expect(screen.getByText(/DocType: papers/i)).toBeInTheDocument();
  });

  test('navigates to different pages', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Navigate to Upload page
    const uploadLink = screen.getByRole('link', { name: /Upload Protocol/i });
    await user.click(uploadLink);
    
    await waitFor(() => {
      expect(window.location.pathname).toBe('/upload');
    });
  });

  test('renders footer with copyright information', () => {
    render(<App />);
    
    expect(screen.getByText(/© 2025 Dr. Debojyoti Chakraborty's RNA Biology Lab/i)).toBeInTheDocument();
  });

  test('applies dark mode styles when toggled', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const darkModeToggle = screen.getByTestId('dark-mode-toggle');
    await user.click(darkModeToggle);
    
    // Check if dark mode class is applied
    await waitFor(() => {
      const appContainer = screen.getByRole('main').closest('div');
      expect(appContainer).toHaveClass('dark:bg-gray-900');
    });
  });

  test('shows showcase link in enhanced UI mode', () => {
    render(<App />);
    
    const showcaseLink = screen.getByText(/View Colossal Showcase/i);
    expect(showcaseLink).toBeInTheDocument();
    expect(showcaseLink).toHaveAttribute('href', '/showcase');
  });

  test('maintains UI state across component re-renders', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<App />);
    
    // Switch to classic UI
    await user.click(screen.getByText(/Classic UI/i));
    expect(screen.getByTestId('advanced-search-box')).toBeInTheDocument();
    
    // Re-render component
    rerender(<App />);
    
    // Should still show classic UI
    expect(screen.getByTestId('advanced-search-box')).toBeInTheDocument();
  });

  test('renders animations with proper initial states', () => {
    render(<App />);
    
    // Check for motion elements
    const header = screen.getByRole('banner');
    const main = screen.getByRole('main');
    
    expect(header).toBeInTheDocument();
    expect(main).toBeInTheDocument();
  });

  test('handles errors gracefully', async () => {
    // Mock console.error to avoid noise in tests
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    // Force an error by passing invalid props
    render(<App invalidProp="test" />);
    
    // App should still render
    expect(screen.getByText(/RNA Lab Navigator/i)).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });
});