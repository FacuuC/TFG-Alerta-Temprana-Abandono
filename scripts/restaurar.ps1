<#
.SYNOPSIS
Restaura un respaldo de scripts\respaldar.ps1 en la base de la plataforma.

.DESCRIPTION
Control de Seguridad: «el procedimiento de restauración se prueba y se documenta en el
manual de instalación». REEMPLAZA todo el contenido de la base por el del respaldo.
Pide confirmación (-Si la omite).

Pasos: detiene el contenedor de la aplicación, copia el respaldo al contenedor «db»,
corta las otras conexiones, restaura con pg_restore --clean --if-exists en una sola
transacción (si algo falla, la base queda como estaba) y vuelve a levantar la aplicación.
Al arrancar, la aplicación no duplica nada: crea solo las tablas, roles, usuarios de
prueba y filas de MODELO que falten. Usa el usuario y la base del contenedor «db».

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\restaurar.ps1 respaldos\demo_20261109-2000.dump
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Ruta,
    [switch]$Si
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
if (-not (Test-Path -PathType Leaf $Ruta)) { Write-Error "No existe el archivo: $Ruta" }
$respaldo = (Resolve-Path $Ruta).Path  # antes de cambiar de carpeta
Set-Location (Join-Path $PSScriptRoot '..')
$temporal = '/tmp/alerta_restaurar.dump'

function Invocar-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Falló el comando: docker $($args -join ' ')" }
}

if (-not (docker compose ps --status running -q db)) {
    Write-Error 'La base no está en ejecución. Levantala con: docker compose up -d db'
}

if (-not $Si) {
    Write-Host "Se va a REEMPLAZAR todo el contenido de la base por el de $respaldo."
    if ((Read-Host 'Escribí SI para continuar') -cne 'SI') {
        Write-Host 'Cancelado: no se modificó nada.'
        exit 1
    }
}

$appDetenida = $false
if (docker compose ps --status running -q app) {
    Write-Host 'Deteniendo la aplicación...'
    Invocar-Docker compose stop app
    $appDetenida = $true
} elseif (-not (docker compose ps -a -q app)) {
    Write-Warning 'No hay contenedor de la aplicación. Si la corrés con uvicorn en el equipo, detenela antes (Ctrl+C).'
}

# Si la aplicación se detuvo, se vuelve a levantar también si algo falla (con
# --single-transaction, una restauración fallida deja la base como estaba).
try {
    Invocar-Docker compose cp $respaldo "db:$temporal"
    Write-Host 'Restaurando...'
    'SELECT count(pg_terminate_backend(pid)) AS conexiones_cortadas FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid();' |
        docker compose exec -T db sh -c 'psql -X -q -U $POSTGRES_USER -d $POSTGRES_DB -v ON_ERROR_STOP=1'
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron cortar las conexiones a la base.' }
    Invocar-Docker compose exec -T db sh -c ('pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists --no-owner --single-transaction ' + $temporal + '; s=$?; rm -f ' + $temporal + '; exit $s')
    Write-Host 'Base restaurada.'
} finally {
    if ($appDetenida) {
        Write-Host 'Levantando la aplicación...'
        & docker compose start app
        $idApp = docker compose ps -q app
        $estado = ''
        for ($i = 0; $i -lt 45 -and $estado -ne 'healthy'; $i++) {
            Start-Sleep -Seconds 2
            $estado = docker inspect --format '{{.State.Health.Status}}' $idApp
        }
        Write-Host "Aplicación: $estado."
    }
}
Write-Host 'Comprobá el contenido con: powershell -ExecutionPolicy Bypass -File scripts\verificar.ps1'
