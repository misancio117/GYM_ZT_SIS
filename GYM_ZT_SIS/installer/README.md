# Empaquetado comercial — GYM ZT SIS

Este directorio documenta cómo generar el instalador **Windows (.exe)** con **electron-builder** y qué debe incluir un paquete listo para distribución.

## Prerrequisitos en la máquina de build

1. **Node.js** LTS (18 o 20) y npm.
2. **Python** 3.10+ con `pip` (para probar el backend antes del empaquetado).
3. **PostgreSQL** no es obligatorio en la máquina de *build*; el cliente final sí lo tendrá instalado o lo instalará con los scripts incluidos.

## Pasos recomendados

### 1. Backend Python

Desde la raíz del repositorio:

```powershell
.\scripts\setup_python_backend.ps1
```

Esto crea `.venv` e instala `backend/requirements.txt`.

### 2. Dependencias de Electron

```powershell
cd desktop
npm install
```

### 3. Python embebido (recomendado para equipos sin Python)

Automático (descarga 3.11.x embeddable, pip y `backend/requirements.txt`):

```powershell
.\scripts\setup_embedded_python.ps1
```

Salida: `desktop/resources/python/` (no se sube a Git; está en `.gitignore`).  
`desktop/package.json` ya incluye esa carpeta en `extraResources`; `npm run dist` comprueba que exista `python.exe` antes de empaquetar.

Manual alternativo: **Windows embeddable package** de python.org (x64), extraer en `desktop/resources/python/`, habilitar `import site` en `python*._pth`, `get-pip.py` y `pip install -r backend/requirements.txt`.

El `main.js` usa `resources/python/python.exe` cuando la app está empaquetada y ese archivo existe.

### 4. Instalador de PostgreSQL (offline)

Coloque el instalador oficial **EDB** `postgresql-*-windows-x64.exe` en `installer/resources/` y distribúyalo junto al producto, o ejecútelo desde un script de post-instalación. Los parámetros de ejemplo están en `scripts/install_postgresql_silent.ps1`.

Ajuste `--servicename` según la versión del instalador (consulte la documentación EDB).

### 5. Generar el instalador

```powershell
cd desktop
npm run dist
```

En Windows, si el build falla al extraer `winCodeSign` (enlaces simbólicos), el `package.json` ya usa `cross-env CSC_IDENTITY_AUTO_DISCOVERY=false` para omitir firma local. Alternativas: activar **Modo de desarrollador** en Windows (permite symlinks sin admin) o ejecutar el terminal como administrador la primera vez que electron-builder descache herramientas.

El artefacto queda en `dist/` (por ejemplo `GYM ZT SIS-Setup-1.0.0.exe`).

## Contenido empaquetado

- **extraResources `backend`**: copia del proyecto Django (sin `__pycache__`, sin `.env` del desarrollador).
- **Scripts**: carpeta `scripts/` para administración y PostgreSQL.
- **Electron**: `main.js` arranca `backend/run_server.py` con el intérprete resuelto (embebido o `python` del sistema).

## App ID y nombre

Definidos en `desktop/package.json`:

- **appId:** `com.misacorp.gym`
- **productName:** `GYM ZT SIS`

## Firma de código (opcional)

Para SmartScreen y distribución empresarial, firme el `.exe` con un certificado de código (Authenticode) mediante `signtool` o la integración de su proveedor CI/CD.
