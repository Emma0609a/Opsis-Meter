"""
Tema visual compartido de Opsis Meter.
Centraliza la paleta de colores, la tipografía y la configuración
global de CustomTkinter para que todas las ventanas sean coherentes.

Paleta oscura con base azul-grisácea: un único azul de acción
("primario" == "acento"), colores semánticos para éxito/peligro/
advertencia y una escala de texto de cuatro niveles.
"""

import customtkinter as ctk

FAMILIA_FUENTE = "Segoe UI"

COLOR = {
    # Superficies (de más profunda a más elevada)
    "fondo": "#14171C",
    "panel": "#1C2026",
    "panel_oscuro": "#171A1F",
    "panel_video": "#0B0D11",
    "borde": "#2E343D",
    # Azul de acción (primario y acento unificados)
    "primario": "#4D8DF7",
    "primario_hover": "#3A77DC",
    "acento": "#4D8DF7",
    "acento_hover": "#3A77DC",
    # Semánticos
    "exito": "#3FB950",
    "exito_hover": "#2EA043",
    "peligro": "#E5534B",
    "peligro_hover": "#CB3A32",
    "advertencia": "#E8923A",
    "advertencia_hover": "#CF7E2E",
    # Botones secundarios
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
