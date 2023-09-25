import { expect, test } from '@playwright/test';

/* Very long cell */
test.describe('diff test4', () => {
  test('The file ends must be aligned', async ({ page }) => {
    const ctxt = page.context();
    page.route(/.+\/diff/, async (route, request) => {
      const response = await ctxt.request.fetch(request);
      if (!response.ok()) {
        route.abort();
        return;
      }

      const buffer = await response!.body();
      const content = buffer.toString();
      route.fulfill({
        body: content.replace(
          '"collapseIdentical": 2',
          '"collapseIdentical": -1',
        ),
      });
    });

    await page.goto('http://localhost:41000/diff');
    await page.locator('#diff-remote').fill('data/diff_test4/left.ipynb');
    await page.locator('#diff-base').fill('data/diff_test4/center.ipynb');
    await page.getByRole('button', { name: 'Diff files' }).click();

    await page.locator('.nbdime-spinner').waitFor({ state: 'hidden' });
    await page.waitForTimeout(300);
    await page.keyboard.press('Control+End');
    await page.waitForTimeout(300);
    expect(await page.screenshot()).toMatchSnapshot();
  });
});
