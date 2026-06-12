"""
Arranque de la aplicación Opsis Meter.
Compone el menú principal y ejecuta el bucle de la interfaz.
"""

import sys
import traceback

from opsis_meter.compartido.tema import configurar_apariencia
from opsis_meter.menu_principal.ventana import MenuPrincipal


def ejecutar():
    """Inicia la aplicación de escritorio."""
    try:
        configurar_apariencia()
        app = MenuPrincipal()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
    except Exception:
        traceback.print_exc()
        sys.exit(1)
