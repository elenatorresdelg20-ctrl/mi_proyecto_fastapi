# my-awesome-api

Proyecto FastAPI reorganizado en paquetes para facilitar mantenimiento y pruebas.

## Estructura principal

La raíz del proyecto contiene un subdirectorio `[A FastAPI project]` que contiene el paquete `app/`.

Principales carpetas dentro de `[A FastAPI project]/app`:

- `app/main.py` - Punto de arranque y registro de routers.
- `app/core/` - Configuración y helpers de bajo nivel: `db.py`, `settings.py`, `security.py`.
- `app/models/` - Modelos SQLAlchemy en `models.py`.
- `app/schemas/` - Schemas Pydantic para las respuestas y peticiones.
- `app/services/` - Lógica de negocio y clientes externos (`ai_client.py`, `sales.py`).
- `app/utils/` - Helpers reutilizables (normalización, parsing, prompt builder).
- `app/routers/` - Routers por funcionalidad (`upload.py`, `explain.py`, `status.py`).

## Comandos de desarrollo

Activar el entorno virtual (desde la raíz del proyecto):
```bash
source /Users/elena/mi_proyecto_fastapi/venv/bin/activate
```

Ejecutar la aplicación (desde la carpeta raíz del repo):
```bash
PYTHONPATH="$(pwd)/[A FastAPI project]" uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Alternativamente, cambiar al subdirectorio y ejecutar directamente:
```bash
cd "[A FastAPI project]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Ejecutar tests:
```bash
PYTHONPATH="$(pwd)/[A FastAPI project]" pytest -q
```

Instalar dependencias en el `venv`:
```bash
/Users/elena/mi_proyecto_fastapi/venv/bin/pip install -r requirements.txt
# paquetes adicionales instalados durante refactor:
/Users/elena/mi_proyecto_fastapi/venv/bin/pip install sqlalchemy pandas numpy scikit-learn httpx "passlib[bcrypt]" loguru cryptography python-multipart uvicorn[standard]
```

## Endpoints principales (ejemplos)

- `GET /status` - Estado del servicio.
- `POST /upload_sales/{tenant_code}` - Subir CSV de ventas.
- `POST /explain/{tenant_code}` - Solicitar explicación basada en IA (requiere configuración de proveedor IA).

## Notas

- En desarrollo se crea automáticamente la base SQLite y las tablas (ver `app/core/db.py`).
- Si usas HF local, configura `AI_PROVIDER=hf_local` y `HF_LOCAL_MODEL`.
- Mantén actualizadas las variables de entorno en `sample.env`.

## Mantenimiento: cifrado de campos sensibles

El proyecto incluye un script y una migración Alembic para cifrar los campos `api_key` y `access_token` en la tabla `external_integrations`.

Precauciones:
- Hacer un backup de la base de datos antes de aplicar cambios.
- Establecer la variable de entorno `FERNET_KEY` con la clave que se usará para cifrar los valores.

Comandos útiles:

Dry-run (no modifica la BD):
```bash
source /Users/elena/mi_proyecto_fastapi/venv/bin/activate
make encrypt-dry-run
```

Aplicar cambios (modifica la BD):
```bash
source /Users/elena/mi_proyecto_fastapi/venv/bin/activate
export FERNET_KEY="<your-fernet-key>"
make encrypt-apply
```

También existe la migración Alembic `alembic/versions/0003_encrypt_external_integrations.py`. Para ejecutarla con Alembic:

```bash
source /Users/elena/mi_proyecto_fastapi/venv/bin/activate
export FERNET_KEY="<your-fernet-key>"
make alembic-upgrade
```

## Opcional: usar Redis para cache de explicaciones

Si quieres mejorar latencia y evitar llamadas repetidas al proveedor de IA, puedes configurar Redis en `REDIS_URL`.

Ejemplo para levantar Redis localmente con Docker:

```bash
docker run -d -p 6379:6379 --name my-redis redis:7
export REDIS_URL=redis://localhost:6379/0
```

La aplicación detecta `REDIS_URL` y usará Redis para cachear respuestas de `/explain`.

## Levantar app en desarrollo con Docker Compose

Incluye servicios: `postgres` (DB), `redis` (cache/rate-limit) y `web` (tu aplicación).

1. Revisar/editar `.env.dev` si quieres cambiar credenciales por defecto.

2. Levantar los servicios:

```bash
cd "/Users/elena/mi_proyecto_fastapi/My Awesome API]"
docker-compose up --build
```

3. La app quedará disponible en `http://localhost:8000` y puedes acceder a `http://localhost:8000/docs`.

4. Para pararla:

```bash
docker-compose down -v
```

Notas:
- El `docker-compose.yml` mapea el subdirectorio `[A FastAPI project]` dentro del contenedor para desarrollo rápido (hot-reload).
- Si prefieres usar la imagen construida sin montar volumen, elimina la sección `volumes` en el servicio `web`.



