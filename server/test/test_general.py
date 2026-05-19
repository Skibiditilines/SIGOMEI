import pytest
from server.src.controllers import OrdenController

# Simulaciones para las pruebas generales
def test_cp_24_crear_orden_servidor_desconectado():
    """
    CP-24: Comms (Neg) - Validar manejo de excepción si no hay DB.
    """
    # Arrange
    controller = OrdenController()
    controller.simular_desconexion_db()
    
    # Act / Assert
    with pytest.raises(Exception, match="Sin conexión al servidor"):
        # Al intentar cualquier operación debe capturar el error de conexión
        controller.crear_orden(None)

def test_cp_25_crear_orden_concurrencia():
    """
    CP-25: Concurr (Pos) - Simular 2 peticiones concurrentes.
    """
    # En TDD puro unitario para Python (sin servidor en vivo), 
    # la concurrencia a menudo se simula con threads o mocks de DB con bloqueos.
    # Dado que aún no hay código, esta prueba representará el cascarón de validación.
    
    # Arrange
    import threading
    controller = OrdenController()
    resultados = []

    def hilo_orden_1():
        resultados.append(controller.crear_orden_mock_concurrencia(datos="Orden A"))

    def hilo_orden_2():
        resultados.append(controller.crear_orden_mock_concurrencia(datos="Orden B"))

    t1 = threading.Thread(target=hilo_orden_1)
    t2 = threading.Thread(target=hilo_orden_2)

    # Act
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Assert
    assert len(resultados) == 2
    assert resultados[0] != resultados[1] # Deben registrarse con distintos IDs/datos
