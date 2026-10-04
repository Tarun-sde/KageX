import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { useEffect, useRef } from 'react';
import { Home } from '../pages/Home';
import { Workspace } from '../pages/Workspace';

export function App() {
  const { pathname } = useLocation();
  const main = useRef<HTMLElement>(null);
  useEffect(() => {
    document.title =
      pathname === '/app' ? 'Workspace — KageX' : 'KageX — Detect the unseen.';
    main.current?.focus();
    window.scrollTo?.(0, 0);
  }, [pathname]);

  return (
    <div className="min-h-screen">
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      <header className="container-shell flex flex-wrap items-center justify-between gap-6 border-b border-line py-7">
        <Link
          to="/"
          aria-label="KageX home"
          className="text-2xl font-semibold tracking-widest"
        >
          KAGE<span className="text-accent">X</span>
        </Link>
        <nav
          aria-label="Main navigation"
          className="flex items-center gap-6 text-sm"
        >
          <NavLink to="/" end>
            Overview
          </NavLink>
          <NavLink to="/app">
            Workspace <span aria-hidden="true">↗</span>
          </NavLink>
        </nav>
      </header>
      <main
        id="main"
        ref={main}
        tabIndex={-1}
        className="container-shell outline-none"
      >
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<Workspace />} />
          <Route
            path="*"
            element={
              <section className="py-24">
                <p className="eyebrow">404 / KageX</p>
                <h1 className="my-6 font-display text-5xl">Page not found.</h1>
                <Link className="button" to="/">
                  Back to overview
                </Link>
              </section>
            }
          />
        </Routes>
      </main>
      <footer className="container-shell flex flex-wrap justify-between gap-4 border-t border-line py-8 text-sm text-muted">
        <p>
          KageX <span aria-hidden="true">/</span> Detect the unseen.
        </p>
        <p>Foundation edition · Static analysis only</p>
      </footer>
    </div>
  );
}
