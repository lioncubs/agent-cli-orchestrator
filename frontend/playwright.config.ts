import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration for Agent CLI Orchestrator E2E Tests
 * 
 * Run tests:
 *   npm run test:e2e          - Run all E2E tests
 *   npm run test:e2e:ui       - Run with Playwright UI
 *   npm run test:e2e:headed   - Run in headed mode
 *   npm run test:e2e:debug    - Debug mode
 */

export default defineConfig({
  testDir: './e2e',
  
  /* Run tests in parallel with 4 workers */
  fullyParallel: true,
  workers: process.env.CI ? 2 : 4,
  
  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,
  
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  
  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ...(process.env.CI ? [['github'] as const] : []),
  ],
  
  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.BASE_URL || 'http://localhost:8001',
    
    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',
    
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Video on failure */
    video: 'retain-on-failure',
  },
  
  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    /* Uncomment to add more browsers
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    */
  ],
  
  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'cd .. && CONFIG_FILE=config.test.yaml python main.py',
    url: 'http://localhost:8001/health',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
  
  /* Global timeout for each test */
  timeout: 30 * 1000,
  
  /* Expect timeout */
  expect: {
    timeout: 10 * 1000,
  },
  
  /* Output folder for test artifacts */
  outputDir: 'test-results/',
});
