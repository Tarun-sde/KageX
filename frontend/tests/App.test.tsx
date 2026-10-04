import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

const user = { id: 'user-1', email: 'alice@example.com' };
const project = {
  id: 'project-1',
  name: 'My project',
  source_type: 'ZIP_UPLOAD',
  status: 'CREATED',
  github_url: null,
  error_code: null,
  file_count: 0,
  source_bytes: 0,
  created_at: '2026-10-04T00:00:00Z',
  updated_at: '2026-10-04T00:00:00Z',
};
function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status });
}
function renderRoute(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}
function mockBackend(ready = true) {
  return vi.fn().mockImplementation((url: string) => {
    if (url.endsWith('/auth/me')) return Promise.resolve(json(user));
    if (url.includes('/projects?')) return Promise.resolve(json([]));
    if (url.endsWith('/source-limits'))
      return Promise.resolve(json({ max_upload_bytes: 1048576 }));
    if (url.endsWith('/projects/project-1'))
      return Promise.resolve(json(project));
    return Promise.resolve(
      json(
        url.endsWith('/health')
          ? { status: 'ok', service: 'kagex-api', version: '0.1.0' }
          : {
              status: ready ? 'ready' : 'unavailable',
              postgres: ready,
              redis: ready,
            },
        url.endsWith('/ready') && !ready ? 503 : 200,
      ),
    );
  });
}

describe('foundation regression', () => {
  it('renders identity and navigates to a connected workspace', async () => {
    vi.stubGlobal('fetch', mockBackend());
    renderRoute();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Detect the unseen.',
    );
    fireEvent.click(screen.getByRole('link', { name: /open workspace/i }));
    expect(await screen.findByText('Backend connected')).toBeInTheDocument();
    expect(
      await screen.findByText('PostgreSQL & Redis ready'),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/extract static metrics without executing code/),
    ).toBeInTheDocument();
  });
  it('shows session loading, handles failure, and supports retry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    renderRoute('/app');
    expect(screen.getByText('Loading your session…')).toBeInTheDocument();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    vi.stubGlobal('fetch', mockBackend());
    fireEvent.click(screen.getByRole('button', { name: 'Retry connection' }));
    expect(
      await screen.findByText('PostgreSQL & Redis ready'),
    ).toBeInTheDocument();
  });
  it('distinguishes liveness from failed dependencies', async () => {
    vi.stubGlobal('fetch', mockBackend(false));
    renderRoute('/app');
    expect(await screen.findByText('Backend connected')).toBeInTheDocument();
    expect(
      await screen.findByText('Dependencies unavailable'),
    ).toBeInTheDocument();
  });
  it('rejects malformed health responses', async () => {
    const backend = mockBackend();
    vi.stubGlobal('fetch', (url: string) =>
      url.endsWith('/health') ? Promise.resolve(json({})) : backend(url),
    );
    renderRoute('/app');
    expect(await screen.findByText('Backend unavailable')).toBeInTheDocument();
  });
  it('provides a not-found route', async () => {
    vi.stubGlobal('fetch', mockBackend());
    renderRoute('/missing');
    expect(
      screen.getByRole('heading', { name: 'Page not found.' }),
    ).toBeInTheDocument();
    await screen.findByRole('button', { name: 'Sign out' });
  });
});

describe('authentication and project flows', () => {
  it('redirects unauthenticated project access to login', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        json(
          {
            error: {
              code: 'UNAUTHENTICATED',
              message: 'Sign in to continue.',
            },
          },
          401,
        ),
      ),
    );
    renderRoute('/app');
    expect(
      await screen.findByRole('heading', { name: 'Welcome back.' }),
    ).toBeInTheDocument();
    expect(screen.queryByText('Your projects')).not.toBeInTheDocument();
  });
  it.each(['login', 'register'])(
    'submits %s credentials and enters the workspace',
    async (mode) => {
      const backend = mockBackend();
      const fetcher = vi.fn((url: string, init?: RequestInit) => {
        if (url.endsWith('/auth/me'))
          return Promise.resolve(
            json(
              { error: { code: 'UNAUTHENTICATED', message: 'Sign in.' } },
              401,
            ),
          );
        if (url.endsWith(`/auth/${mode}`)) return Promise.resolve(json(user));
        return backend(url, init);
      });
      vi.stubGlobal('fetch', fetcher);
      renderRoute(`/${mode}`);
      const submit = screen.getByRole('button', {
        name: mode === 'login' ? 'Sign in' : 'Create account',
      });
      await waitFor(() => expect(submit).toBeEnabled());
      fireEvent.change(screen.getByLabelText('Email'), {
        target: { value: user.email },
      });
      fireEvent.change(screen.getByLabelText('Password'), {
        target: { value: 'correct horse battery staple' },
      });
      fireEvent.click(submit);
      expect(
        await screen.findByText(/No projects on this page/),
      ).toBeInTheDocument();
      expect(fetcher).toHaveBeenCalledWith(
        expect.stringContaining(`/auth/${mode}`),
        expect.objectContaining({ credentials: 'include', method: 'POST' }),
      );
    },
  );
  it('shows login errors without entering the workspace', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          json(
            {
              error: {
                code: 'INVALID_CREDENTIALS',
                message: 'Invalid email or password.',
              },
            },
            401,
          ),
        ),
      ),
    );
    renderRoute('/login');
    const submit = screen.getByRole('button', { name: 'Sign in' });
    await waitFor(() => expect(submit).toBeEnabled());
    fireEvent.submit(submit.closest('form')!);
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Invalid email or password.',
    );
  });
  it('creates a project and displays its actual source state', async () => {
    const backend = mockBackend();
    vi.stubGlobal('fetch', (url: string, init?: RequestInit) =>
      url.endsWith('/projects') && init?.method === 'POST'
        ? Promise.resolve(json(project, 201))
        : backend(url, init),
    );
    renderRoute('/app');
    await screen.findByText(/No projects on this page/);
    fireEvent.change(screen.getByLabelText('Project name'), {
      target: { value: 'My project' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Create project' }));
    expect(
      await screen.findByRole('heading', { name: 'My project' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Awaiting source')).toBeInTheDocument();
    expect(
      screen.getByText(/Static analysis runs are tracked separately/),
    ).toBeInTheDocument();
  });
  it('rejects an empty upload before making a request', async () => {
    const fetcher = mockBackend();
    vi.stubGlobal('fetch', fetcher);
    renderRoute('/app/projects/project-1');
    const input = await screen.findByLabelText('ZIP archive');
    fireEvent.change(input, {
      target: { files: [new File([], 'empty.zip')] },
    });
    // jsdom FormData does not read assigned FileLists; browser E2E covers actual upload.
    fireEvent.submit(input.closest('form')!);
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(
      fetcher.mock.calls.some(([url]) => String(url).endsWith('/source/zip')),
    ).toBe(false);
  });
  it('shows inaccessible project error and retry', async () => {
    const backend = mockBackend();
    vi.stubGlobal('fetch', (url: string) =>
      url.endsWith('/projects/project-1')
        ? Promise.resolve(
            json(
              {
                error: {
                  code: 'PROJECT_NOT_FOUND',
                  message: 'Project not found.',
                },
              },
              404,
            ),
          )
        : backend(url),
    );
    renderRoute('/app/projects/project-1');
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Project not found.',
    );
    expect(
      screen.getByRole('button', { name: 'Retry project' }),
    ).toBeInTheDocument();
  });
  it('redirects on session expiration', async () => {
    vi.stubGlobal('fetch', mockBackend());
    renderRoute('/app');
    await screen.findByText(/No projects on this page/);
    fireEvent(window, new Event('kagex:unauthenticated'));
    expect(
      await screen.findByRole('heading', { name: 'Welcome back.' }),
    ).toBeInTheDocument();
  });
});

it('submits a public GitHub URL and displays source readiness', async () => {
  const backend = mockBackend();
  const github = { ...project, source_type: 'GITHUB' };
  const fetcher = vi.fn((url: string, init?: RequestInit) => {
    if (url.endsWith('/source/github'))
      return Promise.resolve(
        json({
          ...github,
          status: 'READY',
          file_count: 1,
          source_bytes: 13,
          github_url: 'https://github.com/octocat/Hello-World',
        }),
      );
    if (url.endsWith('/projects/project-1'))
      return Promise.resolve(json(github));
    return backend(url, init);
  });
  vi.stubGlobal('fetch', fetcher);
  renderRoute('/app/projects/project-1');
  fireEvent.change(await screen.findByLabelText('Public GitHub URL'), {
    target: { value: 'https://github.com/octocat/Hello-World' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Prepare source' }));
  expect(
    await screen.findByText('Source ready for static analysis'),
  ).toBeInTheDocument();
  expect(fetcher).toHaveBeenCalledWith(
    expect.stringContaining('/source/github'),
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ url: 'https://github.com/octocat/Hello-World' }),
    }),
  );
});
