# SportMatch Backend

Backend de la aplicación SportMatch construido con FastAPI.

## Requisitos

- Python 3.8+
- PostgreSQL (local o en Railway)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/JBE10/SIP-Backend.git
cd SIP-Backend
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## Desarrollo

Para ejecutar el servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

## Documentación

La documentación de la API está disponible en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Despliegue

El proyecto está configurado para desplegarse en Railway. El archivo `Procfile` contiene la configuración necesaria para el despliegue.

## Estructura del Proyecto

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   └── static/
│       └── uploads/
├── requirements.txt
├── Procfile
└── .env.example
```

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contacto

Juan Bautista Espino - [@JBE10](https://github.com/JBE10)

Link del proyecto: [https://github.com/JBE10/SIP-Backend](https://github.com/JBE10/SIP-Backend)
