import type { Problem } from './types';

export const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';

export class ProblemError extends Error {
  constructor(public problem: Problem) {
    super(problem.detail || problem.title);
  }
}

export function newTraceId(): string {
  const bytes = new Uint8Array(8);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'X-Correlation-Id': newTraceId(),
      ...(init?.headers ?? {}),
    },
  });
  const text = await response.text();
  const body = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new ProblemError(
      body && body.code
        ? (body as Problem)
        : { title: response.statusText, status: response.status, detail: text, code: 'http_error' },
    );
  }
  return body as T;
}
