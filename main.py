"""
Opsis Meter - Punto de entrada
Sistema de conteo de limones con inteligencia artificial.
"""

import multiprocessing

if __name__ == "__main__":
    # Necesario en Windows/PyInstaller: el proceso de IA usa multiprocessing
    multiprocessing.freeze_support()

    from opsis_meter.app import ejecutar

    ejecutar()
