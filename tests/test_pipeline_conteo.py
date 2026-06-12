"""
Prueba del pipeline de conteo: detecciones -> rastreador -> línea virtual.
Simula un limón recorriendo la banda de izquierda a derecha.
"""

import numpy as np

from opsis_meter.conteo.linea_conteo import LineaConteo
from opsis_meter.conteo.rastreador import Rastreador

ANCHO, ALTO = 640, 480


def _avanzar(rastreador, linea, detecciones):
    pistas = rastreador.actualizar(detecciones)
    centroides = [
        (p.id, (p.centroide[0] / ANCHO, p.centroide[1] / ALTO)) for p in pistas
    ]
    linea.actualizar(centroides)
    linea.depurar(rastreador.ids_vivos())


def test_un_objeto_que_recorre_la_banda_cuenta_uno():
    rastreador = Rastreador(frames_confirmacion=3)
    linea = LineaConteo.vertical(0.5)

    for paso in range(20):
        x = 100 + paso * 20  # cruza el centro (320) a mitad del recorrido
        deteccion = np.array([[x - 20, 220, x + 20, 260, 0.9]])
        _avanzar(rastreador, linea, deteccion)

    assert linea.total == 1


def test_dos_objetos_en_paralelo_cuentan_dos():
    rastreador = Rastreador(frames_confirmacion=3)
    linea = LineaConteo.vertical(0.5)

    for paso in range(20):
        x = 100 + paso * 20
        detecciones = np.array(
            [
                [x - 20, 80, x + 20, 120, 0.9],
                [x - 20, 360, x + 20, 400, 0.9],
            ]
        )
        _avanzar(rastreador, linea, detecciones)

    assert linea.total == 2


def test_objeto_con_detecciones_intermitentes_cuenta_uno():
    """La banda vibra: el detector falla algunos frames cerca de la línea."""
    rastreador = Rastreador(frames_confirmacion=3)
    linea = LineaConteo.vertical(0.5)

    for paso in range(20):
        x = 100 + paso * 20
        if paso in (9, 12):  # frames perdidos alrededor del cruce
            detecciones = np.zeros((0, 5))
        else:
            detecciones = np.array([[x - 20, 220, x + 20, 260, 0.9]])
        _avanzar(rastreador, linea, detecciones)

    assert linea.total == 1
