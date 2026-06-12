"""Pruebas del rastreador multi-objeto (ByteTrack simplificado)."""

import numpy as np

from opsis_meter.conteo.rastreador import Rastreador


def _caja(x, y, lado=40, conf=0.9):
    return [x, y, x + lado, y + lado, conf]


def test_id_estable_para_objeto_en_movimiento():
    rastreador = Rastreador(frames_confirmacion=3)
    ids_vistos = set()
    for paso in range(10):
        detecciones = np.array([_caja(100 + paso * 5, 200)])
        pistas = rastreador.actualizar(detecciones)
        ids_vistos.update(p.id for p in pistas)

    assert len(ids_vistos) == 1  # un solo ID durante todo el recorrido


def test_confirmacion_requiere_varios_frames():
    rastreador = Rastreador(frames_confirmacion=3)
    assert rastreador.actualizar(np.array([_caja(100, 100)])) == []
    assert rastreador.actualizar(np.array([_caja(102, 100)])) == []
    pistas = rastreador.actualizar(np.array([_caja(104, 100)]))
    assert len(pistas) == 1


def test_deteccion_perdida_no_cambia_el_id():
    rastreador = Rastreador(frames_confirmacion=2)
    for paso in range(4):
        pistas = rastreador.actualizar(np.array([_caja(100 + paso * 5, 200)]))
    id_original = pistas[0].id

    # Un frame sin detección (oclusión / desenfoque)
    rastreador.actualizar(np.zeros((0, 5)))

    pistas = rastreador.actualizar(np.array([_caja(130, 200)]))
    assert len(pistas) == 1
    assert pistas[0].id == id_original


def test_baja_confianza_rescata_la_pista():
    rastreador = Rastreador(umbral_alta=0.5, umbral_baja=0.1, frames_confirmacion=2)
    for paso in range(3):
        rastreador.actualizar(np.array([_caja(100 + paso * 5, 200, conf=0.9)]))

    # El objeto se ve borroso: confianza baja, pero la pista sobrevive
    pistas = rastreador.actualizar(np.array([_caja(115, 200, conf=0.2)]))
    assert len(pistas) == 1

    # Y una detección de baja confianza sola NO crea pistas nuevas
    rastreador2 = Rastreador(umbral_alta=0.5, umbral_baja=0.1)
    rastreador2.actualizar(np.array([_caja(300, 300, conf=0.2)]))
    assert rastreador2.pistas == []


def test_objetos_separados_reciben_ids_distintos():
    rastreador = Rastreador(frames_confirmacion=2)
    for paso in range(3):
        detecciones = np.array(
            [_caja(100 + paso * 5, 100), _caja(400 + paso * 5, 400)]
        )
        pistas = rastreador.actualizar(detecciones)

    assert len(pistas) == 2
    assert pistas[0].id != pistas[1].id


def test_pista_se_elimina_tras_perdida_prolongada():
    rastreador = Rastreador(frames_confirmacion=2, frames_max_perdida=5)
    for paso in range(3):
        rastreador.actualizar(np.array([_caja(100, 100)]))
    assert len(rastreador.pistas) == 1

    for _ in range(7):
        rastreador.actualizar(np.zeros((0, 5)))
    assert rastreador.pistas == []
