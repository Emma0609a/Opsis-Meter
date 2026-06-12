"""
Línea virtual de conteo.

La línea se define en coordenadas relativas (0..1) para ser independiente
de la resolución de la cámara. Un objeto se cuenta exactamente una vez:
cuando el centroide de su pista cambia de lado respecto a la línea. Si la
banda vibra y el objeto vuelve a cruzar, su ID ya quedó registrado y no
se cuenta de nuevo.
"""


class LineaConteo:
    """Cuenta cruces de centroides sobre una línea virtual."""

    def __init__(self, punto_a=(0.5, 0.0), punto_b=(0.5, 1.0)):
        self.punto_a = punto_a
        self.punto_b = punto_b
        self.total = 0
        self._lados = {}  # id_pista -> último lado conocido (-1 o 1)
        self._contados = set()

    @classmethod
    def vertical(cls, posicion=0.5):
        """Línea vertical en la fracción `posicion` del ancho del frame."""
        return cls((posicion, 0.0), (posicion, 1.0))

    @classmethod
    def horizontal(cls, posicion=0.5):
        """Línea horizontal en la fracción `posicion` del alto del frame."""
        return cls((0.0, posicion), (1.0, posicion))

    def lado(self, punto) -> int:
        """Lado de la línea en que cae un punto: -1, 1, o 0 si está sobre ella."""
        (xa, ya), (xb, yb) = self.punto_a, self.punto_b
        cruz = (xb - xa) * (punto[1] - ya) - (yb - ya) * (punto[0] - xa)
        if cruz > 0:
            return 1
        if cruz < 0:
            return -1
        return 0

    def actualizar(self, centroides) -> list:
        """
        Evalúa los centroides del frame actual y suma los cruces nuevos.

        centroides: iterable de (id_pista, (x_rel, y_rel)).
        Devuelve los IDs contados en esta actualización.
        """
        contados_ahora = []
        for id_pista, punto in centroides:
            lado = self.lado(punto)
            if lado == 0:
                # Exactamente sobre la línea: esperar a que defina lado
                continue
            anterior = self._lados.get(id_pista)
            if anterior is not None and anterior != lado and id_pista not in self._contados:
                self._contados.add(id_pista)
                self.total += 1
                contados_ahora.append(id_pista)
            self._lados[id_pista] = lado
        return contados_ahora

    def depurar(self, ids_activos):
        """Olvida los IDs de pistas que ya no existen (evita crecer sin límite)."""
        ids_activos = set(ids_activos)
        self._lados = {i: lado for i, lado in self._lados.items() if i in ids_activos}
        self._contados &= ids_activos

    def reiniciar(self):
        """Pone el contador en cero y olvida todas las pistas."""
        self.total = 0
        self._lados.clear()
        self._contados.clear()
