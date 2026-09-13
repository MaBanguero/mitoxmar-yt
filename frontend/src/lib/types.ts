// Tipos espejo del backend FastAPI (yt-mitoxmar)

export type DispositivoEstado = "inactivo" | "en_tarea" | "trabajando" | "error";

export interface Dispositivo {
  id: string;
  nombre: string;
  estado: DispositivoEstado;
  adb_id: string | null;
  ultima_actualizacion: string | null;
}

export interface Metricas {
  total_esperado: number;
  exitosos: number;
  fallidos: number;
  en_proceso: number;
}

export type TareaEstado =
  | "iniciando"
  | "ejecutando"
  | "deteniendo"
  | "completada"
  | "fallida";

export interface DetalleMetrica {
  tipo: "retencion" | "playlist_video";
  dispositivo_id?: string;
  duracion_s?: number;
  titulo?: string;
  retencion_pct?: number;
}

export interface TareaActiva {
  id: string;
  tipo: string;
  estado: TareaEstado;
  dispositivos_ids: string[];
  metricas: Metricas;
  config: Record<string, unknown>;
  detalle_metricas: DetalleMetrica[];
  fecha_inicio: string;
  fecha_fin: string | null;
}

export interface AdbStatus {
  adb_available: boolean;
  message: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
  tarea_id?: string;
  [key: string]: unknown;
}
