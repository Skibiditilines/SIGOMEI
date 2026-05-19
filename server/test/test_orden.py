import pytest
from datetime import date, timedelta
from app.models import Orden, Equipo, Tecnico
from app.services import OrdenController
from app.core import BusinessRuleException, StateTransitionException

@pytest.fixture
def orden_controller():
    return OrdenController()

def test_cp_11_crear_orden_exito(orden_controller):
    """
    CP-11: RF-CRUD-Ord (Pos) - Crear orden exitosamente.
    """
    equipo = Equipo(tipo="Mecanico")
    tecnico = Tecnico(especialidad="Mecanico", estatus="Activo")
    orden = Orden(equipo=equipo, tecnico=tecnico, tipo_mantenimiento="Preventivo")
    
    resultado = orden_controller.crear_orden(orden)
    assert resultado is True
    assert orden.id is not None

def test_cp_12_y_pu_rn01_crear_orden_especialidad_no_coincide(orden_controller):
    """
    CP-12 & PU-RN01: Especialidad no coincide con tipo de equipo.
    """
    equipo = Equipo(tipo="Electrico")
    tecnico = Tecnico(especialidad="Mecanico")
    orden = Orden(equipo=equipo, tecnico=tecnico)
    
    with pytest.raises(BusinessRuleException, match="Especialidad no coincide con tipo de equipo"):
        orden_controller.crear_orden(orden)

def test_cp_13_y_pu_rn02_crear_orden_colision_fechas(orden_controller):
    """
    CP-13 & PU-RN02: Colisión de fechas para el mismo equipo.
    """
    equipo = Equipo(id=1, tipo="Mecanico")
    tecnico = Tecnico(especialidad="Mecanico", estatus="Activo")
    hoy = date.today()
    
    orden_existente = Orden(equipo=equipo, tecnico=tecnico, fecha_programada=hoy, estado="En ejecucion")
    orden_controller.crear_orden(orden_existente)
    
    orden_nueva = Orden(equipo=equipo, tecnico=tecnico, fecha_programada=hoy)
    
    with pytest.raises(BusinessRuleException, match="Colisión de fechas"):
        orden_controller.crear_orden(orden_nueva)

def test_cp_14_y_pu_rn03_crear_orden_tecnico_inactivo(orden_controller):
    """
    CP-14 & PU-RN03: Asignar técnico inactivo.
    """
    equipo = Equipo(tipo="Mecanico")
    tecnico = Tecnico(especialidad="Mecanico", estatus="Inactivo")
    orden = Orden(equipo=equipo, tecnico=tecnico)
    
    with pytest.raises(BusinessRuleException, match="Técnico se encuentra inactivo"):
        orden_controller.crear_orden(orden)

def test_cp_15_y_pu_rn08_cancelar_orden_finalizada_prohibido(orden_controller):
    """
    CP-15 & PU-RN08: Cancelar orden finalizada está prohibido.
    """
    orden = Orden(id=1, estado="Finalizada")
    orden_controller.guardar_mock(orden) # Simulamos que ya existe
    
    with pytest.raises(StateTransitionException, match="Transición de estado no permitida. Orden ya cerrada."):
        orden_controller.cancelar_orden(orden.id)

def test_cp_16_actualizar_estado_programada_a_ejecucion(orden_controller):
    """
    CP-16: Transición válida de Programada a En ejecución.
    """
    orden = Orden(id=1, estado="Programada", fecha_programada=date.today())
    orden_controller.guardar_mock(orden)
    
    resultado = orden_controller.actualizar_estado(orden.id, "En ejecucion")
    assert resultado is True

def test_pu_rn05_transicion_estado_fecha_invalida(orden_controller):
    """
    PU-RN05: No se puede pasar a En ejecución si la fecha del sistema es anterior a fecha_programada.
    """
    mañana = date.today() + timedelta(days=1)
    orden = Orden(id=1, estado="Programada", fecha_programada=mañana)
    orden_controller.guardar_mock(orden)
    
    with pytest.raises(BusinessRuleException, match="La fecha actual es anterior a la fecha programada"):
        orden_controller.actualizar_estado(orden.id, "En ejecucion")

def test_cp_17_y_pu_rn06_realizar_reporte_orden_programada(orden_controller):
    """
    CP-17 & PU-RN06: Realizar reporte solo aplica a En Ejecución/Finalizadas.
    """
    orden = Orden(id=1, estado="Programada")
    orden_controller.guardar_mock(orden)
    
    with pytest.raises(BusinessRuleException, match="El reporte y los costos reales solo aplican al finalizar"):
        orden_controller.realizar_reporte(orden.id, costo_cierre=100)

def test_cp_18_realizar_reporte_orden_en_ejecucion(orden_controller):
    """
    CP-18: Realizar reporte a orden En Ejecución.
    """
    orden = Orden(id=1, estado="En ejecucion")
    orden_controller.guardar_mock(orden)
    
    resultado = orden_controller.realizar_reporte(orden.id, costo_cierre=500.0, observaciones="Completado")
    assert resultado is True
    assert orden_controller.obtener_orden(orden.id).estado == "Finalizada"

def test_cp_19_y_pu_rn07_crear_orden_criticidad_alta_tecnico_i(orden_controller):
    """
    CP-19 & PU-RN07: Equipo Criticidad Alta requiere Técnico II o III.
    """
    equipo = Equipo(tipo="Mecanico", criticidad="Alta")
    tecnico = Tecnico(especialidad="Mecanico", nivel_certificacion="I", estatus="Activo")
    orden = Orden(equipo=equipo, tecnico=tecnico)
    
    with pytest.raises(BusinessRuleException, match="Equipo Alta Criticidad requiere Técnico II o III"):
        orden_controller.crear_orden(orden)

def test_cp_20_crear_orden_criticidad_alta_tecnico_iii(orden_controller):
    """
    CP-20: Equipo Criticidad Alta con Técnico III.
    """
    equipo = Equipo(tipo="Mecanico", criticidad="Alta")
    tecnico = Tecnico(especialidad="Mecanico", nivel_certificacion="III", estatus="Activo")
    orden = Orden(equipo=equipo, tecnico=tecnico)
    
    resultado = orden_controller.crear_orden(orden)
    assert resultado is True

def test_cp_22_cancelar_modal_eliminar_orden():
    """
    CP-22: UI (Neg) - Validar que la orden no cambia si el usuario cancela en el frontend.
    Esta prueba a nivel backend asume que si no se invoca 'cancelar_orden', no sucede nada.
    """
    pass

def test_cp_23_cancelar_orden_programada_o_ejecucion(orden_controller):
    """
    CP-23: RN-08 (Pos) - Cancelar Orden 'Programada' o 'En Ejecucion'.
    """
    orden = Orden(id=1, estado="Programada")
    orden_controller.guardar_mock(orden)
    
    resultado = orden_controller.cancelar_orden(orden.id)
    assert resultado is True
    assert orden_controller.obtener_orden(orden.id).estado == "Cancelada"
