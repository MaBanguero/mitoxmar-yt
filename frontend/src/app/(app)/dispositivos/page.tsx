"use client";

import { useDispositivos, useAdbStatus } from "@/lib/hooks";
import { Badge, Card, Skeleton } from "@/components/ui/button";
import type { Dispositivo, DispositivoEstado } from "@/lib/types";

const ESTADO_LABEL: Record<DispositivoEstado, string> = {
  inactivo: "Disponible",
  en_tarea: "En tarea",
  trabajando: "Trabajando",
  error: "Error",
};

const ESTADO_TONE: Record<DispositivoEstado, "ok" | "info" | "warn" | "err"> = {
  inactivo: "ok",
  en_tarea: "info",
  trabajando: "warn",
  error: "err",
};

export default function DispositivosPage() {
  const { data, loading, error } = useDispositivos();
  const adb = useAdbStatus();

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">
            Dispositivos
          </h1>
          <p className="mt-0.5 text-sm text-ink-2">{data?.length ?? 0} conectados</p>
        </div>
        <Badge tone={adb.data?.adb_available ? "ok" : "err"} dot>
          {adb.data?.adb_available ? "ADB activo" : "ADB sin conexión"}
        </Badge>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : error ? (
        <Card className="p-6 text-center text-sm text-err">
          No se pudo conectar con el backend: {error}
        </Card>
      ) : !data || data.length === 0 ? (
        <Card className="p-8 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-2 text-ink-3">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <rect x="6" y="2" width="12" height="20" rx="3" strokeWidth="1.8" />
              <path d="M11 18h2" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-ink">Sin dispositivos</p>
          <p className="mt-1 text-xs text-ink-3">
            Conecta un dispositivo por USB o red y refresca.
          </p>
        </Card>
      ) : (
        <div className="space-y-2">
          {data.map((d) => (
            <DeviceDisplayRow key={d.id} device={d} />
          ))}
        </div>
      )}
    </div>
  );
}

function DeviceDisplayRow({ device }: { device: Dispositivo }) {
  return (
    <Card className="flex items-center gap-3 p-3.5">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-ink-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <rect x="6" y="2" width="12" height="20" rx="3" strokeWidth="1.8" />
          <path d="M11 18h2" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-ink">
          {device.nombre}
        </span>
        <span className="block truncate font-mono text-[11px] text-ink-3">
          {device.adb_id ?? device.id}
        </span>
      </span>
      <Badge tone={ESTADO_TONE[device.estado]} dot>
        {ESTADO_LABEL[device.estado]}
      </Badge>
    </Card>
  );
}
