# 002 – Django Admin y autenticación de la API

Documentación de la implementación de **Django Admin** (gestor de usuarios) y **autenticación por token** en la API usando los mismos usuarios de Django.

---

## Resumen

| Aspecto | Detalle |
|--------|---------|
| **Admin** | `/admin/` – gestión de usuarios y grupos (Django auth). |
| **Base de datos** | SQLite (`backend/db.sqlite3`) para auth, sessions y tokens. |
| **Autenticación API** | Token DRF. Header: `Authorization: Token <token>`. |
| **Obtener token** | `POST /api/auth/token/` con `username` y `password` (JSON). |
| **Endpoints públicos** | `GET /api/health/`, `POST /api/auth/token/`, `/api/docs/`, `/api/redoc/`, `/api/schema/`. |
| **Endpoints protegidos** | `POST /api/chat/` (requiere token o sesión). |

---

## Django Admin

- **URL:** `http://<host>:8000/admin/`
- **Apps instaladas:** `django.contrib.admin`, `django.contrib.auth`, `django.contrib.sessions`, `django.contrib.messages`.
- **Uso:** Iniciar sesión con un superusuario. Desde ahí se gestionan usuarios (User) y grupos (Group).

### Primer superusuario

Si aún no existe, crear uno:

```bash
cd /home/rarme/meublesrd_chatbot/backend
venv/bin/python manage.py createsuperuser
```

Se pedirá username, email (opcional) y contraseña. Para automatizar (por ejemplo en despliegue):

```bash
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD="tu_contraseña_segura" \
venv/bin/python manage.py createsuperuser --noinput
```

**Importante:** cambiar la contraseña por defecto tras el primer acceso si se usó una generada o temporal.

---

## Autenticación de la API

### Clases configuradas (settings)

- **DEFAULT_AUTHENTICATION_CLASSES:** `TokenAuthentication`, `SessionAuthentication`.
- **DEFAULT_PERMISSION_CLASSES:** `IsAuthenticated` (por defecto todas las vistas requieren auth).

Vistas que no requieren auth (públicas):

- `HealthCheckView` – `permission_classes = [AllowAny]`
- `ObtainTokenView` – `permission_classes = [AllowAny]`

### Cómo usar el token

1. **Obtener token:**  
   `POST /api/auth/token/` con cuerpo JSON:
   ```json
   { "username": "admin", "password": "tu_contraseña" }
   ```
   Respuesta: `{ "token": "abc123..." }`.

2. **Llamar a la API:**  
   Incluir en cada petición el header:
   ```
   Authorization: Token abc123...
   ```
   (el valor es exactamente la palabra `Token` seguida de un espacio y el token).

### En Swagger UI

1. Ir a `/api/docs/`.
2. Pulsar **Authorize**.
3. En el campo correspondiente al esquema "TokenAuth" (header `Authorization`) introducir:  
   `Token <tu_token>`  
   (sustituir `<tu_token>` por el valor recibido en `POST /api/auth/token/`).
4. Cerrar y probar `POST /api/chat/`.

---

## Archivos relevantes

| Archivo | Cambio / contenido |
|--------|----------------------|
| `mueblesrd_api/settings.py` | `INSTALLED_APPS`: admin, auth, sessions, messages, `rest_framework.authtoken`. `DATABASES` SQLite. `LOGIN_URL`. `AUTH_PASSWORD_VALIDATORS`. `REST_FRAMEWORK`: auth y permisos por defecto. |
| `mueblesrd_api/urls.py` | `path('admin/', admin.site.urls)`. Token bajo `api/` vía `chatbot.urls`. |
| `chatbot/urls.py` | `path('auth/token/', ObtainTokenView.as_view())`. |
| `chatbot/views.py` | `ObtainTokenView` (documentada). `HealthCheckView`: `AllowAny`. `ChatView`: `IsAuthenticated`. |
| `chatbot/serializers.py` | `TokenRequestSerializer`, `TokenResponseSerializer` (solo documentación). |
| `SPECTACULAR_SETTINGS` | Esquema de seguridad `TokenAuth` (header `Authorization`) para Swagger. |

---

## Migraciones

Las tablas de auth, admin, sessions y tokens se crean con:

```bash
cd /home/rarme/meublesrd_chatbot/backend
venv/bin/python manage.py migrate
```

Ya aplicadas en el proyecto: `admin`, `auth`, `authtoken`, `contenttypes`, `sessions`.

---

## Resumen de URLs

| URL | Método | Auth | Uso |
|-----|--------|------|-----|
| `/admin/` | GET | Sesión (login) | Django Admin. |
| `/api/auth/token/` | POST | No | Obtener token (username + password). |
| `/api/health/` | GET | No | Health check. |
| `/api/chat/` | POST | Sí (Token o sesión) | Chat RAG. |
| `/api/docs/` | GET | No | Swagger UI. |
| `/api/redoc/` | GET | No | ReDoc. |
| `/api/schema/` | GET | No | OpenAPI JSON. |
