"""
server/app/network/dispatcher.py
=================================
Enruta cada acción recibida por el Handler hacia el servicio/controlador
correcto y construye la respuesta JSON estándar.

Acciones soportadas:
  Equipos:
    equipo.registrar      → EquipoController.registrar_equipo
    equipo.buscar         → EquipoController.buscar_equipos
    equipo.actualizar     → EquipoController.actualizar_equipo
    equipo.eliminar       → EquipoController.eliminar_equipo
    equipo.obtener        → EquipoController.obtener_equipo
    equipo.listar         → EquipoController.obtener_todos

  Técnicos:
    tecnico.registrar     → TecnicoController.registrar_tecnico
    tecnico.actualizar    → TecnicoController.actualizar_tecnico
    tecnico.obtener       → TecnicoController.obtener_tecnico
    tecnico.eliminar      → TecnicoController.eliminar_tecnico

  Órdenes:
    orden.crear           → OrdenController.crear_orden
    orden.cancelar        → OrdenController.cancelar_orden
    orden.actualizar_estado → OrdenController.actualizar_estado
    orden.reporte         → OrdenController.realizar_reporte
    orden.obtener         → OrdenController.obtener_orden

tag: 1.0.0
"""

import logging
from datetime import date

from app.services.equipo_service import EquipoController
from app.services.tecnico_service import TecnicoController
from app.services.orden_service import OrdenController
from app.models.equipo import Equipo
from app.models.tecnico import Tecnico
from app.models.orden import Orden
from app.core.exceptions import BusinessRuleException, ValidationError, StateTransitionException

logger = logging.getLogger("sigomei.dispatcher")


def _equipo_to_dict(eq: Equipo) -> dict:
    """Serializa un objeto Equipo a diccionario JSON-serializable."""
    if eq is None:
        return None
    return {
        "id": eq.id,
        "serie": eq.serie,
        "marca": eq.marca,
        "modelo": eq.modelo,
        "tipo": eq.tipo,
        "ubicacion": eq.ubicacion,
        "estado_operativo": eq.estado_operativo,
        "criticidad": eq.criticidad,
    }


def _tecnico_to_dict(tec: Tecnico) -> dict:
    """Serializa un objeto Tecnico a diccionario JSON-serializable."""
    if tec is None:
        return None
    return {
        "id": tec.id,
        "nombre": tec.nombre,
        "especialidad": tec.especialidad,
        "rfc": tec.rfc,
        "nivel_certificacion": tec.nivel_certificacion,
        "correo": tec.correo,
        "estatus": tec.estatus,
    }


def _orden_to_dict(ord_: Orden) -> dict:
    """Serializa un objeto Orden (con sus sub-objetos) a diccionario JSON-serializable."""
    if ord_ is None:
        return None
    return {
        "id": ord_.id,
        "equipo": _equipo_to_dict(ord_.equipo),
        "tecnico": _tecnico_to_dict(ord_.tecnico),
        "tipo_mantenimiento": ord_.tipo_mantenimiento,
        "fecha_programada": str(ord_.fecha_programada) if ord_.fecha_programada else None,
        "estado": ord_.estado,
        "costo_estimado": ord_.costo_estimado,
        "costo_real": ord_.costo_real,
        "observaciones": ord_.observaciones,
    }


def _dict_to_equipo(d: dict) -> Equipo:
    """Deserializa un diccionario a objeto Equipo."""
    return Equipo(
        id=d.get("id"),
        serie=d.get("serie", ""),
        marca=d.get("marca", ""),
        modelo=d.get("modelo", ""),
        tipo=d.get("tipo", ""),
        ubicacion=d.get("ubicacion", ""),
        estado_operativo=d.get("estado_operativo", "Disponible"),
        criticidad=d.get("criticidad", "Normal"),
    )


def _dict_to_tecnico(d: dict) -> Tecnico:
    """Deserializa un diccionario a objeto Tecnico."""
    return Tecnico(
        id=d.get("id"),
        nombre=d.get("nombre", ""),
        especialidad=d.get("especialidad", ""),
        rfc=d.get("rfc", ""),
        nivel_certificacion=d.get("nivel_certificacion", "I"),
        correo=d.get("correo", ""),
        estatus=d.get("estatus", "Activo"),
    )


def _dict_to_orden(d: dict) -> Orden:
    """Deserializa un diccionario a objeto Orden (incluye Equipo y Tecnico anidados)."""
    equipo = _dict_to_equipo(d["equipo"]) if d.get("equipo") else None
    tecnico = _dict_to_tecnico(d["tecnico"]) if d.get("tecnico") else None

    fecha_raw = d.get("fecha_programada")
    fecha = date.fromisoformat(fecha_raw) if fecha_raw else None

    return Orden(
        id=d.get("id"),
        equipo=equipo,
        tecnico=tecnico,
        tipo_mantenimiento=d.get("tipo_mantenimiento", ""),
        fecha_programada=fecha,
        estado=d.get("estado", "Programada"),
        costo_estimado=float(d.get("costo_estimado", 0.0)),
        costo_real=float(d.get("costo_real", 0.0)),
        observaciones=d.get("observaciones", ""),
    )


def _ok(data=None) -> dict:
    """Construye una respuesta de éxito estándar."""
    return {"status": "ok", "data": data}


def _err(exc_type: str, message: str) -> dict:
    """Construye una respuesta de error estándar."""
    return {"status": "error", "type": exc_type, "message": message}


class Dispatcher:
    """
    Enrutador central de acciones para el servidor SIGOMEI.

    Mantiene instancias singleton (a nivel de proceso) de los tres
    controladores, thread-safe gracias a los Locks internos de cada uno.
    """

    def __init__(self):
        self._equipos = EquipoController()
        self._tecnicos = TecnicoController()
        self._ordenes = OrdenController()

        # Tabla de enrutamiento: acción → método handler
        self._routes = {
            # --- Equipos ---
            "equipo.registrar":   self._equipo_registrar,
            "equipo.buscar":      self._equipo_buscar,
            "equipo.actualizar":  self._equipo_actualizar,
            "equipo.eliminar":    self._equipo_eliminar,
            "equipo.obtener":     self._equipo_obtener,
            "equipo.listar":      self._equipo_listar,
            # --- Técnicos ---
            "tecnico.registrar":  self._tecnico_registrar,
            "tecnico.actualizar": self._tecnico_actualizar,
            "tecnico.obtener":    self._tecnico_obtener,
            "tecnico.eliminar":   self._tecnico_eliminar,
            "tecnico.listar":     self._tecnico_listar,
            # --- Órdenes ---
            "orden.crear":            self._orden_crear,
            "orden.cancelar":         self._orden_cancelar,
            "orden.actualizar_estado": self._orden_actualizar_estado,
            "orden.reporte":          self._orden_reporte,
            "orden.obtener":          self._orden_obtener,
            "orden.listar":           self._orden_listar,
        }

    def dispatch(self, action: str, payload: dict) -> dict:
        """
        Enruta la acción al handler correspondiente.
        Atrapa las excepciones de dominio y las convierte en respuestas de error.
        """
        handler = self._routes.get(action)
        if handler is None:
            logger.warning("Acción desconocida: '%s'", action)
            return _err("UnknownAction", f"Acción no reconocida: '{action}'")

        try:
            return handler(payload)
        except BusinessRuleException as exc:
            logger.info("BusinessRule violation [%s]: %s", action, exc)
            return _err("BusinessRuleException", str(exc))
        except ValidationError as exc:
            logger.info("Validation error [%s]: %s", action, exc)
            return _err("ValidationError", str(exc))
        except StateTransitionException as exc:
            logger.info("StateTransition error [%s]: %s", action, exc)
            return _err("StateTransitionException", str(exc))
        except Exception as exc:
            logger.exception("Error inesperado [%s]: %s", action, exc)
            return _err("InternalServerError", str(exc))

    # ==========================================================================
    # Handlers — Equipos
    # ==========================================================================

    def _equipo_registrar(self, p: dict) -> dict:
        equipo = _dict_to_equipo(p)
        self._equipos.registrar_equipo(equipo)
        return _ok(_equipo_to_dict(equipo))

    def _equipo_buscar(self, p: dict) -> dict:
        termino = p.get("termino", "")
        resultados = self._equipos.buscar_equipos(termino)
        return _ok([_equipo_to_dict(e) for e in resultados])

    def _equipo_actualizar(self, p: dict) -> dict:
        equipo = _dict_to_equipo(p)
        ok = self._equipos.actualizar_equipo(equipo)
        return _ok({"actualizado": ok})

    def _equipo_eliminar(self, p: dict) -> dict:
        equipo_id = p.get("id")
        ok = self._equipos.eliminar_equipo(equipo_id)
        return _ok({"eliminado": ok})

    def _equipo_obtener(self, p: dict) -> dict:
        equipo_id = p.get("id")
        equipo = self._equipos.obtener_equipo(equipo_id)
        return _ok(_equipo_to_dict(equipo))

    def _equipo_listar(self, p: dict) -> dict:
        equipos = self._equipos.obtener_todos()
        return _ok([_equipo_to_dict(e) for e in equipos])

    # ==========================================================================
    # Handlers — Técnicos
    # ==========================================================================

    def _tecnico_registrar(self, p: dict) -> dict:
        tecnico = _dict_to_tecnico(p)
        self._tecnicos.registrar_tecnico(tecnico)
        return _ok(_tecnico_to_dict(tecnico))

    def _tecnico_actualizar(self, p: dict) -> dict:
        tecnico = _dict_to_tecnico(p)
        ok = self._tecnicos.actualizar_tecnico(tecnico)
        return _ok({"actualizado": ok})

    def _tecnico_obtener(self, p: dict) -> dict:
        tecnico_id = p.get("id")
        tecnico = self._tecnicos.obtener_tecnico(tecnico_id)
        return _ok(_tecnico_to_dict(tecnico))

    def _tecnico_eliminar(self, p: dict) -> dict:
        tecnico_id = p.get("id")
        ok = self._tecnicos.eliminar_tecnico(tecnico_id)
        return _ok({"eliminado": ok})

    def _tecnico_listar(self, p: dict) -> dict:
        tecnicos = list(self._tecnicos._db.values())
        return _ok([_tecnico_to_dict(t) for t in tecnicos])

    # ==========================================================================
    # Handlers — Órdenes
    # ==========================================================================

    def _orden_crear(self, p: dict) -> dict:
        orden = _dict_to_orden(p)
        self._ordenes.crear_orden(orden)
        return _ok(_orden_to_dict(orden))

    def _orden_cancelar(self, p: dict) -> dict:
        orden_id = p.get("id")
        ok = self._ordenes.cancelar_orden(orden_id)
        return _ok({"cancelada": ok})

    def _orden_actualizar_estado(self, p: dict) -> dict:
        orden_id = p.get("id")
        nuevo_estado = p.get("nuevo_estado", "")
        ok = self._ordenes.actualizar_estado(orden_id, nuevo_estado)
        return _ok({"actualizado": ok})

    def _orden_reporte(self, p: dict) -> dict:
        orden_id = p.get("id")
        costo = float(p.get("costo_cierre", 0.0))
        observaciones = p.get("observaciones", "")
        ok = self._ordenes.realizar_reporte(orden_id, costo, observaciones)
        return _ok({"reportado": ok})

    def _orden_obtener(self, p: dict) -> dict:
        orden_id = p.get("id")
        orden = self._ordenes.obtener_orden(orden_id)
        return _ok(_orden_to_dict(orden))

    def _orden_listar(self, p: dict) -> dict:
        ordenes = self._ordenes.obtener_todas()
        return _ok([_orden_to_dict(o) for o in ordenes])
