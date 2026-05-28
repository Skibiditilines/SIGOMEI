"""
models/equipo.py
================
Modelo de dominio para un equipo registrado en SIGOMEI.

Usado en los tests:
  - CP-01: registrar equipo exitoso
  - CP-02: equipo con campo 'serie' vacío
  - CP-03: buscar equipo por modelo
  - CP-04: editar estado_operativo
  - CP-05 & PU-RN04: no eliminar equipo con órdenes asociadas
  - CP-11 al CP-20: usado como parte de una Orden
tag: 1.0.0
"""


class Equipo:
    """
    Representa un equipo físico de la planta que puede recibir mantenimiento.

    Atributos:
        id              -- Identificador único (asignado al persistir).
        serie           -- Número de serie del equipo (requerido).
        marca           -- Marca del fabricante.
        modelo          -- Modelo específico del equipo.
        tipo            -- Tipo/categoría: "Mecanico", "Electrico", etc.
        ubicacion       -- Ubicación física dentro de la planta.
        estado_operativo-- Estado actual: "Disponible", "En Mantenimiento", etc.
        criticidad      -- Nivel de criticidad: "Normal", "Alta".
    """

    def __init__(self, id=None, serie="", marca="", modelo="", tipo="",
                 ubicacion="", estado_operativo="Disponible", criticidad="Normal"):
        self.id = id
        self.serie = serie
        self.marca = marca
        self.modelo = modelo
        self.tipo = tipo
        self.ubicacion = ubicacion
        self.estado_operativo = estado_operativo
        self.criticidad = criticidad
