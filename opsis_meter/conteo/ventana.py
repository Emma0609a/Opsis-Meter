"""
Ventana de Conteo - Opsis Meter
Vista de cámara y control de captura.

Tiene dos modos:

- Vista previa: la captura corre en un hilo propio (captura.FlujoCamara)
  y esta ventana consume el último frame desde un bucle after(), de modo
  que todas las operaciones de Tkinter ocurren en el hilo principal.
- Conteo con IA: se lanza un proceso independiente (conteo.proceso_ia)
  que es dueño de la cámara y ejecuta detección + seguimiento + línea
  virtual; la UI solo dibuja los frames anotados y el total que llegan
  por una cola de multiprocessing.
"""

import multiprocessing
import queue as cola_estandar
import threading
import time
import tkinter.messagebox as messagebox

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk

from opsis_meter.captura.camara import ESTADO_ERROR, FlujoCamara
from opsis_meter.captura.dispositivos import detectar_camaras
from opsis_meter.compartido.configuracion import cargar_configuracion
from opsis_meter.compartido.tema import COLOR, fuente
from opsis_meter.compartido.ventanas import centrar_ventana
from opsis_meter.conteo.mensajes import (
    CMD_DETENER,
    CMD_FPS,
    AvisoConteo,
    ErrorConteo,
    FinConteo,
    FrameConteo,
)
from opsis_meter.conteo.proceso_ia import ejecutar_conteo

ESPERA_CIERRE_PROCESO = 5.0  # segundos para que el proceso cierre el lote


class VentanaConteo(ctk.CTkToplevel):
    """Ventana de conteo con cámara."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Opsis Meter - Iniciar Conteo")
        self.geometry("1200x800")
        self.minsize(1100, 750)

        self.parent = parent

        # Captura de video (vista previa)
        self.flujo: FlujoCamara | None = None
        self.vista_activa = False
        self.fps_limite = 30

        # Proceso de conteo con IA
        self.proceso_ia: multiprocessing.Process | None = None
        self.cola_eventos = None
        self.cola_comandos = None
        self.conteo_activo = False
        self._cierre_limite = None  # plazo para que el proceso confirme el fin

        # Línea virtual de conteo
        self.linea_orientacion = "vertical"
        self.linea_posicion = 0.5

        # Pantalla completa
        self.fullscreen_state = False
        self.normal_geometry = None

        # Fuente de video: 'local' o 'ip'
        self.tipo_camara = "local"
        self.dispositivos = []
        self.dispositivo_actual = 0
        self.resolucion_actual = (640, 480)

        self.crear_widgets()
        self.detectar_dispositivos()
        centrar_ventana(self)

        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)
        self.bind("<F11>", self.alternar_pantalla_completa)
        self.bind("<Escape>", self.salir_pantalla_completa)

    # ----- Detección de dispositivos (en hilo secundario) -----

    def detectar_dispositivos(self):
        """Busca cámaras locales sin bloquear la interfaz."""
        self.device_menu.configure(values=["Buscando..."])
        self.device_menu.set("Buscando...")

        def _buscar():
            encontrados = detectar_camaras()
            try:
                self.after(0, lambda: self._aplicar_dispositivos(encontrados))
            except RuntimeError:
                pass  # la ventana se cerró durante la búsqueda

        threading.Thread(target=_buscar, daemon=True).start()

    def _aplicar_dispositivos(self, encontrados):
        self.dispositivos = encontrados or [0]
        self.dispositivo_actual = self.dispositivos[0]
        self.device_menu.configure(values=[f"Cámara {i}" for i in self.dispositivos])
        self.device_menu.set(f"Cámara {self.dispositivo_actual}")

    # ----- Construcción de la interfaz -----

    def crear_widgets(self):
        """Crea los widgets de la interfaz."""

        main_frame = ctk.CTkFrame(self, fg_color=COLOR["fondo"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # ===== SECCIÓN SUPERIOR: título y regreso =====
        top_frame = ctk.CTkFrame(main_frame, fg_color=COLOR["panel"], corner_radius=15)
        top_frame.pack(fill="x", pady=(0, 20), padx=5)

        top_content = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_content.pack(fill="x", padx=25, pady=18)

        title_label = ctk.CTkLabel(
            top_content,
            text="Iniciar Conteo",
            font=fuente(32, "bold"),
            text_color=COLOR["acento"],
        )
        title_label.pack(side="left")

        back_button = ctk.CTkButton(
            top_content,
            text="Regresar",
            font=fuente(16, "bold"),
            height=42,
            width=160,
            fg_color=COLOR["neutro"],
            hover_color=COLOR["neutro_hover"],
            corner_radius=14,
            command=self.al_cerrar,
        )
        back_button.pack(side="right")

        # ===== PANEL IZQUIERDO: vista de cámara =====
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        camera_frame = ctk.CTkFrame(content_frame, corner_radius=18, fg_color=COLOR["panel"])
        camera_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

        camera_inner = ctk.CTkFrame(camera_frame, fg_color="transparent")
        camera_inner.pack(fill="both", expand=True, padx=25, pady=25)

        preview_header = ctk.CTkFrame(camera_inner, fg_color="transparent")
        preview_header.pack(fill="x", pady=(0, 20))

        preview_label = ctk.CTkLabel(
            preview_header, text="Vista Previa", font=fuente(20, "bold")
        )
        preview_label.pack(side="left")

        self.fps_label = ctk.CTkLabel(
            preview_header,
            text="FPS: 0",
            font=fuente(14),
            text_color=COLOR["exito"],
        )
        self.fps_label.pack(side="right")

        self.camera_display_frame = ctk.CTkFrame(
            camera_inner, corner_radius=12, fg_color=COLOR["panel_video"]
        )
        self.camera_display_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.camera_display = ctk.CTkLabel(
            self.camera_display_frame,
            text="",
            font=fuente(14),
            text_color=COLOR["texto_apagado"],
        )
        self.camera_display.pack(expand=True, fill="both", padx=15, pady=15)

        # ===== PANEL DERECHO: controles =====
        controls_frame = ctk.CTkFrame(
            content_frame, corner_radius=18, fg_color=COLOR["panel"], width=380
        )
        controls_frame.pack(side="right", fill="y")
        controls_frame.pack_propagate(False)

        controls_inner = ctk.CTkFrame(controls_frame, fg_color="transparent")
        controls_inner.pack(fill="both", expand=True, padx=25, pady=25)

        controls_title = ctk.CTkLabel(
            controls_inner,
            text="Controles",
            font=fuente(22, "bold"),
            text_color=COLOR["acento"],
        )
        controls_title.pack(pady=(0, 20))

        # ===== CONTADOR EN VIVO =====
        contador_frame = ctk.CTkFrame(
            controls_inner, fg_color=COLOR["panel_oscuro"], corner_radius=14
        )
        contador_frame.pack(fill="x", pady=(0, 20))

        contador_titulo = ctk.CTkLabel(
            contador_frame,
            text="Total contado",
            font=fuente(14, "bold"),
            text_color=COLOR["texto"],
        )
        contador_titulo.pack(pady=(12, 0))

        self.contador_label = ctk.CTkLabel(
            contador_frame,
            text="0",
            font=fuente(44, "bold"),
            text_color=COLOR["exito"],
        )
        self.contador_label.pack()

        self.estado_conteo_label = ctk.CTkLabel(
            contador_frame,
            text="En escena: 0",
            font=fuente(12),
            text_color=COLOR["texto_suave"],
        )
        self.estado_conteo_label.pack(pady=(0, 12))

        buttons_frame = ctk.CTkFrame(controls_inner, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 25))

        self.count_button = ctk.CTkButton(
            buttons_frame,
            text="Iniciar Conteo IA",
            font=fuente(18, "bold"),
            height=60,
            fg_color=COLOR["acento"],
            hover_color=COLOR["acento_hover"],
            corner_radius=18,
            border_width=0,
            border_spacing=10,
            command=self.iniciar_conteo,
        )
        self.count_button.pack(fill="x", pady=(0, 15))

        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Iniciar Captura",
            font=fuente(18, "bold"),
            height=60,
            fg_color=COLOR["exito"],
            hover_color=COLOR["exito_hover"],
            corner_radius=18,
            border_width=0,
            border_spacing=10,
            command=self.iniciar_captura,
        )
        self.start_button.pack(fill="x", pady=(0, 15))

        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="Detener Captura",
            font=fuente(18, "bold"),
            height=60,
            fg_color=COLOR["peligro"],
            hover_color=COLOR["peligro_hover"],
            corner_radius=18,
            border_width=0,
            border_spacing=10,
            command=self.detener_captura,
            state="disabled",
        )
        self.stop_button.pack(fill="x")

        separator_frame = ctk.CTkFrame(controls_inner, fg_color="transparent")
        separator_frame.pack(fill="x", pady=(0, 20))

        separator = ctk.CTkFrame(separator_frame, height=2, fg_color=COLOR["acento"])
        separator.pack(fill="x", padx=10)

        # ===== OPCIONES =====
        options_title = ctk.CTkLabel(
            controls_inner,
            text="Opciones",
            font=fuente(18, "bold"),
            text_color=COLOR["acento"],
        )
        options_title.pack(pady=(0, 15))

        scrollable_frame = ctk.CTkScrollableFrame(
            controls_inner, fg_color="transparent", corner_radius=10
        )
        scrollable_frame.pack(fill="both", expand=True)

        # Tipo de cámara
        camera_type_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        camera_type_container.pack(fill="x", pady=(0, 20))

        camera_type_label = ctk.CTkLabel(
            camera_type_container,
            text="Tipo de Cámara:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        camera_type_label.pack(fill="x", pady=(0, 8))

        self.camera_type_menu = ctk.CTkComboBox(
            camera_type_container,
            values=["Cámara Local", "Cámara IP"],
            font=fuente(14),
            command=self.al_cambiar_tipo_camara,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color=COLOR["neutro"],
            button_color=COLOR["neutro"],
            button_hover_color=COLOR["neutro_hover"],
        )
        self.camera_type_menu.set("Cámara Local")
        self.camera_type_menu.pack(fill="x")

        # Dispositivo local
        self.device_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.device_container.pack(fill="x", pady=(0, 20))

        device_label = ctk.CTkLabel(
            self.device_container,
            text="Dispositivo:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        device_label.pack(fill="x", pady=(0, 8))

        self.device_menu = ctk.CTkComboBox(
            self.device_container,
            values=["Cámara 0"],
            font=fuente(14),
            command=self.al_cambiar_dispositivo,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color=COLOR["neutro"],
            button_color=COLOR["neutro"],
            button_hover_color=COLOR["neutro_hover"],
        )
        self.device_menu.pack(fill="x")

        # Cámara IP
        self.ip_camera_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.ip_camera_container.pack_forget()

        ip_camera_label = ctk.CTkLabel(
            self.ip_camera_container,
            text="URL/IP de Cámara:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        ip_camera_label.pack(fill="x", pady=(0, 8))

        self.ip_camera_entry = ctk.CTkEntry(
            self.ip_camera_container,
            font=fuente(13),
            height=42,
            corner_radius=12,
            border_width=2,
            border_color=COLOR["neutro"],
            placeholder_text="rtsp://usuario:contraseña@ip:puerto/ruta",
        )
        self.ip_camera_entry.pack(fill="x", pady=(0, 8))

        ip_info_label = ctk.CTkLabel(
            self.ip_camera_container,
            text="Formatos soportados: RTSP, HTTP, MJPEG\n"
            "Ejemplo: rtsp://admin:1234@192.168.1.100:554/stream",
            font=fuente(11),
            text_color=COLOR["texto_apagado"],
            anchor="w",
            justify="left",
        )
        ip_info_label.pack(fill="x")

        # Resolución
        resolution_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        resolution_container.pack(fill="x", pady=(0, 20))

        resolution_label = ctk.CTkLabel(
            resolution_container,
            text="Resolución:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        resolution_label.pack(fill="x", pady=(0, 8))

        self.resolution_menu = ctk.CTkComboBox(
            resolution_container,
            values=["640x480", "800x600", "1024x768", "1280x720", "1920x1080"],
            font=fuente(14),
            command=self.al_cambiar_resolucion,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color=COLOR["neutro"],
            button_color=COLOR["neutro"],
            button_hover_color=COLOR["neutro_hover"],
        )
        self.resolution_menu.set("640x480")
        self.resolution_menu.pack(fill="x")

        # Línea virtual de conteo
        linea_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        linea_container.pack(fill="x", pady=(0, 20))

        linea_label = ctk.CTkLabel(
            linea_container,
            text="Línea de conteo:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        linea_label.pack(fill="x", pady=(0, 8))

        self.linea_orientacion_menu = ctk.CTkComboBox(
            linea_container,
            values=["Vertical", "Horizontal"],
            font=fuente(14),
            command=self.al_cambiar_orientacion_linea,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color=COLOR["neutro"],
            button_color=COLOR["neutro"],
            button_hover_color=COLOR["neutro_hover"],
        )
        self.linea_orientacion_menu.set("Vertical")
        self.linea_orientacion_menu.pack(fill="x", pady=(0, 10))

        self.linea_posicion_slider = ctk.CTkSlider(
            linea_container,
            from_=0.1,
            to=0.9,
            number_of_steps=80,
            command=self.al_mover_linea,
            height=20,
        )
        self.linea_posicion_slider.set(0.5)
        self.linea_posicion_slider.pack(fill="x")

        self.linea_posicion_label = ctk.CTkLabel(
            linea_container,
            text="Posición: 50%",
            font=fuente(11),
            text_color=COLOR["texto_apagado"],
            anchor="w",
        )
        self.linea_posicion_label.pack(fill="x", pady=(6, 0))

        # Límite de FPS
        fps_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        fps_container.pack(fill="x", pady=(0, 20))

        fps_label = ctk.CTkLabel(
            fps_container,
            text="Límite de FPS:",
            font=fuente(15, "bold"),
            anchor="w",
        )
        fps_label.pack(fill="x", pady=(0, 12))

        slider_frame = ctk.CTkFrame(fps_container, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(0, 15))

        self.fps_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=60,
            number_of_steps=59,
            command=self.al_mover_slider_fps,
            height=20,
        )
        self.fps_slider.set(30)
        self.fps_slider.pack(fill="x", side="left", expand=True)

        numeric_frame = ctk.CTkFrame(fps_container, fg_color="transparent")
        numeric_frame.pack(fill="x")

        decrease_btn = ctk.CTkButton(
            numeric_frame,
            text="-",
            font=fuente(20, "bold"),
            width=50,
            height=42,
            fg_color=COLOR["neutro"],
            hover_color=COLOR["neutro_hover"],
            corner_radius=12,
            border_width=0,
            command=lambda: self.fijar_fps(self.fps_limite - 1),
        )
        decrease_btn.pack(side="left", padx=(0, 12))

        self.fps_entry = ctk.CTkEntry(
            numeric_frame,
            font=fuente(16, "bold"),
            width=110,
            height=42,
            corner_radius=12,
            justify="center",
            border_width=2,
            border_color=COLOR["neutro"],
        )
        self.fps_entry.insert(0, "30")
        self.fps_entry.pack(side="left", padx=(0, 12))
        self.fps_entry.bind("<Return>", self.al_editar_fps)
        self.fps_entry.bind("<FocusOut>", self.al_editar_fps)

        fps_unit_short = ctk.CTkLabel(
            numeric_frame,
            text="FPS",
            font=fuente(15, "bold"),
            text_color=COLOR["texto_suave"],
        )
        fps_unit_short.pack(side="left", padx=(0, 12))

        increase_btn = ctk.CTkButton(
            numeric_frame,
            text="+",
            font=fuente(20, "bold"),
            width=50,
            height=42,
            fg_color=COLOR["neutro"],
            hover_color=COLOR["neutro_hover"],
            corner_radius=12,
            border_width=0,
            command=lambda: self.fijar_fps(self.fps_limite + 1),
        )
        increase_btn.pack(side="left")

        fps_info = ctk.CTkLabel(
            fps_container,
            text="Rango: 1-60 FPS",
            font=fuente(11),
            text_color=COLOR["texto_apagado"],
        )
        fps_info.pack(anchor="w", pady=(8, 0))

    # ----- Cambios de opciones -----

    def al_cambiar_tipo_camara(self, eleccion):
        """Maneja el cambio de tipo de cámara."""
        if eleccion == "Cámara Local":
            self.tipo_camara = "local"
            self.device_container.pack(fill="x", pady=(0, 20))
            self.ip_camera_container.pack_forget()
        else:
            self.tipo_camara = "ip"
            self.device_container.pack_forget()
            self.ip_camera_container.pack(fill="x", pady=(0, 20))

        if self.vista_activa:
            self.detener_captura()

    def al_cambiar_dispositivo(self, eleccion):
        """Maneja el cambio de dispositivo."""
        try:
            self.dispositivo_actual = int(eleccion.replace("Cámara ", ""))
        except ValueError:
            return
        if self.vista_activa:
            self.detener_captura()
            self.iniciar_captura()

    def al_cambiar_resolucion(self, eleccion):
        """Maneja el cambio de resolución (reinicia la captura si está activa)."""
        try:
            ancho, alto = map(int, eleccion.split("x"))
        except ValueError:
            return
        self.resolucion_actual = (ancho, alto)
        if self.vista_activa:
            self.detener_captura()
            self.iniciar_captura()

    def al_cambiar_orientacion_linea(self, eleccion):
        self.linea_orientacion = "horizontal" if eleccion == "Horizontal" else "vertical"

    def al_mover_linea(self, valor):
        self.linea_posicion = round(float(valor), 2)
        self.linea_posicion_label.configure(text=f"Posición: {int(self.linea_posicion * 100)}%")

    def al_mover_slider_fps(self, valor):
        self.fijar_fps(int(valor))

    def al_editar_fps(self, event=None):
        try:
            self.fijar_fps(int(self.fps_entry.get()))
        except ValueError:
            self.fijar_fps(self.fps_limite)

    def fijar_fps(self, valor: int):
        """Punto único de cambio de FPS: sincroniza slider, entrada y captura."""
        self.fps_limite = min(60, max(1, valor))
        self.fps_slider.set(self.fps_limite)
        self.fps_entry.delete(0, "end")
        self.fps_entry.insert(0, str(self.fps_limite))
        if self.flujo:
            self.flujo.fijar_limite_fps(self.fps_limite)
        if self.conteo_activo and self.cola_comandos is not None:
            try:
                self.cola_comandos.put_nowait((CMD_FPS, self.fps_limite))
            except cola_estandar.Full:
                pass

    # ----- Captura -----

    def iniciar_captura(self):
        """Inicia la vista previa de la cámara."""
        if self.tipo_camara == "ip":
            fuente_video = self.ip_camera_entry.get().strip()
            if not fuente_video:
                messagebox.showerror(
                    "Error", "Por favor, ingresa la URL/IP de la cámara", parent=self
                )
                return
        else:
            fuente_video = self.dispositivo_actual

        self.flujo = FlujoCamara(
            fuente_video,
            resolucion=self.resolucion_actual,
            limite_fps=self.fps_limite,
            es_ip=(self.tipo_camara == "ip"),
        )
        self.flujo.iniciar()

        self.vista_activa = True
        self._controles_en_captura(True)
        self.camera_display.configure(text="Conectando con la cámara...")
        self._refrescar_vista()

    def detener_captura(self):
        """Detiene la vista previa y libera la cámara."""
        self.vista_activa = False
        if self.flujo:
            self.flujo.detener()
            self.flujo = None

        self._controles_en_captura(False)
        self.camera_display.configure(image="", text="")
        self.camera_display.image = None
        self.fps_label.configure(text="FPS: 0")

    def _controles_en_captura(self, capturando: bool):
        """Habilita/deshabilita controles según el estado de captura."""
        self.start_button.configure(state="disabled" if capturando else "normal")
        self.stop_button.configure(state="normal" if capturando else "disabled")
        estado = "disabled" if capturando else "normal"
        self.camera_type_menu.configure(state=estado)
        if self.tipo_camara == "ip":
            self.ip_camera_entry.configure(state=estado)
        else:
            self.device_menu.configure(state=estado)

    def _refrescar_vista(self):
        """Bucle de refresco de la vista previa (hilo principal, vía after)."""
        if not self.vista_activa or self.flujo is None:
            return

        if self.flujo.estado == ESTADO_ERROR:
            error = self.flujo.error or "Error desconocido de la cámara"
            self.detener_captura()
            messagebox.showerror("Error de cámara", error, parent=self)
            return

        frame = self.flujo.leer_frame()
        if frame is not None:
            self._renderizar_frame(frame)
            self.fps_label.configure(text=f"FPS: {int(self.flujo.fps_real)}")

        periodo = max(15, int(1000 / self.fps_limite))
        self.after(periodo, self._refrescar_vista)

    def _renderizar_frame(self, frame):
        """Convierte un frame BGR a PhotoImage y lo muestra (hilo principal)."""
        alto_frame, ancho_frame = frame.shape[:2]

        ancho_area = self.camera_display_frame.winfo_width() - 30
        alto_area = self.camera_display_frame.winfo_height() - 30

        if ancho_area > 1 and alto_area > 1:
            aspecto = ancho_frame / alto_frame
            aspecto_area = ancho_area / alto_area
            if aspecto > aspecto_area:
                ancho_destino = ancho_area
                alto_destino = int(ancho_area / aspecto)
            else:
                alto_destino = alto_area
                ancho_destino = int(alto_area * aspecto)
            ancho_destino = max(ancho_destino, 100)
            alto_destino = max(alto_destino, 1)
        else:
            ancho_destino = 720
            alto_destino = int(720 * alto_frame / ancho_frame)

        frame = cv2.resize(frame, (ancho_destino, alto_destino), interpolation=cv2.INTER_AREA)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        foto = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))

        self.camera_display.configure(image=foto, text="")
        self.camera_display.image = foto  # mantener referencia

    # ----- Conteo con IA (proceso independiente) -----

    def iniciar_conteo(self):
        """Lanza el proceso de IA que captura, detecta y cuenta."""
        if self.conteo_activo:
            return

        if self.tipo_camara == "ip":
            fuente_video = self.ip_camera_entry.get().strip()
            if not fuente_video:
                messagebox.showerror(
                    "Error", "Por favor, ingresa la URL/IP de la cámara", parent=self
                )
                return
        else:
            fuente_video = self.dispositivo_actual

        # El proceso de IA es el dueño de la cámara: cerrar la vista previa
        if self.vista_activa:
            self.detener_captura()

        config = cargar_configuracion()
        contexto = multiprocessing.get_context("spawn")
        self.cola_eventos = contexto.Queue(maxsize=8)
        self.cola_comandos = contexto.Queue()
        self.proceso_ia = contexto.Process(
            target=ejecutar_conteo,
            args=(
                fuente_video,
                self.tipo_camara == "ip",
                self.resolucion_actual,
                self.fps_limite,
                str(config.ruta_modelo) if config.ruta_modelo else None,
                config.umbral_confianza,
                self.linea_orientacion,
                self.linea_posicion,
                self.cola_eventos,
                self.cola_comandos,
            ),
            daemon=True,
        )
        self.proceso_ia.start()

        self.conteo_activo = True
        self._cierre_limite = None
        self.contador_label.configure(text="0")
        self.estado_conteo_label.configure(
            text="Iniciando proceso de IA...", text_color=COLOR["texto_suave"]
        )
        self.camera_display.configure(text="Iniciando proceso de IA...")
        self._controles_en_conteo(True)
        self._procesar_eventos_ia()

    def detener_conteo(self):
        """Pide al proceso de IA cerrar el lote y espera su resumen."""
        if not self.conteo_activo or self._cierre_limite is not None:
            return
        self._cierre_limite = time.monotonic() + ESPERA_CIERRE_PROCESO
        self.count_button.configure(state="disabled", text="Cerrando lote...")
        try:
            self.cola_comandos.put_nowait((CMD_DETENER,))
        except cola_estandar.Full:
            pass

    def _procesar_eventos_ia(self):
        """Bucle after() que drena la cola de eventos del proceso de IA."""
        if not self.conteo_activo:
            return

        ultimo_frame = None
        try:
            while True:
                evento = self.cola_eventos.get_nowait()
                if isinstance(evento, FrameConteo):
                    ultimo_frame = evento
                elif isinstance(evento, AvisoConteo):
                    self.estado_conteo_label.configure(
                        text=evento.mensaje, text_color=COLOR["advertencia"]
                    )
                elif isinstance(evento, ErrorConteo):
                    self._finalizar_conteo(error=evento.mensaje)
                    return
                elif isinstance(evento, FinConteo):
                    self._finalizar_conteo(fin=evento)
                    return
        except cola_estandar.Empty:
            pass

        if ultimo_frame is not None:
            datos = np.frombuffer(ultimo_frame.jpeg, dtype=np.uint8)
            frame = cv2.imdecode(datos, cv2.IMREAD_COLOR)
            if frame is not None:
                self._renderizar_frame(frame)
            self.contador_label.configure(text=str(ultimo_frame.total))
            if ultimo_frame.con_ia:
                self.estado_conteo_label.configure(
                    text=f"En escena: {ultimo_frame.en_escena}",
                    text_color=COLOR["texto_suave"],
                )
            self.fps_label.configure(text=f"FPS: {int(ultimo_frame.fps)}")

        # El proceso murió sin reportar (crash) o no confirma el cierre a tiempo
        if self.proceso_ia is not None and not self.proceso_ia.is_alive():
            self._finalizar_conteo(error="El proceso de conteo terminó inesperadamente.")
            return
        if self._cierre_limite is not None and time.monotonic() > self._cierre_limite:
            self.proceso_ia.terminate()
            self._finalizar_conteo(error="El proceso de conteo no respondió; se forzó el cierre.")
            return

        self.after(30, self._procesar_eventos_ia)

    def _finalizar_conteo(self, fin: FinConteo | None = None, error: str | None = None):
        """Cierra el proceso de IA y restaura la interfaz."""
        self.conteo_activo = False
        self._cierre_limite = None

        if self.proceso_ia is not None:
            self.proceso_ia.join(timeout=2.0)
            if self.proceso_ia.is_alive():
                self.proceso_ia.terminate()
            self.proceso_ia = None
        self.cola_eventos = None
        self.cola_comandos = None

        self._controles_en_conteo(False)
        self.camera_display.configure(image="", text="")
        self.camera_display.image = None
        self.fps_label.configure(text="FPS: 0")

        if error:
            self.estado_conteo_label.configure(text=error, text_color=COLOR["peligro"])
            messagebox.showerror("Conteo interrumpido", error, parent=self)
        elif fin:
            self.contador_label.configure(text=str(fin.total))
            self.estado_conteo_label.configure(
                text="Lote cerrado", text_color=COLOR["exito"]
            )
            # TODO Bloque 3: persistir la sesión en SQLite y sincronizar
            messagebox.showinfo(
                "Lote cerrado",
                f"Total contado: {fin.total}\n"
                f"Duración: {fin.duracion_segundos:.1f} s\n"
                f"FPS promedio: {fin.fps_promedio:.1f}",
                parent=self,
            )

    def _controles_en_conteo(self, contando: bool):
        """Ajusta los controles cuando el proceso de IA toma la cámara."""
        if contando:
            self.count_button.configure(
                text="Detener Conteo",
                fg_color=COLOR["peligro"],
                hover_color=COLOR["peligro_hover"],
                command=self.detener_conteo,
                state="normal",
            )
        else:
            self.count_button.configure(
                text="Iniciar Conteo IA",
                fg_color=COLOR["acento"],
                hover_color=COLOR["acento_hover"],
                command=self.iniciar_conteo,
                state="normal",
            )

        estado = "disabled" if contando else "normal"
        self.start_button.configure(state=estado)
        self.stop_button.configure(state="disabled")
        self.camera_type_menu.configure(state=estado)
        self.device_menu.configure(state=estado)
        self.ip_camera_entry.configure(state=estado)
        self.resolution_menu.configure(state=estado)
        self.linea_orientacion_menu.configure(state=estado)
        self.linea_posicion_slider.configure(state=estado)

    # ----- Pantalla completa y cierre -----

    def alternar_pantalla_completa(self, event=None):
        """Alterna entre modo pantalla completa y ventana normal."""
        self.fullscreen_state = not self.fullscreen_state
        if self.fullscreen_state:
            self.normal_geometry = self.geometry()
            self.attributes("-fullscreen", True)
        else:
            self.attributes("-fullscreen", False)
            if self.normal_geometry:
                self.geometry(self.normal_geometry)
            else:
                centrar_ventana(self)

    def salir_pantalla_completa(self, event=None):
        if self.fullscreen_state:
            self.alternar_pantalla_completa()

    def al_cerrar(self):
        """Maneja el cierre de la ventana."""
        if self.conteo_activo and self.proceso_ia is not None:
            # Cierre de ventana: no esperamos el resumen, solo soltar la cámara
            self.conteo_activo = False
            try:
                self.cola_comandos.put_nowait((CMD_DETENER,))
            except (cola_estandar.Full, AttributeError):
                pass
            self.proceso_ia.join(timeout=1.0)
            if self.proceso_ia.is_alive():
                self.proceso_ia.terminate()
        self.detener_captura()
        self.destroy()
        self.parent.deiconify()
