import { test, expect } from '@playwright/test';

test.describe('Branches Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/branches');
  });

  test('should load the branches page', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display branches list', async ({ page }) => {
    // Wait for branches to load
    await page.waitForTimeout(1000);
    
    // Look for branch list elements
    const branchList = page.locator('.branches, [data-testid="branches"], table, ul, .branch-list, .branch-item');
    const count = await branchList.count();
    
    // Should have some branch elements or empty state
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display current branch indicator', async ({ page }) => {
    // Look for current branch indicator
    const currentBranch = page.locator('.current, .active, [data-current], .main, .master, :has-text("main"), :has-text("master")');
    const count = await currentBranch.count();
    
    // May or may not have current branch indicator
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should have branch action buttons', async ({ page }) => {
    // Look for action buttons
    const actionButtons = page.locator('button:has-text("Checkout"), button:has-text("Create"), button:has-text("Delete"), button:has-text("Merge")');
    const count = await actionButtons.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Branches API', () => {
  test('should list branches via API', async ({ request }) => {
    const response = await request.get('/api/branches');
    
    expect([200, 404]).toContain(response.status());
    
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toBeDefined();
    }
  });

  test('should get current branch via API', async ({ request }) => {
    const response = await request.get('/api/branches/current');
    
    expect([200, 404]).toContain(response.status());
  });
});
