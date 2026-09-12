from pydantic import BaseModel
from typing import List, Optional, Literal

class SuscripcionesRequest(BaseModel):
    dispositivos_ids: List[str]
    perfil_objetivo: str  # URL del canal de YouTube o perfil de TikTok
    plataforma: Literal['youtube', 'tiktok']
    cantidad_suscripciones: int = 1
    delay_entre_suscripciones: int = 10
    intentos_maximos: int = 5

class SuscripcionesResponse(BaseModel):
    success: bool
    total: int
    exitosos: int
    fallidos: int
    detalles: List[dict]
    tarea_id: Optional[str] = None
