import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Branches } from '../pages/Branches';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Branches', () => {
  it('renders branches page title', () => {
    render(<Branches />, { wrapper: createWrapper() });
    expect(screen.getByText('Branches')).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<Branches />, { wrapper: createWrapper() });
    expect(screen.getByText('View and manage Git branches')).toBeInTheDocument();
  });

  it('renders all branches section', () => {
    render(<Branches />, { wrapper: createWrapper() });
    expect(screen.getByText(/All Branches/i)).toBeInTheDocument();
  });
});
