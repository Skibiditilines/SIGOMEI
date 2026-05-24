# Proyecto SIGOMEI

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

## **Requisitos de software**

* Python \=\< 3.11.9  
* Listado de dependencias dentro del proyecto:  
  * customtkinter (Intefaz Grafica)  
  * pytest (Pruebas unitarias)  
  * sockets tcp (Conexión de sockets)

## Interfaz Grafica

### Estructura

```
ui/
│
├── app/
│   ├── main.py
│   │
│   ├── views/               # Ventanas/pantallas
│   │   ├── home_view.py
│   │   └── settings_view.py
│   │
│   ├── components/          # Widgets reutilizables
│   │   └── sidebar.py
│   │
│   ├── controllers/         # Lógica/interacción
│   │   └── home_controller.py
│   │
│   ├── services/            # Datos/APIs/archivos
│   │   └── api_service.py
│   │
│   ├── utils/
│   │   └── helpers.py
│   │
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   │
│   └── config/
│       └── settings.py
│
└── requirements.txt
```

### Ejecución

```bash

```

### Pruebas

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest tests/
```
## Servidor

### Estructura

```
project/
│
├── app/
│   ├── main.py              # Punto de entrada
│   │
│   ├── core/                # Configuración global
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   │
│   ├── models/              # Modelos ORM
│   │   └── user.py
│   │
│   ├── schemas/             # Pydantic schemas
│   │   └── user.py
│   │
│   ├── routes/              # Endpoints
│   │   └── user.py
│   │
│   ├── services/            # Lógica de negocio
│   │   └── user_service.py
│   │
│   ├── dependencies/        # Depends()
│   │   └── auth.py
│   │
│   └── utils/               # Helpers/utilidades
│
├── tests/
│   └── test_user.py
│
├── requirements.txt
└── .env
```

### Ejecución

```bash

```
