#!/usr/bin/env sh
# Muestra el contenido de la base: estudiantes, cargas por momento, alertas por nivel y por
# estado de seguimiento, cambios de estado, modelos y datos iniciales (scripts/verificar.sql).
# Solo lee. Uso, desde cualquier carpeta:  sh scripts/verificar.sh
# Usa el usuario y la base del contenedor «db» (no lee .env en el equipo).
set -eu
export MSYS_NO_PATHCONV=1  # Git Bash en Windows: no convertir /tmp/... en rutas de Windows
cd "$(dirname "$0")/.."

if [ -z "$(docker compose ps --status running -q db)" ]; then
  echo "La base no está en ejecución. Levantala con: docker compose up -d" >&2
  exit 1
fi

docker compose cp scripts/verificar.sql db:/tmp/alerta_verificar.sql >/dev/null 2>&1 \
  || { echo "No se pudo copiar scripts/verificar.sql al contenedor db." >&2; exit 1; }
docker compose exec -T db sh -c 'psql -X -q -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1 -P pager=off -f /tmp/alerta_verificar.sql; s=$?; rm -f /tmp/alerta_verificar.sql; exit $s'
