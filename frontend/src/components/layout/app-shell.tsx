"use client";

import type { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { BottomNav } from "./bottom-nav";
import { Logo } from "./sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen md:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        {/* Topbar móvil */}
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-surface/95 px-4 backdrop-blur-md md:hidden">
          <Logo small />
        </header>
        {/* Contenido */}
        <main className="mx-auto w-full max-w-3xl px-4 pb-28 pt-4 md:max-w-none md:px-8 md:pb-12 md:pt-8">
          {children}
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
