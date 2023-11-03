import { expect, test } from '@playwright/test';

test.describe('merge test6', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:41000/merge');
    await page.locator('#merge-local').fill('data/merge_test6/left.ipynb');
    await page.locator('#merge-base').fill('data/merge_test6/center.ipynb');
    await page.locator('#merge-remote').fill('data/merge_test6/right.ipynb');
    await page.getByRole('button', { name: 'Merge files' }).click();
  });

  test('take a snapshot at opening', async ({ page }) => {
    await page.getByText('Hide unchanged cells').click();
    await page.getByText('a = "hello the world"').waitFor();
    // Check that single editor are not collapsed; added cell and unchanged cell
    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();
  });
});
