import type { StatusJob } from "../types";

const CORES: Record<StatusJob, string> = {
  pendente: "#fbbf24",
  processando: "#60a5fa",
  concluido: "#34d399",
  falhou: "#f87171",
  morto: "#9ca3af",
};

interface Props {
  contagens: Partial<Record<StatusJob, number>>;
}

const STATUS_ORDEM: StatusJob[] = ["pendente", "processando", "concluido", "falhou", "morto"];

export function BarChart({ contagens }: Props) {
  const dados = STATUS_ORDEM.map((s) => ({ status: s, valor: contagens[s] ?? 0 }));
  const maximo = Math.max(...dados.map((d) => d.valor), 1);

  const largura = 400;
  const altura = 160;
  const paddingEsq = 32;
  const paddingDir = 16;
  const paddingTop = 16;
  const paddingBase = 32;
  const areaLarg = largura - paddingEsq - paddingDir;
  const areaAltura = altura - paddingTop - paddingBase;
  const largBarra = areaLarg / dados.length;
  const espacoBarra = largBarra * 0.6;
  const offsetBarra = (largBarra - espacoBarra) / 2;

  return (
    <svg
      viewBox={`0 0 ${largura} ${altura}`}
      width="100%"
      aria-label="Grafico de barras de jobs por status"
      role="img"
    >
      {/* Linhas de referencia */}
      {[0, 0.5, 1].map((frac) => {
        const y = paddingTop + areaAltura * (1 - frac);
        return (
          <g key={frac}>
            <line x1={paddingEsq} y1={y} x2={largura - paddingDir} y2={y} stroke="#e5e7eb" strokeWidth={1} />
            <text x={paddingEsq - 4} y={y + 4} textAnchor="end" fontSize={10} fill="#9ca3af">
              {Math.round(maximo * frac)}
            </text>
          </g>
        );
      })}

      {/* Barras */}
      {dados.map(({ status, valor }, i) => {
        const altBarra = (valor / maximo) * areaAltura;
        const x = paddingEsq + i * largBarra + offsetBarra;
        const y = paddingTop + areaAltura - altBarra;

        return (
          <g key={status}>
            <rect x={x} y={y} width={espacoBarra} height={altBarra} fill={CORES[status]} rx={3} />
            <text
              x={x + espacoBarra / 2}
              y={altura - paddingBase + 14}
              textAnchor="middle"
              fontSize={10}
              fill="#6b7280"
            >
              {status.slice(0, 5)}
            </text>
            {valor > 0 && (
              <text x={x + espacoBarra / 2} y={y - 4} textAnchor="middle" fontSize={10} fill="#374151">
                {valor}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
