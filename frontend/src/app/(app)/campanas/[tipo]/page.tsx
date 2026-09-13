"use client";

import { useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { accionById } from "@/lib/acciones";
import { api } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Button, Card } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Input, Textarea, Toggle, Slider } from "@/components/ui/field";
import { DevicePicker } from "@/components/devices/device-picker";
import { ChevronLeft } from "lucide-react";

export default function CampanaFormPage() {
  const params = useParams<{ tipo: string }>();
  const router = useRouter();
  const { toast } = useToast();

  const accion = accionById(params.tipo);
  const [selected, setSelected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [values, setValues] = useState<Record<string, string | number | boolean>>({});

  const defaults = useMemo(() => {
    if (!accion) return {};
    const init: Record<string, string | number | boolean> = {};
    for (const f of accion.fields) {
      if (f.type === "slider") {
        init[f.key] = f.defaultPct ?? f.minPct ?? 0;
      } else if (f.type === "toggle") {
        init[f.key] = f.default ?? false;
      } else if (f.type === "number") {
        init[f.key] = f.default ?? f.min ?? 1;
      } else {
        init[f.key] = f.default ?? "";
      }
    }
    return init;
  }, [accion]);

  if (!accion) {
    return (
      <div className="space-y-4">
        <Link href="/campanas" className="flex items-center gap-1 text-sm font-semibold text-ink-2">
          <ChevronLeft className="h-4 w-4" /> Volver
        </Link>
        <Card className="p-8 text-center text-sm text-ink-2">
          Acción no encontrada.
        </Card>
      </div>
    );
  }

  const setField = (key: string, value: string | number | boolean) =>
    setValues((prev) => ({ ...prev, [key]: value }));

  const submit = async () => {
    // Validar required
    for (const f of accion.fields) {
      if (f.required) {
        const v = values[f.key];
        if (v === undefined || v === "" || v === null) {
          toast("error", "Falta un campo", `Completa: ${f.label}`);
          return;
        }
      }
    }
    if (selected.length === 0) {
      toast("error", "Sin dispositivos", "Selecciona al menos un dispositivo.");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        dispositivos_ids: selected,
      };

      for (const f of accion.fields) {
        let v = values[f.key];
        if (f.type === "textarea") {
          // comentarios / personalizados → lista
          const list = String(v ?? "")
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean);
          payload[f.key] = list;
        } else if (f.type === "slider" || f.type === "number") {
          payload[f.key] = Number(v);
        } else {
          payload[f.key] = v;
        }
      }

      const res = await api[accion.endpoint](payload);
      toast(
        "success",
        "Campaña lanzada",
        `Tarea ${res.tarea_id ? res.tarea_id.slice(0, 8) : ""} en ${selected.length} dispositivo(s).`
      );
      router.push("/tareas");
    } catch (e) {
      toast("error", "Error al lanzar", e instanceof Error ? e.message : undefined);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <Link
        href="/campanas"
        className="inline-flex items-center gap-1 text-sm font-semibold text-ink-2 transition hover:text-ink"
      >
        <ChevronLeft className="h-4 w-4" /> Campañas
      </Link>

      <div className="flex items-center gap-3">
        <span
          className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-white ${accion.color}`}
        >
          <Icon name={accion.icono} className="h-6 w-6" />
        </span>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">
            {accion.nombre}
          </h1>
          <p className="text-sm text-ink-2">{accion.descripcion}</p>
        </div>
      </div>

      {/* Formulario */}
      <Card className="space-y-5 p-4 sm:p-5">
        {accion.fields.map((f) => {
          const value = values[f.key] ?? defaults[f.key];
          switch (f.type) {
            case "url":
              return (
                <Input
                  key={f.key}
                  label={f.label}
                  help={f.help}
                  required={f.required}
                  type="url"
                  inputMode="url"
                  placeholder={f.placeholder}
                  value={String(value ?? "")}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              );
            case "text":
              return (
                <Input
                  key={f.key}
                  label={f.label}
                  help={f.help}
                  required={f.required}
                  placeholder={f.placeholder}
                  value={String(value ?? "")}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              );
            case "number":
              return (
                <Input
                  key={f.key}
                  label={f.label}
                  help={f.help}
                  type="number"
                  min={f.min}
                  max={f.max}
                  value={String(value ?? "")}
                  onChange={(e) => setField(f.key, Number(e.target.value))}
                />
              );
            case "textarea":
              return (
                <Textarea
                  key={f.key}
                  label={f.label}
                  help={f.help}
                  placeholder={f.placeholder}
                  value={String(value ?? "")}
                  onChange={(e) => setField(f.key, e.target.value)}
                />
              );
            case "toggle":
              return (
                <Toggle
                  key={f.key}
                  label={f.label}
                  help={f.help}
                  checked={Boolean(value)}
                  onChange={(v) => setField(f.key, v)}
                />
              );
            case "slider":
              return (
                <Slider
                  key={f.key}
                  label={f.label}
                  min={f.minPct ?? 0}
                  max={f.maxPct ?? 100}
                  value={Number(value)}
                  onChange={(v) => setField(f.key, v)}
                />
              );
            default:
              return null;
          }
        })}

        {/* Divider */}
        <div className="h-px bg-line" />

        <DevicePicker selected={selected} onChange={setSelected} />
      </Card>

      {/* Sticky CTA */}
      <div className="sticky bottom-20 z-10 md:bottom-6">
        <Button
          block
          size="lg"
          loading={submitting}
          onClick={submit}
          className="shadow-pop"
        >
          Lanzar campaña
        </Button>
      </div>
    </div>
  );
}
