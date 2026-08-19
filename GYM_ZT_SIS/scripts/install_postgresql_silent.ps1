#Requires -Version 5.1
<#
.SYNOPSIS
  Instalación silenciosa del instalador oficial de PostgreSQL para Windows (EDB).
.PARAMETER InstallerPath
  Ruta al archivo postgresql-*-windows-x64.exe incluido en el paquete comercial.
.PARAMETER SuperPassword
  Contraseña del superusuario postgres (obligatoria para modo unattended).
.PARAMETER Port
  Puerto TCP (por defecto 5432).
.NOTES
  Ejemplo de línea usada por el instalador EDB (ajuste la versión):
  .\postgresql-16.2-1-windows-x64.exe --mode unattended --unattendedmodeui none `
    --superpassword "SU_CLAVE" --servicename "postgresql-x64-16" --serverport 5432
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,
    [Parameter(Mandatory = $true)]
    [string]$SuperPassword,
    [int]$Port = 5432
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $InstallerPath)) {
    Write-Error "No existe el instalador: $InstallerPath"
    exit 1
}

$ver = [System.Diagnostics.FileVersionInfo]::GetVersionInfo((Resolve-Path $InstallerPath).Path).FileVersion
$serviceName = "postgresql-x64-16"
# Ajuste manual si su instalador usa otro nombre de servicio (ver documentación EDB).

$args = @(
    '--mode', 'unattended',
    '--unattendedmodeui', 'none',
    '--superpassword', $SuperPassword,
    '--servicename', $serviceName,
    '--serverport', $Port.ToString()
)

Write-Host "Ejecutando instalador silencioso de PostgreSQL..."
$p = Start-Process -FilePath $InstallerPath -ArgumentList $args -Wait -PassThru
if ($p.ExitCode -ne 0) {
    Write-Error "El instalador terminó con código $($p.ExitCode)."
    exit $p.ExitCode
}

Write-Host "Instalación finalizada. Reinicie el equipo si el instalador lo solicita."
Write-Host "Defina POSTGRES_SUPERUSER_PASSWORD=$SuperPassword en el .env de la aplicación o en credenciales."
exit 0
