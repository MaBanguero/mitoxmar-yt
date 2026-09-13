from fastapi import APIRouter, HTTPException
from typing import List
from api.models import LikesRequest, LikesResponse
from api.services.youtube_service import YoutubeService
from api.services.tareas_service import tareas_service
import os

router = APIRouter()
youtube_service = YoutubeService()


def _normalize_links(primary: str, extras: List[str] | None = None) -> List[str]:
    normalized = []
    if extras:
        normalized.extend([link.strip() for link in extras if isinstance(link, str) and link.strip()])
    primary_clean = (primary or '').strip()
    if primary_clean:
        if not normalized or primary_clean != normalized[0]:
            normalized.insert(0, primary_clean)
    return normalized

# ==================== LIKES ====================

@router.post("/likes/youtube/iniciar", response_model=LikesResponse)
async def iniciar_likes(request: LikesRequest):
    """
    Inicia el proceso de likes en YouTube
    """
    try:
        if not request.dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")
        
        links = _normalize_links(request.link_video, request.link_videos)
        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos un link del video")

        plataforma = (request.plataforma or "youtube").lower()
        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")
        
        # Calcular total esperado
        cuentas_por_dispositivo = int(os.getenv('CUENTAS_POR_DISPOSITIVO', '5'))
        total_esperado = len(request.dispositivos_ids) * cuentas_por_dispositivo * len(links)
        
        # Crear tarea activa
        tarea = await tareas_service.crear_tarea(
            tipo="likes",
            dispositivos_ids=request.dispositivos_ids,
            config={
                "link_video": links[0],
                "link_videos": links,
                "plataforma": plataforma,
                "cantidad_likes": request.cantidad_likes,
                "delay_entre_dispositivos": request.delay_entre_dispositivos,
                "intentos_maximos": request.intentos_maximos,
                "tiempo_espera_entre_ciclos": request.tiempo_espera_entre_ciclos,
                "tiempo_reintento_caducado": request.tiempo_reintento_caducado,
                "tiempo_limite_ciclo": request.tiempo_limite_ciclo,
                "cambiar_cuentas": request.cambiar_cuentas,
            },
            total_esperado=total_esperado
        )
        
        # Actualizar estado a ejecutando
        await tareas_service.actualizar_estado(tarea.id, "ejecutando")
        
        response = youtube_service.iniciar_likes(
            request.dispositivos_ids,
            links,
            request.cantidad_likes,
            request.delay_entre_dispositivos,
            request.intentos_maximos,
            request.tiempo_espera_entre_ciclos,
            request.tiempo_reintento_caducado,
            request.tiempo_limite_ciclo,
            request.cambiar_cuentas,
            tarea_id=tarea.id
        )
        
        if not response.success:
            await tareas_service.finalizar_tarea(tarea.id, exito=False)
        
        return LikesResponse(
            success=response.success,
            message=response.message,
            dispositivos_activados=response.dispositivos_activados,
            tarea_id=tarea.id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/likes/youtube/detener")
async def detener_likes():
    """
    Detiene el proceso de likes en YouTube
    """
    try:
        response = youtube_service.detener_likes()
        return {"success": response.success, "message": response.message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== COMENTARIOS ====================

@router.post("/comentarios/youtube/ejecutar")
async def ejecutar_comentarios(request: dict):
    """
    Ejecuta comentarios en YouTube
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_video = request.get('link_video', '')
        links = _normalize_links(link_video, request.get('link_videos'))
        contexto = request.get('contexto', '').strip()
        comentarios_por_dispositivo = int(request.get('comentarios_por_dispositivo', 1))
        comentarios_personalizados = request.get('comentarios_personalizados', [])
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))
        ai_config = request.get('ai_config', {}) or {}
        if not isinstance(ai_config, dict):
            ai_config = {}
        
        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")
        
        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link del video")

        if not contexto:
            raise HTTPException(status_code=400, detail="Debe proporcionar el contexto para los comentarios")

        if comentarios_por_dispositivo <= 0:
            raise HTTPException(status_code=400, detail="Los comentarios por dispositivo deben ser mayores a cero")
        
        plataforma = (request.get('plataforma') or "youtube").lower()
        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")
        
        # Crear tarea activa
        tarea = await tareas_service.crear_tarea(
            tipo="comentarios",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_video": links[0],
                "link_videos": links,
                "plataforma": plataforma,
                "contexto": contexto,
                "comentarios_por_dispositivo": comentarios_por_dispositivo,
                "comentarios_personalizados": comentarios_personalizados,
                "ai_config": ai_config,
            },
            total_esperado=len(dispositivos_ids) * comentarios_por_dispositivo * len(links)
        )
        
        await tareas_service.actualizar_estado(tarea.id, "ejecutando")
        
        response = youtube_service.ejecutar_comentarios(
            dispositivos_ids,
            links,
            contexto,
            comentarios_por_dispositivo,
            comentarios_personalizados,
            cambiar_cuentas,
            tarea_id=tarea.id,
            ai_overrides=ai_config
        )
        
        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)
        
        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== COMPARTIDAS ====================

@router.post("/compartidas/youtube/ejecutar")
async def ejecutar_compartidas(request: dict):
    """
    Ejecuta compartidas en YouTube
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_video = request.get('link_video', '')
        links = _normalize_links(link_video, request.get('link_videos'))
        cantidad_compartidas = request.get('cantidad_compartidas', 3)
        delay_entre_compartidas = request.get('delay_entre_compartidas', 15)
        intentos_maximos = request.get('intentos_maximos', 5)
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))
        
        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")
        
        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link del video")
        
        plataforma = (request.get('plataforma') or "youtube").lower()
        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")
        
        # Crear tarea activa
        tarea = await tareas_service.crear_tarea(
            tipo="compartidas",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_video": links[0],
                "link_videos": links,
                "plataforma": plataforma,
                "cantidad_compartidas": cantidad_compartidas,
                "delay_entre_compartidas": delay_entre_compartidas,
                "intentos_maximos": intentos_maximos,
            },
            total_esperado=len(dispositivos_ids) * cantidad_compartidas * len(links)
        )
        
        await tareas_service.actualizar_estado(tarea.id, "ejecutando")
        
        response = youtube_service.ejecutar_compartidas(
            dispositivos_ids,
            links,
            cantidad_compartidas,
            delay_entre_compartidas,
            intentos_maximos,
            cambiar_cuentas,
            tarea_id=tarea.id
        )
        
        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)
        
        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SUSCRIPCIONES ====================

@router.post("/suscripciones/youtube/ejecutar")
async def ejecutar_suscripciones(request: dict):
    """
    Ejecuta suscripciones en YouTube
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        perfil_objetivo = request.get('perfil_objetivo', '')
        cantidad_suscripciones = request.get('cantidad_suscripciones', 1)
        delay_entre_suscripciones = request.get('delay_entre_suscripciones', 10)
        intentos_maximos = request.get('intentos_maximos', 5)
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))
        
        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")
        
        if not perfil_objetivo:
            raise HTTPException(status_code=400, detail="Debe proporcionar el perfil objetivo")
        
        plataforma = (request.get('plataforma') or "youtube").lower()
        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")
        
        # Crear tarea activa
        tarea = await tareas_service.crear_tarea(
            tipo="suscripciones",
            dispositivos_ids=dispositivos_ids,
            config={
                "perfil_objetivo": perfil_objetivo,
                "plataforma": plataforma,
                "cantidad_suscripciones": cantidad_suscripciones,
                "delay_entre_suscripciones": delay_entre_suscripciones,
                "intentos_maximos": intentos_maximos,
            },
            total_esperado=len(dispositivos_ids) * cantidad_suscripciones
        )
        
        await tareas_service.actualizar_estado(tarea.id, "ejecutando")
        
        response = youtube_service.ejecutar_suscripciones(
            dispositivos_ids,
            perfil_objetivo,
            cantidad_suscripciones,
            delay_entre_suscripciones,
            intentos_maximos,
            cambiar_cuentas,
            tarea_id=tarea.id
        )
        
        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)
        
        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CALENTAMIENTO ====================

@router.post("/calentamiento/youtube/ejecutar")
async def ejecutar_calentamiento(request: dict):
    """
    Ejecuta un ciclo de calentamiento en YouTube.
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])

        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")

        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))

        tarea = await tareas_service.crear_tarea(
            tipo="calentamiento",
            dispositivos_ids=dispositivos_ids,
            config={"plataforma": "youtube", "cambiar_cuentas": cambiar_cuentas},
            total_esperado=len(dispositivos_ids)
        )

        await tareas_service.actualizar_estado(tarea.id, "ejecutando")

        response = youtube_service.ejecutar_calentamiento(
            dispositivos_ids,
            cambiar_cuentas,
            tarea_id=tarea.id
        )

        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)

        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VIEWS ====================

@router.post("/views/youtube/ejecutar")
async def ejecutar_views(request: dict):
    """
    Ejecuta reproducciones en YouTube.
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_video = request.get('link_video', '')
        links = _normalize_links(link_video, request.get('link_videos'))
        retention_min_pct = float(request.get('retention_min_pct') or request.get('retention_min') or 30)
        retention_max_pct = float(request.get('retention_max_pct') or request.get('retention_max') or 100)
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))
        hacer_like = bool(request.get('hacer_like', False))
        hacer_comentario = bool(request.get('hacer_comentario', False))
        hacer_compartir = bool(request.get('hacer_compartir', False))

        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")

        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link del video")

        tarea = await tareas_service.crear_tarea(
            tipo="views",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_video": links[0],
                "link_videos": links,
                "plataforma": "youtube",
                "retention_min_pct": retention_min_pct,
                "retention_max_pct": retention_max_pct,
                "cambiar_cuentas": cambiar_cuentas,
                "hacer_like": hacer_like,
                "hacer_comentario": hacer_comentario,
                "hacer_compartir": hacer_compartir,
            },
            total_esperado=len(dispositivos_ids) * len(links)
        )

        await tareas_service.actualizar_estado(tarea.id, "ejecutando")

        response = youtube_service.ejecutar_views(
            dispositivos_ids,
            links,
            retention_min_pct,
            retention_max_pct,
            cambiar_cuentas,
            hacer_like,
            hacer_comentario,
            hacer_compartir,
            tarea_id=tarea.id
        )

        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)

        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PLAYLIST ====================

@router.post("/playlist/youtube/ejecutar")
async def ejecutar_playlist(request: dict):
    """
    Ejecuta reproducción de playlist en YouTube.
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_playlist = (request.get('link_playlist') or request.get('link_video') or '').strip()
        links = _normalize_links(link_playlist, request.get('link_videos'))
        retention_min_pct = float(request.get('retention_min_pct') or request.get('retention_min') or 5)
        retention_max_pct = float(request.get('retention_max_pct') or request.get('retention_max') or 100)
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))

        plataforma = (request.get('plataforma') or "youtube").lower()

        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")

        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link de la playlist")

        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")

        tarea = await tareas_service.crear_tarea(
            tipo="playlist",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_playlist": links[0],
                "link_videos": links,
                "plataforma": plataforma,
                "retention_min_pct": retention_min_pct,
                "retention_max_pct": retention_max_pct,
                "cambiar_cuentas": cambiar_cuentas,
            },
            total_esperado=len(dispositivos_ids) * len(links)
        )

        await tareas_service.actualizar_estado(tarea.id, "ejecutando")

        response = youtube_service.ejecutar_playlist(
            dispositivos_ids,
            links,
            retention_min_pct,
            retention_max_pct,
            cambiar_cuentas,
            tarea_id=tarea.id
        )

        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)

        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MAX PERFIL VIEWS ====================

@router.post("/max-perfil/youtube/ejecutar")
async def ejecutar_max_perfil_views(request: dict):
    """
    Ejecuta el proceso de maximizar perfil views en YouTube.
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_perfil = request.get('link_perfil', '').strip()
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))
        plataforma = (request.get('plataforma') or "youtube").lower()

        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")

        if not link_perfil:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link del canal")

        if plataforma != "youtube":
            raise HTTPException(status_code=400, detail="La plataforma debe ser 'youtube' para este endpoint")

        tarea = await tareas_service.crear_tarea(
            tipo="maximizar perfil views",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_perfil": link_perfil,
                "plataforma": plataforma,
            },
            total_esperado=len(dispositivos_ids)
        )

        await tareas_service.actualizar_estado(tarea.id, "ejecutando")

        response = youtube_service.ejecutar_max_perfil_views(
            dispositivos_ids,
            link_perfil,
            cambiar_cuentas,
            tarea_id=tarea.id
        )

        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)

        return {
            **response,
            "tarea_id": tarea.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LIVE ====================

@router.post("/live/youtube/ejecutar")
async def ejecutar_live(request: dict):
    """
    Ejecuta la visualización de un directo (Live) en YouTube.
    """
    try:
        dispositivos_ids = request.get('dispositivos_ids', [])
        link_video = request.get('link_video', '')
        links = _normalize_links(link_video, request.get('link_videos'))

        # Configuración de duración (en minutos)
        duracion_minutos = int(request.get('duracion_minutos', 10))
        cambiar_cuentas = bool(request.get('cambiar_cuentas', True))

        if not dispositivos_ids:
            raise HTTPException(status_code=400, detail="Debe seleccionar al menos un dispositivo")

        if not links:
            raise HTTPException(status_code=400, detail="Debe proporcionar el link del directo")

        # Crear tarea activa para seguimiento en el dashboard
        tarea = await tareas_service.crear_tarea(
            tipo="live",
            dispositivos_ids=dispositivos_ids,
            config={
                "link_video": links[0],
                "link_videos": links,
                "plataforma": "youtube",
                "duracion_minutos": duracion_minutos
            },
            total_esperado=len(dispositivos_ids) * len(links)
        )

        # Marcar como ejecutando
        await tareas_service.actualizar_estado(tarea.id, "ejecutando")

        # Llamada al servicio
        response = youtube_service.ejecutar_live(
            dispositivos_ids,
            links,
            duracion_minutos,
            cambiar_cuentas,
            tarea_id=tarea.id
        )

        if not response.get('success', False):
            await tareas_service.finalizar_tarea(tarea.id, exito=False)

        return {
            **response,
            "tarea_id": tarea.id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/live/youtube/detener")
async def detener_live():
    """
    Detiene el proceso de visualización de Live en todos los dispositivos
    """
    try:
        response = youtube_service.detener_live()
        return {"success": response.success, "message": response.message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


