import { expect, test } from '@playwright/test';


test.beforeEach(  async ({ page }) => {

  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/default/left.ipynb');
  await page.locator('#merge-base').fill('data/default/center.ipynb');
  await page.locator('#merge-remote').fill('data/default/right.ipynb');

  await page.getByRole('button', { name: 'Merge files' }).click();


})

test('should emit an activation console message', async ({ page }) => {


  await expect.soft(page.getByText('⚠')).toHaveCount(2)
  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
});

test('choose left solution for conflict',  async ({ page }) => {



})