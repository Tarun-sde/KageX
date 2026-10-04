import { useEffect, useState } from 'react';
import { getHealth, getReadiness } from '../services/api';
import { Panel } from './Panel';

type State = {
  api: 'checking' | 'connected' | 'unavailable';
  dependencies: 'checking' | 'ready' | 'unavailable' | 'unknown';
};

export function SystemStatus() {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<State>({
    api: 'checking',
    dependencies: 'checking',
  });

  useEffect(() => {
    const controller = new AbortController();
    void getHealth(controller.signal).then(
      () => {
        if (!controller.signal.aborted)
          setState((s) => ({ ...s, api: 'connected' }));
      },
      () => {
        if (!controller.signal.aborted)
          setState((s) => ({ ...s, api: 'unavailable' }));
      },
    );
    void getReadiness(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted)
          setState((s) => ({ ...s, dependencies: data.status }));
      },
      () => {
        if (!controller.signal.aborted)
          setState((s) => ({ ...s, dependencies: 'unknown' }));
      },
    );
    return () => controller.abort();
  }, [attempt]);

  const busy = state.api === 'checking' || state.dependencies === 'checking';
  const apiLabels = {
    checking: 'Checking backend…',
    connected: 'Backend connected',
    unavailable: 'Backend unavailable',
  };
  const dependencyLabels = {
    checking: 'Checking dependencies…',
    ready: 'PostgreSQL & Redis ready',
    unavailable: 'Dependencies unavailable',
    unknown: 'Dependency status unknown',
  };

  return (
    <Panel title="System connection">
      <div role="status" aria-live="polite" className="space-y-4">
        <p className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className={`status-dot ${state.api === 'connected' ? 'is-ready' : ''}`}
          />
          {apiLabels[state.api]}
        </p>
        <p className="text-muted">{dependencyLabels[state.dependencies]}</p>
      </div>
      <button
        className="button mt-8"
        disabled={busy}
        onClick={() => {
          setState({ api: 'checking', dependencies: 'checking' });
          setAttempt((value) => value + 1);
        }}
      >
        {busy ? 'Checking connection' : 'Check again'}
      </button>
    </Panel>
  );
}
