import pytest
# Estas importaciones fallarán en este momento porque no se ha escrito el código (TDD - Fase Roja)
from app.models import Equipo
from app.services import EquipoController
from app.core import BusinessRuleException, ValidationError

@pytest.fixture
def equipo_controller():
    return EquipoController()

def test_cp_01_registrar_equipo_exito(equipo_controller):
    """
    CP-01: RF-CRUD-Eq (Pos) - Registrar equipo con éxito.
    """
    # Arrange (Given)
    nuevo_equipo = Equipo(
        serie="X1", 
        marca="Goulds", 
        modelo="T1", 
        tipo="Mecanico", 
        ubicacion="Planta 1"
    )
    
    # Act (When)
    resultado = equipo_controller.registrar_equipo(nuevo_equipo)
    
    # Assert (Then)
    assert resultado is True
    assert nuevo_equipo.id is not None # Se le debió asignar un ID al guardar

def test_cp_02_registrar_equipo_campo_vacio(equipo_controller):
    """
    CP-02: RF-CRUD-Eq (Neg) - Validar campos vacíos.
    """
    # Arrange
    equipo_incompleto = Equipo(
        serie="", # Vacío
        marca="Goulds", 
        modelo="T1", 
        tipo="Mecanico"
    )
    
    # Act / Assert
    with pytest.raises(ValidationError, match="Campo requerido: serie"):
        equipo_controller.registrar_equipo(equipo_incompleto)

def test_cp_03_buscar_equipo(equipo_controller):
    """
    CP-03: RF-CRUD-Eq (Pos) - Búsqueda de equipos.
    """
    # Arrange
    equipo_controller.registrar_equipo(Equipo(serie="X1", marca="Goulds", modelo="Taladro", tipo="Mecanico"))
    
    # Act
    resultados = equipo_controller.buscar_equipos(termino="Taladro")
    
    # Assert
    assert len(resultados) > 0
    assert "Taladro" in resultados[0].modelo

def test_cp_04_editar_estado_operativo(equipo_controller):
    """
    CP-04: RF-CRUD-Eq (Pos) - Editar estado de un equipo.
    """
    # Arrange
    equipo = Equipo(serie="X2", modelo="Taladro 2005", estado_operativo="Disponible")
    equipo_controller.registrar_equipo(equipo)
    
    # Act
    equipo.estado_operativo = "En Mantenimiento"
    resultado = equipo_controller.actualizar_equipo(equipo)
    
    # Assert
    assert resultado is True
    equipo_actualizado = equipo_controller.obtener_equipo(equipo.id)
    assert equipo_actualizado.estado_operativo == "En Mantenimiento"

def test_cp_05_y_pu_rn04_eliminar_equipo_con_ordenes(equipo_controller):
    """
    CP-05 & PU-RN04: RN-04 (Neg) - No se puede eliminar equipo con órdenes asociadas.
    """
    # Arrange
    equipo = Equipo(serie="X3", modelo="Taladro 2005")
    equipo_controller.registrar_equipo(equipo)
    # Simulamos que internamente el mock de BD o el controlador le asocia una orden
    equipo_controller.asociar_orden_falsa_para_test(equipo.id) 
    
    # Act / Assert
    with pytest.raises(BusinessRuleException, match="No se puede eliminar equipo con órdenes asociadas"):
        equipo_controller.eliminar_equipo(equipo.id)

def test_cp_21_cancelar_registro_equipo(equipo_controller):
    """
    CP-21: UI (Neg) - Cancelar el registro (A nivel controlador, no se invoca guardado).
    """
    # Arrange
    cantidad_inicial = len(equipo_controller.obtener_todos())
    
    # Act
    # El usuario presiona "Cancelar" en la UI, por lo que nunca se llama a registrar_equipo
    pass 
    
    # Assert
    cantidad_final = len(equipo_controller.obtener_todos())
    assert cantidad_inicial == cantidad_final
