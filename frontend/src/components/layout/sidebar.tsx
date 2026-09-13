"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Rocket, Smartphone, ListChecks } from "lucide-react";

const NAV = [
  { href: "/inicio", label: "Inicio", icon: Home },
  { href: "/campanas", label: "Campañas", icon: Rocket },
  { href: "/dispositivos", label: "Dispositivos", icon: Smartphone },
  { href: "/tareas", label: "Tareas", icon: ListChecks },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-line bg-surface md:flex">
      <div className="flex h-16 items-center gap-3 border-b border-line px-5">
        <Logo />
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition ${active ? "bg-brand-soft text-brand" : "text-ink-2 hover:bg-surface-2 hover:text-ink"}`}
            >
              <Icon className="h-5 w-5" strokeWidth={active ? 2.4 : 2} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-line p-4 text-xs text-ink-3">
        yt-mitoxmar · YouTube Master Control
      </div>
    </aside>
  );
}

export function Logo({ small = false }: { small?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-glow shadow-[0_2px_8px_rgba(255,0,51,0.35)]">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
          <path d="M23 7l-1.5 5.5a3 3 0 01-3 2.5H10l-4.5 4v-4H4a3 3 0 01-3-3V6a3 3 0 013-3h16a3 3 0 013 3v1z" />
        </svg>
      </div>
      {!small && (
        <div className="leading-tight">
          <p className="text-[15px] font-bold tracking-tight text-ink">
            mitoxmar
          </p>
          <p className="text-[11px] font-medium text-ink-3">YouTube Control</p>
        </div>
      )}
    </div>
  );
}
