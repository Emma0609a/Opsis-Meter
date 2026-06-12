"""Pruebas de la línea virtual de conteo."""

from opsis_meter.conteo.linea_conteo import LineaConteo


def test_cruce_simple_cuenta_una_vez():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(1, (0.2, 0.5))])
    assert linea.total == 0
    linea.actualizar([(1, (0.4, 0.5))])
    assert linea.total == 0  # mismo lado, no cuenta
    linea.actualizar([(1, (0.6, 0.5))])
    assert linea.total == 1  # cruzó la línea
    linea.actualizar([(1, (0.8, 0.5))])
    assert linea.total == 1  # sigue del mismo lado


def test_vibracion_no_duplica_el_conteo():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(7, (0.45, 0.5))])
    linea.actualizar([(7, (0.55, 0.5))])  # cruza
    linea.actualizar([(7, (0.45, 0.5))])  # la banda vibra: regresa
    linea.actualizar([(7, (0.55, 0.5))])  # vuelve a cruzar
    assert linea.total == 1


def test_varios_objetos_cuentan_por_separado():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(1, (0.3, 0.2)), (2, (0.3, 0.8))])
    linea.actualizar([(1, (0.7, 0.2)), (2, (0.7, 0.8))])
    assert linea.total == 2


def test_punto_sobre_la_linea_no_pierde_el_cruce():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(3, (0.4, 0.5))])
    linea.actualizar([(3, (0.5, 0.5))])  # exactamente sobre la línea
    linea.actualizar([(3, (0.6, 0.5))])
    assert linea.total == 1


def test_linea_horizontal():
    linea = LineaConteo.horizontal(0.5)
    linea.actualizar([(1, (0.5, 0.3))])
    linea.actualizar([(1, (0.5, 0.7))])
    assert linea.total == 1


def test_objeto_que_aparece_despues_de_la_linea_no_cuenta():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(9, (0.8, 0.5))])
    linea.actualizar([(9, (0.9, 0.5))])
    assert linea.total == 0


def test_depurar_olvida_pistas_muertas():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(1, (0.4, 0.5)), (2, (0.4, 0.5))])
    linea.actualizar([(1, (0.6, 0.5))])
    linea.depurar(ids_activos=[2])
    assert linea.total == 1  # depurar no altera el total
    assert 1 not in linea._lados
    assert 2 in linea._lados


def test_reiniciar():
    linea = LineaConteo.vertical(0.5)
    linea.actualizar([(1, (0.4, 0.5))])
    linea.actualizar([(1, (0.6, 0.5))])
    linea.reiniciar()
    assert linea.total == 0
