"use client";

import { useId, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";

interface FieldWrapperProps {
  label?: string;
  help?: string;
  required?: boolean;
  children: React.ReactNode;
}

function FieldWrapper({ label, help, required, children }: FieldWrapperProps) {
  return (
    <label className="block">
      {label && (
        <span className="mb-1.5 flex items-center gap-1 text-sm font-semibold text-ink">
          {label}
          {required && <span className="text-brand">*</span>}
        </span>
      )}
      {children}
      {help && <span className="mt-1.5 block text-xs text-ink-3">{help}</span>}
    </label>
  );
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  help?: string;
}

export function Input({ label, help, required, className = "", ...rest }: InputProps) {
  return (
    <FieldWrapper label={label} help={help} required={required}>
      <input
        className={`h-11 w-full rounded-[var(--radius-input)] border border-line-strong bg-surface px-3.5 text-[15px] text-ink placeholder:text-ink-3 transition focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none ${className}`}
        required={required}
        {...rest}
      />
    </FieldWrapper>
  );
}

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  help?: string;
}

export function Textarea({
  label,
  help,
  required,
  className = "",
  rows = 4,
  ...rest
}: TextareaProps) {
  return (
    <FieldWrapper label={label} help={help} required={required}>
      <textarea
        rows={rows}
        className={`w-full resize-y rounded-[var(--radius-input)] border border-line-strong bg-surface px-3.5 py-3 text-[15px] text-ink placeholder:text-ink-3 transition focus:border-brand focus:ring-2 focus:ring-brand/20 focus:outline-none ${className}`}
        required={required}
        {...rest}
      />
    </FieldWrapper>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
  help,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  help?: string;
}) {
  const id = useId();
  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <div className="min-w-0">
        <label htmlFor={id} className="text-sm font-semibold text-ink">
          {label}
        </label>
        {help && <p className="text-xs text-ink-3">{help}</p>}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-7 w-12 shrink-0 rounded-full transition-colors duration-200 ${checked ? "bg-brand" : "bg-line-strong"}`}
      >
        <span
          className={`absolute top-0.5 h-6 w-6 rounded-full bg-white shadow transition-all duration-200 ${checked ? "left-[22px]" : "left-0.5"}`}
        />
      </button>
    </div>
  );
}

export function Slider({
  value,
  onChange,
  label,
  min,
  max,
  step = 1,
  suffix = "%",
}: {
  value: number;
  onChange: (v: number) => void;
  label: string;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">{label}</span>
        <span className="rounded-lg bg-brand-soft px-2 py-0.5 text-sm font-bold text-brand">
          {value}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-line-strong accent-brand"
        style={{
          background: `linear-gradient(to right, var(--color-brand) ${pct}%, var(--color-line-strong) ${pct}%)`,
        }}
      />
    </div>
  );
}
