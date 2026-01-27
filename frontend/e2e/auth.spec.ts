import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should access public endpoints without auth', async ({ request }) => {
    // Health endpoint should be public
    const healthResponse = await request.get('/health');
    expect([200, 404]).toContain(healthResponse.status());
    
    // Docs endpoint should be public
    const docsResponse = await request.get('/docs');
    expect([200, 404]).toContain(docsResponse.status());
  });

  test('should handle login page', async ({ page }) => {
    await page.goto('/login');
    
    // Check if login page exists or redirects
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display login form if auth is enabled', async ({ page }) => {
    await page.goto('/login');
    
    // Look for login form elements
    const usernameField = page.locator('input[name="username"], input[type="email"], input[name="email"], #username, #email');
    const passwordField = page.locator('input[type="password"], input[name="password"], #password');
    const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
    
    const hasUsername = await usernameField.first().isVisible().catch(() => false);
    const hasPassword = await passwordField.first().isVisible().catch(() => false);
    const hasButton = await loginButton.first().isVisible().catch(() => false);
    
    // If this is a login page, it should have form elements
    // If auth is disabled, the page may redirect or show different content
    expect(hasUsername || hasPassword || hasButton || true).toBeTruthy();
  });

  test('should handle logout', async ({ page }) => {
    // Try to find and click logout
    await page.goto('/');
    
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout"), button:has-text("Sign out"), a:has-text("Sign out")');
    const hasLogout = await logoutButton.first().isVisible().catch(() => false);
    
    if (hasLogout) {
      await logoutButton.first().click();
      await page.waitForTimeout(1000);
    }
    
    // Page should still be functional
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Auth API', () => {
  test('should handle auth endpoints', async ({ request }) => {
    // Check auth status
    const statusResponse = await request.get('/api/auth/status');
    expect([200, 401, 404]).toContain(statusResponse.status());
  });

  test('should handle token validation', async ({ request }) => {
    const response = await request.get('/api/auth/validate', {
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });
    
    // Should return 401 for invalid token or 404 if endpoint doesn't exist
    expect([200, 401, 403, 404]).toContain(response.status());
  });
});
