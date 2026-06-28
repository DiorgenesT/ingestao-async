import { useCallback, useEffect, useState } from "react";
import { BarChart } from "../components/BarChart";
import { StatusBadge } from "../components/StatusBadge";
import { deletarJob, listarJobs, logout } from "../services/api";
import type { Job, StatusJob } from "../types";
import { formatBytes, formatNumero, formatTempo } from "../utils/format";

const COR_ACENTO: Record<StatusJob, string> = {
  pendente: "bg-yellow-400",
  processando: "bg-blue-500",
  concluido: "bg-emerald-500",
  falhou: "bg-red-500",
  morto: "bg-slate-300",
};

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

function formatarData(iso: string): string {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
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

  const contagens = contarPorStatus(jobs);
  const concluidos = contagens.concluido ?? 0;
  const em_fila = (contagens.pendente ?? 0) + (contagens.processando ?? 0);
  const com_erro = (contagens.falhou ?? 0) + (contagens.morto ?? 0);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <header className="bg-slate-900 px-6 py-4 flex items-center justify-between shrink-0">
        <div>
          <p className="text-sm font-semibold text-white leading-none">ingestao-async</p>
          <p className="text-xs text-slate-400 mt-1">Pipeline de ingestao assincrona de dados publicos</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onNovoJob}
            className="bg-indigo-600 text-white rounded-lg px-4 py-1.5 text-sm font-medium hover:bg-indigo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            Novo job
          </button>
          <button
            onClick={handleLogout}
            className="text-sm text-slate-400 hover:text-white transition-colors focus:outline-none"
          >
            Sair
          </button>
        </div>
      </header>

      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-6 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total de jobs", valor: total, cor: "text-slate-800" },
            { label: "Concluidos", valor: concluidos, cor: "text-emerald-600" },
            { label: "Na fila", valor: em_fila, cor: "text-blue-600" },
            { label: "Com erro", valor: com_erro, cor: "text-red-500" },
          ].map(({ label, valor, cor }) => (
            <div key={label} className="bg-white rounded-xl border border-slate-200 p-4">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
              <p className={`text-3xl font-bold mt-1 tabular-nums ${cor}`}>{valor}</p>
            </div>
          ))}
        </div>

        {jobs.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-4">
              Distribuicao por status
            </p>
            <BarChart contagens={contagens} />
          </div>
        )}

        <section aria-label="Lista de jobs">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Jobs ({total})
            </p>
            <button
              onClick={() => { void carregar(); }}
              className="text-xs text-indigo-600 hover:underline focus:outline-none"
            >
              Atualizar
            </button>
          </div>

          {carregando && (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
              <p className="text-sm text-slate-500">Carregando...</p>
            </div>
          )}

          {erro && (
            <p role="alert" className="text-sm text-red-600 text-center py-4">{erro}</p>
          )}

          {!carregando && jobs.length === 0 && !erro && (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
              <p className="text-sm text-slate-500">Nenhum job encontrado.</p>
              <button
                onClick={onNovoJob}
                className="mt-3 text-sm text-indigo-600 hover:underline focus:outline-none"
              >
                Criar o primeiro job
              </button>
            </div>
          )}

          {jobs.length > 0 && (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex"
                >
                  <div className={`w-1 shrink-0 ${COR_ACENTO[job.status]}`} />
                  <div className="flex-1 p-4 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-slate-900 truncate">
                          {job.nome ?? job.id}
                        </p>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          <StatusBadge status={job.status} />
                          <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-medium">
                            {job.tipo.toUpperCase()}
                          </span>
                          {job.tentativas > 1 && (
                            <span className="text-xs text-slate-400">
                              {job.tentativas}x tentativas
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-xs text-slate-400">{formatarData(job.criado_em)}</p>
                        <button
                          onClick={() => { void handleDeletar(job.id); }}
                          className="mt-1.5 text-xs text-red-400 hover:text-red-600 transition-colors focus:outline-none"
                          aria-label="Excluir job"
                        >
                          Excluir
                        </button>
                      </div>
                    </div>

                    {job.resumo && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-slate-100">
                        <div>
                          <p className="text-xs text-slate-400">Registros</p>
                          <p className="text-sm font-semibold text-slate-800 tabular-nums">
                            {formatNumero(job.resumo.linhas)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400">Colunas</p>
                          <p className="text-sm font-semibold text-slate-800 tabular-nums">
                            {job.resumo.colunas.length}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400">Tamanho</p>
                          <p className="text-sm font-semibold text-slate-800">
                            {formatBytes(job.resumo.tamanho_bytes)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400">Processamento</p>
                          <p className="text-sm font-semibold text-slate-800">
                            {formatTempo(job.resumo.tempo_processamento_segundos)}
                          </p>
                        </div>
                      </div>
                    )}

                    {job.resumo?.url && (
                      <a
                        href={job.resumo.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-indigo-500 hover:text-indigo-700 truncate mt-2"
                      >
                        {job.resumo.url}
                      </a>
                    )}

                    {job.erro && (
                      <p className="text-xs text-red-500 mt-2 truncate" title={job.erro}>
                        {job.erro}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
