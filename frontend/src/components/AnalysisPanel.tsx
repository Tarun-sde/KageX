import { useCallback, useEffect, useState } from 'react';
import {
  active,
  getAnalysis,
  getEntities,
  listAnalyses,
  startAnalysis,
  type AnalysisRun,
  type EntityPage,
} from '../services/analyses';
import { errorMessage } from '../services/api';
import { Panel } from './Panel';

export function AnalysisPanel({ projectId }: { projectId: string }) {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selected, setSelected] = useState('');
  const [offset, setOffset] = useState(0);
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void listAnalyses(projectId, offset, controller.signal).then(
      (result) => {
        if (controller.signal.aborted) return;
        setRuns(result);
        setLoading(false);
        setSelected((current) =>
          result.some((r) => r.id === current)
            ? current
            : (result[0]?.id ?? ''),
        );
      },
      (reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(errorMessage(reason));
          setLoading(false);
        }
      },
    );
    return () => controller.abort();
  }, [projectId, offset, attempt]);
  const updateRun = useCallback(
    (run: AnalysisRun) =>
      setRuns((current) =>
        current.map((item) => (item.id === run.id ? run : item)),
      ),
    [],
  );
  function refresh(nextOffset = offset) {
    setError('');
    setLoading(true);
    setOffset(nextOffset);
    setAttempt((value) => value + 1);
  }
  async function start() {
    setBusy(true);
    setError('');
    try {
      const run = await startAnalysis(projectId);
      setRuns((current) => [run, ...current].slice(0, 50));
      setSelected(run.id);
      setOffset(0);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mt-10">
      <Panel title="Static analysis">
        <p className="text-muted">
          Extract real source metrics. Defect prediction is not available.
        </p>
        <div className="my-6 flex flex-wrap gap-3">
          <button
            className="button button-primary"
            disabled={busy || loading || runs.some((run) => active(run.status))}
            onClick={() => {
              void start();
            }}
          >
            {busy ? 'Queueing…' : 'Start static analysis'}
          </button>
          <button
            className="button"
            disabled={loading}
            onClick={() => refresh()}
          >
            Refresh analyses
          </button>
        </div>
        {error && (
          <p role="alert" className="mb-4 text-accent">
            {error}
          </p>
        )}
        {loading ? (
          <p role="status">Loading analysis history…</p>
        ) : !runs.length ? (
          <p>No analysis runs yet.</p>
        ) : (
          <>
            <label className="field">
              Analysis run
              <select
                value={selected}
                onChange={(event) => setSelected(event.target.value)}
              >
                {runs.map((run) => (
                  <option key={run.id} value={run.id}>
                    {new Date(run.created_at).toLocaleString()} · {run.status} ·{' '}
                    {run.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </label>
            {selected && (
              <RunDetails
                key={selected}
                projectId={projectId}
                id={selected}
                onUpdate={updateRun}
              />
            )}
          </>
        )}
        <div className="mt-6 flex gap-3">
          {offset > 0 && (
            <button
              className="button"
              disabled={loading}
              onClick={() => refresh(Math.max(0, offset - 50))}
            >
              Newer runs
            </button>
          )}
          {runs.length === 50 && (
            <button
              className="button"
              disabled={loading}
              onClick={() => refresh(offset + 50)}
            >
              Older runs
            </button>
          )}
        </div>
      </Panel>
    </div>
  );
}

function RunDetails({
  projectId,
  id,
  onUpdate,
}: {
  projectId: string;
  id: string;
  onUpdate: (run: AnalysisRun) => void;
}) {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    async function poll() {
      try {
        const result = await getAnalysis(projectId, id, controller.signal);
        if (controller.signal.aborted) return;
        setRun(result);
        onUpdate(result);
        if (active(result.status))
          timer = setTimeout(() => {
            void poll();
          }, 2000);
      } catch (reason) {
        if (!controller.signal.aborted) setError(errorMessage(reason));
      }
    }
    void poll();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [projectId, id, attempt, onUpdate]);
  return (
    <div className="mt-6">
      {error && (
        <div>
          <p role="alert">{error}</p>
          <button
            className="button mt-3"
            onClick={() => {
              setError('');
              setAttempt((value) => value + 1);
            }}
          >
            Retry analysis status
          </button>
        </div>
      )}
      <p role="status" className="text-accent">
        {!run
          ? 'Loading analysis…'
          : `Static analysis ${run.status.toLowerCase()}`}
      </p>
      {run?.status === 'FAILED' && (
        <p role="alert" className="mt-3">
          {run.error_message} ({run.error_code})
        </p>
      )}
      {run?.status === 'COMPLETED' && (
        <>
          <dl className="my-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              'supported_files',
              'unsupported_files',
              'entities_analyzed',
              'duration_seconds',
            ].map((key) => (
              <div key={key}>
                <dt className="text-sm text-muted">
                  {key.replaceAll('_', ' ')}
                </dt>
                <dd>
                  {typeof run.summary[key] === 'number'
                    ? String(run.summary[key])
                    : 'Unavailable'}
                </dd>
              </div>
            ))}
          </dl>
          <EntityResults projectId={projectId} runId={id} />
        </>
      )}
      {!!run?.warnings.length && (
        <details className="mt-6">
          <summary>Analysis warnings ({run.warnings.length})</summary>
          <ul className="mt-3 space-y-2">
            {run.warnings.map((warning, index) => (
              <li key={index} className="break-all">
                {warning.relative_path}: {warning.code}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

function EntityResults({
  projectId,
  runId,
}: {
  projectId: string;
  runId: string;
}) {
  const [page, setPage] = useState<EntityPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [language, setLanguage] = useState('');
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void getEntities(
      projectId,
      runId,
      offset,
      language,
      controller.signal,
    ).then(
      (result) => {
        if (!controller.signal.aborted) setPage(result);
      },
      (reason: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(reason));
      },
    );
    return () => controller.abort();
  }, [projectId, runId, offset, language, attempt]);
  function changePage(next: number) {
    setPage(null);
    setError('');
    setOffset(next);
  }
  return (
    <div>
      <label className="field">
        Language
        <select
          value={language}
          onChange={(event) => {
            setLanguage(event.target.value);
            changePage(0);
          }}
        >
          <option value="">All languages</option>
          {['java', 'python', 'javascript', 'typescript'].map((value) => (
            <option key={value}>{value}</option>
          ))}
        </select>
      </label>
      {error && (
        <div>
          <p role="alert">{error}</p>
          <button
            className="button mt-3"
            onClick={() => {
              setError('');
              setAttempt((value) => value + 1);
            }}
          >
            Retry metrics
          </button>
        </div>
      )}
      {!page && !error && (
        <p role="status" className="mt-6">
          Loading metrics…
        </p>
      )}
      {page && (
        <>
          <p className="my-4">{page.total} entities matching this view</p>
          <ul className="space-y-6">
            {page.items.map((entity) => (
              <li key={entity.id} className="rounded-lg border border-line p-4">
                <h3 className="break-all text-lg">{entity.qualified_name}</h3>
                <p className="mt-2 break-all text-sm text-muted">
                  {entity.language} · {entity.entity_type} ·{' '}
                  {entity.relative_path}:{entity.start_line}–{entity.end_line}
                </p>
                <p className="mt-2 break-all text-xs text-muted">
                  {entity.analyzer_name} {entity.analyzer_version} ·{' '}
                  {entity.metric_schema_version}
                </p>
                {entity.language === 'typescript' && (
                  <p className="mt-3">
                    TypeScript prediction: MODEL_UNAVAILABLE
                  </p>
                )}
                <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3">
                  {Object.entries(entity.metrics).map(([name, value]) => (
                    <div key={name}>
                      <dt className="break-words text-xs text-muted">{name}</dt>
                      <dd>
                        {value === null
                          ? 'Unavailable'
                          : Number.isInteger(value)
                            ? value
                            : value.toFixed(3)}
                      </dd>
                    </div>
                  ))}
                </dl>
                {!!entity.warnings.length && (
                  <p className="mt-3 break-words text-sm">
                    Warnings: {entity.warnings.join(', ')}
                  </p>
                )}
              </li>
            ))}
          </ul>
          <div className="mt-6 flex gap-3">
            {offset > 0 && (
              <button
                className="button"
                onClick={() => changePage(Math.max(0, offset - 50))}
              >
                Previous entities
              </button>
            )}
            {offset + page.items.length < page.total && (
              <button
                className="button"
                onClick={() => changePage(offset + 50)}
              >
                Next entities
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
