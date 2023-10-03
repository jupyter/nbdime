import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test10/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test10/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test10/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
});

/* notebooks of same length and 1 conflict*/
test.describe('merge test10', () => {
  test('should synchronize the collapse status between editor', async ({ page }) => {
    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();

    // Should display 4 collapsers
    const collapsers = page.getByText('4 unchanged lines');
    await expect.soft(collapsers).toHaveCount(4);
    await expect.soft(page.getByText('gaussian array y')).toHaveCount(0);

    // Click on the base editor collapser
    await page.getByText('4 unchanged lines').nth(1).click();

    // Should not display any collapsers
    await expect.soft(collapsers).toHaveCount(0);
    await expect(page.getByText('gaussian array y')).toHaveCount(4);
  });
});
