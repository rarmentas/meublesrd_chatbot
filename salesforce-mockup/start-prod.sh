#!/usr/bin/env bash
# Inicia la aplicación en modo producción con uvicorn.
# Usa el Python del venv local de este proyecto.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cargar variables desde .env (p. ej. UVICORN_PORT)
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/venv}"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Error: no se encontró el venv en $VENV_DIR. Crea uno con: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

# Activar venv y variables de producción
source "$VENV_DIR/bin/activate"
export DJANGO_DEBUG=0
export DJANGO_SETTINGS_MODULE=config.settings

# De momento aceptar cualquier Host. Para restringir: export ALLOWED_HOSTS=localhost,midominio.com
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-*}"

HOST="${UVICORN_HOST:-0.0.0.0}"
PORT="${UVICORN_PORT:-9101}"

exec uvicorn config.asgi:application --host "$HOST" --port "$PORT"
