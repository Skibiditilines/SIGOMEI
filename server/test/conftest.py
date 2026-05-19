"""
conftest.py — Configuración de pytest para server/test/
=========================================================
Agrega 'server/' al sys.path para que los tests puedan resolver
'from app.xxx import ...' sin necesidad de instalar el paquete.
"""
import sys
import os

# Añade el directorio server/ al path de Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
