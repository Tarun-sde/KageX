import { Panel } from '../components/Panel';
import { SystemStatus } from '../components/SystemStatus';

export function Workspace() {
  return (
    <section className="py-16 sm:py-24">
      <p className="eyebrow">Workspace / Foundation edition</p>
      <h1 className="mt-6 font-display text-5xl sm:text-6xl">
        A place to see <em className="text-accent">more.</em>
      </h1>
      <p className="mt-6 max-w-2xl leading-relaxed text-muted">
        Your KageX workspace is taking shape. Analysis features are not yet
        available.
      </p>
      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <Panel title="No analyses yet">
          <p className="leading-relaxed text-muted">
            Repository import, static metrics, and validated predictions arrive
            in later phases. There are no analysis results to display.
          </p>
          <p className="mt-8 border-t border-line pt-5 text-sm">
            Analysis engine{' '}
            <span className="text-accent">/ Not available yet</span>
          </p>
        </Panel>
        <SystemStatus />
      </div>
    </section>
  );
}
