import pytest
from server.src.models import Tecnico
from server.src.controllers import TecnicoController
from server.src.exceptions import ValidationError

@pytest.fixture
def tecnico_controller():
    return TecnicoController()

def test_cp_06_registrar_tecnico_exito(tecnico_controller):
    """
    CP-06: RF-CRUD-Tec (Pos)
    """
    # Arrange
    tecnico = Tecnico(
        nombre="Juan Perez",
        especialidad="Mecanico",
        rfc="JUPE900101XYZ",
        nivel_certificacion="II",
        correo="juan.perez@empresa.com"
    )
    
    # Act
    resultado = tecnico_controller.registrar_tecnico(tecnico)
    
    # Assert
    assert resultado is True
    assert tecnico.id is not None

def test_cp_07_registrar_tecnico_correo_invalido(tecnico_controller):
    """
    CP-07: RF-CRUD-Tec (Neg) - Correo sin formato.
    """
    # Arrange
    tecnico = Tecnico(
        nombre="Maria Mercado",
        correo="mamercadouvmx" # Sin @
    )
    
    # Act / Assert
    with pytest.raises(ValidationError, match="Formato de correo incorrecto"):
        tecnico_controller.registrar_tecnico(tecnico)

def test_cp_08_editar_tecnico_especialidad(tecnico_controller):
    """
    CP-08: RF-CRUD-Tec (Pos)
    """
    # Arrange
    tecnico = Tecnico(nombre="Magdiel Omar", especialidad="Mecanico")
    tecnico_controller.registrar_tecnico(tecnico)
    
    # Act
    tecnico.especialidad = "Hidraulico"
    resultado = tecnico_controller.actualizar_tecnico(tecnico)
    
    # Assert
    assert resultado is True
    tec_bd = tecnico_controller.obtener_tecnico(tecnico.id)
    assert tec_bd.especialidad == "Hidraulico"

def test_cp_09_eliminar_tecnico_sin_ordenes(tecnico_controller):
    """
    CP-09: RF-CRUD-Tec (Pos)
    """
    # Arrange
    tecnico = Tecnico(nombre="Magdiel Mercado", estatus="Activo")
    tecnico_controller.registrar_tecnico(tecnico)
    
    # Act
    resultado = tecnico_controller.eliminar_tecnico(tecnico.id)
    
    # Assert
    assert resultado is True
    assert tecnico_controller.obtener_tecnico(tecnico.id) is None

def test_cp_10_editar_estatus_inactivo(tecnico_controller):
    """
    CP-10: RF-CRUD-Tec (Pos)
    """
    # Arrange
    tecnico = Tecnico(nombre="Tecnico Activo", estatus="Activo")
    tecnico_controller.registrar_tecnico(tecnico)
    
    # Act
    tecnico.estatus = "Inactivo"
    tecnico_controller.actualizar_tecnico(tecnico)
    
    # Assert
    tec_bd = tecnico_controller.obtener_tecnico(tecnico.id)
    assert tec_bd.estatus == "Inactivo"
