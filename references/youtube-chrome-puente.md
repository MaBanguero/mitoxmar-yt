# Selectores confirmados — Puente Chrome → YouTube nativo (yt-mitoxmar)

Verificados en dispositivo real: Samsung Galaxy A55 (SM-A556E), Android 15, Chrome 152.0.7977.82, YouTube app nativa instalada.

## Flujo confirmado (punta a punta)
1. Abrir Chrome desde shell (`am start com.android.chrome`).
2. Click en la barra de direcciones: `com.android.chrome:id/url_bar` (EditText).
3. Escribir el término de búsqueda `youtube` con `set_text()` (NO `send_keys()`, ver pitfalls).
4. Presionar Enter → Google muestra resultados de búsqueda.
5. Click en el TextView cuyo `text == "https://www.youtube.com"`.
6. Se abre la app NATIVA de YouTube (activity `InternalMainActivity`).
7. En la app: click en botón "Buscar" (content-desc `Buscar`, rid `com.google.android.youtube:id/menu_item_view`).
8. Escribir el video ID en `com.google.android.youtube:id/search_edit_text`, Enter.
9. Click en el primer resultado con content-desc que contenga `ver vídeo` (los Shorts dicen `reproducir Short`).
10. El video abre en el reproductor nativo.

## Selectores clave

### Chrome (puente)
| Elemento | Selector | Tipo |
|---|---|---|
| Barra de direcciones | `com.android.chrome:id/url_bar` | EditText |
| Resultado Google "youtube" | `text="https://www.youtube.com"` | TextView |

### YouTube nativo
| Elemento | Selector |
|---|---|
| Botón Buscar (home) | `content-desc="Buscar"` / rid `com.google.android.youtube:id/menu_item_view` |
| Input de búsqueda | `com.google.android.youtube:id/search_edit_text` |
| Resultado video (regular) | `content-desc` contiene `ver vídeo` |
| Resultado Short | `content-desc` contiene `reproducir Short` |
| Reproductor | `com.google.android.youtube:id/watch_player` (cd `Reproductor de vídeo`) |
| Duración total | `com.google.android.youtube:id/time_bar_total_time` |
| Anuncio (progress) | `com.google.android.youtube:id/ad_progress_text` (text `Patrocinado`) |
| Anuncio (like) | cd `ME GUSTA EL ANUNCIO` |

## Comportamiento crítico descubierto
- Escribir una URL de YouTube (`youtube.com`, `www.youtube.com`, `youtube.com/watch?v=...`) en la barra de Chrome y dar Enter abre `m.youtube.com` (web móvil) DENTRO de Chrome. NO abre la app nativa.
- Motivo: la navegación por omnibox NO dispara app-links de Android. Los app-links solo se disparan al hacer CLICK en un enlace dentro de una página.
- Por eso el flujo usa la búsqueda de Google ("youtube") y el CLICK al resultado `https://www.youtube.com`: ese click SÍ dispara app-links y abre la app nativa.
- En m.youtube.com (web) NO aparece botón "Abrir en la app".

## Setup de dispositivo requerido (una vez)
Los app-links de YouTube venían en `Disabled` por defecto. Hay que habilitarlos para que el click al resultado abra la app nativa:
```
adb shell pm set-app-links-user-selection --user 0 --package com.google.android.youtube true youtube.com m.youtube.com youtu.be www.youtube.com
```

## Pitfalls
- `send_keys("youtube", clear=True)` en Chrome dispara AUTOCOMPLETADO: escribe "youtube" pero el omnibox lo rellena con la URL más visitada (p.ej. `youtube.com/watch?v=...`). Usar `set_text()` que escribe el texto exacto sin autocompletar.
- `clear_text()` de uiautomator2 deja la barra vacía (muestra el hint "Busca en Google o escribe una URL") pero el autocompletado se re-dispara al escribir con send_keys. set_text es la vía fiable.
- Al buscar por ID, el primer resultado es SIEMPRE el video correcto (content-desc `... ver vídeo`), pero pueden aparecer Shorts de OTROS canales que mencionan el mismo ID (content-desc `... reproducir Short`). Filtrar por `ver vídeo`.
- El dispositivo puede recibir llamadas/notificaciones durante la automatización (system UI se interpone). Ignorar nodos de `com.android.systemui` y `android:id/*`.
- El resultado "https://www.youtube.com" en Google tarda en cargar y puede variar de formato. El bridge hace POLLING (6 intentos × 4-6s) buscando `text="https://www.youtube.com"` o `content-desc` que contenga "youtube.com".

## Anuncios (skip)
- El botón de saltar anuncio usa content-desc `Saltar anuncio` / `Omitir anuncio` / `Skip ad` (NO el texto exacto "Saltar"). `saltar_anuncio()` hace polling de estos content-desc/texto hasta ~30s.
- Indicadores de anuncio activo: rid `com.google.android.youtube:id/ad_progress_text`, texto `Patrocinado`, cd `ME GUSTA EL ANUNCIO`.
- Durante el anuncio, `time_bar_total_time` NO está disponible (muestra el tiempo del anuncio). Leer la duración del video solo DESPUÉS de saltar/terminar el anuncio.
