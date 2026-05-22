# Proyecto SIGOMEI

## Tecnologias

- Python
    - Fastapi (Servidor)
    - Pytest (Pruebas unitarias)
    - Selenium (Pruebas de interfaz)
    - CustomTkinter (Interfaz Grafica)
- MySQL

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
