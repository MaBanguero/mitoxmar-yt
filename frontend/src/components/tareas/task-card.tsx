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

  const detalle = tarea.detalle_metricas ?? [];
  const retenciones = detalle
    .filter((d) => d.tipo === "retencion" && typeof d.retencion_pct === "number")
    .map((d) => d.retencion_pct as number);
  const videos = detalle.filter((d) => d.tipo === "playlist_video");
  const hayDetalle = retenciones.length > 0 || videos.length > 0;

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

      {/* Métricas de detalle: retención (video) o videos reproducidos (playlist) */}
      {hayDetalle && (
        <div className="mt-3 border-t border-line pt-3">
          {retenciones.length > 0 && (
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">
                Retención
              </p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {retenciones.map((p, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-surface px-2 py-0.5 text-[11px] font-semibold text-ink-2"
                  >
                    {p}%
                  </span>
                ))}
              </div>
            </div>
          )}

          {videos.length > 0 && (
            <div className={retenciones.length > 0 ? "mt-3" : ""}>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">
                Videos reproducidos ({videos.length})
              </p>
              <ul className="mt-1.5 space-y-1">
                {videos.map((v, i) => (
                  <li
                    key={i}
                    className="flex items-start justify-between gap-2 text-[11px]"
                  >
                    <span className="min-w-0 truncate text-ink-2">
                      {v.titulo ?? "Sin título"}
                    </span>
                    <span className="shrink-0 font-semibold text-ink">
                      {v.retencion_pct ?? 0}%
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
