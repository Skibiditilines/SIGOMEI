"""
server/server_tcp.py
====================
Punto de entrada del servidor TCP SIGOMEI.

Uso:
    cd server/
    python server_tcp.py [--host HOST] [--port PORT]

Defaults:
    HOST = 0.0.0.0   (acepta conexiones en todas las interfaces)
    PORT = 5000

El servidor usa ThreadingTCPServer para atender múltiples clientes
de forma concurrente, cada uno en su propio hilo de SO.
"""

import argparse
import logging
import sys
import os
import socketserver

# Asegurar que 'server/' esté en sys.path para resolver los imports de 'app.*'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.network.handler import SigomeiHandler

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sigomei.server")

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000


class SigomeiTCPServer(socketserver.ThreadingTCPServer):
    """
    Servidor TCP con soporte de hilos para SIGOMEI.

    allow_reuse_address = True  → evita el error "Address already in use"
                                  si el servidor se reinicia rápidamente.
    daemon_threads = True       → los hilos cliente mueren cuando el proceso
                                  principal termina (Ctrl+C limpio).
    """
    allow_reuse_address = True
    daemon_threads = True


def parse_args():
    parser = argparse.ArgumentParser(description="Servidor TCP SIGOMEI")
    parser.add_argument(
        "--host", default=DEFAULT_HOST,
        help=f"Interfaz de escucha (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"Puerto de escucha (default: {DEFAULT_PORT})"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    host, port = args.host, args.port

    try:
        with SigomeiTCPServer((host, port), SigomeiHandler) as server:
            logger.info("=" * 55)
            logger.info("  SIGOMEI — Servidor TCP iniciado")
            logger.info("  Escuchando en  %s:%d", host, port)
            logger.info("  Protocolo      JSON/TCP (newline-delimited)")
            logger.info("  Modelo         ThreadingTCPServer (un hilo/cliente)")
            logger.info("  Presiona Ctrl+C para detener")
            logger.info("=" * 55)
            server.serve_forever()

    except OSError as exc:
        logger.error("No se pudo iniciar el servidor: %s", exc)
        logger.error("¿Ya hay otro proceso usando el puerto %d?", port)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nServidor detenido por el usuario.")
        sys.exit(0)


if __name__ == "__main__":
    main()
