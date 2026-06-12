"""
Vista de Inicio - Opsis Meter
Panel de bienvenida con accesos rápidos e información del sistema.
"""

import customtkinter as ctk

from opsis_meter.compartido.tema import COLOR, fuente


class VistaInicio(ctk.CTkFrame):
    """Panel de inicio dentro de la ventana principal."""

    def __init__(self, parent, controlador):
        super().__init__(parent, fg_color="transparent")
        self.controlador = controlador
        self.crear_widgets()

    def crear_widgets(self):
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=40, pady=32)

        # ===== ENCABEZADO =====
        titulo = ctk.CTkLabel(
            contenido,
            text="Bienvenido a Opsis Meter",
            font=fuente(34, "bold"),
            text_color=COLOR["texto"],
            anchor="w",
        )
        titulo.pack(fill="x")

        subtitulo = ctk.CTkLabel(
            contenido,
            text="Sistema inteligente de conteo de limones para bandas transportadoras",
            font=fuente(15),
            text_color=COLOR["texto_suave"],
            anchor="w",
        )
        subtitulo.pack(fill="x", pady=(4, 28))

        # ===== TARJETAS DE ACCIÓN =====
        tarjetas = ctk.CTkFrame(contenido, fg_color="transparent")
        tarjetas.pack(fill="x")
        tarjetas.grid_columnconfigure(0, weight=1, uniform="tarjetas")
        tarjetas.grid_columnconfigure(1, weight=1, uniform="tarjetas")

        self._tarjeta_accion(
            tarjetas,
            columna=0,
            titulo="Iniciar Conteo",
            descripcion="Conecta una cámara (local, IP o tu móvil), define la línea "
            "virtual y cuenta en tiempo real con detección y seguimiento por IA.",
            texto_boton="Ir al conteo",
            color=COLOR["exito"],
            color_hover=COLOR["exito_hover"],
            comando=lambda: self.controlador.mostrar_vista("conteo"),
        )

        self._tarjeta_accion(
            tarjetas,
            columna=1,
            titulo="Historial",
            descripcion="Consulta las sesiones registradas, estadísticas generales "
            "y administra los lotes cerrados.",
            texto_boton="Ver historial",
            color=COLOR["primario"],
            color_hover=COLOR["primario_hover"],
            comando=lambda: self.controlador.mostrar_vista("historial"),
        )

        # ===== INFORMACIÓN DEL SISTEMA =====
        info = ctk.CTkFrame(
            contenido,
            fg_color=COLOR["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLOR["borde"],
        )
        info.pack(fill="x", pady=(24, 0))

        info_inner = ctk.CTkFrame(info, fg_color="transparent")
        info_inner.pack(fill="x", padx=24, pady=20)

        info_titulo = ctk.CTkLabel(
            info_inner,
            text="Información del Sistema",
            font=fuente(16, "bold"),
            text_color=COLOR["primario"],
            anchor="w",
        )
        info_titulo.pack(fill="x", pady=(0, 12))

        self.model_label = self._fila_info(info_inner, "Modelo AI", self._describir_modelo())
        self.session_label = self._fila_info(info_inner, "Última sesión", "No registrada")

    def _tarjeta_accion(
        self, contenedor, columna, titulo, descripcion, texto_boton, color, color_hover, comando
    ):
        tarjeta = ctk.CTkFrame(
            contenedor,
            fg_color=COLOR["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLOR["borde"],
        )
        tarjeta.grid(row=0, column=columna, padx=(0 if columna == 0 else 16, 0), sticky="nsew")

        interno = ctk.CTkFrame(tarjeta, fg_color="transparent")
        interno.pack(fill="both", expand=True, padx=24, pady=22)

        etiqueta_titulo = ctk.CTkLabel(
            interno, text=titulo, font=fuente(20, "bold"), text_color=COLOR["texto"], anchor="w"
        )
        etiqueta_titulo.pack(fill="x")

        etiqueta_desc = ctk.CTkLabel(
            interno,
            text=descripcion,
            font=fuente(13),
            text_color=COLOR["texto_suave"],
            anchor="w",
            justify="left",
            wraplength=380,
        )
        etiqueta_desc.pack(fill="x", pady=(6, 16))

        boton = ctk.CTkButton(
            interno,
            text=texto_boton,
            font=fuente(15, "bold"),
            height=44,
            corner_radius=12,
            fg_color=color,
            hover_color=color_hover,
            command=comando,
        )
        boton.pack(anchor="w")

    def _fila_info(self, contenedor, titulo, valor):
        fila = ctk.CTkFrame(contenedor, fg_color="transparent")
        fila.pack(fill="x", pady=3)

        etiqueta = ctk.CTkLabel(
            fila,
            text=f"{titulo}:",
            font=fuente(14, "bold"),
            width=130,
            anchor="w",
            text_color=COLOR["texto"],
        )
        etiqueta.pack(side="left", padx=(0, 10))

        valor_label = ctk.CTkLabel(
            fila, text=valor, font=fuente(14), text_color=COLOR["texto_suave"], anchor="w"
        )
        valor_label.pack(side="left", fill="x", expand=True)
        return valor_label

    def _describir_modelo(self) -> str:
        """Describe el modelo ONNX configurado, si existe."""
        from opsis_meter.compartido.configuracion import cargar_configuracion

        config = cargar_configuracion()
        if config.ruta_modelo:
            return config.ruta_modelo.name
        return "No configurado (modo vista previa)"
