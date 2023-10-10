/**
 * Configuration for Playwright
 */

module.exports = {
  reporter: [
    [process.env.CI ? 'github' : 'list'],
    ['html', { open: process.env.CI ? 'never' : 'on-failure' }],
  ],
  reportSlowTests: null,
  retries: process.env.CI ? 1 : 0,
  timeout: 60000,
  use: {
    // Browser options
    // headless: false,
    // slowMo: 500,

    // Context options
    viewport: { width: 1024, height: 768 },

    // Artifacts
    // trace: 'on-first-retry',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm start',
    url: 'http://localhost:41000/merge',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },
};
