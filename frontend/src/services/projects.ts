import { apiRequest } from './api';

export type SourceType = 'ZIP_UPLOAD' | 'GITHUB';
export interface Project {
  id: string;
  name: string;
  source_type: SourceType;
  status: 'CREATED' | 'READY' | 'FAILED';
  github_url: string | null;
  error_code: string | null;
  file_count: number;
  source_bytes: number;
  created_at: string;
  updated_at: string;
}

function projectResponse(data: unknown): Project {
  if (
    !data ||
    typeof data !== 'object' ||
    !('id' in data) ||
    typeof data.id !== 'string' ||
    !('name' in data) ||
    typeof data.name !== 'string' ||
    !('source_type' in data) ||
    !['ZIP_UPLOAD', 'GITHUB'].includes(String(data.source_type)) ||
    !('status' in data) ||
    !['CREATED', 'READY', 'FAILED'].includes(String(data.status)) ||
    !('file_count' in data) ||
    typeof data.file_count !== 'number' ||
    !('source_bytes' in data) ||
    typeof data.source_bytes !== 'number' ||
    !('created_at' in data) ||
    typeof data.created_at !== 'string' ||
    !('updated_at' in data) ||
    typeof data.updated_at !== 'string' ||
    !('github_url' in data) ||
    (data.github_url !== null && typeof data.github_url !== 'string') ||
    !('error_code' in data) ||
    (data.error_code !== null && typeof data.error_code !== 'string')
  )
    throw new Error('Invalid project response');
  return data as Project;
}

export async function listProjects(
  offset = 0,
  signal?: AbortSignal,
): Promise<Project[]> {
  const data = await apiRequest(`/projects?offset=${offset}`, { signal });
  if (!Array.isArray(data)) throw new Error('Invalid project list');
  return data.map(projectResponse);
}
export async function createProject(
  name: string,
  source_type: SourceType,
): Promise<Project> {
  return projectResponse(
    await apiRequest('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, source_type }),
    }),
  );
}
export async function getProject(
  id: string,
  signal?: AbortSignal,
): Promise<Project> {
  return projectResponse(
    await apiRequest(`/projects/${encodeURIComponent(id)}`, { signal }),
  );
}
export async function renameProject(
  id: string,
  name: string,
): Promise<Project> {
  return projectResponse(
    await apiRequest(`/projects/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    }),
  );
}
export async function deleteProject(id: string): Promise<void> {
  await apiRequest(`/projects/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
export async function uploadSource(id: string, file: File): Promise<Project> {
  return projectResponse(
    await apiRequest(`/projects/${encodeURIComponent(id)}/source/zip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/zip' },
      body: file,
    }),
  );
}
export async function importGitHub(id: string, url: string): Promise<Project> {
  return projectResponse(
    await apiRequest(`/projects/${encodeURIComponent(id)}/source/github`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
  );
}
export async function getUploadLimit(signal?: AbortSignal): Promise<number> {
  const data = await apiRequest('/projects/source-limits', { signal });
  if (
    !data ||
    typeof data !== 'object' ||
    !('max_upload_bytes' in data) ||
    typeof data.max_upload_bytes !== 'number'
  )
    throw new Error('Invalid upload limits');
  return data.max_upload_bytes;
}
