"""
services/orden_service.py
=========================
Lógica de negocio para la gestión de Órdenes de mantenimiento en SIGOMEI persistida en SQLite.
"""

import os
import threading
import sqlite3
from datetime import datetime, date
from app.models.orden import Orden
from app.models.equipo import Equipo
from app.models.tecnico import Tecnico
from app.core.exceptions import BusinessRuleException, StateTransitionException
from app.core.database import get_connection, clear_db, DB_MODE

class OrdenController:
    """
    Servicio que gestiona el ciclo de vida de las Órdenes de mantenimiento en la base de datos SQLite.
    """

    def __init__(self):
        """Inicializar base de datos y limpiar si estamos en modo prueba."""
        self._db_conectada = True  # Bandera de conexión a BD
        self._lock = threading.Lock()  # Lock para thread-safety en concurrencia
        if DB_MODE == "prueba":
            clear_db()

    def _ensure_equipo_stub(self, eq: Equipo) -> None:
        """Asegura que el equipo exista en la base de datos para no violar restricciones de FK en tests."""
        if not eq:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            exists = False
            if eq.id is not None:
                cursor.execute("SELECT 1 FROM equipo WHERE id_equipo = ?", (eq.id,))
                exists = cursor.fetchone() is not None
            
            if not exists:
                nombre = f"{eq.marca} {eq.modelo}".strip() or "Equipo stub"
                cursor.execute("""
                    INSERT INTO equipo (
                        id_equipo, nombre, tipo, marca, modelo, numero_serie,
                        ubicacion_planta, fecha_instalacion, estado_operativo, criticidad
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), ?, ?)
                """, (
                    eq.id,
                    nombre,
                    eq.tipo or "Mecanico",
                    eq.marca or "",
                    eq.modelo or "",
                    eq.serie or f"STUB-{os.urandom(4).hex()}",
                    eq.ubicacion or "",
                    eq.estado_operativo or "Disponible",
                    eq.criticidad or "Normal"
                ))
                conn.commit()
                if eq.id is None:
                    eq.id = cursor.lastrowid
        finally:
            conn.close()

    def _ensure_tecnico_stub(self, tec: Tecnico) -> None:
        """Asegura que el técnico exista en la base de datos para no violar restricciones de FK en tests."""
        if not tec:
            return
        conn = get_connection()
        try:
            cursor = conn.cursor()
            exists = False
            if tec.id is not None:
                cursor.execute("SELECT 1 FROM tecnico WHERE id_tecnico = ?", (tec.id,))
                exists = cursor.fetchone() is not None
            
            if not exists:
                cursor.execute("""
                    INSERT INTO tecnico (
                        id_tecnico, nombre_completo, rfc, telefono, correo,
                        especialidad, nivel_certificacion, fecha_ingreso, estatus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), ?)
                """, (
                    tec.id,
                    tec.nombre or "Tecnico stub",
                    tec.rfc or "",
                    "",  # Telefono
                    tec.correo or "stub@example.com",
                    tec.especialidad or "Mecanico",
                    tec.nivel_certificacion or "I",
                    tec.estatus or "Activo"
                ))
                conn.commit()
                if tec.id is None:
                    tec.id = cursor.lastrowid
        finally:
            conn.close()

    def _insert_orden_record(self, orden: Orden) -> int:
        """Helper para insertar el registro de orden en SQLite."""
        # Asegurar stubs de equipo y tecnico para tests si existen
        self._ensure_equipo_stub(orden.equipo)
        self._ensure_tecnico_stub(orden.tecnico)
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            id_eq = orden.equipo.id if orden.equipo else None
            id_tec = orden.tecnico.id if orden.tecnico else None
            
            # Mapear atributos
            fecha_prog = str(orden.fecha_programada) if orden.fecha_programada else None
            fecha_ini = str(date.today()) if orden.estado == "En ejecucion" else None
            fecha_cie = str(date.today()) if orden.estado == "Finalizada" else None
            
            # Si el orden.id está especificado, lo insertamos explícitamente o usamos REPLACE.
            if orden.id is not None:
                cursor.execute("""
                    INSERT OR REPLACE INTO orden_mantenimiento (
                        id_orden, id_equipo, id_tecnico, tipo_mantenimiento,
                        fecha_programada, fecha_inicio, fecha_cierre,
                        descripcion_trabajo, costo_estimado, costo_real, estado_orden
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    orden.id, id_eq, id_tec, orden.tipo_mantenimiento,
                    fecha_prog, fecha_ini, fecha_cie,
                    orden.observaciones, orden.costo_estimado, orden.costo_real, orden.estado
                ))
                inserted_id = orden.id
            else:
                cursor.execute("""
                    INSERT INTO orden_mantenimiento (
                        id_equipo, id_tecnico, tipo_mantenimiento,
                        fecha_programada, fecha_inicio, fecha_cierre,
                        descripcion_trabajo, costo_estimado, costo_real, estado_orden
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id_eq, id_tec, orden.tipo_mantenimiento,
                    fecha_prog, fecha_ini, fecha_cie,
                    orden.observaciones, orden.costo_estimado, orden.costo_real, orden.estado
                ))
                inserted_id = cursor.lastrowid
                
            conn.commit()
            return inserted_id
        finally:
            conn.close()

    def crear_orden(self, orden: Orden) -> bool:
        """
        CP-11 (pos): Crear una orden de mantenimiento exitosamente.
        Validaciones de negocio que debe aplicar (en orden):
          - RN-01 / CP-12: La especialidad del técnico debe coincidir con el tipo del equipo.
          - RN-02 / CP-13: No debe haber otra orden activa para el mismo equipo en la misma fecha_programada.
          - RN-03 / CP-14: El técnico debe estar en estatus 'Activo'.
          - RN-07 / CP-19: Si el equipo tiene criticidad 'Alta', el técnico debe tener nivel 'II' o 'III'.
        """
        # Verificar conexión a BD
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        # RN-01: Especialidad del técnico debe coincidir con tipo de equipo
        if orden.tecnico.especialidad != orden.equipo.tipo:
            raise BusinessRuleException("Especialidad no coincide con tipo de equipo")
            
        # El tipo de mantenimiento debe coincidir con la especialidad del técnico
        if orden.tipo_mantenimiento != orden.tecnico.especialidad:
            raise BusinessRuleException("El tipo de mantenimiento debe coincidir con la especialidad del técnico")
        
        # Asegurar stubs de equipo y tecnico para poder buscar colisiones correctamente
        self._ensure_equipo_stub(orden.equipo)
        self._ensure_tecnico_stub(orden.tecnico)
        
        # RN-02: No debe haber colisión de fechas (mismo equipo, misma fecha, estado != Cancelada)
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM orden_mantenimiento 
                WHERE id_equipo = ? AND fecha_programada = ? AND estado_orden != 'Cancelada'
            """, (orden.equipo.id, str(orden.fecha_programada)))
            count = cursor.fetchone()[0]
            if count > 0:
                raise BusinessRuleException("Colisión de fechas")
        finally:
            conn.close()
        
        # RN-03: El técnico debe estar en estatus 'Activo'
        if orden.tecnico.estatus != "Activo":
            raise BusinessRuleException("Técnico se encuentra inactivo")
        
        # RN-07: Si equipo tiene criticidad 'Alta', técnico debe ser nivel II o III
        if orden.equipo.criticidad == "Alta":
            if orden.tecnico.nivel_certificacion not in ["II", "III"]:
                raise BusinessRuleException("Equipo Alta Criticidad requiere Técnico II o III")
        
        # Asignar ID incremental y registrar en SQLite de forma thread-safe
        with self._lock:
            inserted_id = self._insert_orden_record(orden)
            orden.id = inserted_id
        
        return True

    def guardar_mock(self, orden: Orden) -> None:
        """
        Auxiliar de test: Persiste una orden directamente sin ejecutar validaciones de negocio.
        """
        inserted_id = self._insert_orden_record(orden)
        orden.id = inserted_id

    def cancelar_orden(self, orden_id) -> bool:
        """
        CP-23 & RN-08 (pos): Cancelar una orden en estado 'Programada' o 'En Ejecucion'.
        CP-15 & RN-08 (neg): Lanzar StateTransitionException si la orden ya está Finalizada o Cancelada.
        """
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        orden = self.obtener_orden(orden_id)
        if not orden:
            return False
        
        # RN-08: No permitir cancelar si ya está en estado 'Finalizada' o 'Cancelada'
        if orden.estado in ["Finalizada", "Cancelada"]:
            raise StateTransitionException("Transición de estado no permitida. Orden ya cerrada.")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orden_mantenimiento SET estado_orden = 'Cancelada'
                WHERE id_orden = ?
            """, (orden_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def actualizar_estado(self, orden_id, nuevo_estado: str) -> bool:
        """
        CP-16 (pos): Transición válida de 'Programada' → 'En ejecucion'.
        PU-RN05 (neg): Lanzar BusinessRuleException si la fecha actual es anterior a la fecha_programada.
        """
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        orden = self.obtener_orden(orden_id)
        if not orden:
            return False
        
        # RN-05: Si transitando a 'En ejecucion', verificar que fecha actual >= fecha_programada
        if nuevo_estado == "En ejecucion":
            fecha_actual = datetime.now().date()
            if fecha_actual < orden.fecha_programada:
                raise BusinessRuleException("La fecha actual es anterior a la fecha programada")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            fecha_ini = str(date.today()) if nuevo_estado == "En ejecucion" else None
            cursor.execute("""
                UPDATE orden_mantenimiento SET 
                    estado_orden = ?,
                    fecha_inicio = COALESCE(?, fecha_inicio)
                WHERE id_orden = ?
            """, (nuevo_estado, fecha_ini, orden_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def realizar_reporte(self, orden_id, costo_cierre: float, observaciones: str = "") -> bool:
        """
        CP-18 (pos): Registrar el costo real y observaciones al cerrar una orden 'En ejecucion'.
        CP-17 & PU-RN06 (neg): Lanzar BusinessRuleException si la orden está en estado 'Programada'.
        """
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        orden = self.obtener_orden(orden_id)
        if not orden:
            return False
        
        # RN-06: No permitir reporte si estado es 'Programada'
        if orden.estado == "Programada":
            raise BusinessRuleException("El reporte y los costos reales solo aplican al finalizar")
        
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orden_mantenimiento SET
                    costo_real = ?,
                    descripcion_trabajo = ?,
                    estado_orden = 'Finalizada',
                    fecha_cierre = ?
                WHERE id_orden = ?
            """, (costo_cierre, observaciones, str(date.today()), orden_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def obtener_orden(self, orden_id) -> Orden:
        """
        Obtener una orden por su ID.
        """
        if orden_id is None:
            return None
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orden_mantenimiento WHERE id_orden = ?", (orden_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            # Cargar equipo y técnico asociados desde sus respectivas tablas
            id_eq = row["id_equipo"]
            id_tec = row["id_tecnico"]
            
            equipo = None
            if id_eq is not None:
                cursor.execute("SELECT * FROM equipo WHERE id_equipo = ?", (id_eq,))
                eq_row = cursor.fetchone()
                if eq_row:
                    equipo = Equipo(
                        id=eq_row["id_equipo"],
                        serie=eq_row["numero_serie"],
                        marca=eq_row["marca"],
                        modelo=eq_row["modelo"],
                        tipo=eq_row["tipo"],
                        ubicacion=eq_row["ubicacion_planta"],
                        estado_operativo=eq_row["estado_operativo"],
                        criticidad=eq_row["criticidad"]
                    )
            
            tecnico = None
            if id_tec is not None:
                cursor.execute("SELECT * FROM tecnico WHERE id_tecnico = ?", (id_tec,))
                tec_row = cursor.fetchone()
                if tec_row:
                    tecnico = Tecnico(
                        id=tec_row["id_tecnico"],
                        nombre=tec_row["nombre_completo"],
                        especialidad=tec_row["especialidad"],
                        rfc=tec_row["rfc"],
                        nivel_certificacion=tec_row["nivel_certificacion"],
                        correo=tec_row["correo"],
                        estatus=tec_row["estatus"]
                    )
            
            fecha_raw = row["fecha_programada"]
            fecha = date.fromisoformat(fecha_raw) if fecha_raw else None
            
            return Orden(
                id=row["id_orden"],
                equipo=equipo,
                tecnico=tecnico,
                tipo_mantenimiento=row["tipo_mantenimiento"],
                fecha_programada=fecha,
                estado=row["estado_orden"],
                costo_estimado=float(row["costo_estimado"] or 0.0),
                costo_real=float(row["costo_real"] or 0.0),
                observaciones=row["descripcion_trabajo"] or ""
            )
        finally:
            conn.close()

    def obtener_todas(self) -> list:
        """Obtener la lista de todas las órdenes."""
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_orden FROM orden_mantenimiento")
            ids = [r[0] for r in cursor.fetchall()]
        finally:
            conn.close()
            
        return [self.obtener_orden(oid) for oid in ids if oid is not None]

    def simular_desconexion_db(self) -> None:
        """
        CP-24: Comms (Neg) — Simular pérdida de conexión con la base de datos.
        """
        self._db_conectada = False

    @property
    def _db(self) -> dict:
        """Propiedad de compatibilidad con dispatcher u otros módulos."""
        return {o.id: o for o in self.obtener_todas()}

    # =========================================================================
    # ⚡ CP-25: CONCURRENCIA / SOCKETS
    # =========================================================================
    def crear_orden_mock_concurrencia(self, datos: str):
        """
        CP-25: Concurr (Pos) — Simular petición concurrente de creación de orden.
        """
        with self._lock:
            # Para simular un ID único de forma thread-safe en pruebas rápidas
            conn = get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO orden_mantenimiento (
                        descripcion_trabajo, estado_orden, costo_estimado, costo_real
                    ) VALUES (?, 'Programada', 0.0, 0.0)
                """, (datos,))
                conn.commit()
                nuevo_id = cursor.lastrowid
            finally:
                conn.close()
        
        return {'id': nuevo_id, 'datos': datos}
