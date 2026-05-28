"""
models/tecnico.py
=================
Modelo de dominio para un técnico registrado en SIGOMEI.

Usado en los tests:
  - CP-06: registrar técnico exitoso
  - CP-07: correo sin formato válido
  - CP-08: editar especialidad
  - CP-09: eliminar técnico sin órdenes
  - CP-10: cambiar estatus a 'Inactivo'
  - CP-11 al CP-14, CP-19, CP-20: técnico asignado a una Orden

tag: 1.0.0
"""


class Tecnico:
    """
    Representa a un técnico que puede ser asignado a órdenes de mantenimiento.

    Atributos:
        id                  -- Identificador único (asignado al persistir).
        nombre              -- Nombre completo del técnico.
        especialidad        -- Área de especialización: "Mecanico", "Electrico", etc.
        rfc                 -- RFC del técnico (identificación fiscal).
        nivel_certificacion -- Nivel de certificación: "I", "II" o "III".
        correo              -- Correo electrónico (debe tener formato válido con '@').
        estatus             -- Estado laboral: "Activo" o "Inactivo".
    """

    def __init__(self, id=None, nombre="", especialidad="", rfc="",
                 nivel_certificacion="I", correo="", estatus="Activo"):
        self.id = id
        self.nombre = nombre
        self.especialidad = especialidad
        self.rfc = rfc
        self.nivel_certificacion = nivel_certificacion
        self.correo = correo
        self.estatus = estatus
