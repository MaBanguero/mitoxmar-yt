// Registro declarativo de acciones de YouTube.
// Cada acción define su metadata (icono, color, descripción) y el schema
// de campos que renderiza el formulario data-driven.

export type FieldType =
  | "url"          // input de URL de video/playlist/canal
  | "text"         // texto corto (contexto)
  | "number"       // número entero
  | "textarea"     // lista de comentarios (uno por línea)
  | "slider"       // porcentaje con min/max (retención)
  | "toggle";      // booleano

export interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  help?: string;
  required?: boolean;
  placeholder?: string;
  default?: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  // para slider
  minPct?: number;
  maxPct?: number;
  defaultPct?: number;
  suffix?: string;
}

export interface AccionDef {
  id: string;
  nombre: string;
  descripcion: string;
  icono: string;       // nombre del icono lucide (mapeado en el componente)
  color: string;       // clase de gradiente tailwind
  accent: string;      // color hex para acentos
  endpoint: "views" | "playlist" | "likes" | "comentarios" | "compartidas"
    | "suscripciones" | "calentamiento" | "maxPerfil" | "live";
  fields: FieldDef[];
  // key del payload que recibe el link principal
  linkKey: string;
  retentionDefaultMin?: number;
  retentionDefaultMax?: number;
}

export const ACCIONES: AccionDef[] = [
  {
    id: "views",
    nombre: "Reproducciones",
    descripcion:
      "Genera vistas con retención variable (30–100%) para maximizar retención, satisfacción y suscripción.",
    icono: "Play",
    color: "from-brand to-brand-glow",
    accent: "#ff0033",
    endpoint: "views",
    linkKey: "link_video",
    retentionDefaultMin: 30,
    retentionDefaultMax: 100,
    fields: [
      {
        key: "link_video",
        label: "Enlace del video",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/watch?v=...",
      },
      {
        key: "retention_min_pct",
        label: "Retención mínima",
        type: "slider",
        minPct: 30,
        maxPct: 100,
        defaultPct: 30,
        suffix: "%",
        help: "Porcentaje mínimo del video que se reproducirá por cuenta.",
      },
      {
        key: "retention_max_pct",
        label: "Retención máxima",
        type: "slider",
        minPct: 30,
        maxPct: 100,
        defaultPct: 100,
        suffix: "%",
        help: "Porcentaje máximo del video que se reproducirá por cuenta.",
      },
      {
        key: "hacer_like",
        label: "Dar like al video",
        type: "toggle",
        default: false,
      },
      {
        key: "hacer_comentario",
        label: "Publicar comentario",
        type: "toggle",
        default: false,
      },
      {
        key: "hacer_compartir",
        label: "Compartir el video",
        type: "toggle",
        default: false,
      },
      {
        key: "comentarios",
        label: "Comentarios a asignar",
        type: "textarea",
        default: "",
        placeholder: "Uno por línea. Se asignan en orden a cada cuenta.",
        help: "Opcional. Si está vacío se usa un banco genérico.",
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
        help: "Cambia de cuenta de YouTube entre cada reproducción.",
      },
    ],
  },
  {
    id: "playlist",
    nombre: "Playlist",
    descripcion:
      "Reproduce una lista completa variando la retención en cada video.",
    icono: "ListVideo",
    color: "from-indigo-500 to-violet-500",
    accent: "#6366f1",
    endpoint: "playlist",
    linkKey: "link_playlist",
    retentionDefaultMin: 5,
    retentionDefaultMax: 100,
    fields: [
      {
        key: "link_playlist",
        label: "Enlace de la playlist",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/playlist?list=...",
      },
      {
        key: "retention_min_pct",
        label: "Retención mínima",
        type: "slider",
        minPct: 5,
        maxPct: 100,
        defaultPct: 5,
        suffix: "%",
      },
      {
        key: "retention_max_pct",
        label: "Retención máxima",
        type: "slider",
        minPct: 5,
        maxPct: 100,
        defaultPct: 100,
        suffix: "%",
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "likes",
    nombre: "Likes",
    descripcion: "Da like al video desde cada cuenta seleccionada.",
    icono: "ThumbsUp",
    color: "from-sky-500 to-cyan-400",
    accent: "#0ea5e9",
    endpoint: "likes",
    linkKey: "link_video",
    fields: [
      {
        key: "link_video",
        label: "Enlace del video",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/watch?v=...",
      },
      {
        key: "cantidad_likes",
        label: "Likes por dispositivo",
        type: "number",
        default: 1,
        min: 1,
        max: 20,
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "comentarios",
    nombre: "Comentarios",
    descripcion:
      "Publica comentarios (IA o personalizados) en el video desde cada cuenta.",
    icono: "MessageCircle",
    color: "from-emerald-500 to-teal-400",
    accent: "#10b981",
    endpoint: "comentarios",
    linkKey: "link_video",
    fields: [
      {
        key: "link_video",
        label: "Enlace del video",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/watch?v=...",
      },
      {
        key: "contexto",
        label: "Contexto para la IA",
        type: "text",
        required: true,
        placeholder: "Video sobre programación en Python",
        help: "Se usa para generar comentarios naturales con DeepSeek.",
      },
      {
        key: "comentarios_por_dispositivo",
        label: "Comentarios por dispositivo",
        type: "number",
        default: 1,
        min: 1,
        max: 10,
      },
      {
        key: "comentarios_personalizados",
        label: "Comentarios personalizados",
        type: "textarea",
        default: "",
        placeholder: "Uno por línea (opcional, reemplaza la IA)",
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "compartidas",
    nombre: "Compartidas",
    descripcion: "Comparte el video desde cada cuenta.",
    icono: "Share2",
    color: "from-amber-500 to-orange-400",
    accent: "#f59e0b",
    endpoint: "compartidas",
    linkKey: "link_video",
    fields: [
      {
        key: "link_video",
        label: "Enlace del video",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/watch?v=...",
      },
      {
        key: "cantidad_compartidas",
        label: "Compartidas por dispositivo",
        type: "number",
        default: 3,
        min: 1,
        max: 20,
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "suscripciones",
    nombre: "Suscripciones",
    descripcion: "Suscribe cada cuenta al canal objetivo.",
    icono: "BellRing",
    color: "from-rose-500 to-pink-500",
    accent: "#f43f5e",
    endpoint: "suscripciones",
    linkKey: "perfil_objetivo",
    fields: [
      {
        key: "perfil_objetivo",
        label: "Perfil / canal objetivo",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/@canal",
      },
      {
        key: "cantidad_suscripciones",
        label: "Suscripciones por dispositivo",
        type: "number",
        default: 1,
        min: 1,
        max: 10,
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "calentamiento",
    nombre: "Calentamiento",
    descripcion:
      "Navega por distintos videos con retención 5–100% para calentar cuentas y evitar detección.",
    icono: "Flame",
    color: "from-orange-500 to-red-500",
    accent: "#f97316",
    endpoint: "calentamiento",
    linkKey: "",
    retentionDefaultMin: 5,
    retentionDefaultMax: 100,
    fields: [
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
        help: "Recorre las cuentas del dispositivo en cada ciclo de calentamiento.",
      },
    ],
  },
  {
    id: "max-perfil",
    nombre: "Maximizar perfil",
    descripcion:
      "Recorre el canal objetivo reproduciendo y dando señales de engagement.",
    icono: "UserRound",
    color: "from-fuchsia-500 to-purple-500",
    accent: "#d946ef",
    endpoint: "maxPerfil",
    linkKey: "link_perfil",
    fields: [
      {
        key: "link_perfil",
        label: "Enlace del perfil / canal",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/@canal",
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
  {
    id: "live",
    nombre: "Directo (Live)",
    descripcion: "Mantiene visualización de un directo durante N minutos.",
    icono: "Radio",
    color: "from-red-600 to-rose-500",
    accent: "#dc2626",
    endpoint: "live",
    linkKey: "link_video",
    fields: [
      {
        key: "link_video",
        label: "Enlace del directo",
        type: "url",
        required: true,
        placeholder: "https://www.youtube.com/watch?v=...",
      },
      {
        key: "duracion_minutos",
        label: "Duración (minutos)",
        type: "number",
        default: 10,
        min: 1,
        max: 180,
      },
      {
        key: "cambiar_cuentas",
        label: "Rotar cuentas",
        type: "toggle",
        default: true,
      },
    ],
  },
];

export const accionById = (id: string): AccionDef | undefined =>
  ACCIONES.find((a) => a.id === id);
