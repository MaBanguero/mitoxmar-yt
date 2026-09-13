import threading
import time
import random
from typing import List, Dict, Optional
from api.services.ai_comments_service import AICommentsService, AICommentOptions
from api.services.dispositivo_service import dispositivo_service
from api.services.tareas_service import tareas_service
from api.models import DispositivoEstado, LikesResponse
from api.utils.youtube_automator import YouTubeAutomator

class YoutubeService:
    """
    Servicio singleton para gestionar automaciones de YouTube
    Gestiona threads por dispositivo y estado de ejecución
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Estado de likes
        self.likes_threads: Dict[str, threading.Thread] = {}
        self.likes_detener_flags: Dict[str, threading.Event] = {}
        self.likes_activo = False
        
        # Estado de comentarios
        self.comentarios_threads: Dict[str, threading.Thread] = {}
        self.comentarios_detener_flags: Dict[str, threading.Event] = {}
        
        # Estado de compartidas
        self.compartidas_threads: Dict[str, threading.Thread] = {}
        self.compartidas_detener_flags: Dict[str, threading.Event] = {}
        
        # Estado de suscripciones
        self.suscripciones_threads: Dict[str, threading.Thread] = {}
        self.suscripciones_detener_flags: Dict[str, threading.Event] = {}

        #estado de live
        self.live_threads: Dict[str, threading.Thread] = {}
        self.live_detener_flags: Dict[str, threading.Event] = {}

        # Servicios auxiliares
        self.ai_comments_service = AICommentsService()
        
        self._initialized = True

    def _lanzar_thread_tarea(
        self,
        tarea_id: str,
        dispositivo_id: str,
        detener_flag: threading.Event,
        worker,
        *worker_args
    ) -> threading.Thread:
        """
        Envuelve la ejecución de un worker para asegurar liberación de flags y finalización de tarea.
        """
        tareas_service.registrar_flag(tarea_id, dispositivo_id, detener_flag)

        def runner():
            exito_general = False
            try:
                jitter = random.uniform(1.5, 6.0)
                if detener_flag.wait(jitter):
                    return
                resultado = worker(*worker_args)
                if resultado is None:
                    exito_general = True
                else:
                    exito_general = bool(resultado)
            finally:
                tareas_service.liberar_flag(tarea_id, dispositivo_id)
                tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=exito_general)

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        return thread

    def _resolver_adb_id(self, dispositivo_id: str) -> str:
        """
        Devuelve el ADB ID real del dispositivo a partir del ID hasheado
        """
        dispositivo = dispositivo_service.obtener_dispositivo(dispositivo_id)
        if not dispositivo:
            raise Exception(f"Dispositivo {dispositivo_id} no disponible")
        return dispositivo.adb_id or dispositivo_id
    
    def _should_stop(self, detener_flag: Optional[threading.Event], contexto: str) -> bool:
        if detener_flag and detener_flag.is_set():
            print(f"[YouTubeService] Detención solicitada durante {contexto}.")
            return True
        return False
    
    # ==================== LIKES ====================
    
    def iniciar_likes(
        self,
        dispositivos_ids: List[str],
        link_videos: List[str],
        cantidad_likes: int,
        delay_entre_dispositivos: int,
        intentos_maximos: int,
        tiempo_espera_entre_ciclos: int,
        tiempo_reintento_caducado: int,
        tiempo_limite_ciclo: int,
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> LikesResponse:
        """
        Inicia el proceso de likes en YouTube con threading
        """
        try:
            if self.likes_activo:
                return LikesResponse(
                    success=False,
                    message="Ya hay un proceso de likes activo",
                    dispositivos_activados=0,
                    tarea_id=tarea_id
                )
            
            self.likes_activo = True
            dispositivos_activados = 0
            
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self.likes_detener_flags[dispositivo_id] = detener_flag
                    thread = self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_likes,
                        dispositivo_id,
                        link_videos,
                        cantidad_likes,
                        intentos_maximos,
                        tiempo_espera_entre_ciclos,
                        tiempo_reintento_caducado,
                        tiempo_limite_ciclo,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                    self.likes_threads[dispositivo_id] = thread
                    dispositivos_activados += 1
                    
                    if delay_entre_dispositivos > 0:
                        time.sleep(delay_entre_dispositivos)
                except Exception as device_error:
                    print(f"[YouTube Likes] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            
            return LikesResponse(
                success=True,
                message=f"Proceso de likes iniciado en {dispositivos_activados} dispositivos",
                dispositivos_activados=dispositivos_activados,
                tarea_id=tarea_id
            )
        except Exception as e:
            self.likes_activo = False
            return LikesResponse(
                success=False,
                message=f"Error al iniciar likes: {str(e)}",
                dispositivos_activados=0,
                tarea_id=tarea_id
            )
    
    def detener_likes(self) -> LikesResponse:
        """
        Detiene el proceso de likes en YouTube
        """
        try:
            if not self.likes_activo:
                return LikesResponse(
                    success=False,
                    message="No hay ningún proceso de likes activo",
                    dispositivos_activados=0
                )
            
            # Activar flags de detener
            for flag in self.likes_detener_flags.values():
                flag.set()
            
            # Esperar a que terminen los threads
            for thread in self.likes_threads.values():
                thread.join(timeout=5)
            
            # Limpiar
            self.likes_threads.clear()
            self.likes_detener_flags.clear()
            self.likes_activo = False
            
            return LikesResponse(
                success=True,
                message="Proceso de likes detenido correctamente",
                dispositivos_activados=0
            )
        except Exception as e:
            return LikesResponse(
                success=False,
                message=f"Error al detener likes: {str(e)}",
                dispositivos_activados=0
            )
    
    def _proceso_likes(
        self,
        dispositivo_id: str,
        link_videos: List[str],
        cantidad_likes: int,
        intentos_maximos: int,
        tiempo_espera_entre_ciclos: int,
        tiempo_reintento_caducado: int,
        tiempo_limite_ciclo: int,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        """
        Proceso de likes para un dispositivo especifico utilizando el automator real.
        """
        likes_realizados = 0
        try:
            print(f"[YouTube Likes] Iniciando en dispositivo {dispositivo_id}")

            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)

            for link_index, link_video in enumerate(link_videos, start=1):
                if detener_flag.is_set():
                    break

                print(f"[YouTube Likes] Procesando link {link_index}/{len(link_videos)}: {link_video}")

                for ciclo in range(cantidad_likes):
                    if detener_flag.is_set():
                        break

                    intento = 0
                    exito_ciclo = False

                    while intento < intentos_maximos and not detener_flag.is_set():
                        inicio_ciclo = time.time()
                        try:
                            automator.proceso_likes(link_video, detener_flag=detener_flag)
                            tareas_service.incrementar_completados(tarea_id)
                            likes_realizados += 1
                            exito_ciclo = True
                            break
                        except Exception as e:
                            intento += 1
                            print(f"[YouTube Likes] Error en dispositivo {dispositivo_id} durante el ciclo {ciclo + 1}: {e}")
                            if intento >= intentos_maximos:
                                print(f"[YouTube Likes] Se alcanzo el maximo de intentos para el ciclo {ciclo + 1} en dispositivo {dispositivo_id}")
                                break
                            if detener_flag.wait(tiempo_reintento_caducado):
                                break

                    if not exito_ciclo:
                        break

                    if ciclo < cantidad_likes - 1 and not detener_flag.is_set():
                        duracion_ciclo = time.time() - inicio_ciclo
                        descanso = max(0, min(tiempo_espera_entre_ciclos, max(0, tiempo_limite_ciclo - duracion_ciclo)))
                        if descanso > 0 and detener_flag.wait(descanso):
                            break

                if detener_flag.is_set():
                    break

            if likes_realizados == 0:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)

            print(f"[YouTube Likes] Finalizado en dispositivo {dispositivo_id} con {likes_realizados} likes")

        except Exception as e:
            print(f"[YouTube Likes] Error critico en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0
        return likes_realizados

    
    # ==================== COMENTARIOS ====================
    
    def ejecutar_comentarios(
        self,
        dispositivos_ids: List[str],
        link_videos: List[str],
        contexto: str,
        comentarios_por_dispositivo: int,
        comentarios_personalizados: List[str],
        cambiar_cuentas: bool,
        tarea_id: str,
        ai_overrides: Optional[dict] = None
    ) -> dict:
        """
        Ejecuta comentarios en YouTube
        """
        try:
            ai_options: AICommentOptions | None = None
            if ai_overrides:
                ai_options = self.ai_comments_service.override_options(ai_overrides)

            comentarios_plan = self.ai_comments_service.generate_for_devices(
                dispositivos_ids,
                contexto,
                comentarios_por_dispositivo,
                comentarios_personalizados,
                options=ai_options,
            )

            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self.comentarios_detener_flags[dispositivo_id] = detener_flag
                    comentarios_asignados = comentarios_plan.get(dispositivo_id, [])
                    thread = self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_comentarios,
                        dispositivo_id,
                        link_videos,
                        comentarios_asignados,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                    self.comentarios_threads[dispositivo_id] = thread
                except Exception as device_error:
                    print(f"[YouTube Comentarios] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            
            return {
                "success": True,
                "message": f"Comentarios iniciados en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar comentarios: {str(e)}"
            }
    
    def _proceso_comentarios(
        self,
        dispositivo_id: str,
        link_videos: List[str],
        comentarios_asignados: List[str],
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        total_publicados = 0
        for idx, link_post in enumerate(link_videos, start=1):
            if self._should_stop(detener_flag, "comentarios"):
                break
            print(f"[YouTube Comentarios] Procesando link {idx}/{len(link_videos)}: {link_post}")
            publicados = self._proceso_comentarios_por_link(
                dispositivo_id,
                link_post,
                comentarios_asignados,
                cambiar_cuentas,
                detener_flag,
                tarea_id
            )
            total_publicados += publicados
            if detener_flag.is_set():
                break
        return total_publicados


    def _proceso_comentarios_por_link(
        self,
        dispositivo_id: str,
        link_post: List[str],
        comentarios_asignados: List[str],
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        """
        Proceso de comentarios para un dispositivo utilizando el automator real.
        """
        try:
            print(f"[YouTube Comentarios] Iniciando en dispositivo {dispositivo_id}")

            if not comentarios_asignados:
                print(f"[YouTube Comentarios] Dispositivo {dispositivo_id} sin comentarios asignados")
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
                return 0

            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            publicados = automator.proceso_comentarios(
                link_post,
                comentarios_asignados,
                detener_flag=detener_flag,
            )

            for _ in range(publicados):
                tareas_service.incrementar_completados(tarea_id)

            if publicados > 0:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            print(f"[YouTube Comentarios] Dispositivo {dispositivo_id} publicó {publicados} comentarios")
            return publicados

        except Exception as e:
            print(f"[YouTube Comentarios] Error en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0

    # ==================== COMPARTIDAS ====================
    
    def ejecutar_compartidas(
        self,
        dispositivos_ids: List[str],
        link_videos: List[str],
        cantidad_compartidas: int,
        delay_entre_compartidas: int,
        intentos_maximos: int,
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> dict:
        """
        Ejecuta compartidas en YouTube
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self.compartidas_detener_flags[dispositivo_id] = detener_flag
                    thread = self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_compartidas,
                        dispositivo_id,
                        link_videos,
                        cantidad_compartidas,
                        delay_entre_compartidas,
                        intentos_maximos,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                    self.compartidas_threads[dispositivo_id] = thread
                except Exception as device_error:
                    print(f"[YouTube Compartidas] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            
            return {
                "success": True,
                "message": f"Compartidas iniciadas en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar compartidas: {str(e)}"
            }
    
    def _proceso_compartidas(
        self,
        dispositivo_id: str,
        link_videos: List[str],
        cantidad_compartidas: int,
        delay_entre_compartidas: int,
        intentos_maximos: int,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        compartidas_realizadas = 0
        for idx, link_post in enumerate(link_videos, start=1):
            if self._should_stop(detener_flag, "compartidas"):
                break
            print(f"[YouTube Compartidas] Procesando link {idx}/{len(link_videos)}: {link_post}")
            realizadas = self._proceso_compartidas_por_link(
                dispositivo_id,
                link_post,
                cantidad_compartidas,
                delay_entre_compartidas,
                intentos_maximos,
                cambiar_cuentas,
                detener_flag,
                tarea_id
            )
            compartidas_realizadas += realizadas or 0
            if detener_flag.is_set():
                break
        return compartidas_realizadas


    def _proceso_compartidas_por_link(
        self,
        dispositivo_id: str,
        link_post: str,
        cantidad_compartidas: int,
        delay_entre_compartidas: int,
        intentos_maximos: int,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        """
        Proceso de compartidas para un dispositivo utilizando el automator real.
        """
        compartidas_realizadas = 0
        try:
            print(f"[YouTube Compartidas] Iniciando en dispositivo {dispositivo_id}")

            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            total_ciclos = max(1, cantidad_compartidas)

            for ciclo in range(total_ciclos):
                if detener_flag.is_set():
                    break

                intento = 0
                exito_ciclo = False

                while intento < max(1, intentos_maximos) and not detener_flag.is_set():
                    try:
                        realizadas = automator.proceso_compartidas(link_post, detener_flag=detener_flag) or 0
                        if realizadas <= 0:
                            raise Exception("No se logró completar la compartida")

                        tareas_service.incrementar_completados(tarea_id, incremento=realizadas)
                        compartidas_realizadas += realizadas
                        exito_ciclo = True
                        break
                    except Exception as e:
                        intento += 1
                        print(f"[YouTube Compartidas] Error en dispositivo {dispositivo_id} durante el ciclo {ciclo + 1}: {e}")
                        if intento >= intentos_maximos:
                            print(f"[YouTube Compartidas] Se alcanzó el máximo de intentos para el ciclo {ciclo + 1} en dispositivo {dispositivo_id}")
                            break
                        if detener_flag.wait(max(2, min(10, delay_entre_compartidas))):
                            break

                if not exito_ciclo:
                    break

                if ciclo < total_ciclos - 1 and delay_entre_compartidas > 0 and not detener_flag.is_set():
                    if detener_flag.wait(delay_entre_compartidas):
                        break

            if compartidas_realizadas == 0:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)

            print(f"[YouTube Compartidas] Finalizado en dispositivo {dispositivo_id} con {compartidas_realizadas} compartidas")
            return compartidas_realizadas

        except Exception as e:
            print(f"[YouTube Compartidas] Error crítico en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0
    
    # ==================== SUSCRIPCIONES ====================
    
    def ejecutar_suscripciones(
        self,
        dispositivos_ids: List[str],
        perfil_objetivo: str,
        cantidad_suscripciones: int,
        delay_entre_suscripciones: int,
        intentos_maximos: int,
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> dict:
        """
        Ejecuta suscripciones en YouTube
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    
                    detener_flag = threading.Event()
                    self.suscripciones_detener_flags[dispositivo_id] = detener_flag
                    
                    thread = self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_suscripciones,
                        dispositivo_id,
                        perfil_objetivo,
                        cantidad_suscripciones,
                        delay_entre_suscripciones,
                        intentos_maximos,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                    self.suscripciones_threads[dispositivo_id] = thread
                except Exception as device_error:
                    print(f"[YouTube Suscripciones] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            
            return {
                "success": True,
                "message": f"Suscripciones iniciadas en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar suscripciones: {str(e)}"
            }
    
    def _proceso_suscripciones(
        self,
        dispositivo_id: str,
        perfil_objetivo: str,
        cantidad_suscripciones: int,
        delay_entre_suscripciones: int,
        intentos_maximos: int,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        """
        Proceso de suscripciones para un dispositivo utilizando el automator real.
        """
        suscripciones_realizadas = 0
        try:
            print(f"[YouTube Suscripciones] Iniciando en dispositivo {dispositivo_id}")

            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            total_ciclos = max(1, cantidad_suscripciones)

            for ciclo in range(total_ciclos):
                if detener_flag.is_set():
                    break

                intento = 0
                exito_ciclo = False

                while intento < max(1, intentos_maximos) and not detener_flag.is_set():
                    try:
                        realizadas = automator.proceso_suscripciones(perfil_objetivo, detener_flag=detener_flag) or 0
                        if realizadas <= 0:
                            raise Exception("No se completó la suscripción")

                        tareas_service.incrementar_completados(tarea_id, incremento=realizadas)
                        suscripciones_realizadas += realizadas
                        exito_ciclo = True
                        break
                    except Exception as e:
                        intento += 1
                        print(f"[YouTube Suscripciones] Error en dispositivo {dispositivo_id} durante el ciclo {ciclo + 1}: {e}")
                        if intento >= intentos_maximos:
                            print(f"[YouTube Suscripciones] Se alcanzó el máximo de intentos para el ciclo {ciclo + 1} en dispositivo {dispositivo_id}")
                            break
                        if detener_flag.wait(max(2, min(10, delay_entre_suscripciones))):
                            break

                if not exito_ciclo:
                    break

                if ciclo < total_ciclos - 1 and delay_entre_suscripciones > 0 and not detener_flag.is_set():
                    if detener_flag.wait(delay_entre_suscripciones):
                        break

            if suscripciones_realizadas == 0:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)

            print(f"[YouTube Suscripciones] Finalizado en dispositivo {dispositivo_id} con {suscripciones_realizadas} suscripciones")
            return suscripciones_realizadas

        except Exception as e:
            print(f"[YouTube Suscripciones] Error crítico en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0

    # ==================== CALENTAMIENTO / VIEWS ====================

    def ejecutar_calentamiento(
        self,
        dispositivos_ids: List[str],
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> dict:
        """
        Ejecuta un ciclo de calentamiento en YouTube.
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_calentamiento,
                        dispositivo_id,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                except Exception as device_error:
                    print(f"[YouTube Calentamiento] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            return {
                "success": True,
                "message": f"Calentamiento iniciado en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar calentamiento: {str(e)}"
            }

    def _proceso_calentamiento(
        self,
        dispositivo_id: str,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        try:
            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            automator.proceso_calentamiento(detener_flag=detener_flag)
            tareas_service.incrementar_completados(tarea_id)
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
            return True
        except Exception as e:
            print(f"[YouTube Calentamiento] Error en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return False

    def ejecutar_views(
        self,
        dispositivos_ids: List[str],
        link_videos: List[str],
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        hacer_like: bool,
        hacer_comentario: bool,
        hacer_compartir: bool,
        comentarios: Optional[List[str]],
        tarea_id: str
    ) -> dict:
        """
        Ejecuta reproducciones (retencion) en YouTube.
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_views,
                        dispositivo_id,
                        link_videos,
                        retention_min_pct,
                        retention_max_pct,
                        cambiar_cuentas,
                        hacer_like,
                        hacer_comentario,
                        hacer_compartir,
                        comentarios,
                        detener_flag,
                        tarea_id
                    )
                except Exception as device_error:
                    print(f"[YouTube Views] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            return {
                "success": True,
                "message": f"Views iniciadas en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar views: {str(e)}"
            }

    def _proceso_views(
        self,
        dispositivo_id: str,
        link_videos: List[str],
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        hacer_like: bool,
        hacer_comentario: bool,
        hacer_compartir: bool,
        comentarios: Optional[List[str]],
        detener_flag: threading.Event,
        tarea_id: str
    ):
        sesiones_realizadas = 0
        for idx, link_post in enumerate(link_videos, start=1):
            if self._should_stop(detener_flag, "views"):
                break
            print(f"[YouTube Views] Procesando link {idx}/{len(link_videos)}: {link_post}")
            sesiones = self._proceso_views_por_link(
                dispositivo_id,
                link_post,
                retention_min_pct,
                retention_max_pct,
                cambiar_cuentas,
                hacer_like,
                hacer_comentario,
                hacer_compartir,
                comentarios,
                detener_flag,
                tarea_id
            )
            sesiones_realizadas += sesiones or 0
            if detener_flag.is_set():
                break
        return sesiones_realizadas


    def _proceso_views_por_link(
        self,
        dispositivo_id: str,
        link_post: str,
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        hacer_like: bool,
        hacer_comentario: bool,
        hacer_compartir: bool,
        comentarios: Optional[List[str]],
        detener_flag: threading.Event,
        tarea_id: str
    ):
        try:
            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            sesiones = automator.proceso_views(
                link_post,
                detener_flag=detener_flag,
                retention_min_pct=retention_min_pct,
                retention_max_pct=retention_max_pct,
                hacer_like=hacer_like,
                hacer_comentario=hacer_comentario,
                hacer_compartir=hacer_compartir,
                comentarios=comentarios
            )
            if sesiones > 0:
                tareas_service.incrementar_completados(tarea_id, incremento=sesiones)
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
            else:
                if detener_flag.is_set():
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
                else:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return sesiones
        except Exception as e:
            print(f"[YouTube Views] Error en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0

    def ejecutar_playlist(
        self,
        dispositivos_ids: List[str],
        link_videos: List[str],
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> dict:
        """
        Ejecuta reproducción de playlist en YouTube.
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_playlist,
                        dispositivo_id,
                        link_videos,
                        retention_min_pct,
                        retention_max_pct,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                except Exception as device_error:
                    print(f"[YouTube Playlist] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            return {
                "success": True,
                "message": f"Playlist iniciada en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al reproducir playlist: {str(e)}"
            }

    def _proceso_playlist(
        self,
        dispositivo_id: str,
        link_videos: List[str],
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        playlists_completadas = 0
        for idx, link_post in enumerate(link_videos, start=1):
            if self._should_stop(detener_flag, "reproducir playlist"):
                break
            print(f"[YouTube Playlist] Procesando link {idx}/{len(link_videos)}: {link_post}")
            completados = self._proceso_playlist_por_link(
                dispositivo_id,
                link_post,
                retention_min_pct,
                retention_max_pct,
                cambiar_cuentas,
                detener_flag,
                tarea_id
            )
            playlists_completadas += completados or 0
            if detener_flag.is_set():
                break
        return playlists_completadas

    def _proceso_playlist_por_link(
        self,
        dispositivo_id: str,
        link_post: str,
        retention_min_pct: float,
        retention_max_pct: float,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        try:
            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            completados = automator.proceso_reproducir_playlist(
                link_post,
                detener_flag=detener_flag,
                retention_min_pct=retention_min_pct,
                retention_max_pct=retention_max_pct
            )

            if completados and completados > 0:
                tareas_service.incrementar_completados(tarea_id, incremento=completados)
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return completados or 0

        except Exception as e:
            print(f"[YouTube Playlist] Error en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0

    def ejecutar_max_perfil_views(
        self,
        dispositivos_ids: List[str],
        link_perfil: str,
        cambiar_cuentas: bool,
        tarea_id: str
    ) -> dict:
        """
        Ejecuta el proceso de maximizar perfil en YouTube.
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()

                    self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_max_perfil_views,
                        dispositivo_id,
                        link_perfil,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                except Exception as device_error:
                    print(f"[YouTube Max Perfil] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            return {
                "success": True,
                "message": f"Max Perfil iniciado en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar Max Perfil: {str(e)}"
            }

    def _proceso_max_perfil_views(
        self,
        dispositivo_id: str,
        link_perfil: str,
        cambiar_cuentas: bool,
        detener_flag: threading.Event,
        tarea_id: str
    ):
        try:
            adb_id = self._resolver_adb_id(dispositivo_id)
            automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)
            completados = automator.proceso_maximizar_perfil_views(link_perfil, detener_flag=detener_flag)

            if completados and completados > 0:
                tareas_service.incrementar_completados(tarea_id, incremento=completados)
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
            else:
                dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return completados or 0

        except Exception as e:
            print(f"[YouTube Max Perfil] Error en dispositivo {dispositivo_id}: {str(e)}")
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)
            return 0

    def ejecutar_live(
            self,
            dispositivos_ids: List[str],
            link_videos: List[str],
            duracion_minutos: int,
            cambiar_cuentas: bool,
            tarea_id: str
    ) -> dict:
        """
        Inicia el proceso de visualización de directos (Live) en YouTube
        """
        try:
            for dispositivo_id in dispositivos_ids:
                try:
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.TRABAJANDO)
                    detener_flag = threading.Event()
                    self.live_detener_flags[dispositivo_id] = detener_flag

                    thread = self._lanzar_thread_tarea(
                        tarea_id,
                        dispositivo_id,
                        detener_flag,
                        self._proceso_live,
                        dispositivo_id,
                        link_videos,
                        duracion_minutos,
                        cambiar_cuentas,
                        detener_flag,
                        tarea_id
                    )
                    self.live_threads[dispositivo_id] = thread
                except Exception as device_error:
                    print(f"[YouTube Live] Error preparando dispositivo {dispositivo_id}: {device_error}")
                    tareas_service.liberar_flag(tarea_id, dispositivo_id)
                    tareas_service.marcar_dispositivo_finalizado(tarea_id, exito=False)
                    dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

            return {
                "success": True,
                "message": f"Visualización de Live iniciada en {len(dispositivos_ids)} dispositivos"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al ejecutar Live: {str(e)}"
            }

    def _proceso_live(
            self,
            dispositivo_id: str,
            link_videos: List[str],
            duracion_minutos: int,
            cambiar_cuentas: bool,
            detener_flag: threading.Event,
            tarea_id: str
    ):
        lives_completados = 0
        for idx, link_post in enumerate(link_videos, start=1):
            if self._should_stop(detener_flag, "live"):
                break

            print(f"[YouTube Live] Procesando link {idx}/{len(link_videos)}: {link_post}")

            try:
                adb_id = self._resolver_adb_id(dispositivo_id)
                automator = YouTubeAutomator(adb_id, cambiar_cuentas=cambiar_cuentas)

                # Llamada al método del automator que creamos anteriormente
                completados = automator.proceso_reproducir_live(
                    link_post,
                    duracion_minutos=duracion_minutos,
                    detener_flag=detener_flag
                )

                if completados and completados > 0:
                    tareas_service.incrementar_completados(tarea_id, incremento=completados)
                    lives_completados += completados

            except Exception as e:
                print(f"[YouTube Live] Error en dispositivo {dispositivo_id}: {str(e)}")
                continue

        if lives_completados > 0:
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.INACTIVO)
        else:
            dispositivo_service.actualizar_estado(dispositivo_id, DispositivoEstado.ERROR)

        return lives_completados

    def detener_live(self) -> dict:
        """
        Detiene todos los procesos de visualización de Live activos
        """
        try:
            # Si no hay hilos registrados, no hay nada que detener
            if not self.live_threads:
                return {
                    "success": False,
                    "message": "No hay procesos de Live activos para detener"
                }

            # 1. Activar todos los flags de detener
            # Esto hace que automator.proceso_reproducir_live salga de su bucle
            for dispositivo_id, flag in self.live_detener_flags.items():
                print(f"[YouTube Live] Enviando señal de parada a: {dispositivo_id}")
                flag.set()

            # 2. Esperar brevemente a que los threads finalicen y limpien el estado
            for dispositivo_id, thread in self.live_threads.items():
                if thread.is_alive():
                    thread.join(timeout=3)

            # 3. Limpiar los diccionarios de estado
            self.live_threads.clear()
            self.live_detener_flags.clear()

            return {
                "success": True,
                "message": "Se ha solicitado la detención de todos los directos"
            }
        except Exception as e:
            print(f"[YouTube Live] Error al detener: {e}")
            return {"success": False, "message": str(e)}

# Instancia singleton
youtube_service = YoutubeService()
