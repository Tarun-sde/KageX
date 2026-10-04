import { useEffect, useState, type PropsWithChildren } from 'react';
import {
  authenticate,
  currentUser,
  endSession,
  type User,
} from '../services/auth';
import { ApiError, errorMessage } from '../services/api';
import { AuthContext } from './auth-context';

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void currentUser(controller.signal).then(
      (result) => {
        if (!controller.signal.aborted) {
          setUser(result);
          setLoading(false);
        }
      },
      (reason: unknown) => {
        if (!controller.signal.aborted) {
          setUser(null);
          setLoading(false);
          if (!(reason instanceof ApiError && reason.status === 401))
            setError(errorMessage(reason));
        }
      },
    );
    const expired = () => setUser(null);
    window.addEventListener('kagex:unauthenticated', expired);
    return () => {
      controller.abort();
      window.removeEventListener('kagex:unauthenticated', expired);
    };
  }, [attempt]);
  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        retry: () => {
          setLoading(true);
          setError('');
          setAttempt((value) => value + 1);
        },
        signIn: async (mode, data) => {
          setUser(await authenticate(mode, data));
          setError('');
        },
        signOut: async () => {
          await endSession();
          setUser(null);
        },
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
