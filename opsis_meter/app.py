"""
Aplicación Opsis Meter: ventana raíz maximizada con navegación lateral.

Las vistas (inicio, conteo, historial) viven en un único contenedor y se
intercambian sin abrir ventanas nuevas, aprovechando toda la pantalla.
F11 alterna pantalla completa real; Escape la abandona.
"""

import sys
import tkinter as tk
import traceback

import customtkinter as ctk

from opsis_meter import __version__
from opsis_meter.compartido.tema import COLOR, configurar_apariencia, fuente

ANCHO_BARRA_LATERAL = 240


class AplicacionOpsis(ctk.CTk):
    """Ventana raíz: barra lateral + contenedor de vistas."""

    def __init__(self):
        configurar_apariencia()
        super().__init__(fg_color=COLOR["fondo"])

        self.title("Opsis Meter")
        self.minsize(1100, 700)
        self._maximizar()

        self._pantalla_completa = False
        self.bind("<F11>", self.alternar_pantalla_completa)
        self.bind("<Escape>", self.salir_pantalla_completa)
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        self._vistas = {}
        self._botones_nav = {}
        self._vista_actual = None

        self._crear_estructura()
        self.mostrar_vista("inicio")

    # ----- Ventana -----

    def _maximizar(self):
        """Abre la ventana ocupando toda la pantalla disponible."""
        try:
            self.state("zoomed")  # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)  # X11 / Linux
            except tk.TclError:
                ancho = self.winfo_screenwidth()
                alto = self.winfo_screenheight()
                self.geometry(f"{ancho}x{alto}+0+0")

    def alternar_pantalla_completa(self, event=None):
        self._pantalla_completa = not self._pantalla_completa
        self.attributes("-fullscreen", self._pantalla_completa)

    def salir_pantalla_completa(self, event=None):
        if self._pantalla_completa:
            self.alternar_pantalla_completa()

    # ----- Estructura -----

    def _crear_estructura(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Barra lateral
        barra = ctk.CTkFrame(
            self, width=ANCHO_BARRA_LATERAL, fg_color=COLOR["panel_oscuro"], corner_radius=0
        )
        barra.grid(row=0, column=0, sticky="nsw")
        barra.grid_propagate(False)

        logo_frame = ctk.CTkFrame(barra, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(28, 6))

        logo = ctk.CTkLabel(
            logo_frame,
            text="OPSIS METER",
            font=fuente(22, "bold"),
            text_color=COLOR["primario"],
            anchor="w",
        )
        logo.pack(fill="x")

        lema = ctk.CTkLabel(
            logo_frame,
            text="Conteo inteligente",
            font=fuente(12),
            text_color=COLOR["texto_tenue"],
            anchor="w",
        )
        lema.pack(fill="x")

        separador = ctk.CTkFrame(barra, height=1, fg_color=COLOR["borde"])
        separador.pack(fill="x", padx=16, pady=(14, 14))

        self._crear_boton_nav(barra, "inicio", "Inicio")
        self._crear_boton_nav(barra, "conteo", "Conteo")
        self._crear_boton_nav(barra, "historial", "Historial")
        self._crear_boton_nav(barra, "configuracion", "Configuración")

        # Pie de la barra: estado y versión
        pie = ctk.CTkFrame(barra, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=20, pady=18)

        estado_frame = ctk.CTkFrame(pie, fg_color="transparent")
        estado_frame.pack(fill="x", pady=(0, 8))

        self._estado_punto = ctk.CTkFrame(
            estado_frame, width=9, height=9, corner_radius=5, fg_color=COLOR["exito"]
        )
        self._estado_punto.pack(side="left", padx=(0, 8))

        self._estado_label = ctk.CTkLabel(
            estado_frame,
            text="Listo",
            font=fuente(13, "bold"),
            text_color=COLOR["exito"],
            anchor="w",
        )
        self._estado_label.pack(side="left", fill="x", expand=True)

        version = ctk.CTkLabel(
            pie,
            text=f"v{__version__} · F11 pantalla completa",
            font=fuente(11),
            text_color=COLOR["texto_version"],
            anchor="w",
        )
        version.pack(fill="x")

        # Contenedor de vistas
        self._contenedor = ctk.CTkFrame(self, fg_color="transparent")
        self._contenedor.grid(row=0, column=1, sticky="nsew")

    def _crear_boton_nav(self, barra, clave, texto):
        boton = ctk.CTkButton(
            barra,
            text=texto,
            font=fuente(15, "bold"),
            height=44,
            anchor="w",
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLOR["panel_hover"],
            text_color=COLOR["texto_suave"],
            command=lambda: self.mostrar_vista(clave),
        )
        boton.pack(fill="x", padx=12, pady=3)
        self._botones_nav[clave] = boton

    # ----- Navegación -----

    def _crear_vista(self, clave):
        # Imports diferidos: cada vista carga sus dependencias al usarse
        if clave == "inicio":
            from opsis_meter.menu_principal.ventana import VistaInicio

            return VistaInicio(self._contenedor, self)
        if clave == "conteo":
            from opsis_meter.conteo.ventana import VistaConteo

            return VistaConteo(self._contenedor, self)
        if clave == "historial":
            from opsis_meter.historial.ventana import VistaHistorial

            return VistaHistorial(self._contenedor, self)
        return self._vista_en_construccion()

    def _vista_en_construccion(self):
        vista = ctk.CTkFrame(self._contenedor, fg_color="transparent")
        mensaje = ctk.CTkLabel(
            vista,
            text="Configuración\n\nEn construcción (Bloque 6):\ncámara, modelo de IA y credenciales.",
            font=fuente(16),
            text_color=COLOR["texto_tenue"],
            justify="center",
        )
        mensaje.pack(expand=True)
        return vista

    def mostrar_vista(self, clave):
        """Cambia la vista activa del contenedor."""
        if clave not in self._vistas:
            self._vistas[clave] = self._crear_vista(clave)

        vista = self._vistas[clave]
        if self._vista_actual is vista:
            return

        if self._vista_actual is not None:
            self._vista_actual.pack_forget()
        vista.pack(fill="both", expand=True)
        self._vista_actual = vista

        if hasattr(vista, "al_mostrar"):
            vista.al_mostrar()

        for k, boton in self._botones_nav.items():
            activo = k == clave
            boton.configure(
                fg_color=COLOR["panel"] if activo else "transparent",
                text_color=COLOR["primario"] if activo else COLOR["texto_suave"],
            )

    # ----- Estado global -----

    def fijar_estado(self, texto: str, color: str):
        """Actualiza el indicador de estado de la barra lateral."""
        self._estado_label.configure(text=texto, text_color=color)
        self._estado_punto.configure(fg_color=color)

    def al_cerrar(self):
        """Libera cámara y proceso de IA antes de salir."""
        vista_conteo = self._vistas.get("conteo")
        if vista_conteo is not None:
            vista_conteo.limpiar()
        self.destroy()


def ejecutar():
    """Inicia la aplicación de escritorio."""
    try:
        app = AplicacionOpsis()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
