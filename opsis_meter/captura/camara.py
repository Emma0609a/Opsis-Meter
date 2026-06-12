"""
FlujoCamara: captura de video en un hilo dedicado.

El hilo es el único dueño del objeto cv2.VideoCapture: la apertura, la
lectura, la reconexión y la liberación ocurren siempre dentro del hilo.
El resto de la aplicación solo consume el último frame disponible con
leer_frame(), lo que elimina las condiciones de carrera con el hilo de
la interfaz gráfica.
"""

import threading
import time

import cv2

ESTADO_INACTIVO = "inactivo"
ESTADO_CONECTANDO = "conectando"
ESTADO_ACTIVO = "activo"
ESTADO_ERROR = "error"

FPS_MINIMO = 1
FPS_MAXIMO = 60


class FlujoCamara:
    """Lee frames de una cámara local o IP en segundo plano."""

    MAX_FALLOS_CONSECUTIVOS = 10
    MAX_INTENTOS_RECONEXION = 3

    def __init__(self, fuente, resolucion=None, limite_fps=30, es_ip=False):
        """
        fuente: índice de dispositivo (int) o URL RTSP/HTTP (str).
        resolucion: (ancho, alto) deseado; solo aplica a cámaras locales.
        es_ip: True si la fuente es una cámara de red.
        """
        self.fuente = fuente
        self.resolucion = resolucion
        self.es_ip = es_ip
        self._limite_fps = self._acotar_fps(limite_fps)

        self._continuar = threading.Event()
        self._hilo: threading.Thread | None = None
        self._candado = threading.Lock()
        self._frame = None

        self.estado = ESTADO_INACTIVO
        self.error: str | None = None
        self.fps_real = 0.0

    # ----- API pública (hilo de la UI) -----

    def iniciar(self):
        """Arranca el hilo de captura (idempotente)."""
        if self._hilo and self._hilo.is_alive():
            return
        self.error = None
        self.estado = ESTADO_CONECTANDO
        self._continuar.set()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def detener(self, espera: float = 3.0):
        """Detiene el hilo de captura y espera a que libere la cámara."""
        self._continuar.clear()
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=espera)
        self._hilo = None
        with self._candado:
            self._frame = None
        if self.estado != ESTADO_ERROR:
            self.estado = ESTADO_INACTIVO
        self.fps_real = 0.0

    def leer_frame(self):
        """Devuelve el último frame capturado (BGR) o None si aún no hay."""
        with self._candado:
            return self._frame

    def fijar_limite_fps(self, fps):
        """Cambia el límite de FPS en caliente; el bucle lo aplica de inmediato."""
        self._limite_fps = self._acotar_fps(fps)

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    @staticmethod
    def _acotar_fps(fps) -> int:
        return min(FPS_MAXIMO, max(FPS_MINIMO, int(fps)))

    # ----- Interno (solo el hilo de captura toca la cámara) -----

    def _abrir(self):
        captura = cv2.VideoCapture(self.fuente)
        if not captura.isOpened():
            captura.release()
            return None
        if self.es_ip:
            # Buffer mínimo: reduce la latencia acumulada en cámaras de red
            captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        elif self.resolucion:
            captura.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucion[0])
            captura.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucion[1])
        return captura

    def _reconectar(self, captura):
        """Reabre la cámara tras una pérdida de conexión."""
        if captura is not None:
            captura.release()
        for _ in range(self.MAX_INTENTOS_RECONEXION):
            if not self._continuar.is_set():
                return None
            time.sleep(1.0)
            nueva = self._abrir()
            if nueva is not None:
                return nueva
        return None

    def _bucle(self):
        captura = self._abrir()
        if captura is None:
            self._fallar(
                f"No se pudo abrir la cámara ({self.fuente}). "
                "Verifica la conexión y la configuración."
            )
            return

        self.estado = ESTADO_ACTIVO
        fallos = 0
        marca_anterior = time.monotonic()

        while self._continuar.is_set():
            inicio = time.monotonic()
            ret, frame = captura.read()

            if not ret:
                fallos += 1
                if fallos >= self.MAX_FALLOS_CONSECUTIVOS:
                    captura = self._reconectar(captura)
                    if captura is None:
                        self._fallar("Se perdió la conexión con la cámara.")
                        return
                    fallos = 0
                else:
                    time.sleep(0.5 if self.es_ip else 0.1)
                continue

            fallos = 0
            with self._candado:
                self._frame = frame

            # FPS real medido sobre el ciclo completo (incluida la espera)
            ahora = time.monotonic()
            ciclo = ahora - marca_anterior
            marca_anterior = ahora
            if ciclo > 0:
                instantaneo = 1.0 / ciclo
                self.fps_real = (
                    0.9 * self.fps_real + 0.1 * instantaneo if self.fps_real else instantaneo
                )

            # Respetar el límite vigente (puede cambiar durante la captura)
            restante = (1.0 / self._limite_fps) - (time.monotonic() - inicio)
            if restante > 0:
                time.sleep(restante)

        captura.release()

    def _fallar(self, mensaje: str):
        self.error = mensaje
        self.estado = ESTADO_ERROR
