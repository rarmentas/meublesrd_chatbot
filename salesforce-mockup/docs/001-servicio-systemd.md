# 001 – Mockup corriendo como servicio (systemd)

Documentación de cómo está configurado el mockup de Salesforce (Meubles RD) para ejecutarse como servicio en Linux mediante **systemd**.

---

## Resumen

- **Servicio:** `salesforce-mockup`
- **Unidad:** `salesforce-mockup.service`
- **Usuario:** `rarme`
- **Puerto por defecto:** `8001`
- **Arranque:** script `start-prod.sh` → **uvicorn** con ASGI (`config.asgi:application`)

El servicio se reinicia automáticamente si falla (`Restart=always`, `RestartSec=3`).

---

## Archivos implicados

| Archivo | Función |
|--------|---------|
| `salesforce-mockup.service` | Unidad systemd (descripción, usuario, comando de inicio, reinicio). |
| `start-prod.sh` | Script que activa el venv, define variables de producción y ejecuta `uvicorn`. |

---

## Unidad systemd (`salesforce-mockup.service`)

- **Descripción:** Meubles RD Salesforce mockup (uvicorn).
- **Tipo:** `simple` (el proceso principal es el servidor).
- **Usuario/Grupo:** `rarme`.
- **Directorio de trabajo:** `/home/rarme/meublesrd_chatbot/salesforce-mockup`.
- **Comando de inicio:** `/home/rarme/meublesrd_chatbot/salesforce-mockup/start-prod.sh`.
- **Reinicio:** `Restart=always`, `RestartSec=3`.
- **Arranque al boot:** `WantedBy=multi-user.target` (se habilita con `systemctl enable`).

Variables de entorno opcionales (comentadas en la unidad):

- `ALLOWED_HOSTS` – dominios permitidos (Django).
- `UVICORN_PORT` – puerto de uvicorn (por defecto 8001).

---

## Script de arranque (`start-prod.sh`)

El script:

1. Se posiciona en el directorio del proyecto.
2. Usa el **venv** del proyecto (`venv` en la raíz; configurable con `VENV_DIR`).
3. Activa el venv y define:
   - `DJANGO_DEBUG=0`
   - `DJANGO_SETTINGS_MODULE=config.settings`
   - `ALLOWED_HOSTS` (por defecto `*`; en producción conviene restringir).
4. Define host y puerto de uvicorn:
   - `UVICORN_HOST` (por defecto `0.0.0.0`)
   - `UVICORN_PORT` (por defecto `8001`)
5. Ejecuta:  
   `uvicorn config.asgi:application --host <HOST> --port <PORT>`

Si no existe el directorio del venv, el script sale con error e indica crear el entorno e instalar dependencias.

---

## Instalación del servicio

Desde la raíz del proyecto (o con rutas absolutas):

```bash
sudo cp /home/rarme/meublesrd_chatbot/salesforce-mockup/salesforce-mockup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable salesforce-mockup
sudo systemctl start salesforce-mockup
```

Comprobar estado:

```bash
sudo systemctl status salesforce-mockup
```

---

## Comandos útiles

| Acción | Comando |
|--------|---------|
| Ver estado | `sudo systemctl status salesforce-mockup` |
| Iniciar | `sudo systemctl start salesforce-mockup` |
| Parar | `sudo systemctl stop salesforce-mockup` |
| Reiniciar | `sudo systemctl restart salesforce-mockup` |
| Ver logs (seguir) | `sudo journalctl -u salesforce-mockup -f` |
| Ver logs recientes | `sudo journalctl -u salesforce-mockup -n 100` |
| Habilitar al arranque | `sudo systemctl enable salesforce-mockup` |
| Deshabilitar al arranque | `sudo systemctl disable salesforce-mockup` |

---

## Verificación rápida

- **Servicio activo:** `systemctl is-active salesforce-mockup` → `active`
- **Escuchando en puerto:** `ss -tlnp | grep 8001` (o el puerto configurado)
- **Probar HTTP:** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/` (o la URL que uses)

---

## Entorno y configuración en producción

- **Django:** `DEBUG=False` vía `DJANGO_DEBUG=0` en `start-prod.sh`.
- **ALLOWED_HOSTS:** por defecto `*`; en producción se puede restringir con la variable de entorno `ALLOWED_HOSTS` (en el servicio o en el script).
- **Puerto:** 8001 por defecto; cambiable con `UVICORN_PORT` (por ejemplo en la sección `[Service]` de la unidad con `Environment="UVICORN_PORT=8000"`).

La base de datos por defecto es SQLite (`db.sqlite3` en la raíz del proyecto). El proceso corre con usuario `rarme`, por lo que los permisos del directorio y del archivo de base de datos deben permitir lectura/escritura a ese usuario.

---

## Relación con el resto del proyecto

- **SETUP.md** describe el desarrollo local (Conda, `runserver`, migraciones, datos de prueba).
- Este documento (**001-servicio-systemd.md**) describe solo la puesta en marcha como **servicio systemd** en el servidor (Linux), usando `start-prod.sh` y uvicorn.
