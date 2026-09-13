"""
Base de datos de tracking de acciones ejecutadas en videos por cuenta.

Registra cada accion (vista, like, comentario, compartir, suscripcion) por
(cuenta, video) para evitar repetir acciones (p.ej. no volver a dar like y
terminar quitandolo) y para auditoria.

DB: SQLite (stdlib, sin dependencias). Ruta configurable via TRACKING_DB_PATH.
"""
import os
import sqlite3
import threading
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_PATH = os.path.join(os.path.dirname(_THIS_DIR), "..", "tracking.db")
DB_PATH = os.getenv("TRACKING_DB_PATH", os.path.abspath(_DEFAULT_PATH))

_lock = threading.Lock()


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init():
    with _lock:
        conn = _conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS acciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuenta TEXT NOT NULL,
                dispositivo_id TEXT NOT NULL,
                video_id TEXT NOT NULL,
                accion TEXT NOT NULL,
                valor TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_acciones_lookup ON acciones (cuenta, video_id, accion)"
        )
        conn.commit()
        conn.close()


_init()


def accion_registrada(cuenta: str, video_id: str, accion: str) -> bool:
    """True si la accion ya fue registrada para esa cuenta y video."""
    with _lock:
        conn = _conn()
        cur = conn.execute(
            "SELECT 1 FROM acciones WHERE cuenta=? AND video_id=? AND accion=? LIMIT 1",
            (cuenta, video_id, accion),
        )
        r = cur.fetchone() is not None
        conn.close()
        return r


def registrar_accion(cuenta: str, dispositivo_id: str, video_id: str,
                     accion: str, valor: str = None):
    """Registra una accion ejecutada (idempotente: no duplica)."""
    with _lock:
        conn = _conn()
        ya = conn.execute(
            "SELECT 1 FROM acciones WHERE cuenta=? AND video_id=? AND accion=? LIMIT 1",
            (cuenta, video_id, accion),
        ).fetchone()
        if not ya:
            conn.execute(
                "INSERT INTO acciones (cuenta, dispositivo_id, video_id, accion, valor, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (cuenta, dispositivo_id, video_id, accion, valor, datetime.now().isoformat()),
            )
            conn.commit()
        conn.close()


def listar_acciones(video_id: str = None, cuenta: str = None):
    """Lista acciones (para depuracion/reporte)."""
    with _lock:
        conn = _conn()
        q = "SELECT cuenta, dispositivo_id, video_id, accion, valor, created_at FROM acciones"
        conds, params = [], []
        if video_id:
            conds.append("video_id=?")
            params.append(video_id)
        if cuenta:
            conds.append("cuenta=?")
            params.append(cuenta)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY id DESC"
        cur = conn.execute(q, params)
        rows = cur.fetchall()
        conn.close()
        return rows
