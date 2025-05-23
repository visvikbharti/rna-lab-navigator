import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import App from '../App';

// Mock API endpoints
const server = setupServer(
  rest.post('/api/search/', (req, res, ctx) => {
    return res(
      ctx.json({
        query: req.body.query,
        results: [
          {
            id: 1,
            title: 'RNA Extraction Protocol',
            content: 'Standard protocol for RNA extraction...',
            doc_type: 'protocol',
            relevance_score: 0.95,
            metadata: {
              author: 'Dr. Smith',
              date: '2024-01-15',
              source_file: 'rna_extraction.pdf'
            }
          },
          {
            id: 2,
            title: 'CRISPR Gene Editing in RNA Biology',
            content: 'Recent advances in CRISPR technology...',
            doc_type: 'paper',
            relevance_score: 0.87,
            metadata: {
              author: 'Dr. Johnson',
              date: '2023-12-20',
              source_file: 'crispr_rna.pdf'
            }
          }
        ],
        total_results: 2,
        search_time: 0.234
      })
    );
  }),
  
  rest.post('/api/feedback/', (req, res, ctx) => {
    return res(ctx.json({ status: 'success', feedback_id: 123 }));
  }),
  
  rest.get('/api/search/quality/metrics/', (req, res, ctx) => {
    return res(
      ctx.json({
        avg_response_time: 0.345,
        total_searches: 1250,
        satisfaction_rate: 0.89,
        common_queries: ['RNA extraction', 'CRISPR protocol', 'PCR setup']
      })
    );
  }),
  
  rest.post('/api/protocol/upload/', (req, res, ctx) => {
    return res(
      ctx.json({
        status: 'success',
        document_id: 456,
        message: 'Protocol uploaded successfully'
      })
    );
  })
);

// Setup and teardown
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock components that we're not testing
jest.mock('../components/enhanced', () => ({
  ParticleBackground: () => null,
  FloatingOrbs: () => null,
  GlassCard: ({ children, className }) => <div className={className}>{children}</div>,
  GradientText: ({ text }) => <h1>{text}</h1>,
  Navigation: () => null,
  Loading: () => <div>Loading...</div>,
  ColossalButton: ({ children, onClick }) => <button onClick={onClick}>{children}</button>,
}));

describe('Complete User Flow Integration Tests', () => {
  test('User searches for RNA extraction protocol and provides feedback', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // 1. User lands on homepage
    expect(screen.getByText('RNA Lab Navigator')).toBeInTheDocument();
    expect(screen.getByText(/Your AI assistant for lab protocols/i)).toBeInTheDocument();
    
    // 2. User switches to classic UI for simplicity
    const uiToggle = screen.getByText(/Classic UI/i);
    await user.click(uiToggle);
    expect(screen.getByText(/Enhanced UI/i)).toBeInTheDocument();
    
    // 3. User filters by protocols
    const protocolFilter = screen.getByRole('button', { name: /Protocols/i });
    await user.click(protocolFilter);
    
    // 4. User enters search query
    const searchInput = await screen.findByPlaceholderText(/Ask about RNA lab protocols/i);
    await user.type(searchInput, 'RNA extraction protocol');
    
    // 5. User submits search
    const searchButton = screen.getByRole('button', { name: /Search/i });
    await user.click(searchButton);
    
    // 6. Wait for results
    await waitFor(() => {
      expect(screen.getByText('RNA Extraction Protocol')).toBeInTheDocument();
    });
    
    // 7. Verify search results display
    expect(screen.getByText(/Standard protocol for RNA extraction/i)).toBeInTheDocument();
    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    
    // 8. User provides positive feedback
    const feedbackButton = screen.getByRole('button', { name: /👍/i });
    await user.click(feedbackButton);
    
    // 9. Verify feedback was submitted
    await waitFor(() => {
      expect(screen.getByText(/Thank you for your feedback/i)).toBeInTheDocument();
    });
  });

  test('User uploads a new protocol document', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // 1. Navigate to upload page
    const uploadLink = screen.getByRole('link', { name: /Upload Protocol/i });
    await user.click(uploadLink);
    
    // 2. Wait for upload page to load
    await waitFor(() => {
      expect(screen.getByText(/Upload Protocol Documents/i)).toBeInTheDocument();
    });
    
    // 3. Fill in upload form
    const titleInput = screen.getByLabelText(/Title/i);
    await user.type(titleInput, 'New PCR Protocol');
    
    const descriptionInput = screen.getByLabelText(/Description/i);
    await user.type(descriptionInput, 'Optimized PCR protocol for RNA samples');
    
    // 4. Select file (mocked)
    const fileInput = screen.getByLabelText(/Select file/i);
    const file = new File(['protocol content'], 'pcr_protocol.pdf', { type: 'application/pdf' });
    await user.upload(fileInput, file);
    
    // 5. Submit upload
    const uploadButton = screen.getByRole('button', { name: /Upload/i });
    await user.click(uploadButton);
    
    // 6. Verify success message
    await waitFor(() => {
      expect(screen.getByText(/Protocol uploaded successfully/i)).toBeInTheDocument();
    });
  });

  test('User explores different search modes', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Start in enhanced UI mode (default)
    expect(screen.getByTestId('particle-background')).toBeInTheDocument();
    
    // 1. Test Search & Analyze mode (default)
    expect(screen.getByText('Search & Analyze')).toBeInTheDocument();
    const searchBox = await screen.findByTestId('advanced-search-box');
    expect(searchBox).toBeInTheDocument();
    
    // 2. Switch to Hypothesis Mode
    const hypothesisMode = screen.getByText('Hypothesis Mode').closest('div[data-testid="glass-card"]');
    await user.click(hypothesisMode);
    
    // Wait for mode switch
    await waitFor(() => {
      expect(screen.getByTestId('hypothesis-explorer')).toBeInTheDocument();
    });
    
    // 3. Switch to Protocol Builder
    const protocolMode = screen.getByText('Protocol Builder').closest('div[data-testid="glass-card"]');
    await user.click(protocolMode);
    
    await waitFor(() => {
      expect(screen.getByTestId('protocol-builder')).toBeInTheDocument();
    });
    
    // 4. Return to Search mode
    const searchMode = screen.getByText('Search & Analyze').closest('div[data-testid="glass-card"]');
    await user.click(searchMode);
    
    await waitFor(() => {
      expect(screen.getByTestId('advanced-search-box')).toBeInTheDocument();
    });
  });

  test('User checks search quality dashboard', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Navigate to search quality page
    const qualityLink = screen.getByRole('link', { name: /Search Quality/i });
    await user.click(qualityLink);
    
    // Wait for dashboard to load
    await waitFor(() => {
      expect(screen.getByText(/Search Quality Dashboard/i)).toBeInTheDocument();
    });
    
    // Verify metrics are displayed
    await waitFor(() => {
      expect(screen.getByText(/Average Response Time/i)).toBeInTheDocument();
      expect(screen.getByText(/0.345s/i)).toBeInTheDocument();
      expect(screen.getByText(/Total Searches/i)).toBeInTheDocument();
      expect(screen.getByText(/1,250/i)).toBeInTheDocument();
      expect(screen.getByText(/Satisfaction Rate/i)).toBeInTheDocument();
      expect(screen.getByText(/89%/i)).toBeInTheDocument();
    });
  });

  test('User workflow with error handling', async () => {
    const user = userEvent.setup();
    
    // Mock API error
    server.use(
      rest.post('/api/search/', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );
    
    render(<App />);
    
    // Try to search
    const searchInput = await screen.findByPlaceholderText(/Ask about RNA lab protocols/i);
    await user.type(searchInput, 'test query');
    
    const searchButton = screen.getByRole('button', { name: /Search/i });
    await user.click(searchButton);
    
    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/An error occurred/i)).toBeInTheDocument();
    });
    
    // User should be able to retry
    await user.clear(searchInput);
    await user.type(searchInput, 'retry query');
    
    // Reset handler to success
    server.use(
      rest.post('/api/search/', (req, res, ctx) => {
        return res(ctx.json({ results: [], total_results: 0 }));
      })
    );
    
    await user.click(searchButton);
    
    // Should work now
    await waitFor(() => {
      expect(screen.queryByText(/An error occurred/i)).not.toBeInTheDocument();
    });
  });

  test('Dark mode persists across navigation', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Toggle dark mode
    const darkModeToggle = screen.getByTestId('dark-mode-toggle');
    await user.click(darkModeToggle);
    
    // Verify dark mode is active
    const appContainer = document.querySelector('.min-h-screen');
    expect(appContainer).toHaveClass('dark:bg-gray-900');
    
    // Navigate to different pages
    await user.click(screen.getByRole('link', { name: /Upload Protocol/i }));
    
    // Dark mode should still be active
    await waitFor(() => {
      expect(screen.getByText(/Upload Protocol Documents/i)).toBeInTheDocument();
    });
    
    // Navigate back
    await user.click(screen.getByRole('link', { name: /Home/i }));
    
    // Dark mode should persist
    expect(darkModeToggle).toBeInTheDocument();
  });

  test('Keyboard navigation works throughout the app', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Tab through main elements
    await user.tab(); // UI toggle
    expect(document.activeElement).toHaveTextContent(/Classic UI/i);
    
    await user.tab(); // Dark mode toggle
    expect(document.activeElement).toHaveAttribute('data-testid', 'dark-mode-toggle');
    
    await user.tab(); // First nav link
    expect(document.activeElement).toHaveAttribute('href', '/');
    
    // Continue tabbing through navigation
    for (let i = 0; i < 5; i++) {
      await user.tab();
      expect(document.activeElement).toHaveAttribute('href');
    }
    
    // Tab to filter chips
    await user.tab();
    expect(document.activeElement).toHaveRole('button');
    
    // Use arrow keys to navigate filters
    await user.keyboard('{ArrowRight}');
    await user.keyboard('{Enter}');
    
    // Verify filter was activated
    expect(screen.getByText(/Protocols/i).closest('button')).toHaveClass('bg-gradient-to-r');
  });
});