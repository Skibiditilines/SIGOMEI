"""
core/exceptions.py
==================
Excepciones de dominio del servidor SIGOMEI.

Usadas por los tests:
  - BusinessRuleException  → CP-12, CP-13, CP-14, CP-17, CP-19, PU-RN05, PU-RN06
  - ValidationError        → CP-02, CP-07
  - StateTransitionException → CP-15
tag: 1.0.0
"""


class BusinessRuleException(Exception):
    """
    Excepción lanzada cuando se viola una regla de negocio.
    Ejemplos: especialidad no coincide, colisión de fechas, técnico inactivo,
    criticidad alta con técnico I, reporte en estado incorrecto.
    """
    pass


class ValidationError(Exception):
    """
    Excepción lanzada cuando un campo no supera la validación básica de formato.
    Ejemplos: serie vacía en equipo, correo de técnico sin '@'.
    """
    pass


class StateTransitionException(Exception):
    """
    Excepción lanzada cuando se intenta una transición de estado inválida.
    Ejemplo: cancelar una orden que ya está en estado 'Finalizada'.
    """
    pass
