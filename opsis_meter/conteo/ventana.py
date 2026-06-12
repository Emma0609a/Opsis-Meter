"""
Ventana de Conteo - Opsis Meter
Vista de cámara y control de captura.

La captura corre en un hilo propio (captura.FlujoCamara); esta ventana
solo consume el último frame disponible desde un bucle de refresco con
after(), de modo que todas las operaciones de Tkinter ocurren en el hilo
principal.
"""

import threading
import tkinter.messagebox as messagebox

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

from opsis_meter.captura.camara import ESTADO_ERROR, FlujoCamara
from opsis_meter.captura.dispositivos import detectar_camaras
from opsis_meter.compartido.tema import COLOR, fuente
from opsis_meter.compartido.ventanas import centrar_ventana


class VentanaConteo(ctk.CTkToplevel):
    """Ventana de conteo con cámara."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Opsis Meter - Iniciar Conteo")
        self.geometry("1200x800")
        self.minsize(1100, 750)

        self.parent = parent

        # Captura de video
        self.flujo: FlujoCamara | None = None
        self.vista_activa = False
        self.fps_limite = 30

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

        buttons_frame = ctk.CTkFrame(controls_inner, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 25))

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
        self.detener_captura()
        self.destroy()
        self.parent.deiconify()
