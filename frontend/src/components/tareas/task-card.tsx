"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Badge } from "@/components/ui/button";
import type { TareaActiva, TareaEstado } from "@/lib/types";

const ESTADO_TONE: Record<TareaEstado, "info" | "warn" | "ok" | "err"> = {
  iniciando: "info",
  ejecutando: "warn",
  deteniendo: "warn",
  completada: "ok",
  fallida: "err",
};

const ESTADO_LABEL: Record<TareaEstado, string> = {
  iniciando: "Iniciando",
  ejecutando: "Ejecutando",
  deteniendo: "Deteniendo",
  completada: "Completada",
  fallida: "Fallida",
};

export function TaskCard({ tarea }: { tarea: TareaActiva }) {
  const { toast } = useToast();
  const [cancelling, setCancelling] = useState(false);

  const total = tarea.metricas.total_esperado ?? 0;
  const hechos = tarea.metricas.exitosos + tarea.metricas.fallidos;
  const pct = total > 0 ? Math.min(100, Math.round((hechos / total) * 100)) : 0;
  const activa = ["iniciando", "ejecutando", "deteniendo"].includes(tarea.estado);

  const cancelar = async () => {
    setCancelling(true);
    try {
      const r = await api.cancelarTarea(tarea.id);
      toast("info", "Deteniendo tarea", r.message);
    } catch (e) {
      toast("error", "No se pudo detener", e instanceof Error ? e.message : undefined);
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-sm font-bold capitalize text-ink">
              {tarea.tipo}
            </h3>
            <Badge tone={ESTADO_TONE[tarea.estado]} dot>
              {ESTADO_LABEL[tarea.estado]}
            </Badge>
          </div>
          <p className="mt-0.5 font-mono text-[11px] text-ink-3">
            {tarea.id.slice(0, 8)} · {tarea.dispositivos_ids.length} disp.
          </p>
        </div>
        {activa && (
          <button
            onClick={cancelar}
            disabled={cancelling}
            className="shrink-0 rounded-lg border border-line-strong px-2.5 py-1.5 text-xs font-semibold text-ink-2 transition hover:border-err hover:text-err disabled:opacity-50"
          >
            {cancelling ? "…" : "Detener"}
          </button>
        )}
      </div>

      {/* Progreso */}
      <div className="mt-3">
        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="font-semibold text-ink-2">
            {hechos}/{total} acciones
          </span>
          <span className="font-bold text-ink">{pct}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-brand-glow transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-2 flex gap-3 text-[11px] text-ink-3">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-ok" /> {tarea.metricas.exitosos} ok
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-err" /> {tarea.metricas.fallidos} fallidos
          </span>
        </div>
      </div>
    </div>
  );
}
