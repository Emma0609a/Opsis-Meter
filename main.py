"""
Opsis Meter - Aplicación Principal
Sistema de conteo de limones con inteligencia artificial
"""

import sys
import os
import traceback

# Asegurar que el directorio del proyecto esté en el path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Importar después de configurar el path
try:
    from ui.main_menu import MainMenu
except ImportError as e:
    print(f"Error de importación: {e}")
    print("Asegúrate de que todas las dependencias estén instaladas:")
    print("pip install -r requirements.txt")
    traceback.print_exc()
    input("Presiona Enter para salir...")
    sys.exit(1)


def run_app():
    """Función principal para ejecutar la aplicación"""
    try:
        app = MainMenu()
        app.mainloop()
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        traceback.print_exc()
        input("Presiona Enter para salir...")
        sys.exit(1)


if __name__ == "__main__":
    run_app()

