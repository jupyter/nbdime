import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:41000/diff');
  await page.locator('#diff-remote').fill('data/diff_test1/left.ipynb');
  await page.locator('#diff-base').fill('data/diff_test1/center.ipynb');
  await page.getByRole('button', { name: 'Diff files' }).click();
});

/* added cells between left and right editors */
test.describe('diff test1', () => {
  test('take a snapshot at opening', async ({ page }) => {
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });
});
