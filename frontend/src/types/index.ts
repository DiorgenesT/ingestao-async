export type StatusJob = "pendente" | "processando" | "concluido" | "falhou" | "morto";

export interface ResumoDataset {
  linhas: number;
  colunas: string[];
  tamanho_bytes: number;
  tempo_processamento_segundos: number;
  processado_em: string;
  url?: string;
}

export interface Job {
  id: string;
  tipo: "url" | "csv";
  status: StatusJob;
  tentativas: number;
  erro: string | null;
  criado_em: string;
  atualizado_em: string;
  resumo: ResumoDataset | null;
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
