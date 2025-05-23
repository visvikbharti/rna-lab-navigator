import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EnhancedSearchInterface from '../components/EnhancedSearchInterface';

// Mock child components
jest.mock('../components/AdvancedSearchBox', () => {
  return function MockAdvancedSearchBox({ docType }) {
    return <div data-testid="advanced-search-box">AdvancedSearchBox - DocType: {docType}</div>;
  };
});

jest.mock('../components/HypothesisExplorer', () => {
  return function MockHypothesisExplorer() {
    return <div data-testid="hypothesis-explorer">HypothesisExplorer Component</div>;
  };
});

jest.mock('../components/ProtocolBuilder', () => {
  return function MockProtocolBuilder() {
    return <div data-testid="protocol-builder">ProtocolBuilder Component</div>;
  };
});

jest.mock('../components/enhanced', () => ({
  GlassCard: ({ children, className, onClick }) => (
    <div className={className} onClick={onClick} data-testid="glass-card">
      {children}
    </div>
  ),
  ColossalButton: ({ children, onClick }) => (
    <button onClick={onClick} data-testid="colossal-button">
      {children}
    </button>
  ),
  GradientText: ({ text }) => <span data-testid="gradient-text">{text}</span>,
  Loading: ({ type }) => <div data-testid="loading" data-type={type}>Loading...</div>,
}));

describe('EnhancedSearchInterface Component', () => {
  test('renders all three mode options', () => {
    render(<EnhancedSearchInterface docType="all" />);
    
    expect(screen.getByText('Search & Analyze')).toBeInTheDocument();
    expect(screen.getByText('Hypothesis Mode')).toBeInTheDocument();
    expect(screen.getByText('Protocol Builder')).toBeInTheDocument();
    
    // Check descriptions
    expect(screen.getByText('Search through papers, protocols, and theses')).toBeInTheDocument();
    expect(screen.getByText('Explore "what if" scenarios with AI')).toBeInTheDocument();
    expect(screen.getByText('Generate custom lab protocols')).toBeInTheDocument();
  });

  test('displays search mode by default', () => {
    render(<EnhancedSearchInterface docType="papers" />);
    
    expect(screen.getByTestId('advanced-search-box')).toBeInTheDocument();
    expect(screen.getByText('AdvancedSearchBox - DocType: papers')).toBeInTheDocument();
  });

  test('switches to hypothesis mode when clicked', async () => {
    const user = userEvent.setup();
    render(<EnhancedSearchInterface docType="all" />);
    
    // Click on Hypothesis Mode
    const hypothesisCard = screen.getByText('Hypothesis Mode').closest('[data-testid="glass-card"]');
    await user.click(hypothesisCard);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
    
    // Should show HypothesisExplorer
    expect(screen.getByTestId('hypothesis-explorer')).toBeInTheDocument();
    expect(screen.queryByTestId('advanced-search-box')).not.toBeInTheDocument();
  });

  test('switches to protocol builder mode when clicked', async () => {
    const user = userEvent.setup();
    render(<EnhancedSearchInterface docType="all" />);
    
    // Click on Protocol Builder
    const protocolCard = screen.getByText('Protocol Builder').closest('[data-testid="glass-card"]');
    await user.click(protocolCard);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
    
    // Should show ProtocolBuilder
    expect(screen.getByTestId('protocol-builder')).toBeInTheDocument();
    expect(screen.queryByTestId('advanced-search-box')).not.toBeInTheDocument();
  });

  test('shows loading animation during mode transition', async () => {
    const user = userEvent.setup();
    render(<EnhancedSearchInterface docType="all" />);
    
    // Click on Hypothesis Mode
    const hypothesisCard = screen.getByText('Hypothesis Mode').closest('[data-testid="glass-card"]');
    await user.click(hypothesisCard);
    
    // Should show loading
    expect(screen.getByTestId('loading')).toBeInTheDocument();
    expect(screen.getByTestId('loading')).toHaveAttribute('data-type', 'dna-helix');
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
  });

  test('highlights active mode with different styling', async () => {
    const user = userEvent.setup();
    render(<EnhancedSearchInterface docType="all" />);
    
    // Initially, search mode should be active
    const searchCard = screen.getByText('Search & Analyze').closest('[data-testid="glass-card"]');
    expect(searchCard).toHaveClass('border-2', 'border-white/30', 'bg-white/10');
    
    // Click on Hypothesis Mode
    const hypothesisCard = screen.getByText('Hypothesis Mode').closest('[data-testid="glass-card"]');
    await user.click(hypothesisCard);
    
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
    
    // Hypothesis mode should now be active
    expect(hypothesisCard).toHaveClass('border-2', 'border-white/30', 'bg-white/10');
    expect(searchCard).not.toHaveClass('border-2', 'border-white/30', 'bg-white/10');
  });

  test('passes docType prop correctly to AdvancedSearchBox', () => {
    const { rerender } = render(<EnhancedSearchInterface docType="papers" />);
    
    expect(screen.getByText('AdvancedSearchBox - DocType: papers')).toBeInTheDocument();
    
    // Change docType
    rerender(<EnhancedSearchInterface docType="protocols" />);
    
    expect(screen.getByText('AdvancedSearchBox - DocType: protocols')).toBeInTheDocument();
  });

  test('handles rapid mode switching gracefully', async () => {
    const user = userEvent.setup();
    render(<EnhancedSearchInterface docType="all" />);
    
    // Rapidly click between modes
    const hypothesisCard = screen.getByText('Hypothesis Mode').closest('[data-testid="glass-card"]');
    const protocolCard = screen.getByText('Protocol Builder').closest('[data-testid="glass-card"]');
    
    await user.click(hypothesisCard);
    await user.click(protocolCard);
    await user.click(hypothesisCard);
    
    // Wait for final state
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
    
    // Should end up in hypothesis mode
    expect(screen.getByTestId('hypothesis-explorer')).toBeInTheDocument();
  });

  test('renders mode icons correctly', () => {
    render(<EnhancedSearchInterface docType="all" />);
    
    // Check for SVG icons (they'll be rendered inside the mode cards)
    const modeCards = screen.getAllByTestId('glass-card');
    expect(modeCards).toHaveLength(3);
    
    // Each card should have an icon container with gradient background
    modeCards.forEach(card => {
      const iconContainer = card.querySelector('.bg-gradient-to-r');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  test('maintains mode state when docType prop changes', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<EnhancedSearchInterface docType="papers" />);
    
    // Switch to hypothesis mode
    const hypothesisCard = screen.getByText('Hypothesis Mode').closest('[data-testid="glass-card"]');
    await user.click(hypothesisCard);
    
    await waitFor(() => {
      expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
    });
    
    expect(screen.getByTestId('hypothesis-explorer')).toBeInTheDocument();
    
    // Change docType prop
    rerender(<EnhancedSearchInterface docType="protocols" />);
    
    // Should still be in hypothesis mode
    expect(screen.getByTestId('hypothesis-explorer')).toBeInTheDocument();
  });
});