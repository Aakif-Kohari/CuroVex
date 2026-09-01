import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ValidationBadge from '@/components/ValidationBadge';

describe('ValidationBadge', () => {
  it('shows green clinical trial badge when trial exists', () => {
    render(<ValidationBadge hasClinicalTrial={true} hasLiterature={false} />);
    expect(screen.getByText('Clinical Trial')).toBeInTheDocument();
  });

  it('shows gray no-trial badge when no trial', () => {
    render(<ValidationBadge hasClinicalTrial={false} hasLiterature={false} />);
    expect(screen.getByText('No Trial')).toBeInTheDocument();
  });

  it('shows blue literature badge when literature exists', () => {
    render(<ValidationBadge hasClinicalTrial={false} hasLiterature={true} />);
    expect(screen.getByText('Literature')).toBeInTheDocument();
  });

  it('shows gray no-literature badge when no literature', () => {
    render(<ValidationBadge hasClinicalTrial={false} hasLiterature={false} />);
    expect(screen.getByText('No Literature')).toBeInTheDocument();
  });

  it('shows both green badges when both exist', () => {
    render(<ValidationBadge hasClinicalTrial={true} hasLiterature={true} />);
    expect(screen.getByText('Clinical Trial')).toBeInTheDocument();
    expect(screen.getByText('Literature')).toBeInTheDocument();
  });
});
