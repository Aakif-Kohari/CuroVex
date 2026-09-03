/* eslint-disable react/display-name */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import PredictionCard from '@/components/PredictionCard';

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

const mockPrediction = {
  id: 'pred-001',
  drug_id: '42',
  disease_id: '1',
  drug_name: 'Metformin',
  score: 0.87,
  rank: 1,
};

describe('PredictionCard', () => {
  it('renders drug name', () => {
    render(<PredictionCard prediction={mockPrediction} index={0} diseaseId="1" />);
    expect(screen.getByText('Metformin')).toBeInTheDocument();
  });

  it('renders prediction score', () => {
    render(<PredictionCard prediction={mockPrediction} index={0} diseaseId="1" />);
    expect(screen.getByText('0.8700')).toBeInTheDocument();
  });

  it('renders drug ID', () => {
    render(<PredictionCard prediction={mockPrediction} index={0} diseaseId="1" />);
    expect(screen.getByText('ID: 42')).toBeInTheDocument();
  });

  it('links to explanation page', () => {
    render(<PredictionCard prediction={mockPrediction} index={0} diseaseId="1" />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', expect.stringContaining('/explanation/pred-001'));
  });

  it('shows fallback name when drug_name is missing', () => {
    const pred = { ...mockPrediction, drug_name: undefined };
    render(<PredictionCard prediction={pred} index={0} diseaseId="1" />);
    expect(screen.getByText('Drug 42')).toBeInTheDocument();
  });

  it('renders rank badge for top 3', () => {
    render(<PredictionCard prediction={{ ...mockPrediction, rank: 4 }} index={0} diseaseId="1" />);
    expect(screen.getByText('#4')).toBeInTheDocument();
  });
});
