"""
app/core/database.py
====================
Gestor de base de datos SQLite para SIGOMEI.
Permite configurar el modo de ejecución ("oficial" o "prueba")
y proporciona las conexiones y la creación del esquema.
tag: 1.0.0
"""

import os
import sqlite3
import logging

import sys

logger = logging.getLogger("sigomei.database")

# Detección automática de entorno de pruebas (pytest)
IS_TESTING = "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)

# Configuración del modo de base de datos: "oficial" o "prueba"
DB_MODE = "prueba" if IS_TESTING else "oficial"

# Directorio raíz del proyecto (c:\Users\dogue\projects\SIGOMEI)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DB_PATHS = {
    "oficial": os.path.join(BASE_DIR, "sigomei_oficial.db"),
    "prueba": os.path.join(BASE_DIR, "sigomei_prueba.db")
}

def get_db_path() -> str:
    """Retorna la ruta absoluta al archivo de base de datos actual."""
    return DB_PATHS.get(DB_MODE, DB_PATHS["oficial"])

def get_connection() -> sqlite3.Connection:
    """Abre y retorna una conexión a la base de datos configurada."""
    path = get_db_path()
    conn = sqlite3.connect(path)
    # Habilitar row_factory para poder acceder a columnas por nombre
    conn.row_factory = sqlite3.Row
    return conn

# Esquema SQL basado estrictamente en el diagrama relacional de Mermaid
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS equipo (
    id_equipo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    tipo TEXT,
    marca TEXT,
    modelo TEXT,
    numero_serie TEXT,
    ubicacion_planta TEXT,
    fecha_instalacion TEXT,
    estado_operativo TEXT,
    criticidad TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tecnico (
    id_tecnico INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT,
    rfc TEXT,
    telefono TEXT,
    correo TEXT,
    especialidad TEXT,
    nivel_certificacion TEXT,
    fecha_ingreso TEXT,
    estatus TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orden_mantenimiento (
    id_orden INTEGER PRIMARY KEY AUTOINCREMENT,
    id_equipo INTEGER,
    id_tecnico INTEGER,
    tipo_mantenimiento TEXT,
    fecha_programada TEXT,
    fecha_inicio TEXT,
    fecha_cierre TEXT,
    descripcion_trabajo TEXT,
    costo_estimado REAL,
    costo_real REAL,
    estado_orden TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_equipo) REFERENCES equipo(id_equipo) ON DELETE CASCADE,
    FOREIGN KEY(id_tecnico) REFERENCES tecnico(id_tecnico) ON DELETE SET NULL
);
"""

def init_db(db_path: str = None) -> None:
    """Inicializa las tablas del esquema en la base de datos especificada o actual."""
    path = db_path or get_db_path()
    logger.info("Inicializando esquema SQLite en: %s", path)
    
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
        logger.info("Esquema creado con éxito.")
    finally:
        conn.close()

def clear_db(db_path: str = None) -> None:
    """Limpia los registros de todas las tablas. Útil para resetear en ambiente de pruebas."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    try:
        with conn:
            conn.execute("DELETE FROM orden_mantenimiento")
            conn.execute("DELETE FROM tecnico")
            conn.execute("DELETE FROM equipo")
            # Resetear auto-incrementos
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('equipo', 'tecnico', 'orden_mantenimiento')")
    except sqlite3.OperationalError:
        # En caso de que no existan las secuencias aún
        pass
    finally:
        conn.close()
