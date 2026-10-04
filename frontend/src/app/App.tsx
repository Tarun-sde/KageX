import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import { AuthProvider } from './AuthProvider';
import { useAuth } from './auth-context';
import { AuthPage } from '../pages/AuthPage';
import { ProjectPage } from '../pages/ProjectPage';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { errorMessage } from '../services/api';
import { Home } from '../pages/Home';
import { Workspace } from '../pages/Workspace';

export function App() {
  return (
    <AuthProvider>
      <PageShell />
    </AuthProvider>
  );
}

function PageShell() {
  const auth = useAuth();
  const [logoutError, setLogoutError] = useState('');
  const [loggingOut, setLoggingOut] = useState(false);
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
          {auth.user ? (
            <button
              disabled={loggingOut}
              className="button"
              onClick={() => {
                setLoggingOut(true);
                setLogoutError('');
                void auth
                  .signOut()
                  .catch((error: unknown) =>
                    setLogoutError(errorMessage(error)),
                  )
                  .finally(() => setLoggingOut(false));
              }}
            >
              Sign out
            </button>
          ) : (
            <NavLink to="/login">Sign in</NavLink>
          )}
        </nav>
      </header>
      <main
        id="main"
        ref={main}
        tabIndex={-1}
        className="container-shell outline-none"
      >
        {logoutError && (
          <p role="alert" className="mt-6 text-accent">
            {logoutError}
          </p>
        )}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/login"
            element={<AuthPage key="login" mode="login" />}
          />
          <Route
            path="/register"
            element={<AuthPage key="register" mode="register" />}
          />
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<Workspace />} />
            <Route path="/app/projects/:projectId" element={<ProjectPage />} />
          </Route>
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
        <p>Source preparation · Static analysis only</p>
      </footer>
    </div>
  );
}
