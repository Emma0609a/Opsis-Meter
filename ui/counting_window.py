"""
Ventana de Conteo - Opsis Meter
Vista de cámara y control de captura
"""

import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import threading
import time


class CountingWindow(ctk.CTkToplevel):
    """Ventana de conteo con cámara"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuración de la ventana (más grande y armoniosa)
        self.title("Opsis Meter - Iniciar Conteo")
        self.geometry("1200x800")
        self.minsize(1100, 750)
        
        # Referencia al menú principal
        self.parent = parent
        
        # Variables de control
        self.camera = None
        self.capture_active = False
        self.frame = None
        self.thread = None
        self.fps_limit = 30
        self.fps_actual = 0
        self.last_frame_time = 0
        
        # Estado de pantalla completa
        self.fullscreen_state = False
        self.normal_geometry = None
        
        # Tipo de cámara: 'local' o 'ip'
        self.camera_type = 'local'
        
        # Dispositivos disponibles
        self.available_devices = []
        self.current_device = 0
        self.current_resolution = (640, 480)
        
        # URL/IP de cámara IP
        self.ip_camera_url = ""
        
        # Crear interfaz
        self.create_widgets()
        
        # Detectar dispositivos disponibles
        self.detect_devices()
        
        # Centrar ventana
        self.center_window()
        
        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind para pantalla completa (F11)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def detect_devices(self):
        """Detecta las cámaras disponibles en el sistema"""
        self.available_devices = []
        # Probar hasta 5 dispositivos
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.available_devices.append(i)
                cap.release()
        
        # Si no hay dispositivos, agregar uno por defecto
        if not self.available_devices:
            self.available_devices = [0]
        
        self.current_device = self.available_devices[0]
        self.update_device_menu()
    
    def update_device_menu(self):
        """Actualiza el menú de dispositivos"""
        self.device_menu.configure(values=[f"Cámara {i}" for i in self.available_devices])
        if self.available_devices:
            self.device_menu.set(f"Cámara {self.current_device}")
    
    def create_widgets(self):
        """Crea los widgets de la interfaz"""
        
        # Frame principal con fondo suave
        main_frame = ctk.CTkFrame(self, fg_color=("#1a1a1a", "#2b2b2b"))
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # ===== SECCIÓN SUPERIOR: Título y controles =====
        top_frame = ctk.CTkFrame(main_frame, fg_color=("#1f1f1f", "#2d2d2d"), corner_radius=15)
        top_frame.pack(fill="x", pady=(0, 20), padx=5)
        
        # Frame interno para contenido superior
        top_content = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_content.pack(fill="x", padx=25, pady=18)
        
        # Título
        title_label = ctk.CTkLabel(
            top_content,
            text="Iniciar Conteo",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color="#4A90E2"
        )
        title_label.pack(side="left")
        
        # Botón regresar - diseño mejorado
        back_button = ctk.CTkButton(
            top_content,
            text="Regresar",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=42,
            width=160,
            fg_color="#5C7C9A",
            hover_color="#4A6B8A",
            corner_radius=14,
            border_width=0,
            command=self.on_closing
        )
        back_button.pack(side="right")
        
        # ===== CONTENEDOR PRINCIPAL: Cámara y controles =====
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # ===== PANEL IZQUIERDO: Vista de cámara =====
        camera_frame = ctk.CTkFrame(content_frame, corner_radius=18, fg_color=("#1f1f1f", "#2d2d2d"))
        camera_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Frame interno para cámara
        camera_inner = ctk.CTkFrame(camera_frame, fg_color="transparent")
        camera_inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Etiqueta de vista previa con mejor diseño
        preview_header = ctk.CTkFrame(camera_inner, fg_color="transparent")
        preview_header.pack(fill="x", pady=(0, 20))
        
        preview_label = ctk.CTkLabel(
            preview_header,
            text="Vista Previa",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        )
        preview_label.pack(side="left")
        
        # Información de FPS en el header
        self.fps_label = ctk.CTkLabel(
            preview_header,
            text="FPS: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#4CAF50"
        )
        self.fps_label.pack(side="right")
        
        # Frame para la imagen de la cámara con fondo
        self.camera_display_frame = ctk.CTkFrame(camera_inner, corner_radius=12, fg_color="#0a0a0a")
        self.camera_display_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        self.camera_display = ctk.CTkLabel(
            self.camera_display_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#707070"
        )
        self.camera_display.pack(expand=True, fill="both", padx=15, pady=15)
        
        # ===== PANEL DERECHO: Controles y opciones =====
        controls_frame = ctk.CTkFrame(content_frame, corner_radius=18, fg_color=("#1f1f1f", "#2d2d2d"), width=380)
        controls_frame.pack(side="right", fill="y", padx=(0, 0))
        controls_frame.pack_propagate(False)
        
        # Frame interno para controles
        controls_inner = ctk.CTkFrame(controls_frame, fg_color="transparent")
        controls_inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Título de controles
        controls_title = ctk.CTkLabel(
            controls_inner,
            text="Controles",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#4A90E2"
        )
        controls_title.pack(pady=(0, 20))
        
        # ===== BOTONES DE CONTROL =====
        buttons_frame = ctk.CTkFrame(controls_inner, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 25))
        
        # Botón iniciar captura - diseño mejorado
        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Iniciar Captura",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            height=60,
            fg_color="#4CAF50",
            hover_color="#45A049",
            corner_radius=18,
            border_width=0,
            border_spacing=10,
            command=self.start_capture
        )
        self.start_button.pack(fill="x", pady=(0, 15))
        
        # Botón detener captura - diseño mejorado
        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="Detener Captura",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            height=60,
            fg_color="#F44336",
            hover_color="#D32F2F",
            corner_radius=18,
            border_width=0,
            border_spacing=10,
            command=self.stop_capture,
            state="disabled"
        )
        self.stop_button.pack(fill="x")
        
        # Separador decorativo
        separator_frame = ctk.CTkFrame(controls_inner, fg_color="transparent")
        separator_frame.pack(fill="x", pady=(0, 20))
        
        separator = ctk.CTkFrame(separator_frame, height=2, fg_color="#4A90E2")
        separator.pack(fill="x", padx=10)
        
        # ===== OPCIONES (Scrollable Frame) =====
        options_title = ctk.CTkLabel(
            controls_inner,
            text="Opciones",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#4A90E2"
        )
        options_title.pack(pady=(0, 15))
        
        # Frame scrollable para opciones
        scrollable_frame = ctk.CTkScrollableFrame(controls_inner, fg_color="transparent", corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True)
        
        # Tipo de Cámara
        camera_type_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        camera_type_container.pack(fill="x", pady=(0, 20))
        
        camera_type_label = ctk.CTkLabel(
            camera_type_container,
            text="Tipo de Cámara:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w"
        )
        camera_type_label.pack(fill="x", pady=(0, 8))
        
        self.camera_type_menu = ctk.CTkComboBox(
            camera_type_container,
            values=["Cámara Local", "Cámara IP"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self.on_camera_type_change,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color="#5C7C9A",
            button_color="#5C7C9A",
            button_hover_color="#4A6B8A"
        )
        self.camera_type_menu.set("Cámara Local")
        self.camera_type_menu.pack(fill="x")
        
        # Dispositivo Local (solo visible cuando tipo es "Local")
        self.device_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        self.device_container.pack(fill="x", pady=(0, 20))
        
        device_label = ctk.CTkLabel(
            self.device_container,
            text="Dispositivo:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w"
        )
        device_label.pack(fill="x", pady=(0, 8))
        
        self.device_menu = ctk.CTkComboBox(
            self.device_container,
            values=["Cámara 0"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self.on_device_change,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color="#5C7C9A",
            button_color="#5C7C9A",
            button_hover_color="#4A6B8A"
        )
        self.device_menu.pack(fill="x")
        
        # Configuración de Cámara IP (solo visible cuando tipo es "IP")
        self.ip_camera_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        # Inicialmente oculto
        self.ip_camera_container.pack_forget()
        
        ip_camera_label = ctk.CTkLabel(
            self.ip_camera_container,
            text="URL/IP de Cámara:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w"
        )
        ip_camera_label.pack(fill="x", pady=(0, 8))
        
        self.ip_camera_entry = ctk.CTkEntry(
            self.ip_camera_container,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            height=42,
            corner_radius=12,
            border_width=2,
            border_color="#5C7C9A",
            placeholder_text="rtsp://usuario:contraseña@ip:puerto/ruta"
        )
        self.ip_camera_entry.pack(fill="x", pady=(0, 8))
        
        # Info sobre formatos soportados
        ip_info_label = ctk.CTkLabel(
            self.ip_camera_container,
            text="Formatos soportados: RTSP, HTTP, MJPEG\nEjemplo: rtsp://admin:1234@192.168.1.100:554/stream",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#707070",
            anchor="w",
            justify="left"
        )
        ip_info_label.pack(fill="x")
        
        # Resolución
        resolution_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        resolution_container.pack(fill="x", pady=(0, 20))
        
        resolution_label = ctk.CTkLabel(
            resolution_container,
            text="Resolución:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w"
        )
        resolution_label.pack(fill="x", pady=(0, 8))
        
        self.resolution_menu = ctk.CTkComboBox(
            resolution_container,
            values=["640x480", "800x600", "1024x768", "1280x720", "1920x1080"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            command=self.on_resolution_change,
            state="normal",
            height=42,
            corner_radius=12,
            border_width=2,
            border_color="#5C7C9A",
            button_color="#5C7C9A",
            button_hover_color="#4A6B8A"
        )
        self.resolution_menu.set("640x480")
        self.resolution_menu.pack(fill="x")
        
        # FPS Limit - Opción 1: Slider
        fps_container = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        fps_container.pack(fill="x", pady=(0, 20))
        
        fps_label = ctk.CTkLabel(
            fps_container,
            text="Límite de FPS:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w"
        )
        fps_label.pack(fill="x", pady=(0, 12))
        
        # Opción 1: Slider
        slider_frame = ctk.CTkFrame(fps_container, fg_color="transparent")
        slider_frame.pack(fill="x", pady=(0, 15))
        
        self.fps_slider = ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=60,
            number_of_steps=59,
            command=self.on_fps_slider_change,
            height=20
        )
        self.fps_slider.set(30)
        self.fps_slider.pack(fill="x", side="left", expand=True)
        
        # Opción 2: Control numérico con botones
        numeric_frame = ctk.CTkFrame(fps_container, fg_color="transparent")
        numeric_frame.pack(fill="x")
        
        # Botón disminuir - diseño mejorado
        decrease_btn = ctk.CTkButton(
            numeric_frame,
            text="-",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            width=50,
            height=42,
            fg_color="#5C7C9A",
            hover_color="#4A6B8A",
            corner_radius=12,
            border_width=0,
            command=self.decrease_fps
        )
        decrease_btn.pack(side="left", padx=(0, 12))
        
        # Campo de entrada numérico - diseño mejorado
        self.fps_entry = ctk.CTkEntry(
            numeric_frame,
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=110,
            height=42,
            corner_radius=12,
            justify="center",
            border_width=2,
            border_color="#5C7C9A"
        )
        self.fps_entry.insert(0, "30")
        self.fps_entry.pack(side="left", padx=(0, 12))
        self.fps_entry.bind("<Return>", self.on_fps_entry_change)
        self.fps_entry.bind("<FocusOut>", self.on_fps_entry_change)
        
        # Label FPS al lado del entry
        fps_unit_short = ctk.CTkLabel(
            numeric_frame,
            text="FPS",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#B0B0B0"
        )
        fps_unit_short.pack(side="left", padx=(0, 12))
        
        # Botón aumentar - diseño mejorado
        increase_btn = ctk.CTkButton(
            numeric_frame,
            text="+",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            width=50,
            height=42,
            fg_color="#5C7C9A",
            hover_color="#4A6B8A",
            corner_radius=12,
            border_width=0,
            command=self.increase_fps
        )
        increase_btn.pack(side="left")
        
        # Info adicional
        fps_info = ctk.CTkLabel(
            fps_container,
            text="Rango: 1-60 FPS",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#707070"
        )
        fps_info.pack(anchor="w", pady=(8, 0))
    
    def on_camera_type_change(self, choice):
        """Maneja el cambio de tipo de cámara"""
        if choice == "Cámara Local":
            self.camera_type = 'local'
            self.device_container.pack(fill="x", pady=(0, 20))
            self.ip_camera_container.pack_forget()
        else:  # Cámara IP
            self.camera_type = 'ip'
            self.device_container.pack_forget()
            self.ip_camera_container.pack(fill="x", pady=(0, 20))
        
        # Si hay captura activa, detenerla
        if self.capture_active:
            self.stop_capture()
    
    def on_device_change(self, choice):
        """Maneja el cambio de dispositivo"""
        device_str = choice.replace("Cámara ", "")
        try:
            self.current_device = int(device_str)
            if self.capture_active:
                self.stop_capture()
                self.start_capture()
        except ValueError:
            pass
    
    def on_resolution_change(self, choice):
        """Maneja el cambio de resolución"""
        try:
            width, height = map(int, choice.split('x'))
            self.current_resolution = (width, height)
            if self.camera and self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        except ValueError:
            pass
    
    def on_fps_slider_change(self, value):
        """Maneja el cambio de FPS desde el slider"""
        self.fps_limit = int(value)
        self.fps_entry.delete(0, "end")
        self.fps_entry.insert(0, str(self.fps_limit))
    
    def on_fps_entry_change(self, event=None):
        """Maneja el cambio de FPS desde el campo de entrada"""
        try:
            value = int(self.fps_entry.get())
            if 1 <= value <= 60:
                self.fps_limit = value
                self.fps_slider.set(value)
            else:
                # Valor fuera de rango, restaurar
                self.fps_entry.delete(0, "end")
                self.fps_entry.insert(0, str(self.fps_limit))
                self.fps_slider.set(self.fps_limit)
        except ValueError:
            # Valor no numérico, restaurar
            self.fps_entry.delete(0, "end")
            self.fps_entry.insert(0, str(self.fps_limit))
    
    def increase_fps(self):
        """Aumenta los FPS en 1"""
        if self.fps_limit < 60:
            self.fps_limit += 1
            self.fps_slider.set(self.fps_limit)
            self.fps_entry.delete(0, "end")
            self.fps_entry.insert(0, str(self.fps_limit))
    
    def decrease_fps(self):
        """Disminuye los FPS en 1"""
        if self.fps_limit > 1:
            self.fps_limit -= 1
            self.fps_slider.set(self.fps_limit)
            self.fps_entry.delete(0, "end")
            self.fps_entry.insert(0, str(self.fps_limit))
    
    def start_capture(self):
        """Inicia la captura de video"""
        try:
            # Determinar la fuente según el tipo de cámara
            if self.camera_type == 'ip':
                # Cámara IP: obtener URL del campo de entrada
                self.ip_camera_url = self.ip_camera_entry.get().strip()
                if not self.ip_camera_url:
                    raise Exception("Por favor, ingresa la URL/IP de la cámara")
                
                # Intentar conectar a la cámara IP
                self.camera = cv2.VideoCapture(self.ip_camera_url)
                
                # Configurar timeout para conexión IP (algunas cámaras IP son lentas)
                # Nota: OpenCV no tiene timeout directo, pero podemos verificar si se abre
                if not self.camera.isOpened():
                    raise Exception(f"No se pudo conectar a la cámara IP: {self.ip_camera_url}\nVerifica la URL y la conexión de red.")
            else:
                # Cámara local: usar índice de dispositivo
                self.camera = cv2.VideoCapture(self.current_device)
                if not self.camera.isOpened():
                    raise Exception(f"No se pudo abrir la cámara local (dispositivo {self.current_device})")
            
            # Configurar resolución (solo para cámaras locales, las IP ya tienen su resolución)
            if self.camera_type == 'local':
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.current_resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.current_resolution[1])
            
            # Configurar buffer más pequeño para cámaras IP (reduce latencia)
            if self.camera_type == 'ip':
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.capture_active = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
            # Deshabilitar controles durante la captura
            self.camera_type_menu.configure(state="disabled")
            if self.camera_type == 'ip':
                self.ip_camera_entry.configure(state="disabled")
            else:
                self.device_menu.configure(state="disabled")
            
            # Iniciar thread de captura
            self.thread = threading.Thread(target=self.capture_loop, daemon=True)
            self.thread.start()
            
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", f"No se pudo iniciar la cámara: {str(e)}")
            self.capture_active = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            # Rehabilitar controles
            self.camera_type_menu.configure(state="normal")
            if self.camera_type == 'ip':
                self.ip_camera_entry.configure(state="normal")
            else:
                self.device_menu.configure(state="normal")
    
    def stop_capture(self):
        """Detiene la captura de video"""
        self.capture_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        # Rehabilitar controles
        self.camera_type_menu.configure(state="normal")
        if self.camera_type == 'ip':
            self.ip_camera_entry.configure(state="normal")
        else:
            self.device_menu.configure(state="normal")
        
        # Limpiar display sin mostrar mensaje
        self.camera_display.configure(image="", text="")
        self.fps_label.configure(text="FPS: 0")
    
    def capture_loop(self):
        """Loop de captura en thread separado"""
        frame_time = 1.0 / self.fps_limit if self.fps_limit > 0 else 0
        consecutive_failures = 0
        max_failures = 10  # Máximo de fallos consecutivos antes de detener
        
        while self.capture_active and self.camera:
            try:
                start_time = time.time()
                
                # Verificar que la cámara sigue abierta
                if not self.camera.isOpened():
                    if self.capture_active:
                        # Intentar reconectar
                        time.sleep(0.5)
                        if self.camera_type == 'ip' and self.ip_camera_url:
                            self.camera = cv2.VideoCapture(self.ip_camera_url)
                        else:
                            self.camera = cv2.VideoCapture(self.current_device)
                        if not self.camera.isOpened():
                            consecutive_failures += 1
                            if consecutive_failures >= max_failures:
                                break
                            continue
                        consecutive_failures = 0
                    else:
                        break
                
                ret, frame = self.camera.read()
                if not ret:
                    consecutive_failures += 1
                    # Si no hay frame, puede ser un problema de conexión (especialmente con IP)
                    if self.camera_type == 'ip':
                        # Intentar reconectar después de un breve delay
                        time.sleep(0.5)
                        if consecutive_failures < max_failures:
                            continue
                        else:
                            break
                    else:
                        # Para cámaras locales, si falla varias veces, puede ser un problema
                        if consecutive_failures < max_failures:
                            time.sleep(0.1)
                            continue
                        else:
                            break
                
                # Resetear contador de fallos si se lee correctamente
                consecutive_failures = 0
                
                # Redimensionar frame (solo si es necesario)
                if self.camera_type == 'local':
                    frame = cv2.resize(frame, self.current_resolution)
                    frame_height, frame_width = self.current_resolution[1], self.current_resolution[0]
                else:
                    # Para cámaras IP, usar las dimensiones reales del frame
                    frame_height, frame_width = frame.shape[:2]
                
                # Convertir BGR a RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convertir a PIL Image
                image = Image.fromarray(frame_rgb)
                
                # Redimensionar para mostrar (adaptar al tamaño disponible)
                # Obtener el tamaño del frame de display
                display_frame_width = self.camera_display_frame.winfo_width() - 30
                display_frame_height = self.camera_display_frame.winfo_height() - 30
                
                if display_frame_width > 1 and display_frame_height > 1:
                    # Calcular tamaño manteniendo aspecto
                    aspect_ratio = frame_width / frame_height
                    display_aspect = display_frame_width / display_frame_height
                    
                    if aspect_ratio > display_aspect:
                        # Frame más ancho que el display
                        display_width = display_frame_width
                        display_height = int(display_frame_width / aspect_ratio)
                    else:
                        # Frame más alto que el display
                        display_height = display_frame_height
                        display_width = int(display_frame_height * aspect_ratio)
                    
                    # Asegurar mínimo
                    if display_width < 100:
                        display_width = 720
                        display_height = int(display_width / aspect_ratio)
                else:
                    # Si no se puede obtener el tamaño, usar valores por defecto
                    display_width = 720
                    display_height = int(display_width * (frame_height / frame_width))
                
                image = image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(image=image)
                
                # Actualizar display en el thread principal
                self.after(0, self.update_frame, photo)
                
                # Calcular FPS
                elapsed = time.time() - start_time
                if elapsed > 0:
                    self.fps_actual = 1.0 / elapsed
                    self.after(0, self.update_fps)
                
                # Limitar FPS
                sleep_time = frame_time - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Error en captura: {e}")
                break
        
        # Limpiar al finalizar
        if self.camera:
            self.camera.release()
    
    def update_frame(self, photo):
        """Actualiza el frame en el thread principal"""
        self.camera_display.configure(image=photo)
        self.camera_display.image = photo  # Mantener referencia
    
    def update_fps(self):
        """Actualiza la etiqueta de FPS"""
        self.fps_label.configure(text=f"FPS: {int(self.fps_actual)}")
    
    def toggle_fullscreen(self, event=None):
        """Alterna entre modo pantalla completa y ventana normal"""
        self.fullscreen_state = not self.fullscreen_state
        
        if self.fullscreen_state:
            # Guardar geometría actual
            self.normal_geometry = self.geometry()
            # Entrar en pantalla completa
            self.attributes('-fullscreen', True)
        else:
            # Salir de pantalla completa
            self.attributes('-fullscreen', False)
            # Restaurar geometría si estaba guardada
            if self.normal_geometry:
                self.geometry(self.normal_geometry)
            else:
                self.center_window()
    
    def exit_fullscreen(self, event=None):
        """Sale del modo pantalla completa"""
        if self.fullscreen_state:
            self.toggle_fullscreen()
    
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        self.stop_capture()
        self.destroy()
        self.parent.deiconify()  # Mostrar ventana principal

