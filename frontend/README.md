# mitoxmar · Frontend

Panel de control mobile-first para el backend de automatización YouTube (`yt-mitoxmar`).

## Stack

- **Next.js 16** (App Router, Turbopack) + **React 19**
- **TypeScript**
- **Tailwind CSS v4** (design tokens en `@theme`)
- **lucide-react** (iconos)

## Cómo correr

```bash
cd frontend
npm install
cp .env.example .env.local   # ajusta API_URL si el backend no está en :8000
npm run dev                  # http://localhost:3000
```

El backend FastAPI debe estar corriendo en `http://localhost:8000` (o la URL
configurada en `API_URL`). Las llamadas a `/api/*` se hacen proxy a través de
`next.config.ts` (`rewrites`), así no hay CORS ni se expone la URL del backend.

## Estructura

```
src/
  app/
    layout.tsx                 # layout raíz (fuentes, ToastProvider, viewport)
    page.tsx                   # redirect → /inicio
    (app)/                     # grupo con AppShell (nav)
      layout.tsx
      inicio/page.tsx          # dashboard (stats + quick launch + activas)
      campanas/page.tsx        # grid de acciones
      campanas/[tipo]/page.tsx # formulario data-driven
      dispositivos/page.tsx    # listado de dispositivos
      tareas/page.tsx          # historial con filtros
  components/
    layout/                    # AppShell, Sidebar, BottomNav
    ui/                        # Button, Card, Badge, Skeleton, Input,
                               # Textarea, Toggle, Slider, Toast, Icon
    devices/device-picker.tsx  # selector multi-dispositivo
    tareas/task-card.tsx       # tarjeta de tarea con progreso + detener
  lib/
    types.ts                   # tipos espejo del backend
    api.ts                     # cliente fetch tipado
    acciones.ts                # registro declarativo de las 9 acciones
    hooks.ts                   # polling (dispositivos/tareas/adb)
```

## Acciones soportadas

`views`, `playlist`, `likes`, `comentarios`, `compartidas`, `suscripciones`,
`calentamiento`, `max-perfil`, `live`.

Cada acción se declara una sola vez en `src/lib/acciones.ts` (metadata + schema
de campos). El formulario de `/campanas/[tipo]` lo renderiza de forma
data-driven, así agregar/editar un campo es solo tocar ese archivo.

## UX

- Mobile-first: bottom nav en móvil, sidebar en desktop.
- Toasts de éxito/error, skeletons de carga, polling automático (3–15s).
- Retención configurable con sliders (30–100% views, 5–100% calentamiento).
- Toggle `cambiar_cuentas` en todas las acciones (rotación de cuentas).
- Selección explícita de like/comentario/compartir en views.
