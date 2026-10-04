import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../app/auth-context';
import { errorMessage } from '../services/api';

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (auth.user) return <Navigate to="/app" replace />;
  const register = mode === 'register';
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setError('');
    setBusy(true);
    try {
      await auth.signIn(mode, {
        email: String(data.get('email')),
        password: String(data.get('password')),
      });
      const state: unknown = location.state;
      const from =
        state &&
        typeof state === 'object' &&
        'from' in state &&
        typeof state.from === 'string' &&
        state.from.startsWith('/app')
          ? state.from
          : '/app';
      navigate(from, { replace: true });
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="mx-auto max-w-lg py-16 sm:py-24">
      <p className="eyebrow">Your private workspace</p>
      <h1 className="my-6 font-display text-5xl">
        {register ? 'Create an account.' : 'Welcome back.'}
      </h1>
      <form
        onSubmit={(event) => {
          void submit(event);
        }}
        className="panel space-y-6 p-6 sm:p-8"
      >
        <label className="field">
          Email
          <input
            name="email"
            type="email"
            autoComplete="email"
            maxLength={254}
            required
          />
        </label>
        <label className="field">
          Password
          <input
            name="password"
            type="password"
            autoComplete={register ? 'new-password' : 'current-password'}
            minLength={12}
            maxLength={128}
            required
            aria-describedby="password-help"
          />
        </label>
        <p id="password-help" className="text-sm text-muted">
          Use 12–128 characters. Passwords are never stored in plain text.
        </p>
        {error && (
          <p role="alert" className="text-accent">
            {error}
          </p>
        )}
        <button
          className="button button-primary"
          disabled={busy || auth.loading}
        >
          {busy ? 'Please wait…' : register ? 'Create account' : 'Sign in'}
        </button>
      </form>
      <p className="mt-6 text-muted">
        {register ? 'Already have an account? ' : 'New to KageX? '}
        <Link
          className="text-accent underline"
          to={register ? '/login' : '/register'}
        >
          {register ? 'Sign in' : 'Create an account'}
        </Link>
      </p>
    </section>
  );
}
