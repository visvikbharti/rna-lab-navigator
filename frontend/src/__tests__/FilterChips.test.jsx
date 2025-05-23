import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FilterChips from '../components/FilterChips';
import { AnimationProvider } from '../contexts/AnimationContext';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    button: ({ children, whileHover, whileTap, variants, initial, animate, transition, ...props }) => (
      <button {...props}>{children}</button>
    ),
  },
}));

// Wrapper component to provide AnimationContext
const renderWithContext = (component) => {
  return render(
    <AnimationProvider>
      {component}
    </AnimationProvider>
  );
};

describe('FilterChips Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  test('renders all filter options', () => {
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Protocols')).toBeInTheDocument();
    expect(screen.getByText('Papers')).toBeInTheDocument();
    expect(screen.getByText('Theses')).toBeInTheDocument();
  });

  test('displays correct icons for each filter', () => {
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    expect(screen.getByText('📚')).toBeInTheDocument(); // All
    expect(screen.getByText('🧪')).toBeInTheDocument(); // Protocols
    expect(screen.getByText('📄')).toBeInTheDocument(); // Papers
    expect(screen.getByText('📖')).toBeInTheDocument(); // Theses
  });

  test('highlights the selected filter', () => {
    renderWithContext(<FilterChips selected="paper" onChange={mockOnChange} />);
    
    const paperButton = screen.getByRole('button', { name: /📄 Papers/i });
    const allButton = screen.getByRole('button', { name: /📚 All/i });
    
    // Selected button should have gradient background classes
    expect(paperButton).toHaveClass('bg-gradient-to-r', 'from-primary-600/90', 'to-primary-700/90', 'text-white');
    
    // Non-selected button should have different classes
    expect(allButton).toHaveClass('bg-white/60', 'text-gray-800');
  });

  test('calls onChange when a filter is clicked', async () => {
    const user = userEvent.setup();
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const protocolButton = screen.getByRole('button', { name: /🧪 Protocols/i });
    await user.click(protocolButton);
    
    expect(mockOnChange).toHaveBeenCalledTimes(1);
    expect(mockOnChange).toHaveBeenCalledWith('protocol');
  });

  test('calls onChange with correct filter id for each option', async () => {
    const user = userEvent.setup();
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    // Test each filter
    const filters = [
      { name: /📚 All/i, id: 'all' },
      { name: /🧪 Protocols/i, id: 'protocol' },
      { name: /📄 Papers/i, id: 'paper' },
      { name: /📖 Theses/i, id: 'thesis' },
    ];
    
    for (const filter of filters) {
      const button = screen.getByRole('button', { name: filter.name });
      await user.click(button);
      expect(mockOnChange).toHaveBeenLastCalledWith(filter.id);
    }
    
    expect(mockOnChange).toHaveBeenCalledTimes(4);
  });

  test('updates styling when selected prop changes', () => {
    const { rerender } = renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    // Initially 'all' is selected
    let allButton = screen.getByRole('button', { name: /📚 All/i });
    expect(allButton).toHaveClass('bg-gradient-to-r');
    
    // Change selection to 'thesis'
    rerender(
      <AnimationProvider>
        <FilterChips selected="thesis" onChange={mockOnChange} />
      </AnimationProvider>
    );
    
    allButton = screen.getByRole('button', { name: /📚 All/i });
    const thesisButton = screen.getByRole('button', { name: /📖 Theses/i });
    
    expect(allButton).not.toHaveClass('bg-gradient-to-r');
    expect(thesisButton).toHaveClass('bg-gradient-to-r');
  });

  test('maintains responsive layout with flex wrap', () => {
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const container = screen.getAllByRole('button')[0].parentElement;
    expect(container).toHaveClass('flex', 'flex-wrap', 'gap-2');
  });

  test('applies dark mode classes', () => {
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const nonSelectedButton = screen.getByRole('button', { name: /🧪 Protocols/i });
    
    // Check for dark mode classes
    expect(nonSelectedButton).toHaveClass('dark:bg-gray-800/60', 'dark:text-gray-200');
  });

  test('handles rapid clicks gracefully', async () => {
    const user = userEvent.setup();
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const paperButton = screen.getByRole('button', { name: /📄 Papers/i });
    
    // Rapid clicks
    await user.click(paperButton);
    await user.click(paperButton);
    await user.click(paperButton);
    
    // Should still only register clicks (not cause errors)
    expect(mockOnChange).toHaveBeenCalledTimes(3);
    expect(mockOnChange).toHaveBeenCalledWith('paper');
  });

  test('renders with animation transition classes', () => {
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const buttons = screen.getAllByRole('button');
    
    // Each button should have transition classes
    buttons.forEach(button => {
      expect(button.className).toMatch(/transition/);
    });
  });

  test('button hover states work correctly', async () => {
    const user = userEvent.setup();
    renderWithContext(<FilterChips selected="all" onChange={mockOnChange} />);
    
    const protocolButton = screen.getByRole('button', { name: /🧪 Protocols/i });
    
    // Non-selected button should have hover classes
    expect(protocolButton).toHaveClass('hover:bg-white/80');
    
    // Hover over the button
    await user.hover(protocolButton);
    
    // Button should still be interactive
    expect(protocolButton).toBeEnabled();
  });
});