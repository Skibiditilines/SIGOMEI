# **1\. Manual Tecnico**

## **Instalación**

1. Clonar el repositorio de github desde una terminal: `git clone https://github.com/Skibiditilines/SIGOMEI.git`

## **Configuración**

1. Crear entorno virtual en terminal desde la carpeta de proyecto: `python -m venv venv`  
2. Activar el entorno virtual: `.\venv\Scripts\activate`  
3. Instalar dependencias dentro del entorno:  
   1. `pip install -r server\requirements.txt`  
   2. `pip install -r ui\requirements.txt`

## **Ejecución del servidor:**

Desde una terminal independiente dentro de la carpeta de proyecto “SIGOMEI” y con el entorno virtual activado se debe ejecutar lo siguiente:

1. Acceder a la carpeta servidor: `cd server`  
2. Ejecutar servidor: `python server_tcp.py` 

## **Ejecución del cliente:**

Desde una terminal independiente aparte de la terminal de servidor ya activa e igualmente en la carpeta de proyecto “SIGOMEI” con el entorno virtual activado se ejecuta con los siguiente

1. Acceder a la carpeta de interfaz gráfica / cliente: `cd ui`  
2. Ejecutar la interfaz gráfica: `python main.py`

Si se quiere conectar un cliente o prender un servidor dentro de la misma red, se utiliza: `python [main.py o server_tcp.py] --host [ip del server] --port 5000`

## **Requisitos de software**

* Python \=\< 3.11.9  
  * customtkinter (Intefaz Grafica)  
  * pytest (Pruebas unitarias)  
  * sockets tcp (Conexión de sockets)