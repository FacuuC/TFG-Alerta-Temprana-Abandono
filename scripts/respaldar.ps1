<#
.SYNOPSIS
Respaldo completo de la base de la plataforma (pg_dump en formato custom).

.DESCRIPTION
Control de Seguridad: «un script que genera un respaldo completo». Genera
respaldos\<etiqueta>_<AAAAMMDD-HHMM>.dump (etiqueta por defecto: «respaldo»), que se
restaura con scripts\restaurar.ps1.

El archivo se escribe dentro del contenedor con «pg_dump -f» y se copia con
«docker compose cp»: la redirección «>» de PowerShell reescribe la salida como texto y
corrompe el binario. Usa el usuario y la base del contenedor «db» (no lee .env en el
equipo). respaldos\ no se versiona.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts\respaldar.ps1 -Etiqueta demo
#>
param([string]$Etiqueta = 'respaldo')

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Set-Location (Join-Path $PSScriptRoot '..')

function Invocar-Docker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw "Falló el comando: docker $($args -join ' ')" }
}

# Etiqueta: letras sin acento, dígitos, «-» y «_»; los espacios pasan a «-».
$Etiqueta = ($Etiqueta -replace '\s+', '-') -replace '[^A-Za-z0-9_-]', ''
if (-not $Etiqueta) { $Etiqueta = 'respaldo' }
$destino = "respaldos/${Etiqueta}_$(Get-Date -Format 'yyyyMMdd-HHmm').dump"
$temporal = '/tmp/alerta_respaldo.dump'

if (-not (docker compose ps --status running -q db)) {
    Write-Error 'La base no está en ejecución. Levantala con: docker compose up -d'
}

New-Item -ItemType Directory -Force respaldos | Out-Null
Invocar-Docker compose exec -T db sh -c ('pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -Fc -f ' + $temporal)
# Control: pg_restore tiene que poder leer el archivo (cuenta las tablas con datos).
$tablas = docker compose exec -T db sh -c ('pg_restore -l ' + $temporal + ' | grep -c TABLE.DATA')
if ($LASTEXITCODE -ne 0) { throw 'pg_restore no pudo leer el respaldo generado.' }
Invocar-Docker compose cp "db:$temporal" $destino
Invocar-Docker compose exec -T db rm -f $temporal

$bytes = (Get-Item $destino).Length
Write-Host "Respaldo generado: $destino ($bytes bytes, $tablas tablas con datos)."
