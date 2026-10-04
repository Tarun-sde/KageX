import { Link } from 'react-router-dom';
import { Panel } from '../components/Panel';

export function Home() {
  return (
    <>
      <section className="grid items-center gap-12 py-20 lg:grid-cols-[1.2fr_1fr] lg:py-28">
        <div>
          <p className="eyebrow">
            <span className="status-dot" aria-hidden="true" /> Code intelligence
            / In development
          </p>
          <h1 className="mt-8 font-display text-6xl leading-[1.03] tracking-tight sm:text-7xl lg:text-8xl">
            Detect <br />
            the <em className="text-accent">unseen.</em>
          </h1>
          <p className="mt-8 max-w-xl text-xl leading-relaxed">
            AI-Powered Software Defect Prediction &amp; Code Risk Analysis
          </p>
          <p className="mt-4 max-w-lg leading-relaxed text-muted">
            A clearer view of code risk, built on static analysis and
            language-specific models. The foundation is here. Analysis comes
            next.
          </p>
          <Link to="/app" className="button button-primary mt-9">
            Open workspace <span aria-hidden="true">↗</span>
          </Link>
        </div>
        <div className="panel relative overflow-hidden p-8 sm:p-10">
          <p className="eyebrow">01 / Foundation</p>
          <div aria-hidden="true" className="signal-field my-10">
            <span />
            <span />
            <span />
          </div>
          <h2 className="font-display text-3xl">Built for a closer look.</h2>
          <p className="mt-4 leading-relaxed text-muted">
            Source stays source. Future analysis will inspect code without
            executing it.
          </p>
          <p className="mt-8 border-t border-line pt-5 text-sm text-accent">
            Application shell ready
          </p>
        </div>
      </section>
      <section
        aria-label="Project principles"
        className="grid gap-6 pb-20 md:grid-cols-2"
      >
        <Panel title="Language matters.">
          <p className="leading-relaxed text-muted">
            Separate models are planned for Java classes, Python functions, and
            JavaScript files. Each prediction must match a validated metric
            schema.
          </p>
        </Panel>
        <Panel title="Evidence before prediction.">
          <p className="leading-relaxed text-muted">
            No invented scores. No silent model substitutions. TypeScript
            prediction remains unavailable in the baseline; static analysis is
            planned.
          </p>
        </Panel>
      </section>
    </>
  );
}
