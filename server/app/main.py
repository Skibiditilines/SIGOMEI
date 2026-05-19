"""
app/main.py — Punto de entrada del servidor SIGOMEI
=====================================================
Aquí se inicializará la aplicación FastAPI y se registrarán
las rutas (routes/) cuando estén implementadas.

Por ahora expone los imports necesarios para que los tests
en server/test/ puedan resolver sus dependencias a través de
los módulos src (alias de compatibilidad) definidos abajo.
"""

# Importaciones de dominio disponibles para el resto de la aplicación
from app.models import Equipo, Tecnico, Orden
from app.services import EquipoController, TecnicoController, OrdenController
from app.core import BusinessRuleException, ValidationError, StateTransitionException

# TODO: Inicializar FastAPI y registrar routers cuando se implementen las rutas
# from fastapi import FastAPI
# from app.routes import equipo_router, tecnico_router, orden_router
#
# app = FastAPI(title="SIGOMEI API")
# app.include_router(equipo_router)
# app.include_router(tecnico_router)
# app.include_router(orden_router)
