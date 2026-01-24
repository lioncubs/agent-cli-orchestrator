import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Activity } from '../pages/Activity';

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

describe('Activity', () => {
  it('renders activity log title', () => {
    render(<Activity />, { wrapper: createWrapper() });
    expect(screen.getByText('Activity Log')).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<Activity />, { wrapper: createWrapper() });
    expect(screen.getByText('View recent system activities and operations')).toBeInTheDocument();
  });

  it('renders refresh button', () => {
    render(<Activity />, { wrapper: createWrapper() });
    const refreshButton = screen.getByRole('button', { name: /Refresh/i });
    expect(refreshButton).toBeInTheDocument();
  });

  it('renders show entries selector', () => {
    render(<Activity />, { wrapper: createWrapper() });
    expect(screen.getByText('Show entries')).toBeInTheDocument();
  });

  it('renders recent activities section', () => {
    render(<Activity />, { wrapper: createWrapper() });
    expect(screen.getByText(/Recent Activities/i)).toBeInTheDocument();
  });
});
