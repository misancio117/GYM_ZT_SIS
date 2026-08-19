#Requires -Version 5.1
<#
.SYNOPSIS
  Crea venv e instala dependencias del backend Django.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$venv = Join-Path $root '.venv'

if (-not (Test-Path $backend)) {
    Write-Error "No se encontró la carpeta backend en $backend"
    exit 1
}

if (-not (Test-Path $venv)) {
    python -m venv $venv
}
$pip = Join-Path $venv 'Scripts/pip.exe'
$py = Join-Path $venv 'Scripts/python.exe'
& $pip install --upgrade pip
& $pip install -r (Join-Path $backend 'requirements.txt')
Write-Host "Backend listo. Python: $py"
