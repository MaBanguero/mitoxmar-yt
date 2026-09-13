"use client";

import { useDispositivos } from "@/lib/hooks";
import { Badge, Skeleton } from "@/components/ui/button";
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

export function DevicePicker({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  const { data, loading, error } = useDispositivos();

  if (loading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-err/30 bg-err-soft p-3 text-sm text-err">
        No se pudo cargar la lista de dispositivos. Verifica que el backend esté
        corriendo.
      </div>
    );
  }

  const dispositivos = data ?? [];

  if (dispositivos.length === 0) {
    return (
      <div className="rounded-xl border border-line bg-surface-2 p-5 text-center">
        <p className="text-sm font-semibold text-ink-2">
          No hay dispositivos conectados
        </p>
        <p className="mt-1 text-xs text-ink-3">
          Conecta un dispositivo por USB/ADB y refresca.
        </p>
      </div>
    );
  }

  const allSelected = dispositivos.every((d) => selected.includes(d.id));
  const toggleAll = () =>
    onChange(allSelected ? [] : dispositivos.map((d) => d.id));

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">Dispositivos</span>
        <button
          onClick={toggleAll}
          className="text-xs font-semibold text-brand hover:text-brand-strong"
        >
          {allSelected ? "Deseleccionar todos" : "Seleccionar todos"}
        </button>
      </div>
      <div className="space-y-2">
        {dispositivos.map((d) => (
          <DeviceRow
            key={d.id}
            device={d}
            checked={selected.includes(d.id)}
            onToggle={() =>
              onChange(
                selected.includes(d.id)
                  ? selected.filter((x) => x !== d.id)
                  : [...selected, d.id]
              )
            }
          />
        ))}
      </div>
    </div>
  );
}

export function DeviceRow({
  device,
  checked,
  onToggle,
}: {
  device: Dispositivo;
  checked: boolean;
  onToggle: () => void;
}) {
  const busy = device.estado === "en_tarea" || device.estado === "trabajando";
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left transition ${checked ? "border-brand bg-brand-soft/50" : "border-line bg-surface hover:border-line-strong"} ${busy ? "opacity-70" : ""}`}
    >
      <span
        className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 transition ${checked ? "border-brand bg-brand text-white" : "border-line-strong bg-surface"}`}
      >
        {checked && (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path
              d="M2.5 6.5l2.5 2.5 4.5-5"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
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
    </button>
  );
}
