import type { Job, JobSubmitResponse, ListaJobsResponse, TokenResponse } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

function salvarTokens(resp: TokenResponse): void {
  localStorage.setItem("access_token", resp.access_token);
  localStorage.setItem("refresh_token", resp.refresh_token);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const resp = await fetch(`${BASE_URL}${path}`, { ...init, headers: { ...headers, ...init?.headers } });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error(String(body["detail"] ?? resp.statusText));
  }

  return resp.json() as Promise<T>;
}

export async function registrar(email: string, senha: string): Promise<void> {
  const resp = await request<TokenResponse>("/api/v1/auth/registrar", {
    method: "POST",
    body: JSON.stringify({ email, senha }),
  });
  salvarTokens(resp);
}

export async function login(email: string, senha: string): Promise<void> {
  const resp = await request<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, senha }),
  });
  salvarTokens(resp);
}

export function logout(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function estaAutenticado(): boolean {
  return Boolean(getToken());
}

export async function listarJobs(limite = 50, offset = 0): Promise<ListaJobsResponse> {
  return request<ListaJobsResponse>(`/api/v1/jobs?limite=${limite}&offset=${offset}`);
}

export async function buscarJob(id: string): Promise<Job> {
  return request<Job>(`/api/v1/jobs/${id}`);
}

export async function deletarJob(id: string): Promise<void> {
  const token = getToken();
  const resp = await fetch(`${BASE_URL}/api/v1/jobs/${id}`, {
    method: "DELETE",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok && resp.status !== 204) {
    const body = await resp.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error(String(body["detail"] ?? resp.statusText));
  }
}

export async function submeterUrl(url: string, nome: string): Promise<JobSubmitResponse> {
  return request<JobSubmitResponse>("/api/v1/jobs/url", {
    method: "POST",
    body: JSON.stringify({ url, nome }),
  });
}

export async function submeterCsv(arquivo: File, nome: string): Promise<JobSubmitResponse> {
  const token = getToken();
  const form = new FormData();
  form.append("arquivo", arquivo);
  form.append("nome", nome);

  const resp = await fetch(`${BASE_URL}/api/v1/jobs/csv`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error(String(body["detail"] ?? resp.statusText));
  }

  return resp.json() as Promise<JobSubmitResponse>;
}
