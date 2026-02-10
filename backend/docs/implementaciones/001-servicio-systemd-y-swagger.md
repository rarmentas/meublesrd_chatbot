# 001 – Servicio systemd y documentación Swagger/OpenAPI

Documentación de la implementación del backend de Muebles RD: ejecución como **servicio systemd** con uvicorn y documentación automática de la API con **drf-spectacular** (OpenAPI 3, Swagger UI y ReDoc).

---

## Resumen

| Aspecto | Detalle |
|--------|---------|
| **Servicio** | `mueblesrd-api` |
| **Unidad** | `mueblesrd-api.service` |
| **Usuario** | `rarme` |
| **Puerto por defecto** | `8000` |
| **Arranque** | `start-prod.sh` → **uvicorn** con ASGI (`mueblesrd_api.asgi:application`) |
| **Documentación** | **drf-spectacular**: OpenAPI 3, Swagger UI (`/api/docs/`), ReDoc (`/api/redoc/`), schema (`/api/schema/`) |

El servicio se reinicia automáticamente si falla (`Restart=always`, `RestartSec=3`).

---

## Parte 1: Servicio systemd

### Archivos implicados

| Archivo | Función |
|--------|---------|
| `mueblesrd-api.service` | Unidad systemd (descripción, usuario, comando de inicio, reinicio). |
| `start-prod.sh` | Script que activa el venv, define variables de producción y ejecuta uvicorn. |
| `collect-static.sh` | Recolecta estáticos en `staticfiles/` (opcional; ejecutar antes del primer despliegue o tras cambiar estáticos). |

### Unidad systemd (`mueblesrd-api.service`)

- **Descripción:** Meubles RD API backend (uvicorn).
- **Tipo:** `simple` (el proceso principal es el servidor).
- **Usuario/Grupo:** `rarme`.
- **Directorio de trabajo:** `/home/rarme/meublesrd_chatbot/backend`.
- **Comando de inicio:** `/home/rarme/meublesrd_chatbot/backend/start-prod.sh`.
- **Reinicio:** `Restart=always`, `RestartSec=3`.
- **Arranque al boot:** `WantedBy=multi-user.target` (se habilita con `systemctl enable`).

Variables de entorno opcionales (comentadas en la unidad):

- `ALLOWED_HOSTS` – dominios permitidos (Django).
- `UVICORN_PORT` – puerto de uvicorn (por defecto 8000).

### Script de arranque (`start-prod.sh`)

El script:

1. Se posiciona en el directorio del proyecto.
2. Usa el **venv** del proyecto (`venv` en la raíz del backend; configurable con `VENV_DIR`).
3. Activa el venv y define:
   - `DEBUG=0`
   - `DJANGO_SETTINGS_MODULE=mueblesrd_api.settings`
   - `ALLOWED_HOSTS` (por defecto `*`; en producción conviene restringir).
4. Define host y puerto de uvicorn:
   - `UVICORN_HOST` (por defecto `0.0.0.0`)
   - `UVICORN_PORT` (por defecto `8000`)
5. Ejecuta:  
   `uvicorn mueblesrd_api.asgi:application --host <HOST> --port <PORT>`

Si no existe el directorio del venv, el script sale con error e indica crear el entorno e instalar dependencias.

### Instalación del servicio

Desde la raíz del proyecto (o con rutas absolutas):

```bash
sudo cp /home/rarme/meublesrd_chatbot/backend/mueblesrd-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mueblesrd-api
sudo systemctl start mueblesrd-api
```

Comprobar estado:

```bash
sudo systemctl status mueblesrd-api
```

### Comandos útiles (servicio)

| Acción | Comando |
|--------|---------|
| Ver estado | `sudo systemctl status mueblesrd-api` |
| Iniciar | `sudo systemctl start mueblesrd-api` |
| Parar | `sudo systemctl stop mueblesrd-api` |
| Reiniciar | `sudo systemctl restart mueblesrd-api` |
| Ver logs (seguir) | `sudo journalctl -u mueblesrd-api -f` |
| Ver logs recientes | `sudo journalctl -u mueblesrd-api -n 100` |
| Habilitar al arranque | `sudo systemctl enable mueblesrd-api` |
| Deshabilitar al arranque | `sudo systemctl disable mueblesrd-api` |

### Estáticos (opcional)

Antes del primer despliegue o tras cambiar archivos estáticos:

```bash
cd /home/rarme/meublesrd_chatbot/backend
./collect-static.sh
```

Los archivos se escriben en `backend/staticfiles/`.

---

## Parte 2: Documentación Swagger / OpenAPI (drf-spectacular)

### Objetivo

Exponer la API con documentación interactiva (OpenAPI 3): esquema JSON, **Swagger UI** para probar endpoints y **ReDoc** como alternativa de lectura.

### Dependencia

- **drf-spectacular** (en `requirements.txt`: `drf-spectacular>=0.27`).

### Configuración en el proyecto

**Settings (`mueblesrd_api/settings.py`):**

- `drf_spectacular` en `INSTALLED_APPS`.
- En `REST_FRAMEWORK`: `DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'`.
- Bloque `SPECTACULAR_SETTINGS`:
  - `TITLE`: "Muebles RD Chatbot API"
  - `DESCRIPTION`: descripción de la API
  - `VERSION`: "1.0.0"
  - `SERVE_INCLUDE_SCHEMA`: False

**URLs (`mueblesrd_api/urls.py`):**

| Ruta | Vista | Uso |
|------|--------|-----|
| `api/schema/` | `SpectacularAPIView` | Esquema OpenAPI en JSON. |
| `api/docs/` | `SpectacularSwaggerView` | Interfaz Swagger UI (probar la API). |
| `api/redoc/` | `SpectacularRedocView` | Documentación ReDoc. |

### Cómo se documentan los endpoints

1. **Serializers de documentación** (`chatbot/serializers.py`): definen request/response solo para el esquema (no validan en las vistas):
   - `ChatRequestSerializer` – cuerpo de `POST /api/chat/` (campo `query`).
   - `ChatResponseSerializer` – respuesta 200 (campos `answer`, `sources`).
   - `ChatErrorSerializer` – respuestas 400/500 (campo `error`).
   - `HealthResponseSerializer` – respuesta de `GET /api/health/` (campo `status`).

2. **Decorador `@extend_schema`** en las vistas (`chatbot/views.py`):
   - En `HealthCheckView.get`: summary, description, respuesta 200.
   - En `ChatView.post`: summary, description, request body, respuestas 200, 400 y 500.

Con esto, drf-spectacular genera el OpenAPI y Swagger/ReDoc muestran los esquemas y permiten probar los endpoints.

### URLs de documentación (con el servidor en marcha)

- **Swagger UI:** `http://<host>:8000/api/docs/`
- **ReDoc:** `http://<host>:8000/api/redoc/`
- **Schema (JSON):** `http://<host>:8000/api/schema/`

### Generar el esquema por línea de comandos

```bash
cd /home/rarme/meublesrd_chatbot/backend
venv/bin/python manage.py spectacular --format openapi-json --file schema.json
```

---

## Verificación rápida

- **Servicio activo:** `systemctl is-active mueblesrd-api` → `active`
- **Escuchando en puerto:** `ss -tlnp | grep 8000` (o el puerto configurado)
- **Health:** `curl -s http://127.0.0.1:8000/api/health/`
- **Swagger:** abrir en el navegador `http://127.0.0.1:8000/api/docs/`
- **Schema:** `curl -s http://127.0.0.1:8000/api/schema/ | head -20`

---

## Relación con el resto del proyecto

- **README.md** del backend describe el proyecto y el desarrollo local.
- Este documento (**001-servicio-systemd-y-swagger.md**) describe la puesta en producción como **servicio systemd** y la **documentación de la API** con drf-spectacular (Swagger/OpenAPI).
- El patrón de servicio y scripts es análogo al del mockup de Salesforce (`salesforce-mockup/start-prod.sh`, `salesforce-mockup.service`).
