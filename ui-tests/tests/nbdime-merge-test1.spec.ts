import { expect, test } from '@playwright/test';



/**** Test for the merge application ****/
/*Test1: Notebooks of same length 1 conflict */
test.beforeEach(  async ({ page }) => {

  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/default/test1/left.ipynb');
  await page.locator('#merge-base').fill('data/default/test1/center.ipynb');
  await page.locator('#merge-remote').fill('data/default/test1/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
})

test('open an example and take a snapshot', async ({ page }) => {
  await expect.soft(page.getByText('➭')).toHaveCount(12)
  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
});

test('choose left version for conflict',  async ({ page }) => {
  await page.locator('div:nth-child(2) > .jp-Merge-gutter-picker').first().click();
  await page.getByText('⚠').click();
  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
})

test('choose central version for conflict',  async ({ page }) => {
  await page.locator('div').filter({ hasText: /^➭➭➭$/ }).locator('div').nth(3).click();
  await page.getByText('⚠').click();
  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
})

test('choose right version for conflict',  async ({ page }) => {
  await page.locator('div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(2) > .jp-Merge-gutter-picker').click();
  await page.getByText('⚠').click();
  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
})

