import { createContext, useContext } from 'react';
import type { Credentials, User } from '../services/auth';

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string;
  retry: () => void;
  signIn: (mode: 'login' | 'register', data: Credentials) => Promise<void>;
  signOut: () => Promise<void>;
}
export const AuthContext = createContext<AuthState | null>(null);
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error('AuthProvider is required');
  return context;
}
