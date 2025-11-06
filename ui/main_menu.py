"""
Menú Principal - Opsis Meter
Sistema de conteo de limones con IA
"""

# Configurar path si se ejecuta directamente (no como módulo)
import sys
import os
if __name__ == "__main__":
    # Si se ejecuta directamente, agregar el directorio padre al path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    import customtkinter as ctk  # type: ignore
except ImportError:
    raise ImportError(
        "customtkinter no está instalado. "
        "Instálalo con: pip install customtkinter"
    )

# Configuración de CustomTkinter (solo una vez)
_CTK_CONFIGURED = False

def _configure_ctk():
    """Configura CustomTkinter solo una vez"""
    global _CTK_CONFIGURED
    if not _CTK_CONFIGURED:
        ctk.set_appearance_mode("dark")  # Modos: "light", "dark", "system"
        ctk.set_default_color_theme("blue")  # Temas: "blue", "green", "dark-blue"
        _CTK_CONFIGURED = True

# Configurar al importar el módulo
_configure_ctk()


class MainMenu(ctk.CTk):
    """Ventana principal del menú de Opsis Meter"""
    
    def __init__(self):
        try:
            super().__init__()
            
            # Configuración de la ventana (más alta que ancha)
            self.title("Opsis Meter - Contador de Limones")
            self.geometry("700x900")
            self.minsize(600, 800)
            # Permitir redimensionamiento
            self.resizable(True, True)
            
            # Crear interfaz
            self.create_widgets()
            
            # Centrar ventana en pantalla (después de crear widgets)
            self.after(100, self.center_window)  # Usar after para asegurar que se ejecute después
            
        except Exception as e:
            print(f"Error al inicializar la ventana: {e}")
            raise
    
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
    
    def create_widgets(self):
        """Crea los widgets de la interfaz"""
        
        # Frame principal con padding y fondo sutil
        main_frame = ctk.CTkFrame(self, fg_color=("#1a1a1a", "#2b2b2b"))
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # ===== SECCIÓN DE ENCABEZADO =====
        header_frame = ctk.CTkFrame(main_frame, fg_color=("#1f1f1f", "#2d2d2d"), corner_radius=20)
        header_frame.pack(fill="x", pady=(0, 25), padx=5)
        
        # Frame interno para contenido del header
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=25, pady=25)
        
        # Título principal con estilo mejorado (más vibrante)
        title_label = ctk.CTkLabel(
            header_content,
            text="OPSIS METER",
            font=ctk.CTkFont(family="Segoe UI", size=48, weight="bold"),
            text_color="#5C9EFF"  # Azul más brillante
        )
        title_label.pack(pady=(5, 12))
        
        # Línea decorativa con gradiente visual
        separator1 = ctk.CTkFrame(header_content, height=3, fg_color="#5C9EFF")
        separator1.pack(fill="x", pady=(0, 12))
        
        # Subtítulo con mejor descripción (más visible)
        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Sistema Inteligente de Conteo de Limones",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#D0D0D0"  # Más brillante
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Descripción adicional con mejor formato (más visible)
        description_label = ctk.CTkLabel(
            header_content,
            text="Powered by YOLOv11n AI • Roboflow Integration",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#8A8A8A"  # Más visible
        )
        description_label.pack()
        
        # ===== SECCIÓN DE BOTONES PRINCIPALES =====
        buttons_container = ctk.CTkFrame(main_frame, fg_color=("#1f1f1f", "#2d2d2d"), corner_radius=20)
        buttons_container.pack(fill="both", expand=True, pady=(0, 20), padx=5)
        
        # Frame interno para botones
        buttons_inner = ctk.CTkFrame(buttons_container, fg_color="transparent")
        buttons_inner.pack(expand=True, fill="both", padx=25, pady=25)
        
        # Grid para organizar botones (2 columnas) - escalable
        buttons_frame = ctk.CTkFrame(buttons_inner, fg_color="transparent")
        buttons_frame.pack(expand=True, fill="both")
        # Configurar para escalado
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_rowconfigure(1, weight=1)
        
        # Botón 1: Iniciar Conteo (Principal - más vibrante y llamativo)
        start_button = ctk.CTkButton(
            buttons_frame,
            text="Iniciar Conteo",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            height=100,
            fg_color="#4CAF50",  # Verde vibrante
            hover_color="#45A049",
            corner_radius=22,
            border_width=0,
            border_spacing=15,
            command=self.start_counting
        )
        start_button.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 20), sticky="ew")
        
        # Botón 2: Ver Historial (más vibrante)
        history_button = ctk.CTkButton(
            buttons_frame,
            text="Ver Historial",
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            height=85,
            fg_color="#5C9EFF",  # Azul brillante
            hover_color="#4A8EFF",
            corner_radius=20,
            border_width=0,
            command=self.view_history
        )
        history_button.grid(row=1, column=0, padx=(20, 12), pady=15, sticky="ew")
        
        # Botón 3: Configuración (más vibrante)
        settings_button = ctk.CTkButton(
            buttons_frame,
            text="Configuración",
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            height=85,
            fg_color="#FF9800",  # Naranja vibrante
            hover_color="#F57C00",
            corner_radius=20,
            border_width=0,
            command=self.open_settings
        )
        settings_button.grid(row=1, column=1, padx=(12, 20), pady=15, sticky="ew")
        
        # Configurar columnas para que se expandan
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # ===== SECCIÓN DE INFORMACIÓN DEL SISTEMA =====
        info_container = ctk.CTkFrame(main_frame, corner_radius=18, fg_color=("#1f1f1f", "#2d2d2d"))
        info_container.pack(fill="x", padx=5, pady=(0, 15))
        
        # Título de la sección de información
        info_title_frame = ctk.CTkFrame(info_container, fg_color="transparent")
        info_title_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        info_title = ctk.CTkLabel(
            info_title_frame,
            text="Información del Sistema",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            anchor="w",
            text_color="#5C9EFF"  # Azul brillante
        )
        info_title.pack(side="left")
        
        # Línea decorativa pequeña (más visible)
        separator2 = ctk.CTkFrame(info_title_frame, height=2, fg_color="#5C9EFF", width=50)
        separator2.pack(side="left", padx=(10, 0), fill="x", expand=True)
        
        # Frame interno para información
        info_inner = ctk.CTkFrame(info_container, fg_color="transparent")
        info_inner.pack(fill="x", padx=25, pady=(0, 20))
        
        # Última sesión
        session_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
        session_frame.pack(fill="x", pady=5)
        
        session_title = ctk.CTkLabel(
            session_frame,
            text="Última sesión:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            width=120,
            anchor="w",
            text_color="#D0D0D0"  # Más visible
        )
        session_title.pack(side="left", padx=(0, 10))
        
        self.session_label = ctk.CTkLabel(
            session_frame,
            text="No registrada",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#A0A0A0",  # Más visible
            anchor="w"
        )
        self.session_label.pack(side="left", fill="x", expand=True)
        
        # Modelo configurado
        model_frame = ctk.CTkFrame(info_inner, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)
        
        model_title = ctk.CTkLabel(
            model_frame,
            text="Modelo AI:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            width=120,
            anchor="w",
            text_color="#D0D0D0"  # Más visible
        )
        model_title.pack(side="left", padx=(0, 10))
        
        model_value = ctk.CTkLabel(
            model_frame,
            text="YOLOv11n (No configurado)",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color="#A0A0A0",  # Más visible
            anchor="w"
        )
        model_value.pack(side="left", fill="x", expand=True)
        
        # ===== AVISO DE VERSIÓN (DEMO) - Primero para que aparezca abajo =====
        version_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        version_frame.pack(side="bottom", fill="x", pady=(0, 8))
        
        version_label = ctk.CTkLabel(
            version_frame,
            text="OPSIS METER DEMO 0.1 BY ENIGMA",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#666666"  # Más visible
        )
        version_label.pack()
        
        # ===== SECCIÓN DE ESTADO (Abajo del todo, encima de la versión) =====
        status_container = ctk.CTkFrame(main_frame, corner_radius=18, fg_color=("#1a1a1a", "#252525"))
        status_container.pack(fill="x", padx=5, pady=(0, 5), side="bottom")
        
        # Frame interno para el estado
        status_inner = ctk.CTkFrame(status_container, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=15)
        
        # Estado del sistema con mejor diseño (más visible)
        status_title_label = ctk.CTkLabel(
            status_inner,
            text="Estado:",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w",
            text_color="#D0D0D0"  # Más visible
        )
        status_title_label.pack(side="left", padx=(0, 12))
        
        # Indicador visual del estado (más grande y brillante)
        status_indicator = ctk.CTkFrame(status_inner, width=10, height=10, corner_radius=5, fg_color="#4CAF50")
        status_indicator.pack(side="left", padx=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            status_inner,
            text="Listo para iniciar",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#4CAF50",
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # Guardar referencia del indicador para poder cambiarlo
        self.status_indicator = status_indicator
    
    def start_counting(self):
        """Abre la ventana de conteo"""
        try:
            # Intentar importación relativa primero (recomendado para paquetes)
            try:
                from .counting_window import CountingWindow
            except ImportError:
                # Fallback a importación absoluta si la relativa falla
                # Asegurar que el path esté configurado
                import sys
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(script_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from ui.counting_window import CountingWindow
            
            self.status_label.configure(text="Iniciando conteo...", text_color="#FFA500")
            self.status_indicator.configure(fg_color="#FFA500")
            
            # Ocultar ventana principal
            self.withdraw()
            
            # Abrir ventana de conteo
            counting_window = CountingWindow(self)
            counting_window.focus()
            
            # Restaurar estado
            self.after(1000, lambda: self._restore_status())
            
        except ImportError as e:
            self.status_label.configure(text="Error al cargar módulo", text_color="#F44336")
            self.status_indicator.configure(fg_color="#F44336")
            print(f"Error: {e}")
    
    def view_history(self):
        """Abre la ventana de historial"""
        try:
            # Intentar importación relativa primero (recomendado para paquetes)
            try:
                from .history_window import HistoryWindow
            except ImportError:
                # Fallback a importación absoluta si la relativa falla
                # Asegurar que el path esté configurado
                import sys
                import os
                script_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(script_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                from ui.history_window import HistoryWindow
            
            self.withdraw()
            history_window = HistoryWindow(self)
            history_window.focus()
            
        except ImportError as e:
            print(f"Error al cargar historial: {e}")
    
    def open_settings(self):
        """Abre la ventana de configuración"""
        # TODO: Implementar ventana de configuración (API keys, cámara, modelo)
        pass
    
    def _restore_status(self):
        """Restaura el estado a normal"""
        self.status_label.configure(text="Listo para iniciar", text_color="#4CAF50")
        self.status_indicator.configure(fg_color="#4CAF50")


def main():
    """Función principal para ejecutar la aplicación"""
    app = MainMenu()
    app.mainloop()


if __name__ == "__main__":
    main()


