"use client";

import { useState } from "react";
import Link from "next/link";
import { useTareas } from "@/lib/hooks";
import { Card, Skeleton, Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { TaskCard } from "@/components/tareas/task-card";
import type { TareaEstado } from "@/lib/types";

type Filter = "todas" | TareaEstado;

const FILTERS: { id: Filter; label: string }[] = [
  { id: "todas", label: "Todas" },
  { id: "ejecutando", label: "Activas" },
  { id: "completada", label: "Completadas" },
  { id: "fallida", label: "Fallidas" },
];

export default function TareasPage() {
  const { data, loading, error } = useTareas();
  const [filter, setFilter] = useState<Filter>("todas");

  const tareas = data ?? [];
  const filtered =
    filter === "todas" ? tareas : tareas.filter((t) => t.estado === filter);

  const active = (t: TareaEstado) =>
    ["iniciando", "ejecutando", "deteniendo"].includes(t);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Tareas</h1>
        <p className="mt-0.5 text-sm text-ink-2">
          Historial y progreso de tus campañas.
        </p>
      </div>

      {/* Filtros */}
      <div className="no-scrollbar flex gap-2 overflow-x-auto">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`shrink-0 rounded-full px-4 py-1.5 text-sm font-semibold transition ${filter === f.id ? "bg-brand text-white" : "bg-surface text-ink-2 border border-line hover:border-line-strong"}`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      ) : error ? (
        <Card className="p-6 text-center text-sm text-err">{error}</Card>
      ) : filtered.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-sm font-semibold text-ink">Sin tareas</p>
          <p className="mt-1 text-xs text-ink-3">
            Lanza una campaña para ver su progreso aquí.
          </p>
          <div className="mt-4">
            <Link href="/campanas">
              <Button size="sm" icon={<Icon name="Plus" className="h-4 w-4" />}>
                Nueva campaña
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((t) => (
            <TaskCard key={t.id} tarea={t} />
          ))}
        </div>
      )}
    </div>
  );
}
