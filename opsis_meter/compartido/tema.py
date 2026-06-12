"""
Tema visual compartido de Opsis Meter.
Centraliza la paleta de colores, la tipografía y la configuración
global de CustomTkinter para que todas las ventanas sean coherentes.
"""

import customtkinter as ctk

FAMILIA_FUENTE = "Segoe UI"

COLOR = {
    "fondo": ("#1a1a1a", "#2b2b2b"),
    "panel": ("#1f1f1f", "#2d2d2d"),
    "panel_oscuro": ("#1a1a1a", "#252525"),
    "panel_video": "#0a0a0a",
    "primario": "#5C9EFF",
    "primario_hover": "#4A8EFF",
    "acento": "#4A90E2",
    "acento_hover": "#357ABD",
    "exito": "#4CAF50",
    "exito_hover": "#45A049",
    "peligro": "#F44336",
    "peligro_hover": "#D32F2F",
    "advertencia": "#FF9800",
    "advertencia_hover": "#F57C00",
    "neutro": "#5C7C9A",
    "neutro_hover": "#4A6B8A",
    "texto": "#D0D0D0",
    "texto_suave": "#A0A0A0",
    "texto_tenue": "#8A8A8A",
    "texto_apagado": "#707070",
    "texto_version": "#666666",
}

_configurado = False


def configurar_apariencia():
    """Configura el modo y tema de CustomTkinter (idempotente)."""
    global _configurado
    if not _configurado:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        _configurado = True


def fuente(tamano: int, peso: str | None = None) -> ctk.CTkFont:
    """Crea una fuente del tema con el tamaño y peso indicados."""
    if peso:
        return ctk.CTkFont(family=FAMILIA_FUENTE, size=tamano, weight=peso)
    return ctk.CTkFont(family=FAMILIA_FUENTE, size=tamano)
