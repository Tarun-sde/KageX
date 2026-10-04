import { useEffect, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Panel } from '../components/Panel';
import { SystemStatus } from '../components/SystemStatus';
import {
  createProject,
  listProjects,
  type Project,
  type SourceType,
} from '../services/projects';
import { errorMessage } from '../services/api';

export function Workspace() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [offset, setOffset] = useState(0);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void listProjects(offset, controller.signal).then(
      (result) => {
        if (!controller.signal.aborted) {
          setProjects(result);
          setLoading(false);
        }
      },
      (reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(errorMessage(reason));
          setLoading(false);
        }
      },
    );
    return () => controller.abort();
  }, [offset, attempt]);
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true);
    setError('');
    try {
      const project = await createProject(
        String(data.get('name')),
        String(data.get('source_type')) as SourceType,
      );
      navigate(`/app/projects/${project.id}`);
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }
  function page(next: number) {
    setLoading(true);
    setError('');
    setOffset(next);
  }
  return (
    <section className="py-16 sm:py-24">
      <p className="eyebrow">Workspace / Your projects</p>
      <h1 className="mt-6 font-display text-5xl sm:text-6xl">
        Prepare for a <em className="text-accent">closer look.</em>
      </h1>
      <p className="mt-6 text-muted">
        Securely prepare source and extract static metrics without executing
        code.
      </p>
      {error && (
        <p role="alert" className="my-6 text-accent">
          {error}
        </p>
      )}
      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <Panel title="Your projects">
          {loading ? (
            <p role="status">Loading projects…</p>
          ) : projects.length === 0 ? (
            <p className="text-muted">
              No projects on this page. Create a project to get started.
            </p>
          ) : (
            <ul className="space-y-4">
              {projects.map((project) => (
                <li key={project.id} className="border-b border-line pb-4">
                  <Link
                    to={`/app/projects/${project.id}`}
                    className="block break-words text-lg underline"
                  >
                    {project.name}
                  </Link>
                  <p className="mt-2 text-sm text-muted">
                    {project.source_type === 'ZIP_UPLOAD'
                      ? 'ZIP upload'
                      : 'Public GitHub'}{' '}
                    ·{' '}
                    {project.status === 'READY'
                      ? 'Source ready'
                      : project.status === 'FAILED'
                        ? 'Ingestion failed'
                        : 'Awaiting source'}
                  </p>
                </li>
              ))}
            </ul>
          )}
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="button"
              disabled={loading}
              onClick={() => {
                setError('');
                setLoading(true);
                setAttempt((value) => value + 1);
              }}
            >
              Refresh projects
            </button>
            {offset > 0 && (
              <button
                className="button"
                disabled={loading}
                onClick={() => page(Math.max(0, offset - 50))}
              >
                Previous
              </button>
            )}
            {projects.length === 50 && (
              <button
                className="button"
                disabled={loading}
                onClick={() => page(offset + 50)}
              >
                Next
              </button>
            )}
          </div>
        </Panel>
        <Panel title="Create a project">
          <form
            onSubmit={(event) => {
              void create(event);
            }}
            className="space-y-6"
          >
            <label className="field">
              Project name
              <input name="name" required minLength={1} maxLength={100} />
            </label>
            <label className="field">
              Source type
              <select name="source_type">
                <option value="ZIP_UPLOAD">ZIP upload</option>
                <option value="GITHUB">Public GitHub repository</option>
              </select>
            </label>
            <button className="button button-primary" disabled={busy}>
              {busy ? 'Creating…' : 'Create project'}
            </button>
          </form>
        </Panel>
        <SystemStatus />
      </div>
    </section>
  );
}
