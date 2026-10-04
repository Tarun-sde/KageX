import { test, expect } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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
      page.getByText('Source ready for static analysis', { exact: true }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Start static analysis' }).click();
    await expect(
      page.getByText('Static analysis failed', { exact: true }),
    ).toBeVisible({ timeout: 30000 });
    await expect(page.getByRole('alert')).toContainText(
      'NO_ANALYZABLE_ENTITIES',
    );
    await page.getByLabel('Project name').fill('Renamed project');
    await page
      .getByRole('button', { name: 'Rename project', exact: true })
      .click();
    await expect(
      page.getByRole('heading', { name: 'Renamed project', exact: true }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByText('Source ready for static analysis', { exact: true }),
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

  test(`mixed-language static analysis at ${width}px`, async ({
    page,
    context,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    const headers = { Origin: 'http://localhost:5173', 'X-KageX-Request': '1' };
    const api = 'http://localhost:8000/api/v1';
    const registered = await context.request.post(`${api}/auth/register`, {
      headers,
      data: {
        email: `analysis-${randomUUID()}@example.com`,
        password: 'correct horse battery staple',
      },
    });
    expect(registered.status()).toBe(201);
    const created = await context.request.post(`${api}/projects`, {
      headers,
      data: { name: 'Mixed language fixture', source_type: 'ZIP_UPLOAD' },
    });
    const project = (await created.json()) as { id: string };
    // A fixed test utility archives fixture bytes; it never imports or runs them.
    const fixtureRoot = fileURLToPath(
      new URL('../../backend/tests/fixtures/analysis', import.meta.url),
    );
    const archive = execFileSync('python3', [
      '-I',
      '-c',
      'import io,pathlib,sys,zipfile\nb=io.BytesIO()\nr=pathlib.Path(sys.argv[1])\nwith zipfile.ZipFile(b,"w") as z:\n for f in sorted(r.rglob("*")):\n  if f.is_file(): z.writestr(f.relative_to(r).as_posix(),f.read_bytes())\nsys.stdout.buffer.write(b.getvalue())',
      fixtureRoot,
    ]);
    const prepared = await context.request.post(
      `${api}/projects/${project.id}/source/zip`,
      { headers, data: archive },
    );
    expect(prepared.status()).toBe(200);
    await page.goto(`/app/projects/${project.id}`);
    await page.getByRole('button', { name: 'Start static analysis' }).click();
    await expect(
      page.getByText('Static analysis completed', { exact: true }),
    ).toBeVisible({ timeout: 45000 });
    for (const language of ['java', 'python', 'javascript', 'typescript']) {
      await page
        .getByRole('combobox', { name: 'Language', exact: true })
        .selectOption(language);
      const schema =
        language === 'java'
          ? 'java_class_v1'
          : language === 'python'
            ? 'python_function_v1'
            : `${language}_file_v1`;
      await expect(
        page.getByText(schema, { exact: false }).first(),
      ).toBeVisible();
    }
    await expect(
      page.getByText('TypeScript prediction: MODEL_UNAVAILABLE').first(),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.reload();
    await expect(
      page.getByText('Static analysis completed', { exact: true }),
    ).toBeVisible();
    await expect(
      page
        .getByRole('combobox', { name: 'Analysis run', exact: true })
        .locator('option'),
    ).toHaveCount(1);
    const deleted = await context.request.delete(
      `${api}/projects/${project.id}`,
      { headers },
    );
    expect(deleted.status()).toBe(204);
  });
}
