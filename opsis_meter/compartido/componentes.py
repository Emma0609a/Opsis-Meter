"""
Componentes de interfaz reutilizables con el estilo del tema.

Jerarquía de botones de entorno profesional:
- primario:   acción principal de la vista (relleno azul).
- exito:      acción de arranque/confirmación (relleno verde).
- peligro:    acción destructiva o de detención (relleno rojo).
- secundario: acción de apoyo (delineado, fondo transparente).
- fantasma:   acción terciaria (solo texto, hover sutil).
"""

import customtkinter as ctk

from opsis_meter.compartido.tema import COLOR, fuente

_VARIANTES_BOTON = {
    "primario": dict(
        fg_color=COLOR["primario"],
        hover_color=COLOR["primario_hover"],
        text_color="#FFFFFF",
    ),
    "exito": dict(
        fg_color=COLOR["exito"],
        hover_color=COLOR["exito_hover"],
        text_color="#FFFFFF",
    ),
    "peligro": dict(
        fg_color=COLOR["peligro"],
        hover_color=COLOR["peligro_hover"],
        text_color="#FFFFFF",
    ),
    "secundario": dict(
        fg_color="transparent",
        hover_color=COLOR["panel_hover"],
        text_color=COLOR["texto"],
        border_width=1,
        border_color=COLOR["borde"],
    ),
    "fantasma": dict(
        fg_color="transparent",
        hover_color=COLOR["panel_hover"],
        text_color=COLOR["texto_suave"],
    ),
}


def boton(parent, texto, comando, variante="primario", alto=44, tamano=14, **kwargs):
    """Crea un botón con una de las variantes del tema."""
    estilo = {**_VARIANTES_BOTON[variante], **kwargs}
    return ctk.CTkButton(
        parent,
        text=texto,
        command=comando,
        height=alto,
        corner_radius=10,
        font=fuente(tamano, "bold"),
        **estilo,
    )


def tarjeta(parent, **kwargs):
    """Crea un panel tipo tarjeta: fondo elevado, borde sutil."""
    estilo = dict(
        fg_color=COLOR["panel"],
        corner_radius=12,
        border_width=1,
        border_color=COLOR["borde"],
    )
    estilo.update(kwargs)
    return ctk.CTkFrame(parent, **estilo)
