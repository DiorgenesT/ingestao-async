import { useState } from "react";
import { submeterCsv, submeterUrl } from "../services/api";

interface Props {
  onConcluido: () => void;
}

export function SubmitPage({ onConcluido }: Props) {
  const [tipo, setTipo] = useState<"url" | "csv">("url");
  const [url, setUrl] = useState("");
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    setCarregando(true);

    try {
      if (tipo === "url") {
        const resp = await submeterUrl(url, nome);
        setSucesso(`Job enfileirado: ${resp.job_id}`);
        setUrl("");
      } else {
        if (!arquivo) { setErro("Selecione um arquivo CSV"); return; }
        const resp = await submeterCsv(arquivo, nome);
        setSucesso(`Job enfileirado: ${resp.job_id}`);
        setArquivo(null);
      }
      setNome("");
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Erro ao enviar");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Novo job</h1>
        <button
          onClick={onConcluido}
          className="text-sm text-blue-600 hover:underline focus:outline-none"
        >
          Ver jobs
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {(["url", "csv"] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTipo(t); setErro(null); setSucesso(null); }}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              tipo === t
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
        <div>
          <label htmlFor="nome" className="block text-sm font-medium text-gray-700 mb-1">
            Nome do dataset
          </label>
          <input
            id="nome"
            type="text"
            required
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Ex: Precos de combustiveis 2024"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {tipo === "url" ? (
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
              URL do dataset (CSV)
            </label>
            <input
              id="url"
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://dados.gov.br/dataset/exemplo.csv"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        ) : (
          <div>
            <label htmlFor="arquivo" className="block text-sm font-medium text-gray-700 mb-1">
              Arquivo CSV
            </label>
            <input
              id="arquivo"
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setArquivo(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-gray-600 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
        )}

        {erro && (
          <p role="alert" className="text-sm text-red-600">
            {erro}
          </p>
        )}

        {sucesso && (
          <p role="status" className="text-sm text-green-600">
            {sucesso}
          </p>
        )}

        <button
          type="submit"
          disabled={carregando}
          className="w-full bg-blue-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {carregando ? "Enviando..." : "Enfileirar job"}
        </button>
      </form>
    </div>
  );
}
