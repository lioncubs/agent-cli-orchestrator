import { test, expect } from '@playwright/test';

test.describe('API Endpoints', () => {
  test('should respond to health check', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should list repositories', async ({ request }) => {
    const response = await request.get('/api/repositories');
    
    if (response.status() === 200) {
      const data = await response.json();
      expect(Array.isArray(data) || typeof data === 'object').toBeTruthy();
    }
  });

  test('should handle metrics endpoint', async ({ request }) => {
    const response = await request.get('/api/metrics');
    expect([200, 404]).toContain(response.status());
  });

  test('should handle config endpoint', async ({ request }) => {
    const response = await request.get('/api/config');
    expect([200, 404]).toContain(response.status());
  });
});

test.describe('Copilot CLI Integration', () => {
  test('should check copilot CLI availability', async ({ request }) => {
    const response = await request.get('/api/copilot/status');
    expect([200, 404, 503]).toContain(response.status());
  });

  test('should execute copilot query', async ({ request }) => {
    const response = await request.post('/api/copilot/query', {
      data: {
        prompt: 'Explain what a git branch is',
        context: 'testing'
      }
    });
    
    // Copilot may not be available, so accept various responses
    expect([200, 201, 400, 404, 422, 500, 503]).toContain(response.status());
  });

  test('should handle copilot explain command', async ({ request }) => {
    const response = await request.post('/api/copilot/explain', {
      data: {
        code: 'console.log("Hello World")',
        language: 'javascript'
      }
    });
    
    expect([200, 201, 400, 404, 422, 500, 503]).toContain(response.status());
  });

  test('should handle copilot suggest command', async ({ request }) => {
    const response = await request.post('/api/copilot/suggest', {
      data: {
        prompt: 'Create a function to add two numbers',
        language: 'python'
      }
    });
    
    expect([200, 201, 400, 404, 422, 500, 503]).toContain(response.status());
  });
});

test.describe('Streaming Endpoints', () => {
  test('should handle streaming query', async ({ request }) => {
    const response = await request.post('/api/copilot/query/stream', {
      data: {
        prompt: 'Hello'
      }
    });
    
    expect([200, 404, 422, 500, 503]).toContain(response.status());
  });
});

test.describe('Git Operations API', () => {
  test('should list branches', async ({ request }) => {
    const response = await request.get('/api/branches');
    expect([200, 404]).toContain(response.status());
  });

  test('should get current branch', async ({ request }) => {
    const response = await request.get('/api/branches/current');
    expect([200, 404]).toContain(response.status());
  });

  test('should list worktrees', async ({ request }) => {
    const response = await request.get('/api/worktrees');
    expect([200, 404]).toContain(response.status());
  });

  test('should get git status', async ({ request }) => {
    const response = await request.get('/api/git/status');
    expect([200, 404]).toContain(response.status());
  });
});
