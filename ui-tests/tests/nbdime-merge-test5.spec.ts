import { expect, test } from '@playwright/test';

test.describe('merge test5', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:41000/merge');
    await page.locator('#merge-local').fill('data/merge_test5/left.ipynb');
    await page.locator('#merge-base').fill('data/merge_test5/center.ipynb');
    await page.locator('#merge-remote').fill('data/merge_test5/right.ipynb');
    await page.getByRole('button', { name: 'Merge files' }).click();
  });

  test('take a snapshot at opening', async ({ page }) => {
    await expect.soft(page.getByText('➭')).toHaveCount(16);
    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();
  });
});
