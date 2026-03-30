# FastAPI + SQLAlchemy + PostgreSQL + Docker

Proyecto base para una API REST usando FastAPI, SQLAlchemy y PostgreSQL en contenedores Docker.

## Estructura

```text
.
├── app
│   ├── api/v1/endpoints/users.py
│   ├── core/config.py
│   ├── crud/user.py
│   ├── db/base.py
│   ├── db/session.py
│   ├── models/user.py
│   ├── schemas/user.py
│   └── main.py
├── .env
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Levantar el proyecto

1. Construir y levantar contenedores:

```bash
docker compose up --build
```

2. Abrir documentación interactiva:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints base

- GET `/health`
- GET `/api/v1/users`
- POST `/api/v1/users`

### Ejemplo de creación de usuario

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","full_name":"Test User"}'
```

## Configuración

La configuración principal se maneja vía variables de entorno en `.env`.

Variables importantes:

- `DATABASE_URL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

## Desarrollo local (sin Docker)

1. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

2. Ejecutar API:

```bash
uvicorn app.main:app --reload
```
