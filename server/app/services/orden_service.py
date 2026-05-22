"""
services/orden_service.py
=========================
Lógica de negocio para la gestión de Órdenes de mantenimiento en SIGOMEI.
Corresponde a lo que los tests llaman 'OrdenController'.

Casos de prueba cubiertos:
  - CP-11: Crear orden exitosamente
  - CP-12 & RN-01: Especialidad no coincide con tipo de equipo
  - CP-13 & RN-02: Colisión de fechas para el mismo equipo
  - CP-14 & RN-03: Técnico asignado está inactivo
  - CP-15 & RN-08: Cancelar orden ya finalizada (prohibido)
  - CP-16: Transición válida Programada → En ejecucion
  - CP-17 & RN-06: Reporte solo aplica a En Ejecución/Finalizada
  - CP-18: Reporte en orden En Ejecucion → Finalizada
  - CP-19 & RN-07: Equipo Alta Criticidad requiere Técnico II o III
  - CP-20: Equipo Alta Criticidad con Técnico III (permitido)
  - CP-22: Cancelación UI no afecta backend (sin invocación del servicio)
  - CP-23 & RN-08: Cancelar orden Programada o En Ejecucion (permitido)
  - PU-RN05: No pasar a En ejecucion si fecha actual < fecha_programada
  - CP-24: Excepción si no hay conexión a DB (comms neg)
  - CP-25: Concurrencia / Sockets — dos peticiones simultáneas (ver nota)
"""

import threading
from datetime import datetime, date
from app.models.orden import Orden
from app.core.exceptions import BusinessRuleException, StateTransitionException


class OrdenController:
    """
    Servicio que gestiona el ciclo de vida de las Órdenes de mantenimiento.
    En la arquitectura FastAPI, este servicio es invocado desde las rutas (routes/).
    """

    def __init__(self):
        """Inicializar almacenamiento en memoria, contador de IDs y bandera de conexión."""
        self._db = {}  # Diccionario {id: Orden}
        self._id_counter = 0  # Contador para IDs incrementales
        self._db_conectada = True  # Bandera de conexión a BD
        self._lock = threading.Lock()  # Lock para thread-safety en concurrencia

    def crear_orden(self, orden: Orden) -> bool:
        """
        CP-11 (pos): Crear una orden de mantenimiento exitosamente.
          Asigna un ID único a la orden al persistirla.

        Validaciones de negocio que debe aplicar (en orden):
          - RN-01 / CP-12: La especialidad del técnico debe coincidir
            con el tipo del equipo. Si no → BusinessRuleException
            "Especialidad no coincide con tipo de equipo".
          - RN-02 / CP-13: No debe haber otra orden activa para el mismo
            equipo en la misma fecha_programada. Si hay → BusinessRuleException
            "Colisión de fechas".
          - RN-03 / CP-14: El técnico debe estar en estatus 'Activo'.
            Si no → BusinessRuleException "Técnico se encuentra inactivo".
          - RN-07 / CP-19: Si el equipo tiene criticidad 'Alta', el técnico
            debe tener nivel_certificacion 'II' o 'III'. Si no →
            BusinessRuleException "Equipo Alta Criticidad requiere Técnico II o III".
        """
        # Verificar conexión a BD
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        # RN-01: Especialidad del técnico debe coincidir con tipo de equipo
        if orden.tecnico.especialidad != orden.equipo.tipo:
            raise BusinessRuleException("Especialidad no coincide con tipo de equipo")
        
        # RN-02: No debe haber colisión de fechas (mismo equipo, misma fecha, estado != Cancelada)
        for ord in self._db.values():
            if (ord.equipo.id == orden.equipo.id and
                ord.fecha_programada == orden.fecha_programada and
                ord.estado != "Cancelada"):
                raise BusinessRuleException("Colisión de fechas")
        
        # RN-03: El técnico debe estar en estatus 'Activo'
        if orden.tecnico.estatus != "Activo":
            raise BusinessRuleException("Técnico se encuentra inactivo")
        
        # RN-07: Si equipo tiene criticidad 'Alta', técnico debe ser nivel II o III
        if orden.equipo.criticidad == "Alta":
            if orden.tecnico.nivel_certificacion not in ["II", "III"]:
                raise BusinessRuleException("Equipo Alta Criticidad requiere Técnico II o III")
        
        # Asignar ID incremental (thread-safe)
        with self._lock:
            self._id_counter += 1
            orden.id = self._id_counter
        
        # Guardar en BD en memoria
        self._db[orden.id] = orden
        return True

    def guardar_mock(self, orden: Orden) -> None:
        """
        Auxiliar de test: Persiste una orden directamente en el almacenamiento
        interno sin ejecutar validaciones de negocio.
        Usado en: CP-15, CP-16, CP-17, CP-18, CP-23, PU-RN05.
        """
        # Asignar ID si no lo tiene
        if orden.id is None:
            self._id_counter += 1
            orden.id = self._id_counter
        
        # Guardar en BD sin validar
        self._db[orden.id] = orden

    def cancelar_orden(self, orden_id) -> bool:
        """
        CP-23 & RN-08 (pos): Cancelar una orden en estado 'Programada'
          o 'En Ejecucion'. Cambia su estado a 'Cancelada'.
          Retorna True si la cancelación fue exitosa.
        CP-15 & RN-08 (neg): Lanzar StateTransitionException con mensaje
          "Transición de estado no permitida. Orden ya cerrada."
          si la orden ya está en estado 'Finalizada' o 'Cancelada'.
        """
        # Verificar conexión a BD
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        # Obtener la orden
        if orden_id not in self._db:
            return False
        
        orden = self._db[orden_id]
        
        # RN-08: No permitir cancelar si ya está en estado 'Finalizada' o 'Cancelada'
        if orden.estado in ["Finalizada", "Cancelada"]:
            raise StateTransitionException("Transición de estado no permitida. Orden ya cerrada.")
        
        # Cancelar la orden (permitido desde 'Programada' o 'En ejecucion')
        orden.estado = "Cancelada"
        self._db[orden_id] = orden
        return True

    def actualizar_estado(self, orden_id, nuevo_estado: str) -> bool:
        """
        CP-16 (pos): Transición válida de 'Programada' → 'En ejecucion'.
          Retorna True si el estado fue actualizado.
        PU-RN05 (neg): Lanzar BusinessRuleException con mensaje
          "La fecha actual es anterior a la fecha programada"
          si la fecha del sistema es anterior a la fecha_programada de la orden.
        """
        # Verificar conexión a BD
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        # Obtener la orden
        if orden_id not in self._db:
            return False
        
        orden = self._db[orden_id]
        
        # RN-05: Si transitando a 'En ejecucion', verificar que fecha actual >= fecha_programada
        if nuevo_estado == "En ejecucion":
            fecha_actual = datetime.now().date()
            if fecha_actual < orden.fecha_programada:
                raise BusinessRuleException("La fecha actual es anterior a la fecha programada")
        
        # Actualizar estado
        orden.estado = nuevo_estado
        self._db[orden_id] = orden
        return True

    def realizar_reporte(self, orden_id, costo_cierre: float, observaciones: str = "") -> bool:
        """
        CP-18 (pos): Registrar el costo real y observaciones al cerrar
          una orden 'En ejecucion'; transiciona su estado a 'Finalizada'.
          Retorna True si el reporte fue registrado exitosamente.
        CP-17 & PU-RN06 (neg): Lanzar BusinessRuleException con mensaje
          "El reporte y los costos reales solo aplican al finalizar"
          si la orden está en estado 'Programada'.
        """
        # Verificar conexión a BD
        if not self._db_conectada:
            raise Exception("Sin conexión al servidor")
        
        # Obtener la orden
        if orden_id not in self._db:
            return False
        
        orden = self._db[orden_id]
        
        # RN-06: No permitir reporte si estado es 'Programada'
        if orden.estado == "Programada":
            raise BusinessRuleException("El reporte y los costos reales solo aplican al finalizar")
        
        # Registrar costo real y observaciones
        orden.costo_real = costo_cierre
        orden.observaciones = observaciones
        orden.estado = "Finalizada"
        self._db[orden_id] = orden
        return True

    def obtener_orden(self, orden_id) -> Orden:
        """
        CP-18, CP-23: Obtener una orden por su ID.
          Retorna None si la orden no existe en el almacenamiento.
        """
        return self._db.get(orden_id, None)

    def simular_desconexion_db(self) -> None:
        """
        CP-24: Comms (Neg) — Simular pérdida de conexión con la base de datos.

        Después de llamar a este método, cualquier operación del servicio
        debe lanzar una Exception con el mensaje "Sin conexión al servidor".

        Contexto de Sockets/Comunicación:
          En un sistema con Sockets, este escenario representa que el servidor
          recibe la petición del cliente pero no puede alcanzar su fuente de
          datos (DB remota o servicio interno): equivalente a un
          ConnectionRefusedError o timeout en el socket de la DB.
        """
        self._db_conectada = False

    # =========================================================================
    # ⚡ CP-25: CONCURRENCIA / SOCKETS
    # =========================================================================
    def crear_orden_mock_concurrencia(self, datos: str):
        """
        CP-25: Concurr (Pos) — Simular petición concurrente de creación de orden.

        ¿QUÉ PRUEBA ESTE CASO?
          Que el servidor es capaz de atender DOS peticiones simultáneas
          (representadas por dos threads) y que cada una produce un resultado
          distinto e independiente, emulando el comportamiento de un servidor
          que acepta múltiples clientes por Socket al mismo tiempo.

          El test lanza t1 y t2 concurrentemente y verifica:
              assert len(resultados) == 2
              assert resultados[0] != resultados[1]

        ¿QUÉ HARÁ ESTA FUNCIÓN?
          1. Recibir `datos` (simula el payload enviado por el cliente).
          2. Generar un identificador único thread-safe (UUID o contador
             protegido con threading.Lock) para aislar cada "sesión".
          3. Crear internamente un registro de la orden con ese ID.
          4. Retornar un objeto/dict con al menos el ID único asignado,
             de forma que el test pueda confirmar que los dos resultados difieren.

        ⚠️  NOTA SOBRE SOCKETS:
          Los tests actuales NO abren un socket real (no hay socket.bind /
          socket.listen / socket.accept). La concurrencia se simula a nivel
          de threads de Python internos al proceso de test.

          Si en el futuro se integra un servidor TCP real
          (por ejemplo, socketserver.ThreadingTCPServer), esta función sería
          el handler invocado por cada conexión entrante de cliente, y el test
          debería:
            1. Levantar el servidor en un thread separado.
            2. Conectar dos sockets clientes simultáneamente.
            3. Enviar el payload y comparar las respuestas.
          Sin información suficiente sobre el protocolo de Sockets planeado
          para SIGOMEI, se deja como cascarón hasta obtener la especificación.
        """
        # Generar ID único thread-safe
        with self._lock:
            self._id_counter += 1
            nuevo_id = self._id_counter
        
        # Retornar dict con ID y datos
        return {'id': nuevo_id, 'datos': datos}
