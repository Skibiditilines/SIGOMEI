# server/app/services/__init__.py
from app.services.equipo_service import EquipoController
from app.services.tecnico_service import TecnicoController
from app.services.orden_service import OrdenController

__all__ = ["EquipoController", "TecnicoController", "OrdenController"]
