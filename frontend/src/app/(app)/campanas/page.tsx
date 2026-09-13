"use client";

import Link from "next/link";
import { ACCIONES } from "@/lib/acciones";
import { Card } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { ChevronRight } from "lucide-react";

export default function CampanasPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Campañas</h1>
        <p className="mt-0.5 text-sm text-ink-2">
          Elige una acción para lanzar en tus dispositivos.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {ACCIONES.map((a) => (
          <Link key={a.id} href={`/campanas/${a.id}`}>
            <Card className="flex items-center gap-4 p-4 transition hover:-translate-y-0.5 hover:shadow-float">
              <span
                className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-white ${a.color}`}
              >
                <Icon name={a.icono} className="h-6 w-6" />
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="text-[15px] font-bold text-ink">{a.nombre}</h3>
                <p className="mt-0.5 line-clamp-2 text-xs leading-snug text-ink-2">
                  {a.descripcion}
                </p>
              </div>
              <ChevronRight className="h-5 w-5 shrink-0 text-ink-3" />
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
