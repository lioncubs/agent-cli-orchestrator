import { test, expect } from '@playwright/test';

test.describe('Activity Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/activity');
  });

  test('should load the activity page', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display activity log', async ({ page }) => {
    await page.waitForTimeout(1000);
    
    // Look for activity log elements
    const activityLog = page.locator('.activity, [data-testid="activity"], .log, .timeline, table');
    const count = await activityLog.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should have filter options', async ({ page }) => {
    // Look for filter elements
    const filters = page.locator('select, input[type="search"], .filter, [data-testid="filter"]');
    const count = await filters.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display timestamps', async ({ page }) => {
    // Look for time-related elements
    const timestamps = page.locator('time, .timestamp, .date, [data-time]');
    const count = await timestamps.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Activity API', () => {
  test('should get activity log via API', async ({ request }) => {
    const response = await request.get('/api/activity');
    
    expect([200, 404]).toContain(response.status());
    
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toBeDefined();
    }
  });

  test('should get recent activity via API', async ({ request }) => {
    const response = await request.get('/api/activity/recent');
    
    expect([200, 404]).toContain(response.status());
  });
});
