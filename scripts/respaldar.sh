#!/usr/bin/env sh
# Respaldo completo de la base de la plataforma (control de Seguridad: «un script que genera
# un respaldo completo»). Uso, desde cualquier carpeta:
#
#     sh scripts/respaldar.sh [etiqueta]
#
# Genera respaldos/<etiqueta>_<AAAAMMDD-HHMM>.dump (etiqueta por defecto: «respaldo») con
# pg_dump en formato custom (-Fc), que es el que lee pg_restore (scripts/restaurar.sh).
# El archivo se escribe dentro del contenedor con -f y se copia con «docker compose cp»: así
# el binario no pasa por la consola. Usa el usuario y la base del contenedor «db» (no lee
# .env en el equipo). respaldos/ no se versiona.
set -eu
export MSYS_NO_PATHCONV=1  # Git Bash en Windows: no convertir /tmp/... en rutas de Windows
cd "$(dirname "$0")/.."

# Etiqueta: letras sin acento, dígitos, «-» y «_»; los espacios pasan a «-».
etiqueta=$(printf '%s' "${1:-respaldo}" | tr ' ' '-' | tr -cd 'A-Za-z0-9_-')
[ -n "$etiqueta" ] || etiqueta=respaldo
destino="respaldos/${etiqueta}_$(date +%Y%m%d-%H%M).dump"
temporal=/tmp/alerta_respaldo.dump

if [ -z "$(docker compose ps --status running -q db)" ]; then
  echo "La base no está en ejecución. Levantala con: docker compose up -d" >&2
  exit 1
fi

mkdir -p respaldos
docker compose exec -T db sh -c "pg_dump -U \$POSTGRES_USER -d \$POSTGRES_DB -Fc -f $temporal"
# Control: pg_restore tiene que poder leer el archivo (cuenta las tablas con datos).
tablas=$(docker compose exec -T db sh -c "pg_restore -l $temporal | grep -c 'TABLE DATA'")
docker compose cp "db:$temporal" "$destino"
docker compose exec -T db rm -f "$temporal"

echo "Respaldo generado: $destino ($(wc -c < "$destino" | tr -d ' ') bytes, $tablas tablas con datos)."
