# SIP-Backend

Backend para la aplicación Sport Match, un sistema de gestión de partidos deportivos.

## Descripción

Este proyecto es el backend de la aplicación Sport Match, desarrollado para gestionar partidos deportivos, usuarios, instalaciones y reservas.

## Tecnologías Utilizadas

- Node.js
- Express.js
- MongoDB
- TypeScript
- JWT para autenticación
- Docker

## Requisitos Previos

- Node.js (v18 o superior)
- MongoDB
- npm o yarn

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/JBE10/SIP-Backend.git
cd SIP-Backend
```

2. Instalar dependencias:
```bash
npm install
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
```
Editar el archivo `.env` con tus configuraciones.

4. Iniciar el servidor:
```bash
npm run dev
```

## Estructura del Proyecto

```
src/
├── config/         # Configuraciones
├── controllers/    # Controladores
├── models/        # Modelos de datos
├── routes/        # Rutas de la API
├── services/      # Servicios
├── types/         # Tipos TypeScript
└── utils/         # Utilidades
```

## API Endpoints

### Autenticación
- POST /api/auth/register - Registro de usuarios
- POST /api/auth/login - Inicio de sesión

### Usuarios
- GET /api/users - Obtener usuarios
- GET /api/users/:id - Obtener usuario por ID
- PUT /api/users/:id - Actualizar usuario
- DELETE /api/users/:id - Eliminar usuario

### Instalaciones
- GET /api/facilities - Obtener instalaciones
- POST /api/facilities - Crear instalación
- GET /api/facilities/:id - Obtener instalación por ID
- PUT /api/facilities/:id - Actualizar instalación
- DELETE /api/facilities/:id - Eliminar instalación

### Partidos
- GET /api/matches - Obtener partidos
- POST /api/matches - Crear partido
- GET /api/matches/:id - Obtener partido por ID
- PUT /api/matches/:id - Actualizar partido
- DELETE /api/matches/:id - Eliminar partido

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Juan Bautista Espino - [@JBE10](https://github.com/JBE10)

Link del proyecto: [https://github.com/JBE10/SIP-Backend](https://github.com/JBE10/SIP-Backend)
