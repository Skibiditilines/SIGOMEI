"""
services/equipo_service.py
==========================
Lógica de negocio para la gestión de Equipos en SIGOMEI.
Corresponde a lo que los tests llaman 'EquipoController'.

Casos de prueba cubiertos:
  - CP-01: Registrar equipo con éxito
  - CP-02: Lanzar ValidationError si 'serie' está vacía
  - CP-03: Buscar equipos por término (ej. modelo)
  - CP-04: Editar estado_operativo de un equipo
  - CP-05 & PU-RN04: No eliminar equipo con órdenes asociadas
  - CP-21: Verificar que cancelar en UI no altera el conteo de equipos
"""

from app.models.equipo import Equipo
from app.core.exceptions import BusinessRuleException, ValidationError


class EquipoController:
    """
    Servicio que gestiona el ciclo de vida de los Equipos.
    En la arquitectura FastAPI, este servicio es invocado desde las rutas (routes/).
    """

    def registrar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-01 (pos): Registrar un equipo con todos sus datos válidos.
          Asigna un ID único al equipo al guardarlo exitosamente.
        CP-02 (neg): Lanzar ValidationError con mensaje
          "Campo requerido: serie" si el campo 'serie' está vacío.
        """
        pass

    def buscar_equipos(self, termino: str) -> list:
        """
        CP-03 (pos): Buscar equipos por término de texto.
          Compara el término contra el modelo (y otros campos relevantes).
          Retorna una lista de instancias Equipo que coincidan.
        """
        pass

    def actualizar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-04 (pos): Actualizar los datos de un equipo existente.
          Por ejemplo, cambiar 'estado_operativo' a "En Mantenimiento".
          Retorna True si la actualización fue exitosa.
        """
        pass

    def obtener_equipo(self, equipo_id) -> Equipo:
        """
        CP-04, CP-05: Obtener un equipo por su ID.
          Retorna None si el ID no existe en el almacenamiento.
        """
        pass

    def eliminar_equipo(self, equipo_id) -> bool:
        """
        CP-05 & PU-RN04 (neg): Eliminar un equipo.
          Lanzar BusinessRuleException con mensaje
          "No se puede eliminar equipo con órdenes asociadas"
          si el equipo tiene órdenes vinculadas.
          Retorna True si la eliminación fue exitosa.
        """
        pass

    def obtener_todos(self) -> list:
        """
        CP-21: Retornar todos los equipos registrados.
          Usado para verificar que una cancelación en la UI
          no modifica el conteo de equipos en el backend.
        """
        pass

    def asociar_orden_falsa_para_test(self, equipo_id) -> None:
        """
        Auxiliar de test (CP-05 & PU-RN04):
          Simula internamente que el equipo con 'equipo_id' ya tiene
          una orden asociada, para activar la restricción de eliminación
          sin necesidad de crear una Orden real en la BD.
        """
        pass
