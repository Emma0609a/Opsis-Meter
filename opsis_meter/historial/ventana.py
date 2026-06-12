"""
Ventana de Historial - Opsis Meter
Muestra el registro de conteos de limones desde Supabase.
Las consultas de red corren en hilos secundarios para no congelar la UI.
"""

import threading
import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime

import customtkinter as ctk

from opsis_meter.compartido.configuracion import cargar_configuracion
from opsis_meter.compartido.tema import COLOR, fuente
from opsis_meter.compartido.ventanas import centrar_ventana

LIMITE_REGISTROS = 200


class VentanaHistorial(ctk.CTkToplevel):
    """Ventana de historial de conteos."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Opsis Meter - Historial de Conteos")
        self.geometry("1100x750")
        self.minsize(1000, 700)

        self.parent = parent
        self._cargando = False

        self.supabase = None
        self._init_supabase()

        self.crear_widgets()
        self.cargar_datos()
        centrar_ventana(self)

        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def _init_supabase(self):
        """Inicializa la conexión con Supabase si está configurada."""
        config = cargar_configuracion()
        if not (config.supabase_url and config.supabase_key):
            return
        try:
            from supabase import create_client

            self.supabase = create_client(config.supabase_url, config.supabase_key)
        except Exception as e:
            print(f"Error al inicializar Supabase: {e}")
            self.supabase = None

    def crear_widgets(self):
        """Crea los widgets de la interfaz."""

        main_frame = ctk.CTkFrame(self, fg_color=COLOR["fondo"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        # ===== SECCIÓN SUPERIOR =====
        top_frame = ctk.CTkFrame(main_frame, fg_color=COLOR["panel"], corner_radius=15)
        top_frame.pack(fill="x", pady=(0, 20), padx=5)

        top_content = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_content.pack(fill="x", padx=25, pady=18)

        title_label = ctk.CTkLabel(
            top_content,
            text="Historial de Conteos",
            font=fuente(28, "bold"),
            text_color=COLOR["acento"],
        )
        title_label.pack(side="left")

        back_button = ctk.CTkButton(
            top_content,
            text="Regresar al Menú",
            font=fuente(15, "bold"),
            height=40,
            width=180,
            fg_color=COLOR["neutro"],
            hover_color=COLOR["neutro_hover"],
            corner_radius=12,
            command=self.al_cerrar,
        )
        back_button.pack(side="right")

        # ===== ESTADÍSTICAS =====
        stats_frame = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=COLOR["panel"])
        stats_frame.pack(fill="x", padx=5, pady=(0, 20))

        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(fill="x", padx=25, pady=20)

        stats_title = ctk.CTkLabel(
            stats_inner,
            text="Estadísticas Generales",
            font=fuente(18, "bold"),
            text_color=COLOR["acento"],
        )
        stats_title.pack(anchor="w", pady=(0, 15))

        stats_grid = ctk.CTkFrame(stats_inner, fg_color="transparent")
        stats_grid.pack(fill="x")

        self.total_sessions_label = ctk.CTkLabel(
            stats_grid, text="Total Sesiones: 0", font=fuente(14), anchor="w"
        )
        self.total_sessions_label.grid(row=0, column=0, padx=(0, 30), sticky="w")

        self.total_lemons_label = ctk.CTkLabel(
            stats_grid, text="Total Limones: 0", font=fuente(14), anchor="w"
        )
        self.total_lemons_label.grid(row=0, column=1, padx=(0, 30), sticky="w")

        self.avg_lemons_label = ctk.CTkLabel(
            stats_grid, text="Promedio: 0", font=fuente(14), anchor="w"
        )
        self.avg_lemons_label.grid(row=0, column=2, sticky="w")

        # ===== TABLA DE REGISTROS =====
        table_frame = ctk.CTkFrame(main_frame, corner_radius=15, fg_color=COLOR["panel"])
        table_frame.pack(fill="both", expand=True, padx=5)

        table_inner = ctk.CTkFrame(table_frame, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=25, pady=25)

        header_frame = ctk.CTkFrame(table_inner, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        encabezados = ["Fecha", "Hora", "Cantidad", "Duración", "Resolución", "FPS", "Acciones"]
        anchos = [100, 80, 80, 100, 120, 70, 100]

        for i, (encabezado, ancho) in enumerate(zip(encabezados, anchos)):
            header_label = ctk.CTkLabel(
                header_frame,
                text=encabezado,
                font=fuente(14, "bold"),
                width=ancho,
                anchor="w",
            )
            header_label.grid(row=0, column=i, padx=5, sticky="w")

        self.records_scroll = ctk.CTkScrollableFrame(table_inner, fg_color="transparent")
        self.records_scroll.pack(fill="both", expand=True)

        self.refresh_button = ctk.CTkButton(
            table_inner,
            text="Actualizar",
            font=fuente(14, "bold"),
            height=35,
            fg_color=COLOR["acento"],
            hover_color=COLOR["acento_hover"],
            corner_radius=10,
            command=self.cargar_datos,
        )
        self.refresh_button.pack(pady=(15, 0))

    # ----- Carga de datos (asíncrona) -----

    def cargar_datos(self):
        """Lanza la consulta a Supabase en un hilo secundario."""
        if self._cargando:
            return
        self._cargando = True
        self.refresh_button.configure(state="disabled")
        self._mostrar_mensaje("Cargando registros...", COLOR["texto_suave"])

        threading.Thread(target=self._consultar_sesiones, daemon=True).start()

    def _consultar_sesiones(self):
        """Consulta las sesiones (corre en hilo secundario, sin tocar la UI)."""
        sesiones, error = [], None
        if self.supabase:
            try:
                respuesta = (
                    self.supabase.table("counting_sessions")
                    .select("*")
                    .order("timestamp", desc=True)
                    .limit(LIMITE_REGISTROS)
                    .execute()
                )
                sesiones = respuesta.data or []
            except Exception as e:
                error = str(e)

        self._entregar_a_ui(lambda: self._aplicar_datos(sesiones, error))

    def _entregar_a_ui(self, accion):
        """Programa una acción en el hilo de la UI; ignora si la ventana cerró."""
        try:
            self.after(0, accion)
        except (tk.TclError, RuntimeError):
            pass

    def _aplicar_datos(self, sesiones, error):
        """Vuelca los resultados en la tabla (corre en el hilo de la UI)."""
        self._cargando = False
        self.refresh_button.configure(state="normal")
        self._limpiar_tabla()

        if error:
            print(f"Error al cargar datos de Supabase: {error}")
            self._mostrar_mensaje(
                "Error al conectar con Supabase.\nVerifica la configuración.",
                COLOR["peligro"],
            )
            return

        if self.supabase is None:
            self._mostrar_mensaje(
                "Supabase no está configurado.\nDefine SUPABASE_URL y SUPABASE_KEY en el archivo .env.",
                COLOR["texto_suave"],
            )

        for sesion in sesiones:
            self.agregar_fila(sesion)

        stats = self._calcular_estadisticas(sesiones)
        self.total_sessions_label.configure(text=f"Total Sesiones: {stats['total_sesiones']}")
        self.total_lemons_label.configure(text=f"Total Limones: {stats['total_limones']}")
        self.avg_lemons_label.configure(text=f"Promedio: {stats['promedio']}")

        if not sesiones and self.supabase is not None:
            self._mostrar_mensaje(
                "No hay registros de conteo aún.\nRealiza un conteo para ver los registros aquí.",
                COLOR["texto_suave"],
            )

    def _limpiar_tabla(self):
        for widget in self.records_scroll.winfo_children():
            widget.destroy()

    def _mostrar_mensaje(self, texto: str, color: str):
        self._limpiar_tabla()
        mensaje = ctk.CTkLabel(
            self.records_scroll,
            text=texto,
            font=fuente(14),
            text_color=color,
        )
        mensaje.pack(pady=50)

    def _calcular_estadisticas(self, sesiones):
        """Calcula estadísticas desde los datos."""
        if not sesiones:
            return {"total_sesiones": 0, "total_limones": 0, "promedio": 0}

        total_sesiones = len(sesiones)
        total_limones = sum(s.get("lemon_count", 0) for s in sesiones)
        return {
            "total_sesiones": total_sesiones,
            "total_limones": total_limones,
            "promedio": round(total_limones / total_sesiones, 2),
        }

    def agregar_fila(self, sesion):
        """Agrega una fila de registro a la tabla."""
        row_frame = ctk.CTkFrame(self.records_scroll, fg_color="transparent")
        row_frame.pack(fill="x", pady=5)

        fecha, hora = self._formatear_timestamp(sesion.get("timestamp", ""))

        celdas = [
            (fecha, 100, None, None),
            (hora, 80, None, None),
            (str(sesion.get("lemon_count", 0)), 80, COLOR["exito"], "bold"),
        ]

        duracion = sesion.get("duration_seconds", 0)
        celdas.append((f"{duracion:.1f}s" if duracion else "N/A", 100, None, None))

        res_w = sesion.get("resolution_width", 0)
        res_h = sesion.get("resolution_height", 0)
        celdas.append((f"{res_w}x{res_h}" if res_w and res_h else "N/A", 120, None, None))

        fps = sesion.get("fps_average", 0)
        celdas.append((f"{fps:.1f}" if fps else "N/A", 70, None, None))

        for i, (texto, ancho, color, peso) in enumerate(celdas):
            etiqueta = ctk.CTkLabel(
                row_frame,
                text=texto,
                font=fuente(13, peso) if peso else fuente(13),
                width=ancho,
                anchor="w",
                **({"text_color": color} if color else {}),
            )
            etiqueta.grid(row=0, column=i, padx=5, sticky="w")

        delete_btn = ctk.CTkButton(
            row_frame,
            text="Eliminar",
            font=fuente(11),
            width=80,
            height=25,
            fg_color=COLOR["peligro"],
            hover_color=COLOR["peligro_hover"],
            corner_radius=8,
            command=lambda sid=sesion.get("id"): self.eliminar_sesion(sid),
        )
        delete_btn.grid(row=0, column=6, padx=5)

    @staticmethod
    def _formatear_timestamp(timestamp_str: str) -> tuple[str, str]:
        """Convierte el timestamp ISO de Supabase a (fecha, hora) legibles."""
        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                pass
        return "N/A", "N/A"

    # ----- Eliminación (asíncrona, con confirmación) -----

    def eliminar_sesion(self, sesion_id):
        """Elimina una sesión previa confirmación del operario."""
        if not self.supabase or sesion_id is None:
            return

        confirmado = messagebox.askyesno(
            "Eliminar sesión",
            "¿Seguro que deseas eliminar este registro?\nEsta acción no se puede deshacer.",
            parent=self,
        )
        if not confirmado:
            return

        def _eliminar():
            try:
                self.supabase.table("counting_sessions").delete().eq("id", sesion_id).execute()
                self._entregar_a_ui(self.cargar_datos)
            except Exception as e:
                self._entregar_a_ui(
                    lambda: messagebox.showerror(
                        "Error", f"No se pudo eliminar la sesión: {e}", parent=self
                    )
                )

        threading.Thread(target=_eliminar, daemon=True).start()

    def al_cerrar(self):
        """Maneja el cierre de la ventana."""
        self.destroy()
        self.parent.deiconify()
