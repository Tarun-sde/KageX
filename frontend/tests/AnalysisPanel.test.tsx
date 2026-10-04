import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { AnalysisPanel } from '../src/components/AnalysisPanel';
import type { AnalysisRun } from '../src/services/analyses';

const run: AnalysisRun = {
  id: 'run-1',
  project_id: 'project-1',
  status: 'QUEUED',
  created_at: '2026-10-04T00:00:00Z',
  started_at: null,
  completed_at: null,
  error_code: null,
  error_message: null,
  summary: {},
  warnings: [],
};
const entity = {
  id: 'entity-1',
  language: 'typescript',
  entity_type: 'file',
  relative_path: 'src/main.ts',
  qualified_name: 'src/main.ts',
  start_line: 1,
  end_line: 4,
  metrics: { loc: 4, decision_count: 1 },
  analyzer_name: 'ts-morph',
  analyzer_version: '28.0.0',
  metric_schema_version: 'typescript_file_v1',
  warnings: [],
};
const json = (data: unknown, status = 200) =>
  Promise.resolve(new Response(JSON.stringify(data), { status }));
afterEach(() => vi.useRealTimers());

it('queues, polls, shows real metrics and stops polling after completion', async () => {
  vi.useFakeTimers();
  let polls = 0;
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    if (init?.method === 'POST') return json(run, 202);
    if (url.includes('/entities?'))
      return json({ items: [entity], total: 1, offset: 0, limit: 50 });
    if (url.endsWith('/run-1')) {
      polls++;
      return json({
        ...run,
        status: polls === 1 ? 'RUNNING' : 'COMPLETED',
        summary: {
          supported_files: 1,
          entities_analyzed: 1,
          unsupported_files: 0,
          duration_seconds: 0.5,
        },
        warnings: [{ code: 'FILE_PARSE_FAILED', relative_path: 'bad.py' }],
      });
    }
    return json([]);
  });
  vi.stubGlobal('fetch', fetcher);
  await act(async () => {
    render(<AnalysisPanel projectId="project-1" />);
  });
  expect(screen.getByText('No analysis runs yet.')).toBeInTheDocument();
  await act(async () => {
    fireEvent.click(
      screen.getByRole('button', { name: 'Start static analysis' }),
    );
  });
  expect(screen.getByText('Static analysis running')).toBeInTheDocument();
  expect(
    screen.getByRole('button', { name: 'Start static analysis' }),
  ).toBeDisabled();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(2000);
  });
  expect(screen.getByText('Static analysis completed')).toBeInTheDocument();
  expect(
    screen.getByText('TypeScript prediction: MODEL_UNAVAILABLE'),
  ).toBeInTheDocument();
  expect(screen.getByText('decision_count')).toBeInTheDocument();
  expect(screen.getByText('bad.py: FILE_PARSE_FAILED')).toBeInTheDocument();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(polls).toBe(2);
  await act(async () => {
    fireEvent.change(screen.getByLabelText('Language'), {
      target: { value: 'typescript' },
    });
  });
  expect(
    fetcher.mock.calls.some(([url]) => url.includes('language=typescript')),
  ).toBe(true);
});

it('aborts status requests and cancels polling on unmount', async () => {
  vi.useFakeTimers();
  let polls = 0;
  let signal: AbortSignal | null | undefined;
  vi.stubGlobal('fetch', (url: string, init?: RequestInit) => {
    if (url.endsWith('/run-1')) {
      polls++;
      signal = init?.signal;
      return json(run);
    }
    return json([run]);
  });
  const view = render(<AnalysisPanel projectId="project-1" />);
  await act(async () => {
    await Promise.resolve();
  });
  expect(polls).toBe(1);
  view.unmount();
  expect(signal?.aborted).toBe(true);
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000);
  });
  expect(polls).toBe(1);
});

it('renders persisted failure and allows a new run', async () => {
  const failed = {
    ...run,
    status: 'FAILED',
    error_code: 'ANALYZER_TIMEOUT',
    error_message: 'Time limit exceeded.',
  };
  vi.stubGlobal('fetch', (url: string) =>
    json(url.endsWith('/run-1') ? failed : [failed]),
  );
  render(<AnalysisPanel projectId="project-1" />);
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Time limit exceeded. (ANALYZER_TIMEOUT)',
  );
  expect(
    screen.getByRole('button', { name: 'Start static analysis' }),
  ).toBeEnabled();
});

it('shows queue errors and retries history after a failed request', async () => {
  let history = 0;
  vi.stubGlobal('fetch', (_url: string, init?: RequestInit) => {
    if (init?.method === 'POST')
      return json(
        { error: { code: 'QUEUE_UNAVAILABLE', message: 'Queue unavailable.' } },
        503,
      );
    return ++history === 1
      ? json({ error: { code: 'UNAVAILABLE', message: 'Try again.' } }, 503)
      : json([]);
  });
  render(<AnalysisPanel projectId="project-1" />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Try again.');
  fireEvent.click(screen.getByRole('button', { name: 'Refresh analyses' }));
  await screen.findByText('No analysis runs yet.');
  fireEvent.click(
    screen.getByRole('button', { name: 'Start static analysis' }),
  );
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Queue unavailable.',
  );
});
