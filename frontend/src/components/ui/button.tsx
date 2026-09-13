"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
  block?: boolean;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-brand text-white hover:bg-brand-strong active:bg-brand-strong shadow-[0_1px_2px_rgba(224,0,45,0.4)]",
  secondary:
    "bg-surface text-ink border border-line-strong hover:bg-surface-2 active:bg-surface-2",
  ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink",
  danger: "bg-err text-white hover:bg-red-700 active:bg-red-700",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-3.5 text-sm gap-1.5",
  md: "h-11 px-5 text-sm gap-2",
  lg: "h-12 px-6 text-base gap-2",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  icon,
  block = false,
  className = "",
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-[var(--radius-btn)] font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${sizes[size]} ${block ? "w-full" : ""} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <Spinner className="h-4 w-4" />
      ) : (
        icon && <span className="shrink-0">{icon}</span>
      )}
      {children}
    </button>
  );
}

export function Spinner({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function Card({
  children,
  className = "",
  onClick,
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`card ${onClick ? "cursor-pointer transition hover:shadow-float hover:-translate-y-0.5" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
  dot = false,
}: {
  children: ReactNode;
  tone?: "neutral" | "ok" | "warn" | "err" | "info" | "brand";
  dot?: boolean;
}) {
  const tones: Record<string, string> = {
    neutral: "bg-surface-2 text-ink-2 border-line",
    ok: "bg-ok-soft text-ok border-ok/20",
    warn: "bg-warn-soft text-warn border-warn/20",
    err: "bg-err-soft text-err border-err/20",
    info: "bg-info-soft text-info border-info/20",
    brand: "bg-brand-soft text-brand border-brand/20",
  };
  const dots: Record<string, string> = {
    neutral: "bg-ink-3",
    ok: "bg-ok",
    warn: "bg-warn",
    err: "bg-err",
    info: "bg-info",
    brand: "bg-brand",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${tones[tone]}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dots[tone]}`} />}
      {children}
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-lg ${className}`} />;
}
