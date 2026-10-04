import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Panel } from '../components/Panel';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { errorMessage } from '../services/api';
import {
  deleteProject,
  getProject,
  getUploadLimit,
  importGitHub,
  renameProject,
  uploadSource,
  type Project,
} from '../services/projects';

export function ProjectPage() {
  const { projectId = '' } = useParams();
  return <ProjectDetail key={projectId} id={projectId} />;
}

function ProjectDetail({ id }: { id: string }) {
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [limit, setLimit] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      getProject(id, controller.signal),
      getUploadLimit(controller.signal),
    ]).then(
      ([result, bytes]) => {
        if (!controller.signal.aborted) {
          setProject(result);
          setLimit(bytes);
        }
      },
      (reason: unknown) => {
        if (!controller.signal.aborted) setError(errorMessage(reason));
      },
    );
    return () => controller.abort();
  }, [id, attempt]);
  async function perform(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (reason) {
      setError(errorMessage(reason));
      // A rejected archive may have persisted FAILED; refresh the real server state.
      try {
        setProject(await getProject(id));
      } catch {
        /* Original error remains visible. */
      }
    } finally {
      setBusy(false);
    }
  }
  function rename(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = String(new FormData(event.currentTarget).get('name'));
    void perform(async () => setProject(await renameProject(id, name)));
  }
  function ingest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    if (project?.source_type === 'GITHUB') {
      void perform(async () =>
        setProject(await importGitHub(id, String(data.get('url')))),
      );
      return;
    }
    const file = data.get('file');
    if (
      !(file instanceof File) ||
      !file.size ||
      !file.name.toLowerCase().endsWith('.zip')
    ) {
      setError('Choose a non-empty ZIP file.');
      return;
    }
    if (file.size > limit) {
      setError(`Choose a ZIP no larger than ${limit / 1048576} MiB.`);
      return;
    }
    void perform(async () => setProject(await uploadSource(id, file)));
  }
  return (
    <section className="py-16 sm:py-24">
      <Link to="/app" className="text-accent underline">
        ← Your projects
      </Link>
      {error && (
        <p role="alert" className="my-6 text-accent">
          {error}
        </p>
      )}
      {!project ? (
        <div className="mt-8">
          {error ? (
            <button
              className="button"
              onClick={() => {
                setError('');
                setAttempt((value) => value + 1);
              }}
            >
              Retry project
            </button>
          ) : (
            <p role="status">Loading project…</p>
          )}
        </div>
      ) : (
        <>
          <h1 className="my-8 break-words font-display text-5xl">
            {project.name}
          </h1>
          <p role="status" className="text-accent">
            {busy
              ? 'Saving / preparing source…'
              : project.status === 'READY'
                ? 'Source ready for static analysis'
                : project.status === 'FAILED'
                  ? `Ingestion failed · ${project.error_code}`
                  : 'Awaiting source'}
          </p>
          <p className="mt-4 text-muted">
            Source is stored without execution. Static analysis runs are tracked
            separately below.
          </p>
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            <Panel title="Project source">
              {project.status === 'READY' ? (
                <dl className="space-y-3">
                  <div>
                    <dt className="text-muted">Stored files</dt>
                    <dd>{project.file_count}</dd>
                  </div>
                  <div>
                    <dt className="text-muted">Stored bytes</dt>
                    <dd>{project.source_bytes.toLocaleString()}</dd>
                  </div>
                  {project.github_url && (
                    <div>
                      <dt className="text-muted">Public repository</dt>
                      <dd className="break-all">{project.github_url}</dd>
                    </div>
                  )}
                </dl>
              ) : (
                <form onSubmit={ingest} className="space-y-6">
                  {project.source_type === 'ZIP_UPLOAD' ? (
                    <label className="field">
                      ZIP archive
                      <input
                        name="file"
                        type="file"
                        accept=".zip,application/zip"
                        required
                        disabled={busy}
                      />
                    </label>
                  ) : (
                    <label className="field">
                      Public GitHub URL
                      <input
                        name="url"
                        type="url"
                        placeholder="https://github.com/owner/repository"
                        required
                        maxLength={250}
                        disabled={busy}
                      />
                    </label>
                  )}
                  <p className="text-sm text-muted">
                    Maximum archive: {limit / 1048576} MiB.{' '}
                    {project.source_type === 'GITHUB' &&
                      'GitHub.com public repositories only; default branch.'}{' '}
                    Unsafe archives are rejected.
                  </p>
                  <button className="button button-primary" disabled={busy}>
                    {busy ? 'Preparing source…' : 'Prepare source'}
                  </button>
                </form>
              )}
            </Panel>
            <Panel title="Project settings">
              <form onSubmit={rename} className="space-y-4">
                <label className="field">
                  Project name
                  <input
                    name="name"
                    defaultValue={project.name}
                    required
                    maxLength={100}
                    disabled={busy}
                  />
                </label>
                <button className="button" disabled={busy}>
                  Rename project
                </button>
              </form>
              <button
                className="button mt-8 text-accent"
                disabled={busy}
                onClick={() => {
                  if (
                    window.confirm(
                      'Delete this project and its stored source? This cannot be undone.',
                    )
                  )
                    void perform(async () => {
                      await deleteProject(id);
                      navigate('/app', { replace: true });
                    });
                }}
              >
                Delete project
              </button>
            </Panel>
          </div>
          {project.status === 'READY' && <AnalysisPanel projectId={id} />}
        </>
      )}
    </section>
  );
}
