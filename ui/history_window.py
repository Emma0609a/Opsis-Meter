"""
Ventana de Historial - Opsis Meter
Muestra el registro de conteos de limones desde Supabase
"""

import customtkinter as ctk
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class HistoryWindow(ctk.CTkToplevel):
    """Ventana de historial de conteos"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.title("Opsis Meter - Historial de Conteos")
        self.geometry("1100x750")
        self.minsize(1000, 700)
        
        # Referencia al menú principal
        self.parent = parent
        
        # Inicializar Supabase (se configurará desde variables de entorno)
        self.supabase: Client = None
        self._init_supabase()
        
        # Crear interfaz
        self.create_widgets()
        
        # Cargar datos
        self.load_data()
        
        # Centrar ventana
        self.center_window()
        
        # Protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _init_supabase(self):
        """Inicializa la conexión con Supabase"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
            else:
                # Supabase no configurado aún
                self.supabase = None
        except Exception as e:
            print(f"Error al inicializar Supabase: {e}")
            self.supabase = None
    
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
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color=["#1a1a1a", "#2b2b2b"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # ===== SECCIÓN SUPERIOR =====
        top_frame = ctk.CTkFrame(main_frame, fg_color=["#1f1f1f", "#2d2d2d"], corner_radius=15)
        top_frame.pack(fill="x", pady=(0, 20), padx=5)
        
        top_content = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_content.pack(fill="x", padx=25, pady=18)
        
        # Título
        title_label = ctk.CTkLabel(
            top_content,
            text="Historial de Conteos",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#4A90E2"
        )
        title_label.pack(side="left")
        
        # Botón regresar
        back_button = ctk.CTkButton(
            top_content,
            text="Regresar al Menú",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=40,
            width=180,
            fg_color="#5C7C9A",
            hover_color="#4A6B8A",
            corner_radius=12,
            command=self.on_closing
        )
        back_button.pack(side="right")
        
        # ===== SECCIÓN DE ESTADÍSTICAS =====
        stats_frame = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=["#1f1f1f", "#2d2d2d"])
        stats_frame.pack(fill="x", padx=5, pady=(0, 20))
        
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=25, pady=20)
        
        stats_title = ctk.CTkLabel(
            stats_inner,
            text="Estadísticas Generales",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#4A90E2"
        )
        stats_title.pack(anchor="w", pady=(0, 15))
        
        # Grid de estadísticas
        stats_grid = ctk.CTkFrame(stats_inner, fg_color="transparent")
        stats_grid.pack(fill="x")
        
        # Total de sesiones
        self.total_sessions_label = ctk.CTkLabel(
            stats_grid,
            text="Total Sesiones: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            anchor="w"
        )
        self.total_sessions_label.grid(row=0, column=0, padx=(0, 30), sticky="w")
        
        # Total de limones
        self.total_lemons_label = ctk.CTkLabel(
            stats_grid,
            text="Total Limones: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            anchor="w"
        )
        self.total_lemons_label.grid(row=0, column=1, padx=(0, 30), sticky="w")
        
        # Promedio
        self.avg_lemons_label = ctk.CTkLabel(
            stats_grid,
            text="Promedio: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            anchor="w"
        )
        self.avg_lemons_label.grid(row=0, column=2, sticky="w")
        
        # ===== TABLA DE REGISTROS =====
        table_frame = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=["#1f1f1f", "#2d2d2d"])
        table_frame.pack(fill="both", expand=True, padx=5)
        
        table_inner = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Encabezado de tabla
        header_frame = ctk.CTkFrame(table_inner, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        headers = ["Fecha", "Hora", "Cantidad", "Duración", "Resolución", "FPS", "Acciones"]
        widths = [100, 80, 80, 100, 120, 70, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            header_label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                width=width,
                anchor="w"
            )
            header_label.grid(row=0, column=i, padx=5, sticky="w")
        
        # Frame scrollable para registros
        self.records_scroll = ctk.CTkScrollableFrame(table_inner, fg_color="transparent")
        self.records_scroll.pack(fill="both", expand=True)
        
        # Botón actualizar
        refresh_button = ctk.CTkButton(
            table_inner,
            text="Actualizar",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            height=35,
            fg_color="#4A90E2",
            hover_color="#357ABD",
            corner_radius=10,
            command=self.load_data
        )
        refresh_button.pack(pady=(15, 0))
    
    def load_data(self):
        """Carga los datos desde Supabase"""
        # Limpiar registros anteriores
        for widget in self.records_scroll.winfo_children():
            widget.destroy()
        
        sessions = []
        
        if self.supabase:
            try:
                # Obtener sesiones desde Supabase
                response = self.supabase.table("counting_sessions").select("*").order("timestamp", desc=True).execute()
                sessions = response.data if response.data else []
            except Exception as e:
                print(f"Error al cargar datos de Supabase: {e}")
                # Mostrar mensaje de error
                error_label = ctk.CTkLabel(
                    self.records_scroll,
                    text=f"Error al conectar con Supabase.\nVerifica la configuración.",
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color="#F44336"
                )
                error_label.pack(pady=50)
                return
        
        # Mostrar registros
        for session in sessions:
            self.add_record_row(session)
        
        # Actualizar estadísticas
        stats = self._calculate_statistics(sessions)
        self.total_sessions_label.configure(text=f"Total Sesiones: {stats['total_sessions']}")
        self.total_lemons_label.configure(text=f"Total Limones: {stats['total_lemons']}")
        self.avg_lemons_label.configure(text=f"Promedio: {stats['avg_lemons']}")
        
        # Si no hay registros, mostrar mensaje
        if not sessions:
            no_data_label = ctk.CTkLabel(
                self.records_scroll,
                text="No hay registros de conteo aún.\nRealiza un conteo para ver los registros aquí.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color="#909090"
            )
            no_data_label.pack(pady=50)
    
    def _calculate_statistics(self, sessions):
        """Calcula estadísticas desde los datos"""
        if not sessions:
            return {
                "total_sessions": 0,
                "total_lemons": 0,
                "avg_lemons": 0
            }
        
        total_sessions = len(sessions)
        total_lemons = sum(s.get('lemon_count', 0) for s in sessions)
        avg_lemons = total_lemons / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "total_lemons": total_lemons,
            "avg_lemons": round(avg_lemons, 2)
        }
    
    def add_record_row(self, session):
        """Agrega una fila de registro a la tabla"""
        row_frame = ctk.CTkFrame(self.records_scroll, fg_color="transparent")
        row_frame.pack(fill="x", pady=5)
        
        # Parsear timestamp de Supabase
        timestamp_str = session.get('timestamp', '')
        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                time_str = dt.strftime('%H:%M:%S')
            except:
                date_str = 'N/A'
                time_str = 'N/A'
        else:
            date_str = 'N/A'
            time_str = 'N/A'
        
        # Fecha
        date_label = ctk.CTkLabel(
            row_frame,
            text=date_str,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=100,
            anchor="w"
        )
        date_label.grid(row=0, column=0, padx=5, sticky="w")
        
        # Hora
        time_label = ctk.CTkLabel(
            row_frame,
            text=time_str,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=80,
            anchor="w"
        )
        time_label.grid(row=0, column=1, padx=5, sticky="w")
        
        # Cantidad
        count_label = ctk.CTkLabel(
            row_frame,
            text=str(session.get('lemon_count', 0)),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#4CAF50",
            width=80,
            anchor="w"
        )
        count_label.grid(row=0, column=2, padx=5, sticky="w")
        
        # Duración
        duration = session.get('duration_seconds', 0)
        duration_str = f"{duration:.1f}s" if duration else "N/A"
        duration_label = ctk.CTkLabel(
            row_frame,
            text=duration_str,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=100,
            anchor="w"
        )
        duration_label.grid(row=0, column=3, padx=5, sticky="w")
        
        # Resolución
        res_w = session.get('resolution_width', 0)
        res_h = session.get('resolution_height', 0)
        res_str = f"{res_w}x{res_h}" if res_w and res_h else "N/A"
        res_label = ctk.CTkLabel(
            row_frame,
            text=res_str,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=120,
            anchor="w"
        )
        res_label.grid(row=0, column=4, padx=5, sticky="w")
        
        # FPS
        fps = session.get('fps_average', 0)
        fps_str = f"{fps:.1f}" if fps else "N/A"
        fps_label = ctk.CTkLabel(
            row_frame,
            text=fps_str,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=70,
            anchor="w"
        )
        fps_label.grid(row=0, column=5, padx=5, sticky="w")
        
        # Botón eliminar
        delete_btn = ctk.CTkButton(
            row_frame,
            text="Eliminar",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=80,
            height=25,
            fg_color="#F44336",
            hover_color="#D32F2F",
            corner_radius=8,
            command=lambda sid=session['id']: self.delete_session(sid)
        )
        delete_btn.grid(row=0, column=6, padx=5)
    
    def delete_session(self, session_id):
        """Elimina una sesión desde Supabase"""
        if self.supabase:
            try:
                self.supabase.table("counting_sessions").delete().eq("id", session_id).execute()
                self.load_data()  # Recargar datos
            except Exception as e:
                print(f"Error al eliminar sesión: {e}")
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", f"No se pudo eliminar la sesión: {str(e)}")
    
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        self.destroy()
        self.parent.deiconify()  # Mostrar ventana principal

