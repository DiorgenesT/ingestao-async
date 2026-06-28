import type { StatusJob } from "../types";

const ESTILOS: Record<StatusJob, string> = {
  pendente: "bg-yellow-100 text-yellow-800",
  processando: "bg-blue-100 text-blue-800",
  concluido: "bg-green-100 text-green-800",
  falhou: "bg-red-100 text-red-800",
  morto: "bg-gray-100 text-gray-600",
};

interface Props {
  status: StatusJob;
}

export function StatusBadge({ status }: Props) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${ESTILOS[status]}`}>
      {status}
    </span>
  );
}
