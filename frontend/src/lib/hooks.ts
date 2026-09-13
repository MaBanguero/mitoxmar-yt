"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { AdbStatus, Dispositivo, TareaActiva } from "./types";

function usePolled<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de red");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps]);

  return { data, error, loading, refresh };
}

export function useDispositivos(intervalMs = 5000) {
  return usePolled<Dispositivo[]>(() => api.dispositivos(), intervalMs);
}

export function useAdbStatus(intervalMs = 15000) {
  return usePolled<AdbStatus>(() => api.adbStatus(), intervalMs);
}

export function useTareas(intervalMs = 3000) {
  return usePolled<TareaActiva[]>(() => api.tareas(), intervalMs);
}

export function useTareasActivas(intervalMs = 3000) {
  return usePolled<TareaActiva[]>(() => api.tareasActivas(), intervalMs);
}
