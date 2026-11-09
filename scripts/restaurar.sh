#!/usr/bin/env sh
# Restaura un respaldo de scripts/respaldar.sh (control de Seguridad: «el procedimiento de
# restauración se prueba y se documenta en el manual de instalación»). Uso:
#
#     sh scripts/restaurar.sh respaldos/<archivo>.dump [--si]
#
# REEMPLAZA todo el contenido de la base por el del respaldo. Pide confirmación (--si la
# omite). Pasos: detiene el contenedor de la aplicación, copia el respaldo al contenedor
# «db», corta las otras conexiones, restaura con pg_restore --clean --if-exists en una sola
# transacción (si algo falla, la base queda como estaba) y vuelve a levantar la aplicación.
# Al arrancar, la aplicación no duplica nada: crea solo las tablas, roles, usuarios de
# prueba y filas de MODELO que falten. Usa el usuario y la base del contenedor «db».
set -eu
export MSYS_NO_PATHCONV=1  # Git Bash en Windows: no convertir /tmp/... en rutas de Windows

if [ $# -lt 1 ] || [ ! -f "$1" ]; then
  echo "Uso: sh scripts/restaurar.sh respaldos/<archivo>.dump [--si]" >&2
  [ $# -lt 1 ] || echo "No existe el archivo: $1" >&2
  exit 1
fi
respaldo=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
# Git Bash en Windows: docker.exe necesita la ruta de Windows (C:\...), no /c/...
if command -v cygpath >/dev/null 2>&1; then respaldo=$(cygpath -w "$respaldo"); fi
confirmado=no
[ "${2:-}" = "--si" ] && confirmado=si
cd "$(dirname "$0")/.."
temporal=/tmp/alerta_restaurar.dump

if [ -z "$(docker compose ps --status running -q db)" ]; then
  echo "La base no está en ejecución. Levantala con: docker compose up -d db" >&2
  exit 1
fi

if [ "$confirmado" != si ]; then
  echo "Se va a REEMPLAZAR todo el contenido de la base por el de $respaldo."
  printf 'Escribí SI para continuar: '
  read -r respuesta
  [ "$respuesta" = SI ] || { echo "Cancelado: no se modificó nada."; exit 1; }
fi

# Si la aplicación se detiene, se vuelve a levantar al salir, también si algo falla
# (con --single-transaction, una restauración fallida deja la base como estaba).
app_detenida=no
levantar_app() {
  if [ "$app_detenida" = si ]; then
    app_detenida=no
    echo "Levantando la aplicación..."
    docker compose start app
    id_app=$(docker compose ps -q app)
    estado=desconocido
    for _ in $(seq 1 45); do
      estado=$(docker inspect --format '{{.State.Health.Status}}' "$id_app")
      [ "$estado" = healthy ] && break
      sleep 2
    done
    echo "Aplicación: $estado."
  fi
}
trap levantar_app EXIT

if [ -n "$(docker compose ps --status running -q app)" ]; then
  echo "Deteniendo la aplicación..."
  docker compose stop app
  app_detenida=si
elif [ -z "$(docker compose ps -a -q app)" ]; then
  echo "AVISO: no hay contenedor de la aplicación. Si la corrés con uvicorn en el equipo, detenela antes (Ctrl+C)."
fi

docker compose cp "$respaldo" "db:$temporal"
echo "Restaurando..."
echo "SELECT count(pg_terminate_backend(pid)) AS conexiones_cortadas FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();" \
  | docker compose exec -T db sh -c 'psql -X -q -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1'
docker compose exec -T db sh -c "pg_restore -U \$POSTGRES_USER -d \$POSTGRES_DB --clean --if-exists --no-owner --single-transaction $temporal; s=\$?; rm -f $temporal; exit \$s"
echo "Base restaurada."
levantar_app
echo "Comprobá el contenido con: sh scripts/verificar.sh"
