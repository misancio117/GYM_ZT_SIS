#Requires -Version 5.1
<#
.SYNOPSIS
  Comprueba que el servicio de PostgreSQL esté instalado y en ejecución.
.DESCRIPTION
  Busca servicios cuyo nombre coincida con postgresql* o contenga "PostgreSQL".
  Opcionalmente intenta iniciar el servicio si está detenido.
.PARAMETER TryStart
  Si está presente, intenta iniciar el servicio detenido.
#>
param(
    [switch]$TryStart
)

$ErrorActionPreference = 'Continue'

function Find-PostgresService {
    Get-Service -ErrorAction SilentlyContinue | Where-Object {
        $n = $_.Name.ToLower()
        $d = $_.DisplayName.ToLower()
        $n -like '*postgresql*' -or $d -like '*postgresql*'
    }
}

$services = @(Find-PostgresService)
if ($services.Count -eq 0) {
    Write-Host "NO_POSTGRES_SERVICE: No se encontró un servicio de PostgreSQL."
    Write-Host "Instale PostgreSQL (scripts/install_postgresql_silent.ps1) o añada el binario al PATH."
    exit 2
}

$stopped = @($services | Where-Object { $_.Status -ne 'Running' })
if ($stopped.Count -gt 0 -and $TryStart) {
    foreach ($s in $stopped) {
        try {
            Start-Service -Name $s.Name -ErrorAction Stop
            Write-Host "Servicio iniciado: $($s.Name)"
        } catch {
            Write-Warning "No se pudo iniciar $($s.Name): $_"
        }
    }
    $services = @(Find-PostgresService)
}

$stillDown = @($services | Where-Object { $_.Status -ne 'Running' })
if ($stillDown.Count -gt 0) {
    Write-Host "POSTGRES_STOPPED: Servicios PostgreSQL no en ejecución:"
    $stillDown | ForEach-Object { Write-Host " - $($_.Name) ($($_.Status))" }
    exit 3
}

Write-Host "PostgreSQL OK. Servicios en ejecución:"
$services | Where-Object { $_.Status -eq 'Running' } | ForEach-Object { Write-Host " - $($_.Name)" }
exit 0
