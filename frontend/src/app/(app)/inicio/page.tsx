"use client";

import Link from "next/link";
import { useDispositivos, useTareas, useTareasActivas, useAdbStatus } from "@/lib/hooks";
import { ACCIONES } from "@/lib/acciones";
import { Card, Badge, Skeleton, Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { TaskCard } from "@/components/tareas/task-card";
import { ChevronRight } from "lucide-react";

export default function InicioPage() {
  const dispositivos = useDispositivos();
  const tareas = useTareas();
  const activas = useTareasActivas();
  const adb = useAdbStatus();

  const totalDispositivos = dispositivos.data?.length ?? 0;
  const activosDisponibles =
    dispositivos.data?.filter((d) => d.estado === "inactivo").length ?? 0;
  const tareasActivasCount = activas.data?.length ?? 0;
  const tareasCompletadas =
    tareas.data?.filter((t) => t.estado === "completada").length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">
            Hola, Lucas 👋
          </h1>
          <p className="mt-0.5 text-sm text-ink-2">
            Panel de control de automatización YouTube
          </p>
        </div>
        <StatusPill connected={adb.data?.adb_available} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Dispositivos"
          value={totalDispositivos}
          hint={`${activosDisponibles} disponibles`}
          loading={dispositivos.loading}
          icon={<Icon name="Smartphone" />}
          tone="brand"
        />
        <StatCard
          label="Tareas activas"
          value={tareasActivasCount}
          hint="en ejecución"
          loading={activas.loading}
          icon={<Icon name="Rocket" />}
          tone="info"
        />
        <StatCard
          label="Completadas"
          value={tareasCompletadas}
          hint="histórico"
          loading={tareas.loading}
          icon={<Icon name="ListChecks" />}
          tone="ok"
        />
        <StatCard
          label="Acciones"
          value={ACCIONES.length}
          hint="disponibles"
          loading={false}
          icon={<Icon name="Plus" />}
          tone="warn"
        />
      </div>

      {/* Quick launch */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink">Lanzar campaña</h2>
          <Link
            href="/campanas"
            className="flex items-center gap-1 text-sm font-semibold text-brand"
          >
            Ver todas <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          {ACCIONES.slice(0, 6).map((a) => (
            <Link key={a.id} href={`/campanas/${a.id}`}>
              <Card className="flex flex-col items-center gap-2 p-4 text-center transition hover:-translate-y-0.5 hover:shadow-float">
                <span
                  className={`flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br text-white ${a.color}`}
                >
                  <Icon name={a.icono} />
                </span>
                <span className="text-xs font-semibold leading-tight text-ink">
                  {a.nombre}
                </span>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Tareas activas */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink">Tareas activas</h2>
          <Link
            href="/tareas"
            className="flex items-center gap-1 text-sm font-semibold text-brand"
          >
            Ver todas <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
        {activas.loading ? (
          <div className="space-y-3">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-28 w-full" />
          </div>
        ) : activas.data && activas.data.length > 0 ? (
          <div className="space-y-3">
            {activas.data.map((t) => (
              <TaskCard key={t.id} tarea={t} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="Sin tareas en curso"
            message="Lanza una campaña para empezar a automatizar."
            action={
              <Link href="/campanas">
                <Button size="sm" icon={<Icon name="Plus" className="h-4 w-4" />}>
                  Nueva campaña
                </Button>
              </Link>
            }
          />
        )}
      </section>
    </div>
  );
}

function StatusPill({ connected }: { connected?: boolean }) {
  const label = connected ? "Conectado" : "Sin ADB";
  const tone = connected ? "ok" : "err";
  return (
    <Badge tone={tone} dot>
      {label}
    </Badge>
  );
}

function StatCard({
  label,
  value,
  hint,
  loading,
  icon,
  tone,
}: {
  label: string;
  value: number;
  hint: string;
  loading: boolean;
  icon: React.ReactNode;
  tone: "brand" | "info" | "ok" | "warn";
}) {
  const tones: Record<string, string> = {
    brand: "bg-brand-soft text-brand",
    info: "bg-info-soft text-info",
    ok: "bg-ok-soft text-ok",
    warn: "bg-warn-soft text-warn",
  };
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl ${tones[tone]}`}>
          {icon}
        </span>
      </div>
      <div className="mt-3 text-2xl font-bold tracking-tight text-ink">
        {loading ? <Skeleton className="h-7 w-10" /> : value}
      </div>
      <p className="text-sm font-semibold text-ink-2">{label}</p>
      <p className="text-xs text-ink-3">{hint}</p>
    </Card>
  );
}

function EmptyState({
  title,
  message,
  action,
}: {
  title: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-line-strong bg-surface p-8 text-center">
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-1 text-sm text-ink-3">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
