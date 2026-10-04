import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';

// Small inert ZIP fixtures; no submitted source is executed.
const fixtures = {
  safe: 'UEsDBBQAAAAAAGsyRF2L/hI1FAAAABQAAAALAAAAc3JjL21haW4ucHkjIGluZXJ0IHRlc3Qgc291cmNlClBLAQIUAxQAAAAAAGsyRF2L/hI1FAAAABQAAAALAAAAAAAAAAAAAACAAQAAAABzcmMvbWFpbi5weVBLBQYAAAAAAQABADkAAAA9AAAAAAA=',
  unsafe:
    'UEsDBBQAAAAAAGsyRF2L/hI1FAAAABQAAAAJAAAALi4vZXNjYXBlIyBpbmVydCB0ZXN0IHNvdXJjZQpQSwECFAMUAAAAAABrMkRdi/4SNRQAAAAUAAAACQAAAAAAAAAAAAAAgAEAAAAALi4vZXNjYXBlUEsFBgAAAAABAAEANwAAADsAAAAAAA==',
};

for (const width of [1440, 390]) {
  test(`account and secure project lifecycle at ${width}px`, async ({
    page,
    context,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto('/app');
    await expect(page).toHaveURL(/\/login$/);
    await page
      .getByRole('link', { name: 'Create an account', exact: true })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Create an account.', exact: true }),
    ).toBeVisible();
    const email = `e2e-${randomUUID()}@example.com`;
    const password = 'correct horse battery staple';
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page
      .getByRole('button', { name: 'Create account', exact: true })
      .click();
    await expect(
      page.getByText('No projects on this page.', { exact: false }),
    ).toBeVisible();
    const cookie = (await context.cookies()).find(
      (cookie) => cookie.name === 'kagex_session',
    );
    expect(cookie?.httpOnly).toBe(true);
    expect(await page.evaluate(() => document.cookie)).not.toContain(
      'kagex_session',
    );
    await page.getByLabel('Project name').fill('Browser verification');
    await page
      .getByRole('button', { name: 'Create project', exact: true })
      .click();
    await expect(
      page.getByText('Awaiting source', { exact: true }),
    ).toBeVisible();
    const detailUrl = page.url();
    await page.getByLabel('ZIP archive').setInputFiles({
      name: 'unsafe.zip',
      mimeType: 'application/zip',
      buffer: Buffer.from(fixtures.unsafe, 'base64'),
    });
    await page
      .getByRole('button', { name: 'Prepare source', exact: true })
      .click();
    await expect(page.getByRole('alert')).toContainText('unsafe path');
    await expect(page.getByText(/Ingestion failed/)).toBeVisible();
    await page.getByLabel('ZIP archive').setInputFiles({
      name: 'safe.zip',
      mimeType: 'application/zip',
      buffer: Buffer.from(fixtures.safe, 'base64'),
    });
    await page
      .getByRole('button', { name: 'Prepare source', exact: true })
      .click();
    await expect(
      page.getByText('Source ready for future analysis', { exact: true }),
    ).toBeVisible();
    await page.getByLabel('Project name').fill('Renamed project');
    await page
      .getByRole('button', { name: 'Rename project', exact: true })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Renamed project', exact: true }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByText('Source ready for future analysis', { exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await expect(page).toHaveURL(/\/login$/);
    await page.getByLabel('Email', { exact: true }).fill(email);
    await page.getByLabel('Password', { exact: true }).fill(password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).click();
    await expect(
      page.getByRole('link', { name: 'Renamed project', exact: true }),
    ).toBeVisible();
    await page.goto(detailUrl);
    page.once('dialog', (dialog) => {
      void dialog.accept();
    });
    await page
      .getByRole('button', { name: 'Delete project', exact: true })
      .click();
    await expect(page.getByText(/No projects on this page/)).toBeVisible();
    await page.goto(detailUrl);
    await expect(page.getByRole('alert')).toContainText('Project not found');
    expect(errors).toEqual([]);
  });
}
