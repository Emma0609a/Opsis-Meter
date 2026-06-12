"""
Pruebas del pre/postprocesado del detector YOLO.
No requieren un modelo ONNX: se prueba la matemática de letterbox e
interpretación de salidas construyendo el detector sin sesión.
"""

import numpy as np

from opsis_meter.conteo.detector import DetectorYOLO


def _detector_sin_modelo(tamano=640, umbral=0.35):
    detector = object.__new__(DetectorYOLO)
    detector.umbral_confianza = umbral
    detector.umbral_nms = 0.45
    detector._tamano = tamano
    return detector


def _salida_yolo(anclas, num_total=100):
    """Construye una salida (1, 5, N) con las anclas dadas [cx, cy, w, h, conf]."""
    salida = np.zeros((1, 5, num_total), dtype=np.float32)
    for i, (cx, cy, w, h, conf) in enumerate(anclas):
        salida[0, :, i] = [cx, cy, w, h, conf]
    return salida


def test_letterbox_conserva_aspecto():
    detector = _detector_sin_modelo()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    blob, escala, dx, dy = detector._preparar(frame)

    assert blob.shape == (1, 3, 640, 640)
    assert escala == 0.5
    assert (dx, dy) == (0, 140)
    assert blob.dtype == np.float32
    assert 0.0 <= blob.min() and blob.max() <= 1.0


def test_interpretar_devuelve_caja_en_coordenadas_del_frame():
    detector = _detector_sin_modelo()
    frame_shape = (640, 640, 3)  # escala 1, sin relleno
    salida = _salida_yolo([(100, 100, 40, 40, 0.9)])

    cajas = detector._interpretar(salida, frame_shape, escala=1.0, dx=0, dy=0)

    assert cajas.shape == (1, 6)
    x1, y1, x2, y2, conf, clase = cajas[0]
    assert (round(x1), round(y1), round(x2), round(y2)) == (80, 80, 120, 120)
    assert conf == np.float32(0.9)


def test_interpretar_descarta_baja_confianza():
    detector = _detector_sin_modelo(umbral=0.35)
    salida = _salida_yolo([(100, 100, 40, 40, 0.2)])
    cajas = detector._interpretar(salida, (640, 640, 3), escala=1.0, dx=0, dy=0)
    assert cajas.shape == (0, 6)


def test_nms_funde_detecciones_solapadas():
    detector = _detector_sin_modelo()
    salida = _salida_yolo([(100, 100, 40, 40, 0.9), (102, 101, 40, 40, 0.8)])
    cajas = detector._interpretar(salida, (640, 640, 3), escala=1.0, dx=0, dy=0)
    assert len(cajas) == 1
    assert cajas[0][4] == np.float32(0.9)  # sobrevive la de mayor confianza


def test_interpretar_deshace_el_letterbox():
    detector = _detector_sin_modelo()
    # Frame 1280x720 -> escala 0.5, dy 140: caja centrada en (320, 320)
    # del espacio letterbox corresponde a (640, 360) del frame original
    salida = _salida_yolo([(320, 320, 100, 100, 0.9)])
    cajas = detector._interpretar(salida, (720, 1280, 3), escala=0.5, dx=0, dy=140)

    x1, y1, x2, y2 = cajas[0][:4]
    assert abs((x1 + x2) / 2 - 640) < 1
    assert abs((y1 + y2) / 2 - 360) < 1
    assert abs((x2 - x1) - 200) < 1
