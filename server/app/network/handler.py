"""
server/app/network/handler.py
==============================
RequestHandler del servidor TCP SIGOMEI.

Cada conexión entrante de un cliente es atendida por una instancia
de SigomeiHandler en su propio hilo (ThreadingTCPServer).

Protocolo:
  - El cliente envía UN mensaje JSON terminado con '\\n'.
  - El servidor responde con UN mensaje JSON terminado con '\\n' y cierra.

Formato de petición:
  {"action": "<modulo>.<operacion>", "payload": { ... }}

Formato de respuesta (éxito):
  {"status": "ok", "data": { ... }}

Formato de respuesta (error):
  {"status": "error", "type": "<NombreExcepcion>", "message": "<detalle>"}

tag: 1.0.0
"""

import json
import logging
from socketserver import BaseRequestHandler
from app.network.dispatcher import Dispatcher

logger = logging.getLogger("sigomei.handler")

# Dispatcher compartido entre todos los hilos (thread-safe gracias a los Locks
# internos de cada controlador)
_dispatcher = Dispatcher()


class SigomeiHandler(BaseRequestHandler):
    """
    Maneja una conexión TCP entrante de un cliente SIGOMEI.

    Ciclo de vida por conexión:
      1. receive()  → leer línea JSON del socket
      2. dispatch() → delegar al Dispatcher
      3. send()     → escribir respuesta JSON al socket
    """

    BUFFER_SIZE = 4096
    ENCODING = "utf-8"

    def handle(self):
        """Punto de entrada invocado por ThreadingTCPServer para cada cliente."""
        client_addr = self.client_address
        logger.info("[CONN] Cliente conectado: %s:%d", *client_addr)

        try:
            raw = self._receive_line()
            if not raw:
                self._send_error("ProtocolError", "Mensaje vacío recibido")
                return

            try:
                message = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.warning("[PARSE] JSON inválido de %s: %s", client_addr, exc)
                self._send_error("ProtocolError", f"JSON inválido: {exc}")
                return

            action = message.get("action", "")
            payload = message.get("payload", {})

            logger.debug("[REQ] %s → acción='%s' payload=%s", client_addr, action, payload)

            response = _dispatcher.dispatch(action, payload)
            self._send_json(response)

        except ConnectionResetError:
            logger.warning("[CONN] Conexión reseteada por %s", client_addr)
        except Exception as exc:
            logger.exception("[ERROR] Excepción no controlada con %s: %s", client_addr, exc)
            self._send_error("InternalServerError", str(exc))
        finally:
            logger.info("[CONN] Conexión cerrada: %s:%d", *client_addr)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _receive_line(self) -> str:
        """
        Lee bytes del socket hasta encontrar '\\n' o agotar el buffer.
        Retorna el string decodificado sin el '\\n'.
        """
        data = b""
        while True:
            chunk = self.request.recv(self.BUFFER_SIZE)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        return data.decode(self.ENCODING).strip()

    def _send_json(self, obj: dict) -> None:
        """Serializa `obj` como JSON y lo envía al cliente con '\\n' al final."""
        raw = json.dumps(obj, ensure_ascii=False) + "\n"
        self.request.sendall(raw.encode(self.ENCODING))

    def _send_error(self, error_type: str, message: str) -> None:
        """Envía una respuesta de error estándar."""
        self._send_json({
            "status": "error",
            "type": error_type,
            "message": message
        })
