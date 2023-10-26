import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test4/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test4/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test4/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
});

/* notebooks of same length and 1 conflict*/
test.describe('merge test4', () => {
  test('should synchronize the collapse status between editor', async ({
    page,
  }) => {
    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();

    // Should display 8 collapsers
    const collapsers1 = page.getByText('12 unchanged lines');
    await expect.soft(collapsers1).toHaveCount(4);
    const collapsers2 = page.getByText('5 unchanged lines');
    await expect.soft(collapsers2).toHaveCount(4);
    await expect.soft(page.getByText('import numpy')).toHaveCount(0);
    await expect
      .soft(page.getByText('noise = np.random.normal(0.0, 0.2, nx)'))
      .toHaveCount(0);

    // Click on the base editor collapsers
    await page.getByText('12 unchanged lines').nth(1).click();
    await expect.soft(collapsers1).toHaveCount(0);
    await page.getByText('5 unchanged lines').nth(1).click();
    await expect.soft(collapsers2).toHaveCount(0);

    // Should not display any collapser

    await expect(page.getByText('import numpy')).toHaveCount(4);
    await expect(
      page.getByText('noise = np.random.normal(0.0, 0.2, nx)'),
    ).toHaveCount(4);
  });
});
