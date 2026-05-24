"""
services/equipo_service.py
==========================
Lógica de negocio para la gestión de Equipos en SIGOMEI persistida en SQLite.
"""

from app.models.equipo import Equipo
from app.core.exceptions import BusinessRuleException, ValidationError
from app.core.database import get_connection, clear_db, DB_MODE
import sqlite3

class EquipoController:
    """
    Servicio que gestiona el ciclo de vida de los Equipos en la base de datos SQLite.
    """

    def __init__(self):
        """Inicializar base de datos y limpiar si estamos en modo prueba."""
        self._fake_orders = set()  # Set de equipment_ids con órdenes simuladas para test
        if DB_MODE == "prueba":
            clear_db()

    def _row_to_equipo(self, row: sqlite3.Row) -> Equipo:
        """Helper para convertir una fila de la BD a un objeto Equipo de dominio."""
        return Equipo(
            id=row["id_equipo"],
            serie=row["numero_serie"],
            marca=row["marca"],
            modelo=row["modelo"],
            tipo=row["tipo"],
            ubicacion=row["ubicacion_planta"],
            estado_operativo=row["estado_operativo"],
            criticidad=row["criticidad"]
        )

    def registrar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-01 (pos): Registrar un equipo con todos sus datos válidos.
        CP-02 (neg): Lanzar ValidationError si el campo 'serie' está vacío.
        """
        # Validación: serie no debe estar vacía
        if not equipo.serie or equipo.serie.strip() == "":
            raise ValidationError("Campo requerido: serie")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # El nombre se compone a partir de la marca y el modelo
            nombre = f"{equipo.marca} {equipo.modelo}".strip() or "Equipo sin nombre"
            cursor.execute("""
                INSERT INTO equipo (
                    nombre, tipo, marca, modelo, numero_serie, 
                    ubicacion_planta, fecha_instalacion, estado_operativo, criticidad
                ) VALUES (?, ?, ?, ?, ?, ?, date('now'), ?, ?)
            """, (
                nombre,
                equipo.tipo,
                equipo.marca,
                equipo.modelo,
                equipo.serie,
                equipo.ubicacion,
                equipo.estado_operativo,
                equipo.criticidad
            ))
            conn.commit()
            equipo.id = cursor.lastrowid
            return True
        finally:
            conn.close()

    def buscar_equipos(self, termino: str) -> list:
        """
        CP-03 (pos): Buscar equipos por término de texto (modelo, marca, tipo).
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            termino_pattern = f"%{termino}%"
            cursor.execute("""
                SELECT * FROM equipo 
                WHERE modelo LIKE ? OR marca LIKE ? OR tipo LIKE ?
            """, (termino_pattern, termino_pattern, termino_pattern))
            rows = cursor.fetchall()
            return [self._row_to_equipo(row) for row in rows]
        finally:
            conn.close()

    def actualizar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-04 (pos): Actualizar los datos de un equipo existente.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            nombre = f"{equipo.marca} {equipo.modelo}".strip() or "Equipo sin nombre"
            cursor.execute("""
                UPDATE equipo SET
                    nombre = ?,
                    tipo = ?,
                    marca = ?,
                    modelo = ?,
                    numero_serie = ?,
                    ubicacion_planta = ?,
                    estado_operativo = ?,
                    criticidad = ?
                WHERE id_equipo = ?
            """, (
                nombre,
                equipo.tipo,
                equipo.marca,
                equipo.modelo,
                equipo.serie,
                equipo.ubicacion,
                equipo.estado_operativo,
                equipo.criticidad,
                equipo.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def obtener_equipo(self, equipo_id) -> Equipo:
        """
        Obtener un equipo por su ID.
        """
        if equipo_id is None:
            return None
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipo WHERE id_equipo = ?", (equipo_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_equipo(row)
            return None
        finally:
            conn.close()

    def eliminar_equipo(self, equipo_id) -> bool:
        """
        CP-05 & PU-RN04 (neg): Eliminar un equipo.
        Lanzar BusinessRuleException si el equipo tiene órdenes vinculadas.
        """
        # Verificar si el equipo tiene órdenes simuladas en tests
        if equipo_id in self._fake_orders:
            raise BusinessRuleException("No se puede eliminar equipo con órdenes asociadas")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # Verificar si tiene órdenes reales asociadas en la BD
            cursor.execute("""
                SELECT COUNT(*) FROM orden_mantenimiento 
                WHERE id_equipo = ?
            """, (equipo_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                raise BusinessRuleException("No se puede eliminar equipo con órdenes asociadas")
            
            cursor.execute("DELETE FROM equipo WHERE id_equipo = ?", (equipo_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def obtener_todos(self) -> list:
        """
        CP-21: Retornar todos los equipos registrados.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipo")
            rows = cursor.fetchall()
            return [self._row_to_equipo(row) for row in rows]
        finally:
            conn.close()

    def asociar_orden_falsa_para_test(self, equipo_id) -> None:
        """
        Auxiliar de test (CP-05 & PU-RN04): Simula que el equipo tiene una orden
        asociada para probar la restricción de eliminación.
        """
        self._fake_orders.add(equipo_id)
