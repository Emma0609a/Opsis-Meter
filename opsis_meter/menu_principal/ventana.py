"""
Menú Principal - Opsis Meter
Pantalla de inicio: acceso al conteo, al historial y a la configuración.
"""

import customtkinter as ctk

from opsis_meter.compartido.tema import COLOR, configurar_apariencia, fuente
from opsis_meter.compartido.ventanas import centrar_ventana


class MenuPrincipal(ctk.CTk):
    """Ventana principal del menú de Opsis Meter."""

    def __init__(self):
        configurar_apariencia()
        super().__init__()

        self.title("Opsis Meter - Contador de Limones")
        self.geometry("700x900")
        self.minsize(600, 800)
        self.resizable(True, True)

        self.crear_widgets()

        # Centrar después de que la geometría inicial esté aplicada
        self.after(100, lambda: centrar_ventana(self))

        # Al volver de una ventana secundaria (deiconify) se restaura el estado
        self.bind("<Map>", self._al_mostrarse)

    def crear_widgets(self):
        """Crea los widgets de la interfaz."""

        main_frame = ctk.CTkFrame(self, fg_color=COLOR["fondo"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # ===== ENCABEZADO =====
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLOR["panel"], corner_radius=20)
        header_frame.pack(fill="x", pady=(0, 25), padx=5)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=25, pady=25)

        title_label = ctk.CTkLabel(
            header_content,
            text="OPSIS METER",
            font=fuente(48, "bold"),
            text_color=COLOR["primario"],
        )
        title_label.pack(pady=(5, 12))

        separator1 = ctk.CTkFrame(header_content, height=3, fg_color=COLOR["primario"])
        separator1.pack(fill="x", pady=(0, 12))

        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Sistema Inteligente de Conteo de Limones",
            font=fuente(18, "bold"),
            text_color=COLOR["texto"],
        )
        subtitle_label.pack(pady=(0, 10))

        description_label = ctk.CTkLabel(
            header_content,
            text="Powered by YOLO + ByteTrack • Offline-First",
            font=fuente(12),
            text_color=COLOR["texto_tenue"],
        )
        description_label.pack()

        # ===== BOTONES PRINCIPALES =====
        buttons_container = ctk.CTkFrame(main_frame, fg_color=COLOR["panel"], corner_radius=20)
        buttons_container.pack(fill="both", expand=True, pady=(0, 20), padx=5)

        buttons_inner = ctk.CTkFrame(buttons_container, fg_color="transparent")
        buttons_inner.pack(expand=True, fill="both", padx=25, pady=25)

        buttons_frame = ctk.CTkFrame(buttons_inner, fg_color="transparent")
        buttons_frame.pack(expand=True, fill="both")
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        start_button = ctk.CTkButton(
            buttons_frame,
            text="Iniciar Conteo",
            font=fuente(24, "bold"),
            height=100,
            fg_color=COLOR["exito"],
            hover_color=COLOR["exito_hover"],
            corner_radius=22,
            border_width=0,
            border_spacing=15,
            command=self.abrir_conteo,
        )
        start_button.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 20), sticky="ew")

        history_button = ctk.CTkButton(
            buttons_frame,
            text="Ver Historial",
            font=fuente(19, "bold"),
            height=85,
            fg_color=COLOR["primario"],
            hover_color=COLOR["primario_hover"],
            corner_radius=20,
            border_width=0,
            command=self.abrir_historial,
        )
        history_button.grid(row=1, column=0, padx=(20, 12), pady=15, sticky="ew")

        settings_button = ctk.CTkButton(
            buttons_frame,
            text="Configuración",
            font=fuente(19, "bold"),
            height=85,
            fg_color=COLOR["advertencia"],
            hover_color=COLOR["advertencia_hover"],
            corner_radius=20,
            border_width=0,
            command=self.abrir_configuracion,
        )
        settings_button.grid(row=1, column=1, padx=(12, 20), pady=15, sticky="ew")

        # ===== INFORMACIÓN DEL SISTEMA =====
        info_container = ctk.CTkFrame(main_frame, corner_radius=18, fg_color=COLOR["panel"])
        info_container.pack(fill="x", padx=5, pady=(0, 15))

        info_title_frame = ctk.CTkFrame(info_container, fg_color="transparent")
        info_title_frame.pack(fill="x", padx=20, pady=(20, 15))

        info_title = ctk.CTkLabel(
            info_title_frame,
            text="Información del Sistema",
            font=fuente(18, "bold"),
            anchor="w",
            text_color=COLOR["primario"],
        )
        info_title.pack(side="left")

        separator2 = ctk.CTkFrame(info_title_frame, height=2, fg_color=COLOR["primario"], width=50)
        separator2.pack(side="left", padx=(10, 0), fill="x", expand=True)

        info_inner = ctk.CTkFrame(info_container, fg_color="transparent")
        info_inner.pack(fill="x", padx=25, pady=(0, 20))

        session_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
        session_frame.pack(fill="x", pady=5)

        session_title = ctk.CTkLabel(
            session_frame,
            text="Última sesión:",
            font=fuente(15, "bold"),
            width=120,
            anchor="w",
            text_color=COLOR["texto"],
        )
        session_title.pack(side="left", padx=(0, 10))

        self.session_label = ctk.CTkLabel(
            session_frame,
            text="No registrada",
            font=fuente(15),
            text_color=COLOR["texto_suave"],
            anchor="w",
        )
        self.session_label.pack(side="left", fill="x", expand=True)

        model_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)

        model_title = ctk.CTkLabel(
            model_frame,
            text="Modelo AI:",
            font=fuente(15, "bold"),
            width=120,
            anchor="w",
            text_color=COLOR["texto"],
        )
        model_title.pack(side="left", padx=(0, 10))

        self.model_label = ctk.CTkLabel(
            model_frame,
            text=self._describir_modelo(),
            font=fuente(15),
            text_color=COLOR["texto_suave"],
            anchor="w",
        )
        self.model_label.pack(side="left", fill="x", expand=True)

        # ===== VERSIÓN =====
        version_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        version_frame.pack(side="bottom", fill="x", pady=(0, 8))

        version_label = ctk.CTkLabel(
            version_frame,
            text="OPSIS METER DEMO 0.2 BY ENIGMA",
            font=fuente(11),
            text_color=COLOR["texto_version"],
        )
        version_label.pack()

        # ===== ESTADO =====
        status_container = ctk.CTkFrame(main_frame, corner_radius=18, fg_color=COLOR["panel_oscuro"])
        status_container.pack(fill="x", padx=5, pady=(0, 5), side="bottom")

        status_inner = ctk.CTkFrame(status_container, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=15)

        status_title_label = ctk.CTkLabel(
            status_inner,
            text="Estado:",
            font=fuente(15, "bold"),
            anchor="w",
            text_color=COLOR["texto"],
        )
        status_title_label.pack(side="left", padx=(0, 12))

        self.status_indicator = ctk.CTkFrame(
            status_inner, width=10, height=10, corner_radius=5, fg_color=COLOR["exito"]
        )
        self.status_indicator.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(
            status_inner,
            text="Listo para iniciar",
            font=fuente(15, "bold"),
            text_color=COLOR["exito"],
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

    def _describir_modelo(self) -> str:
        """Describe el modelo ONNX configurado, si existe."""
        # Import local: evita cargar dotenv/config si solo se navega la UI
        from opsis_meter.compartido.configuracion import cargar_configuracion

        config = cargar_configuracion()
        if config.ruta_modelo:
            return config.ruta_modelo.name
        return "No configurado"

    def abrir_conteo(self):
        """Abre la ventana de conteo."""
        # Import diferido: la ventana de conteo carga OpenCV
        from opsis_meter.conteo.ventana import VentanaConteo

        self._fijar_estado("En conteo...", COLOR["advertencia"])
        self.withdraw()
        ventana = VentanaConteo(self)
        ventana.focus()

    def abrir_historial(self):
        """Abre la ventana de historial."""
        from opsis_meter.historial.ventana import VentanaHistorial

        self._fijar_estado("Consultando historial...", COLOR["advertencia"])
        self.withdraw()
        ventana = VentanaHistorial(self)
        ventana.focus()

    def abrir_configuracion(self):
        """Abre la ventana de configuración."""
        # TODO Bloque 6: ventana de configuración (cámara, modelo, credenciales)
        pass

    def _al_mostrarse(self, event=None):
        """Restaura el estado cuando la ventana vuelve a mostrarse."""
        self._fijar_estado("Listo para iniciar", COLOR["exito"])

    def _fijar_estado(self, texto: str, color: str):
        self.status_label.configure(text=texto, text_color=color)
        self.status_indicator.configure(fg_color=color)
