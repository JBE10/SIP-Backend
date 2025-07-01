# Configuración de Entornos - SportMatch Backend

## Desarrollo Local

### 1. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```env
# Desarrollo local
BASE_URL=http://localhost:8000
DATABASE_URL=postgresql://postgres:bRGGofTE...
SECRET_KEY=tu_secret_key_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Frontend
El frontend automáticamente detectará que está en desarrollo y usará:
- `http://localhost:8000` para las APIs

## Producción (Railway)

### 1. Variables de Entorno en Railway
Configura estas variables en tu proyecto de Railway:

```env
BASE_URL=https://web-production-07ed64.up.railway.app
DATABASE_URL=postgresql://postgres:bRGGofTE...
SECRET_KEY=tu_secret_key_seguro_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Frontend
El frontend automáticamente detectará que está en producción y usará:
- `https://web-production-07ed64.up.railway.app` para las APIs

## Cómo Funciona

### Backend
- Lee `BASE_URL` de las variables de entorno
- Si no está definida, usa `http://localhost:8000` por defecto
- Genera URLs de archivos usando esta base URL

### Frontend
- Detecta automáticamente el entorno (`NODE_ENV`)
- En desarrollo: usa `localhost:8000`
- En producción: usa `https://web-production-07ed64.up.railway.app`
- Se puede sobrescribir con `NEXT_PUBLIC_API_URL`

## Verificación

### Desarrollo
```bash
# Backend
curl http://localhost:8000/health

# Frontend
# Las peticiones van a localhost:8000
```

### Producción
```bash
# Backend
curl https://web-production-07ed64.up.railway.app/health

# Frontend
# Las peticiones van a Railway
``` 