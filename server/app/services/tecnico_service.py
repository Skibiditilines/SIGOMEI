"""
services/tecnico_service.py
===========================
Lógica de negocio para la gestión de Técnicos en SIGOMEI.
Corresponde a lo que los tests llaman 'TecnicoController'.

Casos de prueba cubiertos:
  - CP-06: Registrar técnico con datos completos y válidos
  - CP-07: Lanzar ValidationError si el correo no tiene formato válido
  - CP-08: Editar especialidad de un técnico
  - CP-09: Eliminar técnico sin órdenes activas
  - CP-10: Cambiar estatus a 'Inactivo'
"""

from app.models.tecnico import Tecnico
from app.core.exceptions import ValidationError


class TecnicoController:
    """
    Servicio que gestiona el ciclo de vida de los Técnicos.
    En la arquitectura FastAPI, este servicio es invocado desde las rutas (routes/).
    """

    def registrar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-06 (pos): Registrar un técnico con datos completos y válidos.
          Asigna un ID único al técnico al guardarlo exitosamente.
        CP-07 (neg): Lanzar ValidationError con mensaje
          "Formato de correo incorrecto" si el correo no contiene '@'.
        """
        pass

    def actualizar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-08 (pos): Actualizar datos de un técnico existente.
          Ejemplo: cambiar 'especialidad' de "Mecanico" a "Hidraulico".
        CP-10 (pos): Cambiar el 'estatus' de un técnico a "Inactivo".
          Retorna True si la actualización fue exitosa.
        """
        pass

    def obtener_tecnico(self, tecnico_id) -> Tecnico:
        """
        CP-08, CP-09, CP-10: Obtener un técnico por su ID.
          Retorna None si el técnico fue eliminado o no existe
          (verificación post-eliminación en CP-09).
        """
        pass

    def eliminar_tecnico(self, tecnico_id) -> bool:
        """
        CP-09 (pos): Eliminar un técnico que no tenga órdenes activas.
          Retorna True si la eliminación fue exitosa.
        """
        pass
