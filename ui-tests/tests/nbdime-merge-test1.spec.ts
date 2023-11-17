import { expect, test } from '@playwright/test';

/* notebooks of same length and 1 conflict*/
test.describe('merge test1', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:41000/merge');
    await page.locator('#merge-local').fill('data/merge_test1/left.ipynb');
    await page.locator('#merge-base').fill('data/merge_test1/center.ipynb');
    await page.locator('#merge-remote').fill('data/merge_test1/right.ipynb');
    await page.getByRole('button', { name: 'Merge files' }).click();
  });

  test('take a snapshot at opening', async ({ page }) => {
    await expect.soft(page.getByText('➭')).toHaveCount(11);

    await expect.soft(page.locator('#nbdime-header-base')).toHaveText('Base');

    expect.soft(await page.locator('#main').screenshot()).toMatchSnapshot();

    await page.getByRole('button', { name: 'Download' }).click();

    await expect(page.locator('.dialog .msg')).toHaveText(
      'There are conflicts remaining. Do you still want to download the merge output?',
    );
  });

  test('choose left version for conflict', async ({ page }) => {
    await page
      .locator('.cm-merge-left-editor')
      .nth(1) // This select the cell; 0 being the notebook metadata
      .locator('.jp-Merge-gutter-picker')
      .last()
      .click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('choose central version for conflict', async ({ page }) => {
    await page
      .locator('.cm-central-editor')
      .nth(1) // This select the cell; 0 being the notebook metadata
      .locator('.jp-Merge-gutter-picker')
      .nth(1)
      .click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('choose right version for conflict', async ({ page }) => {
    await page
      .locator('.cm-merge-right-editor')
      .nth(1) // This select the cell; 0 being the notebook metadata
      .locator('.jp-Merge-gutter-picker')
      .last()
      .click();
    await page.getByText('⚠').click();
    expect(await page.locator('#main').screenshot()).toMatchSnapshot();
  });

  test('should download a merge result without conflict', async ({ page }) => {
    await page
      .locator(
        'div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(2) > .jp-Merge-gutter-picker',
      )
      .click();
    await page.getByText('⚠').click();
    const download1Promise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download1 = await download1Promise;
    // Finalize download
    expect(await download1.failure()).toBeNull();
  });

  test('should not collapse source for unchanged metadata', async ({ page }) => {
    await page.locator('.jp-Metadata-merge .jp-CollapsiblePanel-header-icon').click();
    expect(await page.locator('#main').screenshot({animations: 'disabled'})).toMatchSnapshot();
  });
});

test('3 panels view', async ({ page }) => {
  const ctxt = page.context();
  page.route(/.+\/merge/, async (route, request) => {
    const response = await ctxt.request.fetch(request);
    if (!response.ok()) {
      route.abort();
      return;
    }

    const buffer = await response!.body();
    const content = buffer.toString();
    route.fulfill({
      body: content.replace('"showBase": true', '"showBase": false'),
    });
  });

  // Load the page
  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test1/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test1/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test1/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();

  await expect.soft(page.getByText('➭')).toHaveCount(8);

  await expect.soft(page.locator('#nbdime-header-base')).toHaveText('Merged');

  expect(await page.locator('#main').screenshot()).toMatchSnapshot();
});
