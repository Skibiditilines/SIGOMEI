"""
ui/client/socket_client.py
===========================
Cliente TCP de bajo nivel para comunicarse con el servidor SIGOMEI.

Gestiona el ciclo de vida de la conexión y la serialización/deserialización
de mensajes JSON.  Cada llamada a `send()` abre una nueva conexión TCP,
envía el mensaje y devuelve la respuesta (conexión efímera / request-response).

Uso típico desde SigomeiAPI:
    client = SigomeiClient(host="127.0.0.1", port=9000)
    response = client.send("equipo.registrar", {"serie": "SN-001", ...})
    if response["status"] == "ok":
        equipo = response["data"]

Razón del modelo de conexión efímera:
    Simplifica la gestión de estado en la UI: no se necesita
    mantener un socket abierto ni manejar reconexiones automáticas.
    El overhead de TCP handshake es despreciable en LAN.
"""

import json
import socket
import logging
from typing import Any

logger = logging.getLogger("sigomei.client")

ENCODING = "utf-8"
BUFFER_SIZE = 65536  # 64 KiB — suficiente para listas grandes


class ConnectionError(Exception):
    """El cliente no pudo conectar al servidor SIGOMEI."""
    pass


class TimeoutError(Exception):
    """El servidor no respondió en el tiempo límite."""
    pass


class SigomeiClient:
    """
    Cliente TCP para el servidor SIGOMEI.

    Parámetros:
        host    -- Dirección IP o hostname del servidor (default: "127.0.0.1")
        port    -- Puerto TCP del servidor (default: 9000)
        timeout -- Segundos de espera por respuesta (default: 10)
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5000, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, action: str, payload: dict = None) -> dict:
        """
        Envía una petición al servidor y retorna la respuesta.

        Args:
            action  -- Identificador de la operación, e.g. "equipo.registrar"
            payload -- Diccionario con los datos de la petición (opcional)

        Returns:
            Diccionario con al menos {"status": "ok"|"error", ...}

        Raises:
            ConnectionError -- No se pudo conectar al servidor
            TimeoutError    -- El servidor no respondió a tiempo
        """
        if payload is None:
            payload = {}

        message = {"action": action, "payload": payload}
        raw_out = json.dumps(message, ensure_ascii=False) + "\n"

        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                logger.debug("[SEND] %s → %s", action, payload)
                sock.sendall(raw_out.encode(ENCODING))

                # Leer respuesta (puede venir en múltiples chunks)
                raw_in = b""
                while True:
                    chunk = sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    raw_in += chunk
                    if b"\n" in raw_in:
                        break

                response = json.loads(raw_in.decode(ENCODING).strip())
                logger.debug("[RECV] %s ← %s", action, response.get("status"))
                return response

        except socket.timeout as exc:
            raise TimeoutError(
                f"El servidor {self.host}:{self.port} no respondió en {self.timeout}s"
            ) from exc
        except (ConnectionRefusedError, OSError) as exc:
            raise ConnectionError(
                f"No se pudo conectar al servidor {self.host}:{self.port} — {exc}"
            ) from exc

    def ping(self) -> bool:
        """
        Verifica si el servidor está activo.
        Retorna True si la conexión TCP puede establecerse, False en caso contrario.
        """
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout):
                return True
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"SigomeiClient(host={self.host!r}, port={self.port})"
