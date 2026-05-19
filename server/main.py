"""
SIGOMEI - Servidor Principal
=============================
Este módulo define los modelos, excepciones y controladores que los tests
del servidor requieren (TDD - Fase Roja → Verde).

Archivos de prueba cubiertos:
  - test_equipo.py   → CP-01 al CP-05, CP-21
  - test_tecnico.py  → CP-06 al CP-10
  - test_orden.py    → CP-11 al CP-20, CP-22, CP-23, PU-RN05
  - test_general.py  → CP-24 (Sin conexión DB), CP-25 (Concurrencia / Sockets)

⚠️  NOTA SOBRE CP-25 (Sockets / Concurrencia):
  El test CP-25 simula dos peticiones concurrentes usando threads, lo que
  refleja el comportamiento de un servidor que atiende múltiples clientes
  simultáneamente a través de Sockets (similar a un servidor TCP con
  accept() en bucle). La función `crear_orden_mock_concurrencia` debe
  garantizar que cada hilo-cliente reciba un resultado distinto (ID único),
  reproduciendo así la lógica de aislamiento de sesión por socket.
  Sin embargo, los tests actuales NO levantan un socket real (no hay
  socket.bind / socket.accept); simulan la concurrencia a nivel de threads
  internos. No hay información suficiente para determinar si existe un
  servidor Socket real separado — si lo hay, se indicará en su propio módulo.
"""

import threading


# =============================================================================
# EXCEPCIONES DE DOMINIO
# =============================================================================

class BusinessRuleException(Exception):
    """
    Excepción lanzada cuando se viola una regla de negocio.
    Usada en: CP-12, CP-13, CP-14, CP-19, PU-RN05, PU-RN06/CP-17.
    """
    pass


class ValidationError(Exception):
    """
    Excepción lanzada cuando un campo no supera la validación básica.
    Usada en: CP-02 (Equipo con serie vacía), CP-07 (Técnico correo inválido).
    """
    pass


class StateTransitionException(Exception):
    """
    Excepción lanzada cuando se intenta una transición de estado inválida.
    Usada en: CP-15 (cancelar orden ya finalizada).
    """
    pass


# =============================================================================
# MODELOS
# =============================================================================

class Equipo:
    """
    Modelo de dominio para un equipo registrado en el sistema.
    Usado en: CP-01 al CP-05, CP-11 al CP-20.
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


class Tecnico:
    """
    Modelo de dominio para un técnico registrado en el sistema.
    Usado en: CP-06 al CP-10, CP-11 al CP-14, CP-19, CP-20.
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


class Orden:
    """
    Modelo de dominio para una orden de mantenimiento.
    Usado en: CP-11 al CP-20, CP-22, CP-23, PU-RN05.
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


# =============================================================================
# CONTROLADORES
# =============================================================================

class EquipoController:
    """
    Controlador para operaciones CRUD sobre Equipos.
    Cubre los casos de prueba: CP-01, CP-02, CP-03, CP-04, CP-05, CP-21.
    """

    def registrar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-01: Registrar un equipo con todos sus datos válidos.
        CP-02 (neg): Lanzar ValidationError si 'serie' está vacía.
        Asignará un ID único al equipo al guardarlo exitosamente.
        """
        pass

    def buscar_equipos(self, termino: str) -> list:
        """
        CP-03: Buscar equipos por término (ej. modelo).
        Retorna lista de equipos que coincidan con el término de búsqueda.
        """
        pass

    def actualizar_equipo(self, equipo: Equipo) -> bool:
        """
        CP-04: Actualizar los datos de un equipo existente (ej. estado_operativo).
        Retorna True si la actualización fue exitosa.
        """
        pass

    def obtener_equipo(self, equipo_id) -> Equipo:
        """
        CP-04, CP-05: Obtener un equipo por su ID.
        Retorna None si no existe.
        """
        pass

    def eliminar_equipo(self, equipo_id) -> bool:
        """
        CP-05 & PU-RN04: Eliminar un equipo.
        Lanzar BusinessRuleException si el equipo tiene órdenes asociadas.
        """
        pass

    def obtener_todos(self) -> list:
        """
        CP-21: Retorna todos los equipos registrados.
        Usado para verificar que cancelar en la UI no altera el conteo.
        """
        pass

    def asociar_orden_falsa_para_test(self, equipo_id) -> None:
        """
        Auxiliar de test (CP-05): Simula que un equipo ya tiene una orden
        asociada, para probar la restricción de eliminación (RN-04).
        """
        pass


class TecnicoController:
    """
    Controlador para operaciones CRUD sobre Técnicos.
    Cubre los casos de prueba: CP-06, CP-07, CP-08, CP-09, CP-10.
    """

    def registrar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-06: Registrar un técnico con datos completos y válidos.
        CP-07 (neg): Lanzar ValidationError si el correo no tiene formato válido.
        Asignará un ID único al técnico al guardarlo exitosamente.
        """
        pass

    def actualizar_tecnico(self, tecnico: Tecnico) -> bool:
        """
        CP-08: Actualizar datos de un técnico existente (ej. especialidad).
        CP-10: Cambiar el estatus de un técnico a 'Inactivo'.
        Retorna True si la actualización fue exitosa.
        """
        pass

    def obtener_tecnico(self, tecnico_id) -> Tecnico:
        """
        CP-08, CP-09, CP-10: Obtener un técnico por su ID.
        Retorna None si no existe (usado en CP-09 para verificar eliminación).
        """
        pass

    def eliminar_tecnico(self, tecnico_id) -> bool:
        """
        CP-09: Eliminar un técnico que no tenga órdenes activas.
        Retorna True si fue eliminado correctamente.
        """
        pass


class OrdenController:
    """
    Controlador para operaciones sobre Órdenes de mantenimiento.
    Cubre: CP-11 al CP-20, CP-22, CP-23, PU-RN05, CP-24, CP-25.
    """

    def crear_orden(self, orden: Orden) -> bool:
        """
        CP-11 (pos): Crear una orden de mantenimiento exitosamente.
          - Valida que la especialidad del técnico coincida con el tipo de equipo (RN-01 / CP-12).
          - Valida que no haya colisión de fechas para el mismo equipo (RN-02 / CP-13).
          - Valida que el técnico esté en estatus 'Activo' (RN-03 / CP-14).
          - Valida criticidad 'Alta': requiere técnico nivel II o III (RN-07 / CP-19, CP-20).
        Retorna True si la orden fue creada. Asigna un ID a la orden.
        """
        pass

    def guardar_mock(self, orden: Orden) -> None:
        """
        Auxiliar de test: Guarda una orden directamente en el almacenamiento
        interno sin pasar por las validaciones de negocio.
        Usado en: CP-15, CP-16, CP-17, CP-18, CP-23, PU-RN05.
        """
        pass

    def cancelar_orden(self, orden_id) -> bool:
        """
        CP-23 (pos): Cancelar una orden en estado 'Programada' o 'En Ejecucion'.
        CP-15 & PU-RN08 (neg): Lanzar StateTransitionException si la orden
          ya está en estado 'Finalizada' o 'Cancelada'.
        Retorna True si la cancelación fue exitosa.
        """
        pass

    def actualizar_estado(self, orden_id, nuevo_estado: str) -> bool:
        """
        CP-16: Transición válida de 'Programada' → 'En ejecucion'.
        PU-RN05 (neg): Lanzar BusinessRuleException si la fecha actual
          es anterior a la fecha_programada de la orden.
        Retorna True si el estado fue actualizado correctamente.
        """
        pass

    def realizar_reporte(self, orden_id, costo_cierre: float, observaciones: str = "") -> bool:
        """
        CP-17 & PU-RN06 (neg): Lanzar BusinessRuleException si la orden
          está en estado 'Programada' (no se puede reportar aún).
        CP-18 (pos): Registrar costo real y observaciones; transicionar
          la orden de 'En ejecucion' → 'Finalizada'.
        Retorna True si el reporte fue registrado exitosamente.
        """
        pass

    def obtener_orden(self, orden_id) -> Orden:
        """
        CP-18, CP-23: Obtener una orden por su ID.
        Retorna None si no existe.
        """
        pass

    def simular_desconexion_db(self) -> None:
        """
        CP-24: Comms (Neg) - Simular pérdida de conexión con la base de datos.
        Después de llamar a este método, cualquier operación del controlador
        debe lanzar una Exception con el mensaje "Sin conexión al servidor".

        Contexto de Sockets/Comunicación:
          Este caso representa el escenario en que el servidor no puede
          alcanzar su fuente de datos (DB remota o servicio interno). En
          un sistema con Sockets, esto equivale a que el servidor recibe
          la petición del cliente pero falla al procesar porque el recurso
          de fondo no está disponible (ConnectionRefusedError / timeout).
        """
        pass

    # =========================================================================
    # ⚡ CP-25: CONCURRENCIA / SOCKETS
    # =========================================================================
    def crear_orden_mock_concurrencia(self, datos: str):
        """
        CP-25: Concurr (Pos) - Simular petición concurrente de creación de orden.

        ¿Qué prueba este caso?
          Que el servidor es capaz de atender DOS peticiones simultáneas
          (representadas por dos threads) y que cada una produce un resultado
          distinto e independiente — emulando el comportamiento de un servidor
          que acepta múltiples clientes por Socket al mismo tiempo.

        ¿Qué hará esta función?
          1. Recibir los `datos` de la orden (simula el payload del cliente).
          2. Generar un identificador único para la operación (UUID o timestamp)
             de forma thread-safe (usando un Lock si es necesario).
          3. Crear internamente un objeto Orden con esos datos y el ID generado.
          4. Retornar un dict/objeto con al menos el ID único asignado, para
             que el test pueda comparar que resultados[0] != resultados[1].

        ⚠️  NOTA SOBRE SOCKETS:
          Los tests actuales NO abren un socket real (no hay socket.bind /
          socket.listen / socket.accept). La concurrencia se simula a nivel
          de threads de Python. Si en el futuro se integra un servidor TCP
          real (ej. socketserver.ThreadingTCPServer), esta función sería el
          handler invocado por cada conexión entrante, y el test debería
          levantar un servidor en un thread separado y conectarse con dos
          sockets clientes simultáneos para validar el aislamiento.

          Sin información suficiente sobre la implementación de Sockets real
          planeada para SIGOMEI, no es posible agregar más detalle aquí.
          Se dejará como cascarón hasta obtener la especificación del protocolo.
        """
        pass
