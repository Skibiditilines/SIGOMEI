"""
services/tecnico_service.py
===========================
Lógica de negocio para la gestión de Técnicos en SIGOMEI persistida en SQLite.
"""

from app.models.tecnico import Tecnico
from app.core.exceptions import ValidationError
from app.core.database import get_connection, clear_db, DB_MODE
import sqlite3

class TecnicoController:
    """
    Servicio que gestiona el ciclo de vida de los Técnicos en la base de datos SQLite.
    """

    def __init__(self):
        """Inicializar base de datos y limpiar si estamos en modo prueba."""
        if DB_MODE == "prueba":
            clear_db()

    def _row_to_tecnico(self, row: sqlite3.Row) -> Tecnico:
        """Helper para convertir una fila de la BD a un objeto Tecnico de dominio."""
        return Tecnico(
            id=row["id_tecnico"],
            nombre=row["nombre_completo"],
            especialidad=row["especialidad"],
            rfc=row["rfc"],
            nivel_certificacion=row["nivel_certificacion"],
            correo=row["correo"],
            estatus=row["estatus"]
        )

    def registrar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-06 (pos): Registrar un técnico con datos completos y válidos.
        CP-07 (neg): Lanzar ValidationError si el correo no tiene formato válido (no contiene '@').
        """
        # Validación: si correo está presente, debe contener '@'
        if tecnico.correo and '@' not in tecnico.correo:
            raise ValidationError("Formato de correo incorrecto")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tecnico (
                    nombre_completo, rfc, telefono, correo, 
                    especialidad, nivel_certificacion, fecha_ingreso, estatus
                ) VALUES (?, ?, ?, ?, ?, ?, date('now'), ?)
            """, (
                tecnico.nombre,
                tecnico.rfc,
                "",  # telefono por defecto vacío
                tecnico.correo,
                tecnico.especialidad,
                tecnico.nivel_certificacion,
                tecnico.estatus
            ))
            conn.commit()
            tecnico.id = cursor.lastrowid
            return True
        finally:
            conn.close()

    def actualizar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-08 (pos): Actualizar datos de un técnico existente.
        CP-10 (pos): Cambiar el 'estatus' de un técnico a "Inactivo".
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tecnico SET
                    nombre_completo = ?,
                    rfc = ?,
                    correo = ?,
                    especialidad = ?,
                    nivel_certificacion = ?,
                    estatus = ?
                WHERE id_tecnico = ?
            """, (
                tecnico.nombre,
                tecnico.rfc,
                tecnico.correo,
                tecnico.especialidad,
                tecnico.nivel_certificacion,
                tecnico.estatus,
                tecnico.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def obtener_tecnico(self, tecnico_id) -> Tecnico:
        """
        Obtener un técnico por su ID.
        """
        if tecnico_id is None:
            return None
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tecnico WHERE id_tecnico = ?", (tecnico_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_tecnico(row)
            return None
        finally:
            conn.close()

    def eliminar_tecnico(self, tecnico_id) -> bool:
        """
        CP-09 (pos): Eliminar un técnico que no tenga órdenes activas.
        """
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tecnico WHERE id_tecnico = ?", (tecnico_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def obtener_todos(self) -> list:
        """Obtener la lista de todos los técnicos."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tecnico")
            rows = cursor.fetchall()
            return [self._row_to_tecnico(row) for row in rows]
        finally:
            conn.close()

    @property
    def _db(self) -> dict:
        """Propiedad de compatibilidad con dispatcher para no alterar la capa de red."""
        return {t.id: t for t in self.obtener_todos()}
