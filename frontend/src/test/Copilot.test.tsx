import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Copilot } from '../pages/Copilot';

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

describe('Copilot', () => {
  it('renders copilot page title', () => {
    render(<Copilot />, { wrapper: createWrapper() });
    expect(screen.getByText('GitHub Copilot CLI')).toBeInTheDocument();
  });

  it('renders configuration section', () => {
    render(<Copilot />, { wrapper: createWrapper() });
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('Repository')).toBeInTheDocument();
  });

  it('renders prompt input field', () => {
    render(<Copilot />, { wrapper: createWrapper() });
    const promptInput = screen.getByPlaceholderText(/Enter your Copilot prompt here/i);
    expect(promptInput).toBeInTheDocument();
  });

  it('renders execute button (disabled when empty)', () => {
    render(<Copilot />, { wrapper: createWrapper() });
    const executeButton = screen.getByRole('button', { name: /Execute/i });
    expect(executeButton).toBeInTheDocument();
    expect(executeButton).toBeDisabled();
  });

  it('renders streaming checkbox', () => {
    render(<Copilot />, { wrapper: createWrapper() });
    const checkbox = screen.getByLabelText('Use streaming output');
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toBeChecked();
  });
});
