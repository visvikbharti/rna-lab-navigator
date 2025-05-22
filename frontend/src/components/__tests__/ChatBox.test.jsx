import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ChatBox from '../ChatBox';
import { submitQuery } from '../../api/query';

// Mock the API module
jest.mock('../../api/query', () => ({
  submitQuery: jest.fn(),
}));

describe('ChatBox Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    submitQuery.mockReset();
  });

  test('renders correctly with initial state', () => {
    render(<ChatBox />);
    
    // Verify input field is present
    expect(screen.getByPlaceholderText(/Ask a question about RNA biology/i)).toBeInTheDocument();
    
    // Verify submit button is present
    expect(screen.getByRole('button', { name: /Submit/i })).toBeInTheDocument();
    
    // Verify initial messages (welcome message)
    expect(screen.getByText(/How can I help you/i)).toBeInTheDocument();
  });

  test('submits a query when form is submitted', async () => {
    // Mock API response
    submitQuery.mockResolvedValue({
      answer: 'RNA is a nucleic acid.',
      sources: [
        { title: 'RNA Biology', authors: 'Author 1', year: 2023 },
      ],
      confidence_score: 0.95,
    });
    
    render(<ChatBox />);
    
    // Type in the input field
    const input = screen.getByPlaceholderText(/Ask a question about RNA biology/i);
    fireEvent.change(input, { target: { value: 'What is RNA?' } });
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Verify API was called with the right parameters
    expect(submitQuery).toHaveBeenCalledWith({
      question: 'What is RNA?',
      doc_type: 'all',
      max_results: 5,
    });
    
    // Wait for the response to be rendered
    await waitFor(() => {
      expect(screen.getByText('RNA is a nucleic acid.')).toBeInTheDocument();
    });
    
    // Verify source is displayed
    expect(screen.getByText(/RNA Biology/i)).toBeInTheDocument();
  });

  test('shows loading state while waiting for response', async () => {
    // Mock API with delayed response
    submitQuery.mockImplementation(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve({
            answer: 'RNA is a nucleic acid.',
            sources: [
              { title: 'RNA Biology', authors: 'Author 1', year: 2023 },
            ],
            confidence_score: 0.95,
          });
        }, 100);
      });
    });
    
    render(<ChatBox />);
    
    // Type and submit
    const input = screen.getByPlaceholderText(/Ask a question about RNA biology/i);
    fireEvent.change(input, { target: { value: 'What is RNA?' } });
    
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Check for loading indicator
    expect(screen.getByText(/Generating response/i)).toBeInTheDocument();
    
    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('RNA is a nucleic acid.')).toBeInTheDocument();
    });
    
    // Loading indicator should be gone
    expect(screen.queryByText(/Generating response/i)).not.toBeInTheDocument();
  });

  test('handles error state when API call fails', async () => {
    // Mock API with error
    submitQuery.mockRejectedValue(new Error('Network error'));
    
    render(<ChatBox />);
    
    // Type and submit
    const input = screen.getByPlaceholderText(/Ask a question about RNA biology/i);
    fireEvent.change(input, { target: { value: 'What is RNA?' } });
    
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Sorry, there was an error/i)).toBeInTheDocument();
    });
  });

  test('displays low confidence warning for uncertain answers', async () => {
    // Mock API with low confidence response
    submitQuery.mockResolvedValue({
      answer: 'I am not sure about RNA structure.',
      sources: [],
      confidence_score: 0.3, // Low confidence
    });
    
    render(<ChatBox />);
    
    // Type and submit
    const input = screen.getByPlaceholderText(/Ask a question about RNA biology/i);
    fireEvent.change(input, { target: { value: 'What is the detailed structure of RNA?' } });
    
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/I am not sure about RNA structure./i)).toBeInTheDocument();
    });
    
    // Should show low confidence warning
    expect(screen.getByText(/This answer has low confidence/i)).toBeInTheDocument();
  });

  test('clears input after submission', async () => {
    // Mock API response
    submitQuery.mockResolvedValue({
      answer: 'RNA is a nucleic acid.',
      sources: [],
      confidence_score: 0.95,
    });
    
    render(<ChatBox />);
    
    // Type in the input field
    const input = screen.getByPlaceholderText(/Ask a question about RNA biology/i);
    fireEvent.change(input, { target: { value: 'What is RNA?' } });
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /Submit/i });
    fireEvent.click(submitButton);
    
    // Input should be cleared
    expect(input.value).toBe('');
    
    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('RNA is a nucleic acid.')).toBeInTheDocument();
    });
  });
});