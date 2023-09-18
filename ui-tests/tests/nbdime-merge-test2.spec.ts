import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test2/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test2/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test2/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
});

/* notebooks of same length with 0 conflict*/
test.describe('merge test2 ', () => {
  test('take a snapshot at opening', async ({ page }) => {
    await expect.soft(page.getByText('➭')).toHaveCount(12);
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('choose left version', async ({ page }) => {
    await page
      .locator('div:nth-child(2) > .jp-Merge-gutter-picker')
      .first()
      .click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('choose central version', async ({ page }) => {
    await page
      .locator('div')
      .filter({ hasText: /^➭➭➭$/ })
      .locator('div')
      .nth(3)
      .click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('choose right version', async ({ page }) => {
    await page
      .locator(
        'div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(2) > .jp-Merge-gutter-picker',
      )
      .click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });
});
