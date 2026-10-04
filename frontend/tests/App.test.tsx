import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

function renderRoute(path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

function mockBackend(ready = true) {
  return vi.fn().mockImplementation((url: string) =>
    Promise.resolve(
      new Response(
        JSON.stringify(
          url.endsWith('/health')
            ? { status: 'ok', service: 'kagex-api', version: '0.1.0' }
            : {
                status: ready ? 'ready' : 'unavailable',
                postgres: ready,
                redis: ready,
              },
        ),
        { status: url.endsWith('/ready') && !ready ? 503 : 200 },
      ),
    ),
  );
}

describe('foundation shell', () => {
  it('renders the identity and navigates to a connected workspace', async () => {
    vi.stubGlobal('fetch', mockBackend());
    renderRoute();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Detect the unseen.',
    );
    expect(
      screen.getByText(
        'AI-Powered Software Defect Prediction & Code Risk Analysis',
      ),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('link', { name: /open workspace/i }));
    expect(await screen.findByText('Backend connected')).toBeInTheDocument();
    expect(
      await screen.findByText('PostgreSQL & Redis ready'),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Analysis features are not yet available/),
    ).toBeInTheDocument();
  });

  it('shows loading, handles failure, and supports retry', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    renderRoute('/app');
    expect(screen.getByText('Checking backend…')).toBeInTheDocument();
    expect(await screen.findByText('Backend unavailable')).toBeInTheDocument();
    expect(
      await screen.findByText('Dependency status unknown'),
    ).toBeInTheDocument();
    vi.stubGlobal('fetch', mockBackend());
    fireEvent.click(screen.getByRole('button', { name: 'Check again' }));
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

  it('does not report malformed health responses as connected', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')));
    renderRoute('/app');
    expect(await screen.findByText('Backend unavailable')).toBeInTheDocument();
  });

  it('provides a not-found route', () => {
    renderRoute('/missing');
    expect(
      screen.getByRole('heading', { name: 'Page not found.' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Back to overview' }),
    ).toHaveAttribute('href', '/');
  });
});
