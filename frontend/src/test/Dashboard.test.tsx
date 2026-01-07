import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from '../pages/Dashboard';

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

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders welcome message', () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    expect(screen.getByText(/Welcome to Agent CLI Orchestrator/i)).toBeInTheDocument();
  });

  it('renders stats grid', () => {
    render(<Dashboard />, { wrapper: createWrapper() });
    expect(screen.getByText('Repositories')).toBeInTheDocument();
    expect(screen.getByText('Current Branch')).toBeInTheDocument();
    expect(screen.getByText('Worktrees')).toBeInTheDocument();
    expect(screen.getByText('Recent Activities')).toBeInTheDocument();
  });
});
