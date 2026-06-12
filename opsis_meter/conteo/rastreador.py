"""
Rastreador multi-objeto estilo ByteTrack (simplificado).

Asigna un ID estable a cada objeto detectado para que la vibración de la
banda o una detección perdida no dupliquen el conteo. Implementa la idea
central de ByteTrack: asociar primero las detecciones de alta confianza
y rescatar las pistas restantes con las de baja confianza, usando IoU y
un filtro de Kalman de velocidad constante para predecir el movimiento.
"""

import numpy as np

try:
    from scipy.optimize import linear_sum_assignment

    _HAY_SCIPY = True
except ImportError:  # pragma: no cover - scipy está en requirements
    _HAY_SCIPY = False


class _FiltroKalman:
    """Filtro de Kalman de velocidad constante sobre (cx, cy, w, h)."""

    _STD_POSICION = 1.0 / 20.0
    _STD_VELOCIDAD = 1.0 / 160.0

    def __init__(self, medida):
        # Estado: [cx, cy, w, h, vcx, vcy, vw, vh]
        self.x = np.concatenate([medida, np.zeros(4)])
        self.F = np.eye(8)
        self.F[:4, 4:] = np.eye(4)
        self.H = np.eye(4, 8)
        escala = max(medida[3], 1.0)
        self.P = np.diag([(escala / 10.0) ** 2] * 4 + [(escala / 16.0) ** 2] * 4)

    def predecir(self):
        alto = max(self.x[3], 1.0)
        ruido = np.diag(
            [(self._STD_POSICION * alto) ** 2] * 4 + [(self._STD_VELOCIDAD * alto) ** 2] * 4
        )
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + ruido

    def corregir(self, medida):
        alto = max(medida[3], 1.0)
        ruido = np.diag([(self._STD_POSICION * alto) ** 2] * 4)
        S = self.H @ self.P @ self.H.T + ruido
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ (medida - self.H @ self.x)
        self.P = (np.eye(8) - K @ self.H) @ self.P


class Pista:
    """Un objeto seguido a lo largo del tiempo, con ID propio."""

    def __init__(self, id_pista: int, caja_xyxy, puntuacion: float):
        self.id = id_pista
        self.puntuacion = puntuacion
        self.aciertos = 1
        self.frames_perdida = 0
        self.confirmada = False
        self._kf = _FiltroKalman(self._a_cxcywh(caja_xyxy))

    @staticmethod
    def _a_cxcywh(caja):
        x1, y1, x2, y2 = caja[:4]
        return np.array([(x1 + x2) / 2.0, (y1 + y2) / 2.0, x2 - x1, y2 - y1])

    @property
    def caja(self):
        """Caja actual estimada [x1, y1, x2, y2]."""
        cx, cy, w, h = self._kf.x[:4]
        w, h = max(w, 1.0), max(h, 1.0)
        return np.array([cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0])

    @property
    def centroide(self):
        return float(self._kf.x[0]), float(self._kf.x[1])

    def predecir(self):
        self._kf.predecir()

    def actualizar(self, deteccion):
        self._kf.corregir(self._a_cxcywh(deteccion))
        self.puntuacion = float(deteccion[4])
        self.aciertos += 1
        self.frames_perdida = 0


def _matriz_iou(cajas_a, cajas_b):
    """IoU entre cada par de cajas (A x B), vectorizado."""
    a = np.asarray(cajas_a, dtype=float)
    b = np.asarray(cajas_b, dtype=float)
    x1 = np.maximum(a[:, None, 0], b[None, :, 0])
    y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2])
    y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    interseccion = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area_a = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    area_b = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    return interseccion / (area_a[:, None] + area_b[None, :] - interseccion + 1e-9)


class Rastreador:
    """Seguimiento multi-objeto con asociación en dos etapas (ByteTrack)."""

    def __init__(
        self,
        umbral_alta=0.5,
        umbral_baja=0.1,
        iou_minimo=0.2,
        frames_max_perdida=30,
        frames_confirmacion=3,
    ):
        self.umbral_alta = umbral_alta
        self.umbral_baja = umbral_baja
        self.iou_minimo = iou_minimo
        self.frames_max_perdida = frames_max_perdida
        self.frames_confirmacion = frames_confirmacion
        self.pistas: list[Pista] = []
        self._siguiente_id = 1

    def actualizar(self, detecciones) -> list[Pista]:
        """
        Procesa las detecciones de un frame ([x1, y1, x2, y2, score], ...).
        Devuelve las pistas confirmadas y visibles en este frame.
        """
        detecciones = np.asarray(detecciones, dtype=float)
        if detecciones.size == 0:
            detecciones = np.zeros((0, 5))

        altas = detecciones[detecciones[:, 4] >= self.umbral_alta]
        bajas = detecciones[
            (detecciones[:, 4] >= self.umbral_baja) & (detecciones[:, 4] < self.umbral_alta)
        ]

        for pista in self.pistas:
            pista.predecir()

        # Etapa 1: todas las pistas contra detecciones de alta confianza
        parejas, idx_pistas_sueltas, idx_altas_sueltas = self._asociar(self.pistas, altas)
        for i_pista, i_det in parejas:
            self.pistas[i_pista].actualizar(altas[i_det])

        # Etapa 2 (núcleo de ByteTrack): rescatar las pistas restantes
        # con las detecciones de baja confianza (oclusiones, desenfoque)
        pistas_sueltas = [self.pistas[i] for i in idx_pistas_sueltas]
        parejas_baja, idx_sin_deteccion, _ = self._asociar(pistas_sueltas, bajas)
        for i_pista, i_det in parejas_baja:
            pistas_sueltas[i_pista].actualizar(bajas[i_det])

        # Pistas que no vieron ninguna detección en este frame
        for i in idx_sin_deteccion:
            pistas_sueltas[i].frames_perdida += 1

        # Eliminar: tentativas que fallaron y confirmadas perdidas hace mucho
        self.pistas = [
            p
            for p in self.pistas
            if (p.confirmada and p.frames_perdida <= self.frames_max_perdida)
            or (not p.confirmada and p.frames_perdida == 0)
        ]

        # Crear pistas nuevas con las detecciones de alta confianza sin pareja
        for i in idx_altas_sueltas:
            self.pistas.append(Pista(self._siguiente_id, altas[i], float(altas[i][4])))
            self._siguiente_id += 1

        # Confirmar pistas con suficientes aciertos consecutivos
        for pista in self.pistas:
            if not pista.confirmada and pista.aciertos >= self.frames_confirmacion:
                pista.confirmada = True

        return [p for p in self.pistas if p.confirmada and p.frames_perdida == 0]

    def ids_vivos(self):
        """IDs de todas las pistas que siguen en memoria."""
        return [p.id for p in self.pistas]

    def _asociar(self, pistas, detecciones):
        """
        Empareja pistas y detecciones por IoU.
        Devuelve (parejas, índices de pistas sueltas, índices de detecciones sueltas).
        """
        if not pistas or len(detecciones) == 0:
            return [], list(range(len(pistas))), list(range(len(detecciones)))

        iou = _matriz_iou([p.caja for p in pistas], detecciones[:, :4])

        if _HAY_SCIPY:
            filas, columnas = linear_sum_assignment(1.0 - iou)
            candidatas = zip(filas.tolist(), columnas.tolist())
        else:
            # Emparejamiento voraz por IoU descendente
            ordenadas = np.dstack(np.unravel_index(np.argsort(-iou, axis=None), iou.shape))[0]
            usadas_p, usadas_d, candidatas = set(), set(), []
            for f, c in ordenadas:
                if f not in usadas_p and c not in usadas_d:
                    usadas_p.add(f)
                    usadas_d.add(c)
                    candidatas.append((int(f), int(c)))

        parejas = [(f, c) for f, c in candidatas if iou[f, c] >= self.iou_minimo]
        con_pareja_p = {f for f, _ in parejas}
        con_pareja_d = {c for _, c in parejas}
        sueltas_p = [i for i in range(len(pistas)) if i not in con_pareja_p]
        sueltas_d = [i for i in range(len(detecciones)) if i not in con_pareja_d]
        return parejas, sueltas_p, sueltas_d
