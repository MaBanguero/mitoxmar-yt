"use client";

import { AppShell } from "@/components/layout/app-shell";

export default function GroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppShell>{children}</AppShell>;
}
