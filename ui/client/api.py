"""
ui/client/api.py
=================
API de alto nivel para la interfaz gráfica de SIGOMEI.

Wrappea SigomeiClient con métodos semánticos que corresponden a las
operaciones de cada módulo del sistema.  La UI solo necesita importar
SigomeiAPI y llamar a sus métodos; toda la lógica de red queda oculta.

Manejo de errores:
    - Si el servidor responde {"status": "error"}, se lanza SigomeiAPIError
      con el tipo y mensaje del error.
    - Si hay problemas de red, se propagan las excepciones de SigomeiClient
      (ConnectionError, TimeoutError).

Uso básico desde la UI:
    api = SigomeiAPI(host="127.0.0.1", port=9000)

    # Equipos
    equipo = api.registrar_equipo(serie="SN-001", marca="ABB", ...)
    equipos = api.listar_equipos()

    # Técnicos
    tecnico = api.registrar_tecnico(nombre="Juan", correo="j@e.com", ...)

    # Órdenes
    orden = api.crear_orden(equipo=equipo, tecnico=tecnico, ...)

tag: 1.0.0
"""

from client.socket_client import SigomeiClient


class SigomeiAPIError(Exception):
    """
    Excepción lanzada cuando el servidor retorna {"status": "error"}.

    Atributos:
        error_type -- Nombre de la excepción de dominio (e.g. "BusinessRuleException")
        message    -- Mensaje de detalle del error
    """
    def __init__(self, error_type: str, message: str):
        super().__init__(message)
        self.error_type = error_type
        self.message = message

    def __str__(self):
        return f"[{self.error_type}] {self.message}"


class SigomeiAPI:
    """
    Interfaz de alto nivel para comunicarse con el servidor SIGOMEI.

    Todos los métodos retornan los datos deserializados (dicts o listas).
    En caso de error de negocio, lanzan SigomeiAPIError.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, timeout: float = 10.0):
        self._client = SigomeiClient(host=host, port=port, timeout=timeout)

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def esta_conectado(self) -> bool:
        """Retorna True si el servidor está accesible."""
        return self._client.ping()

    def set_server(self, host: str, port: int) -> None:
        """Cambia el host/puerto del servidor (útil desde la barra de conexión de la UI)."""
        self._client.host = host
        self._client.port = port

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _call(self, action: str, payload: dict = None) -> object:
        """Envía la petición y retorna `data`. Lanza SigomeiAPIError si hay error."""
        response = self._client.send(action, payload or {})
        if response.get("status") == "error":
            raise SigomeiAPIError(
                error_type=response.get("type", "Error"),
                message=response.get("message", "Error desconocido"),
            )
        return response.get("data")

    # ------------------------------------------------------------------
    # Equipos
    # ------------------------------------------------------------------

    def registrar_equipo(
        self,
        serie: str,
        marca: str = "",
        modelo: str = "",
        tipo: str = "",
        ubicacion: str = "",
        estado_operativo: str = "Disponible",
        criticidad: str = "Normal",
    ) -> dict:
        """
        Registra un nuevo equipo en el sistema.
        Retorna el equipo creado con su ID asignado.
        Lanza SigomeiAPIError si 'serie' está vacía (ValidationError).
        """
        return self._call("equipo.registrar", {
            "serie": serie,
            "marca": marca,
            "modelo": modelo,
            "tipo": tipo,
            "ubicacion": ubicacion,
            "estado_operativo": estado_operativo,
            "criticidad": criticidad,
        })

    def buscar_equipos(self, termino: str) -> list:
        """Busca equipos por término de texto (modelo, marca o tipo)."""
        return self._call("equipo.buscar", {"termino": termino})

    def actualizar_equipo(
        self,
        id: int,
        serie: str = "",
        marca: str = "",
        modelo: str = "",
        tipo: str = "",
        ubicacion: str = "",
        estado_operativo: str = "Disponible",
        criticidad: str = "Normal",
    ) -> dict:
        """Actualiza los datos de un equipo existente por su ID."""
        return self._call("equipo.actualizar", {
            "id": id,
            "serie": serie,
            "marca": marca,
            "modelo": modelo,
            "tipo": tipo,
            "ubicacion": ubicacion,
            "estado_operativo": estado_operativo,
            "criticidad": criticidad,
        })

    def eliminar_equipo(self, id: int) -> dict:
        """
        Elimina un equipo por su ID.
        Lanza SigomeiAPIError si el equipo tiene órdenes asociadas (BusinessRuleException).
        """
        return self._call("equipo.eliminar", {"id": id})

    def obtener_equipo(self, id: int) -> dict:
        """Obtiene un equipo por su ID. Retorna None si no existe."""
        return self._call("equipo.obtener", {"id": id})

    def listar_equipos(self) -> list:
        """Retorna la lista completa de equipos registrados."""
        return self._call("equipo.listar")

    # ------------------------------------------------------------------
    # Técnicos
    # ------------------------------------------------------------------

    def registrar_tecnico(
        self,
        nombre: str,
        especialidad: str = "",
        rfc: str = "",
        nivel_certificacion: str = "I",
        correo: str = "",
        estatus: str = "Activo",
    ) -> dict:
        """
        Registra un nuevo técnico en el sistema.
        Lanza SigomeiAPIError si el correo tiene formato inválido (ValidationError).
        """
        return self._call("tecnico.registrar", {
            "nombre": nombre,
            "especialidad": especialidad,
            "rfc": rfc,
            "nivel_certificacion": nivel_certificacion,
            "correo": correo,
            "estatus": estatus,
        })

    def actualizar_tecnico(
        self,
        id: int,
        nombre: str = "",
        especialidad: str = "",
        rfc: str = "",
        nivel_certificacion: str = "I",
        correo: str = "",
        estatus: str = "Activo",
    ) -> dict:
        """Actualiza los datos de un técnico existente por su ID."""
        return self._call("tecnico.actualizar", {
            "id": id,
            "nombre": nombre,
            "especialidad": especialidad,
            "rfc": rfc,
            "nivel_certificacion": nivel_certificacion,
            "correo": correo,
            "estatus": estatus,
        })

    def obtener_tecnico(self, id: int) -> dict:
        """Obtiene un técnico por su ID. Retorna None si no existe."""
        return self._call("tecnico.obtener", {"id": id})

    def eliminar_tecnico(self, id: int) -> dict:
        """Elimina un técnico por su ID."""
        return self._call("tecnico.eliminar", {"id": id})

    def listar_tecnicos(self) -> list:
        """Retorna la lista completa de técnicos registrados."""
        return self._call("tecnico.listar")

    # ------------------------------------------------------------------
    # Órdenes de mantenimiento
    # ------------------------------------------------------------------

    def crear_orden(
        self,
        equipo: dict,
        tecnico: dict,
        tipo_mantenimiento: str = "",
        fecha_programada: str = "",   # ISO format: "YYYY-MM-DD"
        costo_estimado: float = 0.0,
        observaciones: str = "",
    ) -> dict:
        """
        Crea una nueva orden de mantenimiento.
        Puede lanzar SigomeiAPIError por:
          - Especialidad no coincide con tipo de equipo (RN-01)
          - Colisión de fechas (RN-02)
          - Técnico inactivo (RN-03)
          - Equipo Alta Criticidad requiere Técnico II o III (RN-07)
        """
        return self._call("orden.crear", {
            "equipo": equipo,
            "tecnico": tecnico,
            "tipo_mantenimiento": tipo_mantenimiento,
            "fecha_programada": fecha_programada,
            "costo_estimado": costo_estimado,
            "observaciones": observaciones,
        })

    def cancelar_orden(self, id: int) -> dict:
        """
        Cancela una orden en estado Programada o En Ejecucion.
        Lanza SigomeiAPIError si la orden ya está Finalizada o Cancelada.
        """
        return self._call("orden.cancelar", {"id": id})

    def actualizar_estado_orden(self, id: int, nuevo_estado: str) -> dict:
        """
        Actualiza el estado de una orden.
        Lanza SigomeiAPIError si la fecha actual < fecha_programada (RN-05).
        """
        return self._call("orden.actualizar_estado", {
            "id": id,
            "nuevo_estado": nuevo_estado,
        })

    def realizar_reporte(self, id: int, costo_cierre: float, observaciones: str = "") -> dict:
        """
        Registra el cierre de una orden con su costo real y observaciones.
        Lanza SigomeiAPIError si la orden aún está en estado Programada (RN-06).
        """
        return self._call("orden.reporte", {
            "id": id,
            "costo_cierre": costo_cierre,
            "observaciones": observaciones,
        })

    def obtener_orden(self, id: int) -> dict:
        """Obtiene una orden por su ID. Retorna None si no existe."""
        return self._call("orden.obtener", {"id": id})
