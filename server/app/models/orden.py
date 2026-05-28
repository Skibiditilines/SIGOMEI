"""
models/orden.py
===============
Modelo de dominio para una orden de mantenimiento en SIGOMEI.

Usado en los tests:
  - CP-11: crear orden exitosa
  - CP-12: especialidad no coincide (RN-01)
  - CP-13: colisión de fechas (RN-02)
  - CP-14: técnico inactivo (RN-03)
  - CP-15 & PU-RN08: cancelar orden finalizada (prohibido)
  - CP-16: transición Programada → En ejecucion
  - CP-17 & PU-RN06: reporte solo aplica a ciertas etapas
  - CP-18: reporte en orden En Ejecucion → Finalizada
  - CP-19 & PU-RN07: criticidad alta requiere técnico II o III
  - CP-20: criticidad alta con técnico III (permitido)
  - CP-22: cancelación desde UI (sin efecto en backend)
  - CP-23 & PU-RN08: cancelar orden Programada o En Ejecucion
  - PU-RN05: no pasar a En ejecucion si fecha actual < fecha_programada

tag: 1.0.0
"""

from app.models.equipo import Equipo
from app.models.tecnico import Tecnico


class Orden:
    """
    Representa una orden de mantenimiento asignada a un equipo y un técnico.

    Atributos:
        id                  -- Identificador único (asignado al persistir).
        equipo              -- Instancia de Equipo al que se aplica el mantenimiento.
        tecnico             -- Instancia de Tecnico asignado a la orden.
        tipo_mantenimiento  -- Tipo: "Preventivo", "Correctivo", etc.
        fecha_programada    -- Fecha en que se ejecutará el mantenimiento (date).
        estado              -- Estado actual: "Programada", "En ejecucion",
                               "Finalizada" o "Cancelada".
        costo_estimado      -- Costo estimado antes de ejecutar.
        costo_real          -- Costo real registrado al finalizar.
        observaciones       -- Notas adicionales al cerrar la orden.
    """

    def __init__(self, id=None, equipo=None, tecnico=None,
                 tipo_mantenimiento="", fecha_programada=None, estado="Programada",
                 costo_estimado=0.0, costo_real=0.0, observaciones=""):
        self.id = id
        self.equipo = equipo
        self.tecnico = tecnico
        self.tipo_mantenimiento = tipo_mantenimiento
        self.fecha_programada = fecha_programada
        self.estado = estado
        self.costo_estimado = costo_estimado
        self.costo_real = costo_real
        self.observaciones = observaciones
