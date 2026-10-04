import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../app/auth-context';

export function ProtectedRoute() {
  const auth = useAuth();
  const location = useLocation();
  if (auth.loading)
    return (
      <p role="status" className="py-16">
        Loading your session…
      </p>
    );
  if (auth.error)
    return (
      <div className="py-16">
        <p role="alert">{auth.error}</p>
        <button className="button mt-4" onClick={auth.retry}>
          Retry connection
        </button>
      </div>
    );
  return auth.user ? (
    <Outlet />
  ) : (
    <Navigate to="/login" replace state={{ from: location.pathname }} />
  );
}
