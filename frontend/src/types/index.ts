export type StatusJob = "pendente" | "processando" | "concluido" | "falhou" | "morto";

export interface Job {
  id: string;
  tipo: "url" | "csv";
  status: StatusJob;
  tentativas: number;
  erro: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface ListaJobsResponse {
  items: Job[];
  total: number;
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
