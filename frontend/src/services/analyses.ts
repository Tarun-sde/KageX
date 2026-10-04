import { apiRequest } from './api';

export type RunStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
export interface AnalysisRun {
  id: string;
  project_id: string;
  status: RunStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  summary: Record<string, unknown>;
  warnings: { code: string; relative_path: string }[];
}
export interface AnalysisEntity {
  id: string;
  language: string;
  entity_type: string;
  relative_path: string;
  qualified_name: string;
  start_line: number;
  end_line: number;
  metrics: Record<string, number | null>;
  analyzer_name: string;
  analyzer_version: string;
  metric_schema_version: string;
  warnings: string[];
}
export interface EntityPage {
  items: AnalysisEntity[];
  total: number;
  offset: number;
  limit: number;
}
function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function run(data: unknown): AnalysisRun {
  if (
    !record(data) ||
    typeof data.id !== 'string' ||
    typeof data.project_id !== 'string' ||
    !['QUEUED', 'RUNNING', 'COMPLETED', 'FAILED'].includes(
      String(data.status),
    ) ||
    typeof data.created_at !== 'string' ||
    !record(data.summary) ||
    !['started_at', 'completed_at', 'error_code', 'error_message'].every(
      (key) => data[key] === null || typeof data[key] === 'string',
    ) ||
    !Array.isArray(data.warnings) ||
    !data.warnings.every(
      (w) =>
        record(w) &&
        typeof w.code === 'string' &&
        typeof w.relative_path === 'string',
    )
  )
    throw new Error('Invalid analysis response');
  return data as unknown as AnalysisRun;
}
const base = (id: string) => `/projects/${encodeURIComponent(id)}/analyses`;
export const active = (status: RunStatus) =>
  status === 'QUEUED' || status === 'RUNNING';
export async function startAnalysis(project: string): Promise<AnalysisRun> {
  return run(await apiRequest(base(project), { method: 'POST' }));
}
export async function listAnalyses(
  project: string,
  offset = 0,
  signal?: AbortSignal,
): Promise<AnalysisRun[]> {
  const data = await apiRequest(`${base(project)}?offset=${offset}`, {
    signal,
  });
  if (!Array.isArray(data)) throw new Error('Invalid analysis history');
  return data.map(run);
}
export async function getAnalysis(
  project: string,
  id: string,
  signal?: AbortSignal,
): Promise<AnalysisRun> {
  return run(
    await apiRequest(`${base(project)}/${encodeURIComponent(id)}`, { signal }),
  );
}
export async function getEntities(
  project: string,
  id: string,
  offset: number,
  language: string,
  signal?: AbortSignal,
): Promise<EntityPage> {
  const query = new URLSearchParams({ offset: String(offset), limit: '50' });
  if (language) query.set('language', language);
  const data = await apiRequest(
    `${base(project)}/${encodeURIComponent(id)}/entities?${query}`,
    { signal },
  );
  if (
    !record(data) ||
    !Number.isInteger(data.total) ||
    !Number.isInteger(data.offset) ||
    !Number.isInteger(data.limit) ||
    !Array.isArray(data.items)
  )
    throw new Error('Invalid entities response');
  for (const item of data.items) {
    if (
      !record(item) ||
      ![
        'id',
        'language',
        'entity_type',
        'relative_path',
        'qualified_name',
        'analyzer_name',
        'analyzer_version',
        'metric_schema_version',
      ].every((key) => typeof item[key] === 'string') ||
      !Number.isInteger(item.start_line) ||
      !Number.isInteger(item.end_line) ||
      !record(item.metrics) ||
      !Object.values(item.metrics).every(
        (v) => v === null || (typeof v === 'number' && Number.isFinite(v)),
      ) ||
      !Array.isArray(item.warnings) ||
      !item.warnings.every((w) => typeof w === 'string')
    )
      throw new Error('Invalid entity');
  }
  return data as unknown as EntityPage;
}
