"""
Detector de objetos YOLO sobre ONNX Runtime.

Compatible con modelos YOLOv8/YOLOv11 exportados a ONNX (salida con
forma [1, 4+nc, N] o [1, N, 4+nc]). El modelo se ejecuta 100% local,
sin depender de servicios externos.
"""

from pathlib import Path

import cv2
import numpy as np

COLOR_RELLENO_LETTERBOX = 114


class DetectorNoDisponible(RuntimeError):
    """El detector no puede crearse (falta el modelo o el runtime)."""


class DetectorYOLO:
    """Detección de frutas en frames BGR usando un modelo YOLO en ONNX."""

    def __init__(self, ruta_modelo, umbral_confianza=0.35, umbral_nms=0.45):
        try:
            import onnxruntime as ort
        except ImportError as e:
            raise DetectorNoDisponible(
                "onnxruntime no está instalado (pip install onnxruntime)"
            ) from e

        if not ruta_modelo or not Path(ruta_modelo).exists():
            raise DetectorNoDisponible(
                "No hay modelo ONNX configurado. Coloca el modelo en models/ "
                "o define OPSIS_MODELO en .env"
            )

        self.umbral_confianza = umbral_confianza
        self.umbral_nms = umbral_nms

        self._sesion = ort.InferenceSession(
            str(ruta_modelo), providers=["CPUExecutionProvider"]
        )
        entrada = self._sesion.get_inputs()[0]
        self._nombre_entrada = entrada.name
        # Tamaño de entrada del modelo; 640 si el eje es dinámico
        lado = entrada.shape[2]
        self._tamano = int(lado) if isinstance(lado, int) else 640

    def detectar(self, frame) -> np.ndarray:
        """
        Detecta objetos en un frame BGR.
        Devuelve un arreglo (N, 6): [x1, y1, x2, y2, confianza, clase].
        """
        blob, escala, dx, dy = self._preparar(frame)
        salida = self._sesion.run(None, {self._nombre_entrada: blob})[0]
        return self._interpretar(salida, frame.shape, escala, dx, dy)

    def _preparar(self, frame):
        """Letterbox: redimensiona conservando el aspecto y rellena a cuadrado."""
        alto, ancho = frame.shape[:2]
        lado = self._tamano
        escala = min(lado / ancho, lado / alto)
        nuevo_ancho, nuevo_alto = round(ancho * escala), round(alto * escala)

        lienzo = np.full((lado, lado, 3), COLOR_RELLENO_LETTERBOX, dtype=np.uint8)
        redimensionado = cv2.resize(frame, (nuevo_ancho, nuevo_alto))
        dx, dy = (lado - nuevo_ancho) // 2, (lado - nuevo_alto) // 2
        lienzo[dy : dy + nuevo_alto, dx : dx + nuevo_ancho] = redimensionado

        # BGR -> RGB, HWC -> NCHW, normalizado a [0, 1]
        blob = lienzo[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        return np.ascontiguousarray(blob), escala, dx, dy

    def _interpretar(self, salida, forma_frame, escala, dx, dy):
        """Convierte la salida cruda del modelo en cajas sobre el frame original."""
        predicciones = salida[0]
        # Normalizar a (N, 4+nc): los exports de YOLO traen (4+nc, N)
        if predicciones.shape[0] < predicciones.shape[1]:
            predicciones = predicciones.T

        puntuaciones_clases = predicciones[:, 4:]
        clases = puntuaciones_clases.argmax(axis=1)
        confianzas = puntuaciones_clases.max(axis=1)

        mascara = confianzas >= self.umbral_confianza
        if not mascara.any():
            return np.zeros((0, 6))

        cajas = predicciones[mascara, :4]
        confianzas = confianzas[mascara]
        clases = clases[mascara]

        # (cx, cy, w, h) en espacio letterbox -> (x1, y1, x2, y2) en el frame
        cx, cy, w, h = cajas[:, 0], cajas[:, 1], cajas[:, 2], cajas[:, 3]
        x1 = (cx - w / 2 - dx) / escala
        y1 = (cy - h / 2 - dy) / escala
        x2 = (cx + w / 2 - dx) / escala
        y2 = (cy + h / 2 - dy) / escala

        alto_frame, ancho_frame = forma_frame[:2]
        x1 = np.clip(x1, 0, ancho_frame - 1)
        y1 = np.clip(y1, 0, alto_frame - 1)
        x2 = np.clip(x2, 0, ancho_frame - 1)
        y2 = np.clip(y2, 0, alto_frame - 1)

        cajas_xywh = np.stack([x1, y1, x2 - x1, y2 - y1], axis=1)
        indices = cv2.dnn.NMSBoxes(
            cajas_xywh.tolist(),
            confianzas.tolist(),
            self.umbral_confianza,
            self.umbral_nms,
        )
        if len(indices) == 0:
            return np.zeros((0, 6))
        indices = np.asarray(indices).flatten()

        return np.stack(
            [x1[indices], y1[indices], x2[indices], y2[indices], confianzas[indices], clases[indices].astype(float)],
            axis=1,
        )
