#!/usr/bin/env bash
# Recolecta archivos estáticos en STATIC_ROOT (staticfiles).
# Ejecutar antes del primer despliegue o tras cambiar estáticos.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${VENV_DIR:-$SCRIPT_DIR/venv}"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "Error: no se encontró el venv en $VENV_DIR."
  exit 1
fi

source "$VENV_DIR/bin/activate"
export DJANGO_SETTINGS_MODULE=mueblesrd_api.settings

python manage.py collectstatic --noinput

echo "Collectstatic terminado. Archivos en: $SCRIPT_DIR/staticfiles"
