"""
Configuración de la aplicación.
Lee las variables de entorno (.env) una sola vez y expone un objeto
inmutable con los parámetros de Supabase y del modelo de IA.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

load_dotenv(RAIZ_PROYECTO / ".env")


@dataclass(frozen=True)
class Configuracion:
    supabase_url: str | None
    supabase_key: str | None
    ruta_modelo: Path | None
    umbral_confianza: float


def _resolver_modelo() -> Path | None:
    """Busca el modelo ONNX: variable OPSIS_MODELO o models/*.onnx."""
    ruta_env = os.getenv("OPSIS_MODELO")
    if ruta_env:
        ruta = Path(ruta_env)
        if not ruta.is_absolute():
            ruta = RAIZ_PROYECTO / ruta
        return ruta if ruta.exists() else None

    carpeta_modelos = RAIZ_PROYECTO / "models"
    if carpeta_modelos.is_dir():
        candidatos = sorted(carpeta_modelos.glob("*.onnx"))
        if candidatos:
            return candidatos[0]
    return None


def cargar_configuracion() -> Configuracion:
    """Construye la configuración a partir del entorno."""
    try:
        umbral = float(os.getenv("OPSIS_CONFIANZA", "0.35"))
    except ValueError:
        umbral = 0.35

    return Configuracion(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY"),
        ruta_modelo=_resolver_modelo(),
        umbral_confianza=umbral,
    )
