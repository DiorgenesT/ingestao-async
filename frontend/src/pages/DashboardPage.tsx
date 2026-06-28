import { useCallback, useEffect, useState } from "react";
import { BarChart } from "../components/BarChart";
import { StatusBadge } from "../components/StatusBadge";
import { deletarJob, listarJobs, logout } from "../services/api";
import type { Job, StatusJob } from "../types";

interface Props {
  onLogout: () => void;
  onNovoJob: () => void;
}

function contarPorStatus(jobs: Job[]): Partial<Record<StatusJob, number>> {
  const contagens: Partial<Record<StatusJob, number>> = {};
  for (const job of jobs) {
    contagens[job.status] = (contagens[job.status] ?? 0) + 1;
  }
  return contagens;
}

export function DashboardPage({ onLogout, onNovoJob }: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const carregar = useCallback(async () => {
    try {
      setErro(null);
      const resp = await listarJobs();
      setJobs(resp.items);
      setTotal(resp.total);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao carregar jobs");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
    const intervalo = setInterval(() => { void carregar(); }, 5000);
    return () => clearInterval(intervalo);
  }, [carregar]);

  async function handleDeletar(id: string) {
    await deletarJob(id);
    void carregar();
  }

  function handleLogout() {
    logout();
    onLogout();
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-900">ingestao-async</h1>
        <div className="flex gap-3">
          <button
            onClick={onNovoJob}
            className="bg-blue-600 text-white rounded-lg px-4 py-1.5 text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Novo job
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 hover:text-gray-900 focus:outline-none"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6 space-y-6">
        <section aria-label="Distribuicao de jobs por status">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Distribuicao por status
          </h2>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <BarChart contagens={contarPorStatus(jobs)} />
          </div>
        </section>

        <section aria-label="Lista de jobs">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
              Jobs ({total})
            </h2>
            <button
              onClick={() => { void carregar(); }}
              className="text-xs text-blue-600 hover:underline focus:outline-none"
            >
              Atualizar
            </button>
          </div>

          {carregando && (
            <p className="text-sm text-gray-500 text-center py-8">Carregando...</p>
          )}

          {erro && (
            <p role="alert" className="text-sm text-red-600 text-center py-4">
              {erro}
            </p>
          )}

          {!carregando && jobs.length === 0 && !erro && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <p className="text-sm text-gray-500">Nenhum job encontrado.</p>
              <button
                onClick={onNovoJob}
                className="mt-3 text-sm text-blue-600 hover:underline focus:outline-none"
              >
                Criar o primeiro job
              </button>
            </div>
          )}

          {jobs.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
              {jobs.map((job) => (
                <div key={job.id} className="px-4 py-3 space-y-1.5">
                  <div className="flex items-center gap-3">
                    <StatusBadge status={job.status} />
                    <span className="text-xs font-mono text-gray-400 uppercase">{job.tipo}</span>
                    <span className="text-xs text-gray-500 font-mono truncate flex-1">{job.id}</span>
                    <span className="text-xs text-gray-400 shrink-0">
                      {new Date(job.criado_em).toLocaleString("pt-BR")}
                    </span>
                    <button
                      onClick={() => { void handleDeletar(job.id); }}
                      className="text-xs text-red-400 hover:text-red-600 focus:outline-none shrink-0"
                      aria-label="Excluir job"
                    >
                      Excluir
                    </button>
                  </div>
                  {job.resumo && (
                    <div className="flex flex-wrap gap-x-4 gap-y-1 pl-1 text-xs text-gray-500">
                      <span>
                        <span className="font-medium text-gray-700">{job.resumo.linhas.toLocaleString("pt-BR")}</span> linhas
                      </span>
                      <span>
                        <span className="font-medium text-gray-700">{job.resumo.colunas.length}</span> colunas
                      </span>
                      <span>
                        <span className="font-medium text-gray-700">{(job.resumo.tamanho_bytes / 1024).toFixed(1)}</span> KB
                      </span>
                      <span>
                        <span className="font-medium text-gray-700">{job.resumo.tempo_processamento_segundos}s</span> processamento
                      </span>
                    </div>
                  )}
                  {job.erro && (
                    <p className="text-xs text-red-500 truncate pl-1" title={job.erro}>
                      {job.erro}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
