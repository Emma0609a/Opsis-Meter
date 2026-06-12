"""
Proceso B: cerebro de inteligencia artificial.

Corre en un proceso independiente (multiprocessing) para que la inferencia
no compita por el GIL con la interfaz gráfica. Mientras el conteo está
activo, este proceso es el dueño exclusivo de la cámara: captura, detecta
(YOLO/ONNX), sigue (ByteTrack) y cuenta (línea virtual), y envía frames
anotados y estado a la UI por una cola.

Si la cola de la UI está llena, los frames se descartan: el conteo no se
ve afectado porque ocurre dentro de este proceso, no en la visualización.
"""

import queue as cola_estandar
import time

import cv2

from opsis_meter.conteo.mensajes import (
    CMD_DETENER,
    CMD_FPS,
    AvisoConteo,
    ErrorConteo,
    FinConteo,
    FrameConteo,
)

ANCHO_MAX_TRANSMISION = 960
CALIDAD_JPEG = 75
MAX_FALLOS_LECTURA = 30

# Umbral con el que el detector filtra: bajo a propósito, para que
# ByteTrack pueda usar las detecciones de baja confianza en la 2da etapa
UMBRAL_DETECTOR = 0.1

COLOR_LINEA = (0, 215, 255)  # BGR: ámbar
COLOR_CAJA = (80, 200, 80)
COLOR_TEXTO = (255, 255, 255)


class _DetenerConteo(Exception):
    """Señal interna para salir del bucle de conteo."""


def ejecutar_conteo(
    fuente,
    es_ip,
    resolucion,
    limite_fps,
    ruta_modelo,
    umbral_confianza,
    orientacion_linea,
    posicion_linea,
    cola_eventos,
    cola_comandos,
):
    """
    Punto de entrada del proceso de IA.
    Debe ser una función de nivel superior para que multiprocessing (spawn)
    pueda importarla en Windows.
    """
    # Imports pesados dentro del proceso: no penalizan el arranque de la UI
    from opsis_meter.conteo.detector import DetectorNoDisponible, DetectorYOLO
    from opsis_meter.conteo.linea_conteo import LineaConteo
    from opsis_meter.conteo.rastreador import Rastreador

    detector = None
    try:
        detector = DetectorYOLO(ruta_modelo, umbral_confianza=UMBRAL_DETECTOR)
    except DetectorNoDisponible as e:
        cola_eventos.put(AvisoConteo(f"Conteo sin IA ({e}). Solo vista previa."))
    except Exception as e:
        cola_eventos.put(AvisoConteo(f"No se pudo cargar el modelo: {e}. Solo vista previa."))

    rastreador = Rastreador(umbral_alta=umbral_confianza)
    if orientacion_linea == "horizontal":
        linea = LineaConteo.horizontal(posicion_linea)
    else:
        linea = LineaConteo.vertical(posicion_linea)

    captura = _abrir_camara(fuente, es_ip, resolucion)
    if captura is None:
        cola_eventos.put(ErrorConteo(f"No se pudo abrir la cámara ({fuente})."))
        return

    inicio = time.monotonic()
    frames_procesados = 0
    fps_suavizado = 0.0
    fallos = 0
    marca_anterior = time.monotonic()

    try:
        while True:
            ciclo_inicio = time.monotonic()
            limite_fps = _atender_comandos(cola_comandos, limite_fps)

            ret, frame = captura.read()
            if not ret:
                fallos += 1
                if fallos >= MAX_FALLOS_LECTURA:
                    captura.release()
                    captura = _abrir_camara(fuente, es_ip, resolucion)
                    if captura is None:
                        cola_eventos.put(ErrorConteo("Se perdió la conexión con la cámara."))
                        return
                    fallos = 0
                else:
                    time.sleep(0.1)
                continue
            fallos = 0
            frames_procesados += 1

            alto, ancho = frame.shape[:2]
            pistas = []
            if detector is not None:
                detecciones = detector.detectar(frame)
                pistas = rastreador.actualizar(detecciones)
                centroides = [
                    (p.id, (p.centroide[0] / ancho, p.centroide[1] / alto)) for p in pistas
                ]
                linea.actualizar(centroides)
                linea.depurar(rastreador.ids_vivos())

            _dibujar(frame, pistas, linea, detector is not None)

            # FPS sobre el ciclo completo, con suavizado exponencial
            ahora = time.monotonic()
            ciclo = ahora - marca_anterior
            marca_anterior = ahora
            if ciclo > 0:
                instantaneo = 1.0 / ciclo
                fps_suavizado = (
                    0.9 * fps_suavizado + 0.1 * instantaneo if fps_suavizado else instantaneo
                )

            _publicar_frame(
                cola_eventos,
                frame,
                total=linea.total,
                en_escena=len(pistas),
                fps=fps_suavizado,
                con_ia=detector is not None,
            )

            restante = (1.0 / max(limite_fps, 1)) - (time.monotonic() - ciclo_inicio)
            if restante > 0:
                time.sleep(restante)

    except _DetenerConteo:
        pass
    finally:
        captura.release()
        duracion = time.monotonic() - inicio
        fps_promedio = frames_procesados / duracion if duracion > 0 else 0.0
        cola_eventos.put(
            FinConteo(total=linea.total, duracion_segundos=duracion, fps_promedio=fps_promedio)
        )
        # TODO Bloque 3: respaldar el resultado en SQLite (offline-first)


def _abrir_camara(fuente, es_ip, resolucion):
    captura = cv2.VideoCapture(fuente)
    if not captura.isOpened():
        captura.release()
        return None
    if es_ip:
        captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    elif resolucion:
        captura.set(cv2.CAP_PROP_FRAME_WIDTH, resolucion[0])
        captura.set(cv2.CAP_PROP_FRAME_HEIGHT, resolucion[1])
    return captura


def _atender_comandos(cola_comandos, limite_fps):
    """Aplica los comandos pendientes; lanza _DetenerConteo si corresponde."""
    while True:
        try:
            comando = cola_comandos.get_nowait()
        except cola_estandar.Empty:
            return limite_fps
        if comando[0] == CMD_DETENER:
            raise _DetenerConteo
        if comando[0] == CMD_FPS:
            limite_fps = max(1, int(comando[1]))


def _dibujar(frame, pistas, linea, con_ia):
    """Dibuja la línea virtual, las cajas con ID y el total sobre el frame."""
    alto, ancho = frame.shape[:2]

    p1 = (int(linea.punto_a[0] * ancho), int(linea.punto_a[1] * alto))
    p2 = (int(linea.punto_b[0] * ancho), int(linea.punto_b[1] * alto))
    cv2.line(frame, p1, p2, COLOR_LINEA, 2)

    for pista in pistas:
        x1, y1, x2, y2 = pista.caja.astype(int)
        cv2.rectangle(frame, (x1, y1), (x2, y2), COLOR_CAJA, 2)
        cv2.putText(
            frame,
            f"#{pista.id}",
            (x1, max(y1 - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            COLOR_CAJA,
            2,
        )

    etiqueta = f"Total: {linea.total}" if con_ia else "SIN IA (solo vista)"
    cv2.putText(frame, etiqueta, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4)
    cv2.putText(frame, etiqueta, (12, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, COLOR_TEXTO, 2)


def _publicar_frame(cola_eventos, frame, total, en_escena, fps, con_ia):
    """Codifica el frame a JPEG y lo envía; si la cola está llena, lo descarta."""
    alto, ancho = frame.shape[:2]
    if ancho > ANCHO_MAX_TRANSMISION:
        nueva_escala = ANCHO_MAX_TRANSMISION / ancho
        frame = cv2.resize(
            frame,
            (ANCHO_MAX_TRANSMISION, int(alto * nueva_escala)),
            interpolation=cv2.INTER_AREA,
        )

    ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG])
    if not ok:
        return
    try:
        cola_eventos.put_nowait(
            FrameConteo(
                jpeg=jpeg.tobytes(),
                total=total,
                en_escena=en_escena,
                fps=fps,
                con_ia=con_ia,
            )
        )
    except cola_estandar.Full:
        pass  # la UI va atrasada: descartar el frame, el conteo no se pierde
