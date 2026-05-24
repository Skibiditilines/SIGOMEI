"""
init_databases.py
=================
Script para inicializar físicamente las dos bases de datos SQLite
(de prueba y oficial) del proyecto SIGOMEI con su esquema relacional.
"""

import os
import sys

# Asegurar que el directorio server/ esté en el path de búsqueda
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.database import DB_PATHS, init_db

def main():
    print("=" * 60)
    print("  SIGOMEI — Inicializador de Bases de Datos SQLite")
    print("=" * 60)
    
    for mode, path in DB_PATHS.items():
        print(f"\nInicializando base de datos [{mode.upper()}]:")
        print(f"Ruta: {path}")
        
        # Eliminar archivo si existiera y queremos partir de cero,
        # o simplemente inicializar las tablas si no existen.
        # En este caso, simplemente inicializamos tablas de forma segura (IF NOT EXISTS)
        try:
            init_db(path)
            print(f" -> Base de datos [{mode.upper()}] creada e inicializada.")
        except Exception as e:
            print(f" -> Error al inicializar [{mode.upper()}]: {e}")
            
    print("\n" + "=" * 60)
    print("  Bases de datos listas para su ejecución.")
    print("=" * 60)

if __name__ == "__main__":
    main()
