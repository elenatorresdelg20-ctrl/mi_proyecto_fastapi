# Contratos API para frontend Next.js

## Autenticación
- **POST** `/api/auth/login`
  - Body: `{ "email": string, "password": string }`
  - Respuesta: `{ "access_token": string, "token_type": "bearer", "tenant": string, "user": { id, username, email } }`

## Upload
- **POST** `/api/upload/{tenant}` (multipart/form-data)
  - Campo `file`: CSV
  - Respuesta: `{ tenant, file_name, columns: [{name,dtype}], sample_rows: [{...}], total_rows }`

## Dashboards protegidos (requiere `Authorization: Bearer <token>`)
- **GET** `/api/analysis/{tenant}` → KPIs, tendencia y desglose canales.
- **GET** `/api/forecast/{tenant}` → Serie semanal con `actual`/`forecast` y metadata.
- **GET** `/api/report/{tenant}` → Cards de highlights y tabla de segmentos.
- **GET** `/api/sales/{tenant}` → Funnel de ventas y top productos.

Todas las rutas usan el `tenant_code` embebido en el JWT para validar acceso multi-tenant.
