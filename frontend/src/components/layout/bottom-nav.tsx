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

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 backdrop-blur-md md:hidden">
      <div className="mx-auto grid max-w-lg grid-cols-4">
        {NAV.map((item) => {
          const active =
            pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group flex flex-col items-center gap-1 py-2.5"
            >
              <span
                className={`flex h-8 w-14 items-center justify-center rounded-full transition-all ${active ? "bg-brand-soft text-brand" : "text-ink-3 group-hover:text-ink"}`}
              >
                <Icon className="h-5 w-5" strokeWidth={active ? 2.4 : 2} />
              </span>
              <span
                className={`text-[11px] font-semibold ${active ? "text-brand" : "text-ink-3"}`}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
      {/* safe area */}
      <div className="h-[env(safe-area-inset-bottom)]" />
    </nav>
  );
}
