# Descarga Python embeddable para Windows x64, habilita pip e instala backend/requirements.txt
# en desktop/resources/python/ para empaquetarlo con electron-builder.
# Uso (PowerShell, desde cualquier carpeta):
#   .\scripts\setup_embedded_python.ps1
# Opcional: -Force para volver a descargar y reinstalar paquetes

param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PyDir = Join-Path $RepoRoot 'desktop\resources\python'
$ReqFile = Join-Path $RepoRoot 'backend\requirements.txt'

$PythonVersion = '3.11.9'
$EmbedZipName = "python-$PythonVersion-embed-amd64.zip"
$EmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/$EmbedZipName"

if (-not (Test-Path $ReqFile)) {
    Write-Error "No se encuentra requirements.txt en: $ReqFile"
}

if ((Test-Path (Join-Path $PyDir 'python.exe')) -and -not $Force) {
    Write-Host "Ya existe desktop\resources\python\python.exe. Use -Force para reinstalar." -ForegroundColor Yellow
    exit 0
}

Write-Host "Descargando Python embeddable $PythonVersion (amd64)..." -ForegroundColor Cyan
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "gym_zt_sis_embed_py_$(Get-Random)"
New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
$ZipPath = Join-Path $TempRoot $EmbedZipName

try {
    Invoke-WebRequest -Uri $EmbedUrl -OutFile $ZipPath -UseBasicParsing

    if (Test-Path $PyDir) {
        Remove-Item -Path $PyDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $PyDir -Force | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $PyDir -Force

    $PthFile = Get-ChildItem -Path $PyDir -Filter 'python*._pth' | Select-Object -First 1
    if (-not $PthFile) {
        Write-Error "No se encontró python*._pth en la extracción."
    }
    $PthPath = $PthFile.FullName
    $raw = [System.IO.File]::ReadAllText($PthPath)
    if ($raw.Length -gt 0 -and [int][char]$raw[0] -eq 0xFEFF) {
        $raw = $raw.Substring(1)
    }
    $lines = $raw -split "`r?`n"
    $out = foreach ($line in $lines) {
        if ($line -match '^#\s*import site\s*$') { 'import site' } else { $line }
    }
    $joined = ($out -join "`r`n").TrimEnd() + "`r`n"
    if ($joined -notmatch '(?m)^import site\s*$') {
        $joined = $joined.TrimEnd() + "`r`nimport site`r`n"
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($PthPath, $joined, $utf8NoBom)

    $PyExe = Join-Path $PyDir 'python.exe'
    $prevHome = $env:PYTHONHOME
    Remove-Item Env:\PYTHONHOME -ErrorAction SilentlyContinue

    Write-Host "Instalando pip..." -ForegroundColor Cyan
    $GetPip = Join-Path $TempRoot 'get-pip.py'
    Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $GetPip -UseBasicParsing
    & $PyExe $GetPip --no-warn-script-location

    Write-Host "Instalando dependencias del backend (puede tardar)..." -ForegroundColor Cyan
    & $PyExe -m pip install --no-warn-script-location -r $ReqFile

    if ($null -ne $prevHome) { $env:PYTHONHOME = $prevHome }

    Write-Host "`nListo: $PyDir" -ForegroundColor Green
    Write-Host "Ejecute desde desktop\: npm run dist" -ForegroundColor Green
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Path $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
