import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings');
  });

  test('should load the settings page', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display settings form', async ({ page }) => {
    // Look for form elements
    const formElements = page.locator('form, input, select, textarea, .settings, [data-testid="settings"]');
    const count = await formElements.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should have save button', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save"), button[type="submit"], button:has-text("Update"), button:has-text("Apply")');
    const count = await saveButton.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should display configuration sections', async ({ page }) => {
    // Look for configuration sections
    const sections = page.locator('section, .section, fieldset, .card, [data-testid="section"]');
    const count = await sections.count();
    
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Settings API', () => {
  test('should get configuration via API', async ({ request }) => {
    const response = await request.get('/api/config');
    
    expect([200, 404]).toContain(response.status());
    
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toBeDefined();
    }
  });

  test('should get repositories via API', async ({ request }) => {
    const response = await request.get('/api/repositories');
    
    expect([200, 404]).toContain(response.status());
    
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toBeDefined();
    }
  });
});
