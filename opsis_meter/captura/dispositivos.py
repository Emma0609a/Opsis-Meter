"""Detección de cámaras locales disponibles en el sistema."""

import cv2


def detectar_camaras(maximo: int = 5) -> list[int]:
    """
    Devuelve los índices de las cámaras locales que se pueden abrir.

    Probar cada índice puede tardar varios segundos: esta función bloquea,
    así que debe llamarse desde un hilo secundario, nunca desde la UI.
    """
    disponibles = []
    for indice in range(maximo):
        captura = cv2.VideoCapture(indice)
        if captura.isOpened():
            disponibles.append(indice)
        captura.release()
    return disponibles
