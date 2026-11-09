<#
.SYNOPSIS
Muestra el contenido de la base de la plataforma (solo lee).

.DESCRIPTION
Estudiantes, cargas por momento de predicción, alertas por nivel de urgencia y por estado
de seguimiento, filas de CAMBIO_ESTADO, modelos y datos iniciales (scripts/verificar.sql).
Usa el usuario y la base del contenedor «db»: no lee .env en el equipo.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\verificar.ps1
#>
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Set-Location (Join-Path $PSScriptRoot '..')

function Invocar-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Falló el comando: docker $($args -join ' ')" }
}

if (-not (docker compose ps --status running -q db)) {
    Write-Error 'La base no está en ejecución. Levantala con: docker compose up -d'
}

# Sin el progreso de la copia (en Windows PowerShell, el stderr redirigido se vuelve error).
$ErrorActionPreference = 'Continue'
docker compose cp scripts/verificar.sql db:/tmp/alerta_verificar.sql *> $null
$ErrorActionPreference = 'Stop'
if ($LASTEXITCODE -ne 0) { throw 'No se pudo copiar scripts\verificar.sql al contenedor db.' }
Invocar-Docker compose exec -T db sh -c 'psql -X -q -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1 -P pager=off -f /tmp/alerta_verificar.sql; s=$?; rm -f /tmp/alerta_verificar.sql; exit $s'
