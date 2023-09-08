import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('http://localhost:41000/merge');
  await page.locator('#merge-local').fill('data/merge_test3/left.ipynb');
  await page.locator('#merge-base').fill('data/merge_test3/center.ipynb');
  await page.locator('#merge-remote').fill('data/merge_test3/right.ipynb');
  await page.getByRole('button', { name: 'Merge files' }).click();
});

/* 2 cells with merge conflict */
test.describe('merge test3', () => {
  test('should warn for remaining conflicts', async ({ page }) => {
    await expect.soft(page.getByText('➭')).toHaveCount(25);

    await page.getByRole('button', { name: 'Download' }).click();

    await expect(page.locator('.dialog .msg')).toHaveText(
      'There are conflicts remaining. Do you still want to download the merge output?',
    );
  });

  test('should download a merge result without conflict', async ({ page }) => {
    // Pick a solution
    await page
      .locator(
        'div:nth-child(3) > .cm-editor > .cm-scroller > .cm-gutters > div:nth-child(2) > div:nth-child(3) > .jp-Merge-gutter-picker',
      )
      .first()
      .click();
    // Mark a conflict as resolved
    await page.getByText('⚠').click();
    // Manually edit the merge result
    await page
      .locator('.cm-merge-m-chunk-end-mixed')
      .last()
      .click({ clickCount: 3 });
    await page.keyboard.press('Backspace');

    const download1Promise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    const download1 = await download1Promise;

    let readResolve: (value: unknown) => void;
    const readDownload = new Promise(resolve => {
      readResolve = resolve;
    });
    const stream = (await download1.createReadStream())!;
    stream.setEncoding('utf-8');
    let content = '';
    const chunks: string[] = [];

    stream.on('readable', () => {
      let chunk: string;
      while (null !== (chunk = stream.read())) {
        chunks.push(chunk);
      }
    });

    stream.on('end', () => {
      content = chunks.join('');
      readResolve(void 0);
    });

    await readDownload;

    expect(content).toBe(EXPECTED_RESOLVED_MERGE);
  });
});

const EXPECTED_RESOLVED_MERGE = `{
  "cells": [
    {
      "cell_type": "code",
      "execution_count": null,
      "id": "9e423ee0-5ba3-4792-8b16-b20fe7a775e3",
      "metadata": {
      },
      "outputs": [
      ],
      "source": [
        "import pandas as pd  # programmers like shortening names for things, so they usually import pandas as \\"pd\\"\\n",
        "import superior as sup # again with the shortening of names\\n",
        "import requests # we use it for downloading the data so we don't have to save it on GitHub (too big!)\\n",
        "import tarfile # for de-compressing the files we download from the EPAimport numpy as np"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "id": "08e85e68-1722-4847-a13f-97c921829073",
      "metadata": {
      },
      "outputs": [
      ],
      "source": [
        "# Download the data from the EPA website\\n",
        "data_file_urls = [\\n",
        "    'https://aqs.epa.gov/aqsweb/airdata/daily_88101_2017.zip',\\n",
        "    'https://aqs.epa.gov/aqsweb/airdata/daily_88101_2018.zip',\\n",
        "]\\n",
        "# copied this example from https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests\\n",
        "for url in data_file_urls:\\n",
        "    local_filename = \\"data/{}\\".format(url.split('/')[-1])\\n",
        "    with requests.get(url, stream=True) as r:\\n",
        "        r.raise_for_status()\\n",
        "        with open(local_filename, 'r') as f:\\n",
        "            for chunk in r.iter_content(chunk_size=8192): \\n",
        "                f.write(chunk)"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3 (ipykernel)",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "codemirror_mode": {
        "name": "ipython",
        "version": 3
      },
      "file_extension": ".py",
      "mimetype": "text/x-python",
      "name": "python",
      "nbconvert_exporter": "python",
      "pygments_lexer": "ipython3",
      "version": "3.11.4"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}`;
