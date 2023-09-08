import { expect, test } from '@playwright/test';


test.beforeEach(async ({ page }) => {

  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test1/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test1/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test1/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
})

/* notebooks of same length and 1 conflict*/
test.describe('merge test1', () => {

  test('take a snapshot at opening', async ({ page }) => {
    await expect.soft(page.getByText('➭')).toHaveCount(12)
    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();

    await page.getByRole('button', { name: 'Download' }).click();

    await expect(page.locator('.dialog .msg')).toHaveText('There are conflicts remaining. Do you still want to download the merge output?');
  });

  test('choose left version for conflict', async ({ page }) => {
    await page.locator('div:nth-child(2) > .jp-Merge-gutter-picker').first().click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  })

  test('choose central version for conflict', async ({ page }) => {
    await page.locator('div').filter({ hasText: /^➭➭➭$/ }).locator('div').nth(3).click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  })

  test('choose right version for conflict', async ({ page }) => {
    await page.locator('div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(2) > .jp-Merge-gutter-picker').click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  })

  test('should download a merge result without conflict', async ({ page }) => {
    await page.locator('div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(2) > .jp-Merge-gutter-picker').click();
    await page.getByText('⚠').click();
    const download1Promise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download1 = await download1Promise;
    // Finalize download
    expect(await download1.failure()).toBeNull();
  });
});
