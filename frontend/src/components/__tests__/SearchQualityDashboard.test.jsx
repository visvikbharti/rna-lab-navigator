import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SearchQualityDashboard from '../SearchQualityDashboard';
import { 
  getQualityMetrics, 
  getFeedbackTrends, 
  getUserSatisfaction, 
  getTopFailureQueries 
} from '../../api/search';

// Mock the API module
jest.mock('../../api/search', () => ({
  getQualityMetrics: jest.fn(),
  getFeedbackTrends: jest.fn(),
  getUserSatisfaction: jest.fn(),
  getTopFailureQueries: jest.fn(),
}));

describe('SearchQualityDashboard Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    getQualityMetrics.mockReset();
    getFeedbackTrends.mockReset();
    getUserSatisfaction.mockReset();
    getTopFailureQueries.mockReset();
    
    // Default mock implementations
    getQualityMetrics.mockResolvedValue({
      total_queries: 1000,
      avg_confidence: 0.85,
      positive_feedback_rate: 0.78,
      zero_results_rate: 0.05,
      citation_rate: 0.92,
    });
    
    getFeedbackTrends.mockResolvedValue([
      { date: '2023-01-01', positive: 80, negative: 20 },
      { date: '2023-01-02', positive: 85, negative: 15 },
    ]);
    
    getUserSatisfaction.mockResolvedValue({
      overall: 0.82,
      by_doc_type: [
        { doc_type: 'paper', satisfaction: 0.85 },
        { doc_type: 'thesis', satisfaction: 0.79 },
        { doc_type: 'protocol', satisfaction: 0.88 },
      ]
    });
    
    getTopFailureQueries.mockResolvedValue([
      { query: 'complex RNA structure', count: 12, avg_confidence: 0.32 },
      { query: 'RNA binding proteins', count: 8, avg_confidence: 0.41 },
    ]);
  });

  test('renders loading state initially', () => {
    render(<SearchQualityDashboard />);
    
    // Check for loading indicators
    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  test('renders dashboard with metrics after loading', async () => {
    render(<SearchQualityDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument();
    });
    
    // Check for key metrics
    expect(screen.getByText(/1,000/)).toBeInTheDocument(); // Total queries
    expect(screen.getByText(/85%/)).toBeInTheDocument(); // Avg confidence
    expect(screen.getByText(/78%/)).toBeInTheDocument(); // Positive feedback
    
    // Check for section headings
    expect(screen.getByText(/Feedback Trends/i)).toBeInTheDocument();
    expect(screen.getByText(/User Satisfaction/i)).toBeInTheDocument();
    expect(screen.getByText(/Top Failure Queries/i)).toBeInTheDocument();
  });

  test('displays top failure queries correctly', async () => {
    render(<SearchQualityDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument();
    });
    
    // Check for failure queries
    expect(screen.getByText(/complex RNA structure/i)).toBeInTheDocument();
    expect(screen.getByText(/RNA binding proteins/i)).toBeInTheDocument();
    
    // Check for their metrics
    expect(screen.getByText(/12/)).toBeInTheDocument(); // Count for first query
    expect(screen.getByText(/32%/)).toBeInTheDocument(); // Confidence for first query
  });

  test('handles error state when API calls fail', async () => {
    // Mock API with error
    getQualityMetrics.mockRejectedValue(new Error('Failed to fetch metrics'));
    
    render(<SearchQualityDashboard />);
    
    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/Error loading metrics/i)).toBeInTheDocument();
    });
  });

  test('displays satisfaction by document type', async () => {
    render(<SearchQualityDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument();
    });
    
    // Check for document type satisfaction
    expect(screen.getByText(/paper/i)).toBeInTheDocument();
    expect(screen.getByText(/thesis/i)).toBeInTheDocument();
    expect(screen.getByText(/protocol/i)).toBeInTheDocument();
    
    // Check for percentage values
    expect(screen.getByText(/85%/)).toBeInTheDocument(); // Paper satisfaction
    expect(screen.getByText(/79%/)).toBeInTheDocument(); // Thesis satisfaction
    expect(screen.getByText(/88%/)).toBeInTheDocument(); // Protocol satisfaction
  });

  test('renders the dashboard tabs correctly', async () => {
    render(<SearchQualityDashboard />);
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument();
    });
    
    // Check for dashboard tabs
    expect(screen.getByRole('tab', { name: /Overview/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Feedback Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Query Analysis/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Recommendations/i })).toBeInTheDocument();
  });
});