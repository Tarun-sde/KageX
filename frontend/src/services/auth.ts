import { apiRequest } from './api';

export interface User {
  id: string;
  email: string;
}
export interface Credentials {
  email: string;
  password: string;
}

function userResponse(data: unknown): User {
  if (
    !data ||
    typeof data !== 'object' ||
    !('id' in data) ||
    typeof data.id !== 'string' ||
    !('email' in data) ||
    typeof data.email !== 'string'
  )
    throw new Error('Invalid user response');
  return { id: data.id, email: data.email };
}

export async function currentUser(signal?: AbortSignal): Promise<User> {
  return userResponse(await apiRequest('/auth/me', { signal }));
}
export async function authenticate(
  mode: 'login' | 'register',
  data: Credentials,
): Promise<User> {
  return userResponse(
    await apiRequest(`/auth/${mode}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  );
}
export async function endSession(): Promise<void> {
  await apiRequest('/auth/logout', { method: 'POST' });
}
