"""
Tema visual compartido de Opsis Meter.
Centraliza la paleta de colores, la tipografía y la configuración
global de CustomTkinter para que todas las ventanas sean coherentes.

Paleta oscura sobria (estilo entorno profesional): un único azul de
acción, semánticos contenidos y escala de texto de cuatro niveles.
La tipografía se resuelve en tiempo de ejecución: se usa la primera
fuente disponible de la lista de preferidas.
"""

import customtkinter as ctk

_FUENTES_PREFERIDAS = [
    "Inter",
    "SF Pro Text",
    "Segoe UI Variable Text",
    "Segoe UI",
    "Roboto",
    "Ubuntu",
    "Noto Sans",
    "Helvetica Neue",
    "Arial",
]

COLOR = {
    # Superficies (de más profunda a más elevada)
    "fondo": "#14171C",
    "panel": "#1C2026",
    "panel_hover": "#252A32",
    "panel_oscuro": "#171A1F",
    "panel_video": "#0B0D11",
    "borde": "#2E343D",
    # Azul de acción (primario y acento unificados)
    "primario": "#3B82F6",
    "primario_hover": "#2563EB",
    "acento": "#3B82F6",
    "acento_hover": "#2563EB",
    # Semánticos
    "exito": "#2EA043",
    "exito_hover": "#238636",
    "peligro": "#DA3633",
    "peligro_hover": "#B62324",
    "advertencia": "#D29922",
    "advertencia_hover": "#B8860B",
    # Botones secundarios / controles
    "neutro": "#39414E",
    "neutro_hover": "#46505F",
    # Escala de texto
    "texto": "#E6E8EB",
    "texto_suave": "#A8AEB8",
    "texto_tenue": "#7D8590",
    "texto_apagado": "#636B76",
    "texto_version": "#4F565F",
}

_configurado = False
_familia_resuelta: str | None = None


def configurar_apariencia():
    """Configura el modo y tema de CustomTkinter (idempotente)."""
    global _configurado
    if not _configurado:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        _configurado = True


def _familia() -> str:
    """Primera fuente preferida instalada en el sistema (se cachea)."""
    global _familia_resuelta
    if _familia_resuelta is None:
        try:
            import tkinter.font as tkfont

            disponibles = set(tkfont.families())
            _familia_resuelta = next(
                (f for f in _FUENTES_PREFERIDAS if f in disponibles), "Segoe UI"
            )
        except Exception:
            _familia_resuelta = "Segoe UI"
    return _familia_resuelta


def fuente(tamano: int, peso: str | None = None) -> ctk.CTkFont:
    """Crea una fuente del tema con el tamaño y peso indicados."""
    if peso:
        return ctk.CTkFont(family=_familia(), size=tamano, weight=peso)
    return ctk.CTkFont(family=_familia(), size=tamano)
