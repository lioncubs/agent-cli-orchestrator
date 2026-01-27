import { test, expect } from '@playwright/test';

/**
 * Copilot CLI Integration Tests
 * 
 * These tests verify the actual Copilot CLI integration works correctly
 * by sending real prompts and validating responses.
 */

test.describe('Copilot CLI Real Integration', () => {
  // Set longer timeout for Copilot CLI responses
  test.setTimeout(60000);

  test('should execute simple math prompt via API', async ({ request }) => {
    const response = await request.post('/prompt', {
      data: {
        prompt: 'What is 5 + 5?'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.output).toBeDefined();
    // Output can be a number or string depending on the response
    const outputStr = String(data.output).toLowerCase();
    expect(outputStr).toContain('10');
  });

  test('should execute code explanation prompt', async ({ request }) => {
    const response = await request.post('/prompt', {
      data: {
        prompt: 'What does the print function do in Python?'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.output).toBeDefined();
    expect(data.output.length).toBeGreaterThan(10);
  });

  test('should execute git-related prompt', async ({ request }) => {
    const response = await request.post('/prompt', {
      data: {
        prompt: 'What command shows git status?'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('success');
    expect(data.output).toBeDefined();
    expect(data.output.toLowerCase()).toMatch(/git\s+status/);
  });

  test('should log copilot interactions', async ({ request }) => {
    const response = await request.post('/prompt', {
      data: {
        prompt: 'Say hello'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.log_file).toBeDefined();
    expect(data.log_file).toContain('copilot_');
  });
});

test.describe('Copilot Streaming Integration', () => {
  test.setTimeout(60000);

  test('should stream response for simple prompt', async ({ request }) => {
    const response = await request.post('/prompt/stream', {
      data: {
        prompt: 'What is 1+1?'
      }
    });
    
    expect(response.status()).toBe(200);
    
    const body = await response.text();
    expect(body).toContain('data:');
    expect(body).toContain('"type": "start"');
  });
});

test.describe('Session Management Integration', () => {
  let sessionId: string;

  test('should create a new session', async ({ request }) => {
    const response = await request.post('/sessions', {
      data: {
        name: 'E2E Test Session',
        description: 'Created by Playwright E2E test',
        type: 'research',
        repo_name: 'test-repo',
        user_id: 'playwright-test-user'
      }
    });
    
    expect(response.status()).toBe(201);
    
    const data = await response.json();
    expect(data.session).toBeDefined();
    expect(data.session.id).toBeDefined();
    sessionId = data.session.id;
    expect(data.session.status).toBe('active');
  });

  test('should list sessions', async ({ request }) => {
    const response = await request.get('/sessions');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.sessions).toBeDefined();
    expect(Array.isArray(data.sessions)).toBe(true);
  });

  test('should get session details', async ({ request }) => {
    // First create a session to get
    const createResponse = await request.post('/sessions', {
      data: {
        name: 'Detail Test Session',
        description: 'For testing session details',
        type: 'research',
        repo_name: 'test-repo',
        user_id: 'playwright-test-user'
      }
    });
    
    const createData = await createResponse.json();
    const id = createData.session.id;
    
    const response = await request.get(`/sessions/${id}`);
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.session).toBeDefined();
    expect(data.session.id).toBe(id);
  });
});

test.describe('Repository API Integration', () => {
  test('should get repository info', async ({ request }) => {
    const response = await request.get('/repo');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.repository).toBeDefined();
    expect(data.path).toBeDefined();
  });

  test('should list branches', async ({ request }) => {
    const response = await request.get('/branches');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.branches).toBeDefined();
    expect(Array.isArray(data.branches)).toBe(true);
    expect(data.count).toBeDefined();
    expect(data.count.total).toBeGreaterThan(0);
  });

  test('should get current branch', async ({ request }) => {
    const response = await request.get('/branch/current');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.branch).toBeDefined();
    expect(data.branch.length).toBeGreaterThan(0);
  });

  test('should list worktrees', async ({ request }) => {
    const response = await request.get('/worktrees');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.worktrees).toBeDefined();
    expect(Array.isArray(data.worktrees)).toBe(true);
  });
});

test.describe('Health and Metrics', () => {
  test('should return healthy status', async ({ request }) => {
    const response = await request.get('/health');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.version).toBeDefined();
  });

  test('should return API info at root', async ({ request }) => {
    const response = await request.get('/');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.message).toContain('Agent CLI Orchestrator');
    expect(data.endpoints).toBeDefined();
    expect(data.session_management).toBeDefined();
    expect(data.mcp_server).toBeDefined();
  });

  test('should get logs', async ({ request }) => {
    const response = await request.get('/logs');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.logs).toBeDefined();
  });

  test('should get copilot logs', async ({ request }) => {
    const response = await request.get('/logs/copilot');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.logs).toBeDefined();
    expect(Array.isArray(data.logs)).toBe(true);
  });
});

test.describe('Copilot Sessions', () => {
  test('should list copilot sessions', async ({ request }) => {
    const response = await request.get('/copilot/sessions');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toBeDefined();
  });
});

test.describe('Documentation Endpoints', () => {
  test('should serve OpenAPI docs', async ({ request }) => {
    const response = await request.get('/docs');
    
    expect(response.status()).toBe(200);
  });

  test('should serve ReDoc', async ({ request }) => {
    const response = await request.get('/redoc');
    
    expect(response.status()).toBe(200);
  });

  test('should serve OpenAPI JSON', async ({ request }) => {
    const response = await request.get('/openapi.json');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data.openapi).toBeDefined();
    expect(data.info).toBeDefined();
    expect(data.paths).toBeDefined();
  });
});
