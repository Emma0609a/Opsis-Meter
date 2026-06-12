"""
Mensajes intercambiados entre el proceso de IA y la interfaz gráfica.
Viajan por colas de multiprocessing, así que deben ser serializables.
"""

from dataclasses import dataclass

# Comandos UI -> proceso (tuplas: (comando, *argumentos))
CMD_DETENER = "detener"
CMD_FPS = "fps"


@dataclass
class FrameConteo:
    """Frame anotado (JPEG) con el estado del conteo en ese instante."""

    jpeg: bytes
    total: int
    en_escena: int
    fps: float
    con_ia: bool


@dataclass
class AvisoConteo:
    """Advertencia no fatal (por ejemplo: no hay modelo, modo sin IA)."""

    mensaje: str


@dataclass
class ErrorConteo:
    """Error fatal del proceso de IA; el conteo se detiene."""

    mensaje: str


@dataclass
class FinConteo:
    """Resumen del lote al detener el conteo."""

    total: int
    duracion_segundos: float
    fps_promedio: float
