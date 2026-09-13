import type {
  AdbStatus,
  ApiResponse,
  Dispositivo,
  TareaActiva,
} from "./types";

const BASE = "/api";

async function http<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* noop */
    }
    throw new Error(detail);
  }

  // 204 / empty body
  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const api = {
  // ── Dispositivos ──────────────────────────
  dispositivos: () => http<Dispositivo[]>("/dispositivos"),
  adbStatus: () => http<AdbStatus>("/adb/status"),

  // ── Tareas ────────────────────────────────
  tareas: () => http<TareaActiva[]>("/tareas"),
  tareasActivas: () => http<TareaActiva[]>("/tareas/activas"),
  tarea: (id: string) => http<TareaActiva>(`/tareas/${id}`),
  cancelarTarea: (id: string) =>
    http<{ message: string; dispositivos_notificados: number }>(
      `/tareas/${id}`,
      { method: "DELETE" }
    ),

  // ── Acciones YouTube ──────────────────────
  views: (body: Record<string, unknown>) =>
    http<ApiResponse>("/views/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  playlist: (body: Record<string, unknown>) =>
    http<ApiResponse>("/playlist/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  likes: (body: Record<string, unknown>) =>
    http<ApiResponse>("/likes/youtube/iniciar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  comentarios: (body: Record<string, unknown>) =>
    http<ApiResponse>("/comentarios/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  compartidas: (body: Record<string, unknown>) =>
    http<ApiResponse>("/compartidas/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  suscripciones: (body: Record<string, unknown>) =>
    http<ApiResponse>("/suscripciones/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  calentamiento: (body: Record<string, unknown>) =>
    http<ApiResponse>("/calentamiento/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  maxPerfil: (body: Record<string, unknown>) =>
    http<ApiResponse>("/max-perfil/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  live: (body: Record<string, unknown>) =>
    http<ApiResponse>("/live/youtube/ejecutar", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
